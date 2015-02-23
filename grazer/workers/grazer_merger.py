# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import gc
import json
import socket

import boto
import boto.s3
import boto.s3.key
import psycopg2
from amqp import AMQPError
from boto.exception import S3ResponseError, BotoServerError

from grazer.model.model_constants import *
from grazer.model.utils import csv_header
from grazer.model.mq_merger_request import MqMergerRequest
from grazer.model.scrape_state import ScrapeState
from grazer.model.scrape_content import ScrapeContent
from grazer.system.performance_tracker import MergerTracker

from synergy.conf import settings
from synergy.workers.abstract_mq_worker import AbstractMqWorker
from synergy.system.time_qualifier import QUALIFIER_REAL_TIME
from synergy.system import time_helper
from synergy.system.utils import fully_qualified_table_name, create_s3_file_uri, break_s3_file_uri
from synergy.mq.flopsy import Consumer, PublishersPool

# parameter {0}: defines target table_name
# parameter {1}: defines list of column; same as CSV header
# parameter {2}: defines manifest file with log files for the table
# parameter {3}: defines aws access key id
# parameter {4}: defines aws access secret key
RED_SHIFT_COPY_COMMAND = ("COPY {0} ({1}) FROM '{2}' "
                          "CREDENTIALS 'aws_access_key_id={3};aws_secret_access_key={4}' "
                          "MANIFEST CSV IGNOREBLANKLINES TRIMBLANKS "
                          "DELIMITER ',' "
                          "QUOTE AS '''' "
                          "NULL AS 'null' "
                          # "MAXERROR AS 100 "
                          "IGNOREHEADER AS 1;")

# parameter {0}: defines target table_name. anticipated value: ext.tbl_scrape_content
# parameter {1}: defines source table_name. anticipated value: ext.temp_scrape_content
SQL_INSERT_APP = ("INSERT INTO {0} (package, "
                  "    platform, "
                  "    application_id, "
                  "    title, "
                  "    primary_category, "
                  "    category_string, "
                  "    description, "
                  "    creator, "
                  "    seller, "
                  "    view_url, "
                  "    cover_art_url, "
                  "    version, "
                  "    price, "
                  "    rating, "
                  "    rating_count, "
                  "    release_date, "
                  "    updated_at) "
                  "SELECT DISTINCT "
                  "    src.package_name, "  # package
                  "    src.platform, "      # platform
                  "    src.entry_id, "      # application_id
                  "    src.title, "         # title
                  "    src.category, "      # primary_category
                  "    src.category_path, "  # category_string
                  "    src.description, "   # description
                  "    src.developer, "     # creator
                  "    src.seller, "        # seller
                  "    src.package_url, "   # view_url
                  "    src.cover_url, "     # cover_art_url
                  "    src.version, "       # version
                  "    src.price, "         # price
                  "    src.rating, "        # rating
                  "    src.rating_count, "  # rating_count
                  "    src.release_date, "  # release_date
                  "    src.last_updated "   # updated_at
                  "FROM {1} AS src "
                  "LEFT JOIN {0} AS ref "
                  "    ON ref.package = src.package_name "
                  "    AND ref.platform = src.platform "
                  "WHERE ref.package IS NULL "
                  "    AND ref.platform IS NULL ")

