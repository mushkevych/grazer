# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

import httplib
import urllib2
from datetime import datetime

from grazer.model.model_constants import *
from grazer.model.scrape_state import ScrapeState
from grazer.model.mq_scrape_wrapper import MqScrapeWrapper
from grazer.workers.scrape_post_processor import do_scrape_processing
from settings import https_proxy_list


class AbstractScraperEngine(object):
    def __init__(self, logger, package_name, platform):
        self.logger = logger
        self.package_name = package_name
        self.platform = platform

    @property
    def content_uris(self):
        """ returns list of the fully formatted and valid Content URIs
        use @AbstractScraperEngine.content_uris.getter annotation to override the property"""
        raise NotImplementedError('property store_urls must be overridden in the child class')

    def _scrape_content(self, unicode_content, content_url):
        """ scrapes the content and returns dict presenting the web page impression
        :param unicode_content: unicode object representing the string
        :param content_url: defines source of the content
        :raises ValueError if the scrape can not be completed
        :see http://stackoverflow.com/a/643810/3171310 for explanation of unicode vs string"""
        raise NotImplementedError('method _scrape_content must be overridden in the child class')

    def do_search(self):
        scrape_state = ScrapeState()
        result = MqScrapeWrapper()
        result.scrape_state_doc = scrape_state

        scrape_state.platform = self.platform
        scrape_state.package_name = self.package_name
        scrape_state.scrape_state = STATE_FAILURE
        scrape_state.last_updated = datetime.now().strftime(TIMESTAMP_FORMAT)

        for store_url in self.content_uris:
            for http_proxy in https_proxy_list:
                try:
                    if http_proxy:
                        # Proxy set up
                        proxy = urllib2.ProxyHandler({'https': http_proxy})

                        # Create an URL opener utilizing proxy
                        opener = urllib2.build_opener(proxy)
                        urllib2.install_opener(opener)

                    # Acquire data from URL
                    request = urllib2.Request(store_url)
                    request.add_unredirected_header('User-Agent', 'Mozilla/5.0')
                    message = urllib2.urlopen(request)
                    status_code = message.getcode()
                    scrape_state.scrape_http_code = status_code

                    if status_code == httplib.OK:
                        content = message.read()
                        unicode_content = unicode(string=content, encoding='UTF-8', errors='ignore')

                        scrape = self._scrape_content(unicode_content, store_url)
                        scrape = do_scrape_processing(scrape)

                        scrape_state.scrape_state = STATE_SUCCESS
                        scrape_state.store_url = store_url.split('?')[0]
                        scrape_state.scrape_url = store_url

                        result.scrape_content_doc = scrape
                        break

                except ValueError as e:
                    self.logger.debug('URL %s yields no valid APP results, due to %s' % (store_url, str(e)))
                except urllib2.HTTPError as e:
                    if e.code in [httplib.BAD_REQUEST, httplib.NOT_FOUND]:
                        self.logger.debug('URL %s resulted in an HTTP error: %s' % (store_url, str(e)))
                    else:
                        self.logger.error('URL %s resulted in an HTTP error: %s' % (store_url, str(e)))

                    scrape_state.scrape_http_code = e.code if e.code else UNKNOWN_ERROR_CODE
                    if e.code == httplib.FORBIDDEN:
                        # no sense in scraping other country-specific stores, if we are banned by the primary one
                        break
                except urllib2.URLError as e:
                    self.logger.error('URL %s resulted in an URLError: %s' % (store_url, str(e)))
                    scrape_state.scrape_http_code = e.errno if e.errno else UNKNOWN_ERROR_CODE
                except Exception as e:
                    self.logger.error('URL %s resulted in an unexpected error: %s' % (store_url, str(e)))
                    scrape_state.scrape_http_code = UNKNOWN_ERROR_CODE

            else:
                continue
            break

        return result
