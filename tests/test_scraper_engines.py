# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import unittest
from unittest import TestCase

from mock import Mock

from constants import PROCESS_GRAZER_CONTENT_SCRAPER
from grazer.model.utils import csv_line
from grazer.model.model_constants import *
from grazer.model.mq_scrape_wrapper import MqScrapeWrapper
from grazer.system.performance_tracker import WebScraperTracker
from grazer.workers.scrape_post_processor import do_scrape_processing
from grazer.workers.content_scraper import ContentScraper, scrape_runner
from synergy.system.utils import unicode_truncate
from tests.utils import create_scrape_content
from tests.base_fixtures import get_test_worker, TestMessage


success_android_playstore = ['androidpixst.nyanya',
                             'apps.ignisamerica.batterysaver',
                             'com.mobibrick.games.balloonarchery',
                             'com.appgeneration.setimaapp',
                             'com.cptandroid',
                             'org.skinmonitor',
                             'com.rhamesgames.atoz',
                             'com.webclap.sweetstyle.sweetDigitalClockHappy']

failure_android_playstore = ['tr.a3.adblockplus',
                             'com.bing.mCalendar',
                             'iconnect.princess.sketch',
                             'com.mbower.www.doudizhuphone',
                             'com.languagecube.english.realcube_fb_B4',
                             'Quiz.U']


def _overridden_mq_callback(worker):
    def _wrapper(message):
        publisher = worker.publishers.get(worker.queue_sink)
        scrape_runner(message, worker.logger, publisher, worker.consumer, worker.performance_ticker)
    return _wrapper


class TestScraperEngines(TestCase):
    @classmethod
    def setUpClass(cls):
        import settings as module_settings
        module_settings.enable_test_mode()

    def setUp(self):
        super(TestScraperEngines, self).setUp()
        self.worker = get_test_worker(ContentScraper, PROCESS_GRAZER_CONTENT_SCRAPER, WebScraperTracker)
        self.worker._mq_callback = _overridden_mq_callback(self.worker)

        self.publisher_mock = Mock()
        publisher_pool_mock = Mock()
        publisher_pool_mock.get = Mock(return_value=self.publisher_mock)
        self.worker.publishers = publisher_pool_mock

    def tearDown(self):
        del self.worker
        super(TestScraperEngines, self).tearDown()

    # @unittest.skip('concentrate on one UT at a time')
    def test_android_success_packages(self):
        for package_name in success_android_playstore:
            message = TestMessage()
            message.body = {FIELD_PLATFORM: PLATFORM_ANDROID,
                            FIELD_PACKAGE_NAME: package_name}
            self.worker._mq_callback(message)

            json_obj = self.publisher_mock.publish.call_args_list[0][0][0]
            scrape_wrapper = MqScrapeWrapper.from_json(json_obj)
            self.assertTrue(scrape_wrapper.scrape_state_doc.scrape_state == STATE_SUCCESS,
                            'Valid package %s reported as FAILED' % package_name)

    @unittest.skip('concentrate on one UT at a time')
    def test_android_failure_packages(self):
        for package_name in failure_android_playstore:
            message = TestMessage()
            message.body = {FIELD_PLATFORM: PLATFORM_ANDROID,
                            FIELD_PACKAGE_NAME: package_name}
            self.worker._mq_callback(message)

            json_obj = self.publisher_mock.publish.call_args_list[0][0][0]
            scrape_wrapper = MqScrapeWrapper.from_json(json_obj)
            self.assertTrue(scrape_wrapper.scrape_state_doc.scrape_state == STATE_FAILURE,
                            'Mistakenly valid package %s with URL %s'
                            % (package_name, scrape_wrapper.scrape_state_doc.scrape_url))

    #@unittest.skip('concentrate on one UT at a time')
    def test_escaping(self):
        scrape_content = create_scrape_content()
        fixture = dict()
        fixture["short"] = "short"
        fixture[" (' "] = " ('' "
        fixture[" ('lalal\\'al') "] = " (''lalal\\''al'') "
        fixture[" ('tata\'ta') "] = " (''tata''ta'') "

        for k, v in fixture.iteritems():
            scrape_content.category = k
            self.assertTrue(v in csv_line(scrape_content), 'actual vs expected: %s vs %s' % (v, csv_line(scrape_content)))

    #@unittest.skip('concentrate on one UT at a time')
    def test_post_processing(self):
        scrape_content = create_scrape_content()
        fixture = dict()
        fixture[""] = UNKNOWN_VALUE
        fixture[NULL_VALUE] = UNKNOWN_VALUE
        fixture["short"] = "short"
        fixture[" first & second "] = "first & second"
        fixture[" first &amp; second "] = "first & second"
        fixture["first part - Android Apps on Google Play - second part"] = "first part - second part"

        for k, v in fixture.iteritems():
            scrape_content.category = k
            scrape_content = do_scrape_processing(scrape_content)
            self.assertTrue(v == scrape_content.category, 'actual vs expected: %s vs %s' % (v, scrape_content.category))

    #@unittest.skip('concentrate on one UT at a time')
    def test_date_formatting(self):
        scrape_content = create_scrape_content()

        fixture = dict()
        fixture["January 06, 2010"] = "2010-01-06 00:00:00"
        fixture["January 06, 2010"] = "2010-01-06 00:00:00"
        fixture["January 6, 2010"] = "2010-01-06 00:00:00"
        fixture["Jan 6, 2010"] = "2010-01-06 00:00:00"
        fixture["Jan 06, 2010"] = "2010-01-06 00:00:00"
        fixture["2010-01-06T02:25:59Z"] = "2010-01-06 02:25:59"
        fixture["2010-01-06 02:25:59"] = "2010-01-06 02:25:59"
        fixture["2010-06 02:25:59"] = NULL_VALUE
        fixture[NULL_VALUE] = NULL_VALUE
        fixture[None] = NULL_VALUE

        for k, v in fixture.iteritems():
            scrape_content.release_date = k
            scrape_content = do_scrape_processing(scrape_content)
            self.assertTrue(v == scrape_content.release_date, 'actual vs expected: %s vs %s' % (v, scrape_content.category))

    #@unittest.skip('concentrate on one UT at a time')
    def test_unicode_truncation(self):
        fixture = dict()
        fixture[u"абвгдеєжзиіїйклмнопрстуфхцчшщюяь"] = u"абвгдеєжзи"
        fixture[u"ウィキペディアにようこそ"] = u"ウィキペディ"
        fixture["abcdefghijklmnopqrstuvwxyz"] = "abcdefghijklmnopqrst"
        fixture["Jan 06, 2010"] = "Jan 06, 2010"

        for k, v in fixture.iteritems():
            actual = unicode_truncate(k, 20)
            self.assertTrue(actual == v, 'actual vs expected: %s vs %s' % (actual, v))

if __name__ == '__main__':
    unittest.main()