# parameter {0}: defines target table_name. anticipated value: ext.tbl_scrape_content
# parameter {1}: defines source table_name. anticipated value: ext.temp_scrape_content
SQL_UPDATE_APP = ("UPDATE {0} SET "
                  "    application_id = "
                  "    CASE WHEN (src.entry_id IS NOT NULL AND src.entry_id != 'unknown') "
                  "    THEN src.entry_id "
                  "    ELSE {0}.application_id "
                  "    END, "
                  "    title = "
                  "    CASE WHEN (src.title IS NOT NULL AND src.title != 'unknown') "
                  "    THEN src.title "
                  "    ELSE {0}.title "
                  "    END, "
                  "    primary_category = "
                  "    CASE WHEN (src.category IS NOT NULL AND src.category != 'unknown') "
                  "    THEN src.category "
                  "    ELSE {0}.primary_category "
                  "    END, "
                  "    category_string = "
                  "    CASE WHEN (src.category_path IS NOT NULL AND src.category_path != 'unknown') "
                  "    THEN src.category_path "
                  "    ELSE {0}.category_string "
                  "    END, "
                  "    description = "
                  "    CASE WHEN (src.description IS NOT NULL AND src.description != 'unknown') "
                  "    THEN src.description "
                  "    ELSE {0}.description "
                  "    END, "
                  "    creator = "
                  "    CASE WHEN (src.developer IS NOT NULL AND src.developer != 'unknown') "
                  "    THEN src.developer "
                  "    ELSE {0}.creator "
                  "    END, "
                  "    seller = "
                  "    CASE WHEN (src.seller IS NOT NULL AND src.seller != 'unknown') "
                  "    THEN src.seller "
                  "    ELSE {0}.seller "
                  "    END, "
                  "    view_url = "
                  "    CASE WHEN (src.package_url IS NOT NULL AND src.package_url != 'unknown') "
                  "    THEN src.package_url "
                  "    ELSE {0}.view_url "
                  "    END, "
                  "    cover_art_url = "
                  "    CASE WHEN (src.cover_url IS NOT NULL AND src.cover_url != 'unknown') "
                  "    THEN src.cover_url "
                  "    ELSE {0}.cover_art_url "
                  "    END, "
                  "    version = "
                  "    CASE WHEN (src.version IS NOT NULL AND src.version != 'unknown') "
                  "    THEN src.version "
                  "    ELSE {0}.version "
                  "    END, "
                  "    price = "
                  "    CASE WHEN (src.price IS NOT NULL AND src.price != 'unknown') "
                  "    THEN src.price "
                  "    ELSE {0}.price "
                  "    END, "
                  "    rating = "
                  "    CASE WHEN (src.rating IS NOT NULL AND src.rating != 'unknown') "
                  "    THEN src.rating "
                  "    ELSE {0}.rating "
                  "    END, "
                  "    rating_count = "
                  "    CASE WHEN (src.rating_count IS NOT NULL AND src.rating_count != 'unknown') "
                  "    THEN src.rating_count "
                  "    ELSE {0}.rating_count "
                  "    END, "
                  "    updated_at = src.last_updated "          # updated_at
                  "FROM {1} AS src "
                  "WHERE {0}.package = src.package_name "
                  "    AND {0}.platform = src.platform "
                  "    AND {0}.package IS NOT NULL "
                  "    AND {0}.platform IS NOT NULL ")

# parameter {0}: defines target table_name. anticipated value: ext.tbl_scrape_state
# parameter {1}: defines source table_name. anticipated value: ext.temp_scrape_state
SQL_UPDATE_APP_PACKAGE_STATE = ("UPDATE {0} SET "
                                "    package_name = src.package_name, "
                                "    platform = src.platform, "
                                "    store_url = src.store_url, "
                                "    scrape_state = src.scrape_state, "
                                "    scrape_url = src.scrape_url, "
                                "    scrape_http_code = src.scrape_http_code, "
                                "    last_updated = src.last_updated "
                                "FROM {1} AS src "
                                "WHERE {0}.package_name = src.package_name "
                                "    AND {0}.platform = src.platform "
                                "    AND {0}.package_name IS NOT NULL "
                                "    AND {0}.platform IS NOT NULL ")


