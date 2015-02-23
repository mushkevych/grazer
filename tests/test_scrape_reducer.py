# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import boto
import boto.s3
import boto.s3.key

import unittest
from unittest import TestCase
from mock import Mock

from settings import settings
from grazer.model.model_constants import *
from grazer.model.mq_scrape_wrapper import MqScrapeWrapper
from grazer.model.mq_merger_request import MqMergerRequest
from grazer.system.performance_tracker import ScrapeReducerTracker
from grazer.workers.scrape_reducer import ScrapeReducer
from tests.utils import create_scrape_state, create_scrape_content
from tests.base_fixtures import get_test_worker, TestMessage
from constants import PROCESS_GRAZER_SCRAPE_REDUCER
from synergy.system.utils import break_s3_file_uri


class TestScrapeReducer(TestCase):
    @classmethod
    def setUpClass(cls):
        import settings as module_settings
        module_settings.enable_test_mode()

    def setUp(self):
        super(TestScrapeReducer, self).setUp()
        self.worker = get_test_worker(ScrapeReducer, PROCESS_GRAZER_SCRAPE_REDUCER, tracker_class=ScrapeReducerTracker)

        self.publisher_mock = Mock()
        publisher_pool_mock = Mock()
        publisher_pool_mock.get = Mock(return_value=self.publisher_mock)
        self.worker.publishers = publisher_pool_mock

    def tearDown(self):
        del self.worker
        super(TestScrapeReducer, self).tearDown()

    def test_processing(self):
        factor = 3
        for _ in range(0, settings['csv_bulk_threshold'] * factor):
            scrape_wrapper = MqScrapeWrapper()
            scrape_wrapper.scrape_state_doc = create_scrape_state()
            if scrape_wrapper.scrape_state_doc.scrape_state == STATE_SUCCESS:
                scrape_wrapper.scrape_content_doc = create_scrape_content()

            mq_message = TestMessage()
            mq_message.body = scrape_wrapper.document
            self.worker._mq_callback(mq_message)
        self.worker._flush_aggregated_objects()

        self.assertTrue(len(self.publisher_mock.publish.call_args_list) >= 2)
        for i in range(0, len(self.publisher_mock.publish.call_args_list)):
            json_obj = self.publisher_mock.publish.call_args_list[0][0][0]
            merge_request = MqMergerRequest(json_obj)

            # assert that files were created
            s3_key = boto.s3.key.Key(self.worker.s3_bucket)
            for file_name in [merge_request.s3_file_scrape_state, merge_request.s3_file_scrape_content]:
                s3_prefix, s3_file_key_name = break_s3_file_uri(file_name)

                manifest_s3_key = boto.s3.key.Key(bucket=s3_key.bucket, name=s3_file_key_name)
                self.assertTrue(manifest_s3_key.exists(), 'Manifest file %s was not found' % file_name)


if __name__ == '__main__':
    unittest.main()
