# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import datetime
import psycopg2

from synergy.conf import settings, context
from synergy.mq.flopsy import PublishersPool, purge_mq_queue
from synergy.workers.abstract_mq_worker import AbstractMqWorker
from synergy.system.utils import fully_qualified_table_name
from grazer.model.model_constants import *
from grazer.model.scrape_state import ScrapeState
from grazer.system.performance_tracker import PackageManagerTracker

# parameter {0}: defines scrape_state table name. anticipated value: ext.tbl_scrape_state
SQL_NEW_PACKAGES_TO_PROCESS = ("SELECT package_name, platform, store_url, scrape_state, scrape_url, "
                               "    scrape_http_code, last_updated "
                               "FROM {0} "
                               "WHERE scrape_state = 'STATE_EMBRYO' ")

# parameter {0}: defines scrape_state table name. anticipated value: ext.tbl_scrape_state
SQL_PACKAGES_TO_REPROCESS = ("SELECT package_name, platform, store_url, scrape_state, scrape_url, "
                             "    scrape_http_code, last_updated "
                             "FROM {0} "
                             "WHERE scrape_state IN ('STATE_SUCCESS', 'STATE_RESCRAPE_FAILURE', 'STATE_FAILURE') "
                             "    AND last_updated < GETDATE() - INTERVAL '180 days' "
                             "OR scrape_state = 'STATE_FAILURE' "
                             "    AND scrape_http_code IN (403, 500, 503, 522, 999) "
                             "ORDER BY package_name ")


class GrazerManager(AbstractMqWorker):
    def __init__(self, process_name):
        super(GrazerManager, self).__init__(process_name)
        self.publishers = PublishersPool(self.logger)
        self.queue_sink = context.process_context[self.process_name].sink

    def __del__(self):
        try:
            self.logger.info('Closing Flopsy Publishers Pool...')
            self.publishers.close()
        except Exception as e:
            self.logger.error('Exception caught while closing Flopsy Publishers Pool: %s' % str(e))

        super(GrazerManager, self).__del__()

    def _init_performance_ticker(self, logger):
        # notice - we are not starting the thread. only creating an instance
        self.performance_ticker = PackageManagerTracker(logger)
        self.performance_ticker.start()

    def _db_row_to_model(self, row):
        dt_obj = row[6]
        if isinstance(dt_obj, datetime.datetime):
            dt_obj = dt_obj.strftime(TIMESTAMP_FORMAT)

        scrape_state = ScrapeState()
        scrape_state.package_name = row[0]
        scrape_state.platform = row[1]
        scrape_state.store_url = row[2]
        scrape_state.scrape_state = row[3]
        scrape_state.scrape_url = row[4]
        scrape_state.scrape_http_code = row[5]
        scrape_state.last_updated = dt_obj
        return scrape_state

    def _publish_requests(self, db_rows, tracker):
        publisher = self.publishers.get(self.queue_sink)
        for row in db_rows:
            scrape_state = self._db_row_to_model(row)
            publisher.publish(scrape_state.to_json())
            tracker.increment_success()

    def execute_query(self, sql_query, tracker):
        with psycopg2.connect(host=settings.settings['aws_redshift_host'],
                              database=settings.settings['aws_redshift_db'],
                              user=settings.settings['aws_redshift_user'],
                              password=settings.settings['aws_redshift_password'],
                              port=settings.settings['aws_redshift_port']) as conn:
            with conn.cursor() as cursor:
                try:
                    total_counter = 0
                    cursor.execute(sql_query)
                    rows = cursor.fetchmany(settings.settings['sql_bulk_threshold'])
                    while rows:
                        total_counter += len(rows)
                        self._publish_requests(rows, tracker)
                        rows = cursor.fetchmany(settings.settings['sql_bulk_threshold'])

                    self.logger.info('SELECT command SUCCESSFUL. Published %d package names. Status message: %s'
                                     % (total_counter, cursor.statusmessage))
                except Exception:
                    self.logger.error('SELECT command FAILED. SQL = %s' % sql_query, exc_info=True)

    def run(self):
        # purge any left-overs from the previous run
        purge_mq_queue(self.queue_sink)

        try:
            self.execute_query(SQL_NEW_PACKAGES_TO_PROCESS.format(fully_qualified_table_name(TABLE_SCRAPE_STATE)),
                               self.performance_ticker.new_packages)
            self.execute_query(SQL_PACKAGES_TO_REPROCESS.format(fully_qualified_table_name(TABLE_SCRAPE_STATE)),
                               self.performance_ticker.reprocess)
            self.logger.info('Completed scope of the run. Exiting.')
        finally:
            self.__del__()
            self.logger.info('Exiting main thread. All auxiliary threads stopped.')


if __name__ == '__main__':
    from constants import PROCESS_GRAZER_MANAGER

    worker = GrazerManager(PROCESS_GRAZER_MANAGER)
    worker.start()