class Merger(AbstractMqWorker):
    """
    this class receives merge requests, aggregates them into manifest files and execute COPY, MERGE on RedShift
    """

    def __init__(self, process_name):
        super(Merger, self).__init__(process_name)
        self.publishers = PublishersPool(self.logger)
        self.aggregated_requests = list()

        try:
            self.s3_connection = boto.connect_s3(settings.settings['aws_access_key_id'],
                                                 settings.settings['aws_secret_access_key'])
            self.s3_bucket = self.s3_connection.get_bucket(settings.settings['aws_s3_bucket'])
        except S3ResponseError as e:
            self.logger.error('AWS Credentials are NOT valid. Terminating.', exc_info=True)
            raise ValueError(e)

    def __del__(self):
        try:
            self._flush_aggregated_objects()
        except Exception:
            self.logger.error('Error while flushing aggregated objects', exc_info=True)

        try:
            self.logger.info('Closing Flopsy Publishers Pool...')
            self.publishers.close()
        except Exception as e:
            self.logger.error('Exception caught while closing Flopsy Publishers Pool: %s' % str(e))

        try:
            self.logger.info('Closing S3 Connection...')
            self.s3_connection.close()
        except Exception as e:
            self.logger.error('Exception caught while closing S3 Connection: %s' % str(e))

        super(Merger, self).__del__()

    def _init_performance_ticker(self, logger):
        self.performance_ticker = MergerTracker(logger)
        self.performance_ticker.start()

    def _flush_aggregated_objects(self):
        """ create a manifest file, execute:
          1. SQL Truncate temp_scrape_content
          2. SQL Truncate temp_scrape_state
          3. RedShift COPY
          4. SQL Merge temporary temp_scrape_content into ext.tbl_scrape_content
          5. SQL Merge temporary temp_scrape_state into ext.tbl_scrape_state
        """
        if len(self.aggregated_requests) == 0:
            # nothing to do
            return None

        self.logger.info('Performing flush of %d aggregated Merge Requests.' % len(self.aggregated_requests))
        current_timestamp = time_helper.actual_timeperiod(QUALIFIER_REAL_TIME)
        self.truncate_table(TABLE_TEMP_SCRAPE_STATE)
        manifest_uri_1 = self.perform_copy_command(current_timestamp, TABLE_TEMP_SCRAPE_STATE)

        self.truncate_table(TABLE_TEMP_SCRAPE_CONTENT)
        manifest_uri_2 = self.perform_copy_command(current_timestamp, TABLE_TEMP_SCRAPE_CONTENT)

        fqtn_app = fully_qualified_table_name(TABLE_SCRAPE_CONTENT)
        fqtn_tmp_scrape_content = fully_qualified_table_name(TABLE_TEMP_SCRAPE_CONTENT)
        fqtn_scrape_state = fully_qualified_table_name(TABLE_SCRAPE_STATE)
        fqtn_tmp_scrape_state = fully_qualified_table_name(TABLE_TEMP_SCRAPE_STATE)

        self.execute_sql(SQL_UPDATE_APP.format(fqtn_app, fqtn_tmp_scrape_content), 'UPDATE EXISTING APPS %s' % fqtn_app)
        self.execute_sql(SQL_INSERT_APP.format(fqtn_app, fqtn_tmp_scrape_content), 'INSERT NEW APPS INTO %s' % fqtn_app)
        self.execute_sql(SQL_UPDATE_APP_PACKAGE_STATE.format(fqtn_scrape_state, fqtn_tmp_scrape_state),
                         'UPDATE APP_PACKAGE_STATE %s' % fqtn_scrape_state)

        self.clean_s3_footprint([manifest_uri_1, manifest_uri_2])

        del self.aggregated_requests
        self.aggregated_requests = list()
        gc.collect()

    def _init_mq_consumer(self):
        self.consumer = Consumer(self.queue_source)

    def clean_s3_footprint(self, manifest_uris):
        """ iterates over the aggregated requests and removes all files it reference from the S3
          Also, manifest file is removed """
        s3_file_uris = []
        s3_file_uris.extend(manifest_uris)
        for request in self.aggregated_requests:
            s3_file_uris.append(request.s3_scrape_file)
            s3_file_uris.append(request.s3_app_package_file)

        for s3_file_uri in s3_file_uris:
            try:
                s3_key = boto.s3.key.Key(self.s3_bucket)
                s3_key.key = break_s3_file_uri(s3_file_uri)[1]
                s3_key.delete()
                self.logger.error('S3 clean-up: successfully removed file: %s' % s3_file_uri)
            except Exception as e:
                self.logger.error('Exception on removing S3 Key: %s due to: %s' % (s3_file_uri, str(e)))
        self.logger.error('S3 clean-up: completed')

    def truncate_table(self, table_name):
        truncate_command = 'TRUNCATE TABLE %s' % fully_qualified_table_name(table_name)
        self.execute_sql(truncate_command, 'TRUNCATE')

    def _get_manifest_file_content(self, table_name):
        """ returns JSON dictionary in format
        {
            "entries": [
                {"url":"s3://mybucket-alpha/custdata.1","mandatory":True},
                {"url":"s3://mybucket-alpha/custdata.2","mandatory":True},
            ]
        }
        """
        content = dict()
        content[MANIFEST_ENTRIES] = list()
        for request in self.aggregated_requests:
            if table_name == TABLE_TEMP_SCRAPE_CONTENT:
                file_name = request.s3_scrape_file
            elif table_name == TABLE_TEMP_SCRAPE_STATE:
                file_name = request.s3_app_package_file
            else:
                raise ValueError('Not supported table_name %s' % table_name)

            content[MANIFEST_ENTRIES].append({ENTRY_URL: file_name, ENTRY_MANDATORY: True})
        return content

    def _get_table_headers(self, table_name):
        """ returns comma-separated list of CSV file column names """
        if table_name == TABLE_TEMP_SCRAPE_CONTENT:
            return csv_header(ScrapeState) + ',' + csv_header(ScrapeContent)
        elif table_name == TABLE_TEMP_SCRAPE_STATE:
            return csv_header(ScrapeState)
        else:
            raise ValueError('Not supported table_name %s' % table_name)

    def _create_manifest_file(self, timeperiod, table_name):
        """method prepares manifest file for every table in RedShift that will be updated during the COPY command
        COPY command manifest file lists all files that should be loaded into RedShift's specific table
        format of the manifest file is following:
        {
            "entries": [
                {"url":"s3://mybucket-alpha/custdata.1","mandatory":true},
                {"url":"s3://mybucket-alpha/custdata.2","mandatory":true},
                {"url":"s3://mybucket-beta/custdata.1","mandatory":false}
            ]
        }
        @see http://docs.aws.amazon.com/redshift/latest/dg/r_COPY.html

        manifest file is then placed into S3 under following path:
        s3://grazer-scrapes/manifests/YYYYMMDDmmHHSS-table_name.manifest
        """
        manifest_folder_name = 'manifests'
        manifest_file_name = '%s-%s.manifest' % (timeperiod, table_name)
        s3_manifest_file_url = create_s3_file_uri(settings.settings['aws_s3_bucket'],
                                                  manifest_folder_name,
                                                  manifest_file_name)

        json_content = self._get_manifest_file_content(table_name)
        s3_key = boto.s3.key.Key(self.s3_bucket)
        s3_key.key = manifest_folder_name + '/' + manifest_file_name
        s3_key.set_contents_from_string(string_data=json.dumps(json_content))
        return s3_manifest_file_url

    def perform_copy_command(self, timeperiod, table_name):
        """ executes copy command:
        1. create manifest file
        2. create DB connection to the RedShift
        3. execute COPY command """

        manifest_file_uri = self._create_manifest_file(timeperiod, table_name)

        copy_command = RED_SHIFT_COPY_COMMAND.format(fully_qualified_table_name(table_name),
                                                     self._get_table_headers(table_name),
                                                     manifest_file_uri,
                                                     settings.settings['aws_access_key_id'],
                                                     settings.settings['aws_secret_access_key'])

        self.logger.info('Executing COPY command \n<%s>\n against redshift instance: %s.'
                         % (copy_command, settings.settings['aws_redshift_db']))
        self.execute_sql(copy_command, 'COPY')
        return manifest_file_uri

    def execute_sql(self, sql_statement, command_name):
        with psycopg2.connect(host=settings.settings['aws_redshift_host'],
                              database=settings.settings['aws_redshift_db'],
                              user=settings.settings['aws_redshift_user'],
                              password=settings.settings['aws_redshift_password'],
                              port=settings.settings['aws_redshift_port']) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql_statement)
                    self.logger.info('%s command SUCCESS. Status message: %s' % (command_name, cursor.statusmessage))
                except Exception:
                    self.logger.error('%s command FAILED.' % command_name, exc_info=True)
                    raise

    # ********************** abstract methods ****************************
    def _mq_callback(self, message):
        """ wraps call of abstract method with try/except
        in case exception breaks the abstract method, this method:
        - catches the exception
        - logs the exception"""
        try:
            mq_merger_request = MqMergerRequest.from_json(message.body)
            self.aggregated_requests.append(mq_merger_request)
            self.performance_ticker.android.increment_success(mq_merger_request.stat_android_success)
            self.performance_ticker.android.increment_failure(mq_merger_request.stat_android_failure)

            if len(self.aggregated_requests) >= settings.settings['merge_bulk_threshold']:
                self._flush_aggregated_objects()

            self.consumer.acknowledge(message.delivery_tag)
            self.performance_ticker.inbox.increment_success()
        except (KeyError, IndexError) as e:
            self.logger.error('Error is considered Unrecoverable: %r\nCancelled message: %r' % (e, message.body))
            self.consumer.cancel(message.delivery_tag)
            self.performance_ticker.inbox.increment_failure()
        except Exception as e:
            self.logger.error('Error is considered Recoverable: %r\nRe-queueing message: %r' % (e, message.body))
            self.consumer.reject(message.delivery_tag)
            self.performance_ticker.inbox.increment_failure()

    def _run_mq_listener(self):
        try:
            self.consumer.register(self._mq_callback)
            while self.consumer.is_running:
                try:
                    self.consumer.wait(settings.settings['mq_timeout_sec'] / 2)
                except socket.timeout:
                    # reaching this point, means that no new Merge Requests have been received in N minutes
                    if len(self.aggregated_requests) == 0:
                        log_message = 'Queue %s is likely empty. Worker is idle until next merge request arrives' \
                                      % self.consumer.queue
                    else:
                        log_message = 'Queue %s is likely empty. Flushing accumulated merge requests' \
                                      % self.consumer.queue

                    self.logger.warn(log_message)
                    self._flush_aggregated_objects()

        except (AMQPError, IOError) as e:
            self.logger.error('AMQPError: %s' % str(e))
        except BotoServerError as e:
            self.logger.error('BotoServerError: %s' % str(e))
        finally:
            self.__del__()
            self.logger.info('Exiting main thread. All auxiliary threads stopped.')


if __name__ == '__main__':
    from constants import PROCESS_GRAZER_MERGER

    worker = Merger(PROCESS_GRAZER_MERGER)
    worker.start()
