# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import time
import threading
from datetime import datetime

from synergy.conf import settings
from synergy.mq.flopsy import PublishersPool, Consumer
from synergy.workers.abstract_mq_worker import AbstractMqWorker
from grazer.system.performance_tracker import WebScraperTracker
from grazer.model.scrape_state import ScrapeState
from grazer.model.model_constants import *
# from grazer.model.mq_scrape_wrapper import MqScrapeWrapper
from workers.scraper_engine_amazon import ScraperEngineAmazon


def scrape_runner(message, logger, publisher, mq_consumer, performance_tracker):
    try:
        request = ScrapeState.from_json(message.body)
        if request.platform == PLATFORM_ANDROID:
            engines = [ScraperEngineAmazon(logger, request.package_name, request.platform)]
            tracker = performance_tracker.android
        else:
            raise ValueError('Platform %s is not supported' % request.platform)

        for engine in engines:
            response = engine.do_search()
            # assert isinstance(response, MqScrapeWrapper)
            if response.scrape_state_doc.scrape_state == STATE_SUCCESS:
                break

        # in case the package was successfully scraped in the past,
        # but now it has been de-listed from all known app_stores,
        # then only update the "last_update" field, so it is excluded from re-scrape list
        if request.scrape_state == STATE_SUCCESS \
                and response.scrape_state_doc.scrape_state == STATE_FAILURE:
            response.scrape_state_doc.scrape_state = STATE_RESCRAPE_FAILURE
            response.scrape_state_doc.store_url = request.store_url
            response.scrape_state_doc.scrape_url = request.scrape_url
            response.scrape_state_doc.scrape_http_code = request.scrape_http_code
            response.scrape_state_doc.platform = request.platform
            response.scrape_state_doc.package_name = request.package_name
            response.scrape_state_doc.last_updated = datetime.now().strftime(TIMESTAMP_FORMAT)

        publisher.publish(response.document)
        mq_consumer.acknowledge(message.delivery_tag)

        if response.scrape_content_doc is not None:
            tracker.increment_success()
            performance_tracker.total.increment_success()
        else:
            tracker.increment_failure()
            performance_tracker.total.increment_failure()
    except (KeyError, IndexError, ValueError) as e:
        logger.error('Error is considered Unrecoverable: %r\nCancelled message: %r' % (e, message.body))
        mq_consumer.cancel(message.delivery_tag)
        performance_tracker.total.increment_failure()
    except Exception as e:
        logger.error('Error is considered Recoverable: %r\nRe-queueing message: %r' % (e, message.body))
        mq_consumer.reject(message.delivery_tag)
        performance_tracker.total.increment_failure()
    finally:
        publisher.release()


class ContentScraper(AbstractMqWorker):
    """
    this class reads messages from RabbitMQ and scrapes requested app from App Store.
    scrapes impression is then published back to MQ for further processing
    """

    def __init__(self, process_name):
        super(ContentScraper, self).__init__(process_name)
        self.publishers = PublishersPool(self.logger)
        self.initial_thread_count = threading.active_count()

    def __del__(self):
        try:
            self.logger.info('Closing Flopsy Publishers Pool...')
            self.publishers.close()
        except Exception as e:
            self.logger.error('Exception caught while closing Flopsy Publishers Pool: %s' % str(e))

        super(ContentScraper, self).__del__()

    def _init_performance_ticker(self, logger):
        self.performance_ticker = WebScraperTracker(logger)
        self.performance_ticker.start()

    # ********************** abstract methods ****************************
    def _init_mq_consumer(self):
        self.consumer = Consumer(self.queue_source)

    def _mq_callback(self, message):
        while threading.active_count() > settings.settings['scrape_threads_count'] + self.initial_thread_count:
            time.sleep(0.01)

        publisher = self.publishers.get(self.queue_sink)
        t = threading.Thread(target=scrape_runner,
                             args=(message, self.logger, publisher, self.consumer, self.performance_ticker))
        t.daemon = True
        t.start()


if __name__ == '__main__':
    from constants import PROCESS_GRAZER_CONTENT_SCRAPER

    worker = ContentScraper(PROCESS_GRAZER_CONTENT_SCRAPER)
    worker.start()
