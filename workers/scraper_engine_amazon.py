# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from bs4 import BeautifulSoup

from settings import amazon_appstore_urls
from grazer.model.scrape_content import ScrapeContent
from grazer.workers.abstract_scraper_engine import AbstractScraperEngine


class ScraperEngineAmazon(AbstractScraperEngine):
    def __init__(self, logger, package_name, platform):
        super(ScraperEngineAmazon, self).__init__(logger, package_name, platform)

    @AbstractScraperEngine.content_uris.getter
    def content_uris(self):
        """ returns list of the fully formatted and valid App Store URLs """
        return [store_url % self.package_name for store_url in amazon_appstore_urls]

    def _scrape_content(self, unicode_content, content_url):
        scrape = ScrapeContent()
        scrape.content_url = content_url

        parsed_data = BeautifulSoup(unicode_content)

        title_div = parsed_data.find('span', attrs={'id': 'btAsinTitle'})

        if title_div:
            title_contents = title_div.findChild('div')

            if title_contents and title_contents.contents:
                scrape.title = title_contents.contents[0]

        # populate other scrape fields here based on parsed html content

        return scrape
