# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import gc
import socket
import boto
import boto.s3
import boto.s3.key
from boto.exception import S3ResponseError

from grazer.model.utils import csv_header, csv_line
from grazer.model.mq_scrape_wrapper import MqScrapeWrapper
from grazer.model.scrape_state import ScrapeState
from grazer.model.model_constants import *
from grazer.model.mq_merger_request import MqMergerRequest
from grazer.model.scrape_content import ScrapeContent
from grazer.system.performance_tracker import ScrapeReducerTracker
from synergy.system import time_helper
from synergy.system.time_qualifier import QUALIFIER_REAL_TIME
from synergy.system.utils import create_s3_file_uri
from synergy.workers.abstract_mq_worker import AbstractMqWorker
from synergy.mq.flopsy import Consumer, PublishersPool
from synergy.conf import settings


class ScrapeReducer(AbstractMqWorker):
    """ Module receives scraped content from the MQ and dumps it into S3 filesystem """

    def __init__(self, process_name):
        super(ScrapeReducer, self).__init__(process_name)
        self.publishers = PublishersPool(self.logger)
        self.fqdn = socket.getfqdn()
        self.aggregated_scrape_states = list()
        self.aggregated_scrape_contents = list()
        self.stat_apple_success = 0
        self.stat_apple_failure = 0
        self.stat_android_success = 0
        self.stat_android_failure = 0

        try:
            self.s3_connection = boto.connect_s3(settings.settings['aws_access_key_id'],
                                                 settings.settings['aws_secret_access_key'])
            self.s3_bucket = self.s3_connection.get_bucket(settings.settings['aws_s3_bucket'])
        except S3ResponseError as e:
            self.logger.error('AWS Credentials are NOT valid. Terminating.', exc_info=True)
            raise ValueError(e)

    def __del__(self):
        self._flush_aggregated_objects()

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

        super(ScrapeReducer, self).__del__()

    def _init_performance_ticker(self, logger):
        # notice - we are not starting the thread. only creating an instance
        self.performance_ticker = ScrapeReducerTracker(logger)
        self.performance_ticker.start()

    def _init_mq_consumer(self):
        self.consumer = Consumer(self.queue_source)

    # ********************** abstract methods ****************************
    def _flush_aggregated_objects(self):
        s3_file_scrape_state = self._flush_collection(self.aggregated_scrape_states,
                                                      TABLE_TEMP_SCRAPE_STATE,
                                                      csv_header(ScrapeState))
        del self.aggregated_scrape_states
        self.aggregated_scrape_states = list()
        self.performance_ticker.meta.increment_success()

        s3_file_scrape_content = self._flush_collection(self.aggregated_scrape_contents,
                                                        TABLE_TEMP_SCRAPE_CONTENT,
                                                        csv_header(ScrapeState) + ',' + csv_header(ScrapeContent))
        del self.aggregated_scrape_contents
        self.aggregated_scrape_contents = list()
        self.performance_ticker.scrape.increment_success()

        if s3_file_scrape_state is not None or s3_file_scrape_content is not None:
            request = MqMergerRequest()
            request.s3_file_scrape_state = s3_file_scrape_state
            request.s3_file_scrape_content = s3_file_scrape_content
            request.stat_android_success = self.stat_android_success
            request.stat_android_failure = self.stat_android_failure

            publisher = self.publishers.get(self.queue_sink)
            publisher.publish(request.document)

        self.stat_android_success = 0
        self.stat_android_failure = 0
        gc.collect()

    def _flush_collection(self, collection, target_folder_name, csv_header):
        """ method puts aggregated objects into S3
            @return URI of the created file in the S3 """
        if len(collection) == 0:
            # nothing to do
            return None

        self.logger.info('Performing flush for: %d %s.' % (len(collection), target_folder_name))

        content = csv_header + '\n'
        content += '\n'.join(collection)

        s3_file_name = '%s-%s.csv' % (time_helper.actual_timeperiod(QUALIFIER_REAL_TIME),
                                      self.fqdn)
        s3_file_uri = create_s3_file_uri(settings.settings['aws_s3_bucket'],
                                         target_folder_name,
                                         s3_file_name)
        s3_key = boto.s3.key.Key(self.s3_bucket)
        s3_key.key = target_folder_name + '/' + s3_file_name
        s3_key.set_contents_from_string(string_data=content)
        return s3_file_uri

    def _process_stat_counters(self, mq_scrape_wrapper):
        assert isinstance(mq_scrape_wrapper, MqScrapeWrapper)
        if mq_scrape_wrapper.scrape_state_doc.platform == PLATFORM_ANDROID:
            if mq_scrape_wrapper.scrape_state_doc.scrape_state == STATE_SUCCESS:
                self.stat_android_success += 1
            else:
                self.stat_android_failure += 1
        else:
            self.logger.warn('Unknown platform %s. Could not update stat counters.'
                             % mq_scrape_wrapper.scrape_state_doc.platform)

    def _mq_callback(self, message):
        try:
            mq_scrape_wrapper = MqScrapeWrapper.from_json(message.body)
            self._process_stat_counters(mq_scrape_wrapper)
            self.aggregated_scrape_states.append(csv_line(mq_scrape_wrapper.scrape_state_doc))

            if mq_scrape_wrapper.scrape_state_doc.scrape_state == STATE_SUCCESS \
                and mq_scrape_wrapper.scrape_content_doc is not None:
                # we skip those packages that has been marked as STATE_SUCCESS
                # because they were de-listed from known app stores
                self.aggregated_scrape_contents.append(csv_line(mq_scrape_wrapper.scrape_state_doc)
                                                       + ','
                                                       + csv_line(mq_scrape_wrapper.scrape_content_doc))

            threshold = settings.settings['csv_bulk_threshold']
            if len(self.aggregated_scrape_contents) >= threshold or len(self.aggregated_scrape_states) > threshold * 2:
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


if __name__ == '__main__':
    from constants import PROCESS_GRAZER_SCRAPE_REDUCER

    worker = ScrapeReducer(PROCESS_GRAZER_SCRAPE_REDUCER)
    worker.start()
