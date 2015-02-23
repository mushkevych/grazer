# -*- coding: utf-8 -*-
__author__ = 'Nadir Merchant'

import unittest

from opstools.settings import settings as ops_settings
import boto.ec2

from settings import enable_test_mode
enable_test_mode()

from tests.base_fixtures import TestMessage
from tests.test_abstract_worker import get_test_aggregator
from tests import base_fixtures
from synergy.system import time_helper
from synergy.system.time_qualifier import QUALIFIER_DAILY
from synergy.db.dao.unit_of_work_dao import UnitOfWorkDao
from synergy.conf import settings
from grazer.workers.grazer_hatchery import GrazerHatchery
from constants import PROCESS_GRAZER_CONTENT_SCRAPER
from tests.ut_context import PROCESS_UNIT_TEST


class GrazerHatcheryWorker(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(GrazerHatcheryWorker, self).__init__(methodName)
        self.conn = None
        self.conn = boto.ec2.connect_to_region(ops_settings['REGION'],
                                               aws_access_key_id=ops_settings['AWS_KEY_ID'],
                                               aws_secret_access_key=ops_settings['AWS_SECRET_KEY'])
        self.parameters = [self.conn,
                           settings.settings['grazer_worker_ami'],
                           settings.settings['grazer_worker_size'],
                           ['bluewhale', 'grazer_security'],
                           1,
                           settings.settings['grazer_worker_environment'],
                           settings.settings['grazer_worker_google']]

    def setUp(self):
        # creating unit_of_work entity, requesting to process created above statistics
        self.uow_id = base_fixtures.create_and_insert_unit_of_work(process_name=PROCESS_UNIT_TEST,
                                                                   start_id=0,
                                                                   end_id=1,
                                                                   timeperiod=time_helper.
                                                                   actual_timeperiod(QUALIFIER_DAILY))

        self.worker = get_test_aggregator(GrazerHatchery, PROCESS_GRAZER_CONTENT_SCRAPER)

    def tearDown(self):
        uow_dao = UnitOfWorkDao(self.worker.logger)
        uow_dao.remove(self.uow_id)

        for instance in self.worker.instances:
            self.conn.stop_instances(instance.id)

        # killing the worker
        del self.worker

    def test_execution(self):
        message = TestMessage()
        message.body = str(self.uow_id)
        self.worker._mq_callback(message)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
