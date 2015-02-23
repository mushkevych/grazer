# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from synergy.system.performance_tracker import SimpleTracker


# pylint: disable=E1002
def get_test_worker(base_class, process_name, tracker_class=SimpleTracker):
    class TestWorker(base_class):
        def __init__(self, pn):
            super(TestWorker, self).__init__(pn)

        def _init_mq_consumer(self):
            self.consumer = TestConsumer()

        def _init_performance_ticker(self, logger):
            # notice - we are not starting the thread. only creating an instance
            self.performance_ticker = tracker_class(logger)

    return TestWorker(process_name)


class TestConsumer(object):
    """ empty class that should substitute MQ Flopsy Consumer. Used for testing only """

    def acknowledge(self, delivery_tag):
        pass

    def close(self):
        pass

    def reject(self, delivery_tag):
        pass

    def cancel(self, delivery_tag):
        pass


class TestMessage(object):
    """ empty class that should substitute MQ Message. Used for testing only """

    def __init__(self):
        self.body = None
        self.delivery_tag = None
