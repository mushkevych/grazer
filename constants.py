# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'


# List of Processes
PROCESS_LAUNCH_PY = 'LaunchPy'
PROCESS_GRAZER_HATCHERY = 'GrazerHatchery'
PROCESS_GRAZER_MANAGER = 'GrazerManager'
PROCESS_GRAZER_CONTENT_SCRAPER = 'ContentScraper'
PROCESS_GRAZER_SCRAPE_REDUCER = 'ScrapeReducer'
PROCESS_GRAZER_MERGER = 'GrazerMerger'

# Process tokens. There should be one token per one Timetable tree or stand-alone process
TOKEN_LAUNCH_PY = 'launch_py'
TOKEN_GRAZER_HATCHERY = 'grazer_hatchery'
TOKEN_GRAZER_MANAGER = 'grazer_manager'
TOKEN_GRAZER_CONTENT_SCRAPER = 'content_scraper'
TOKEN_GRAZER_SCRAPE_REDUCER = 'scrape_reducer'
TOKEN_GRAZER_MERGER = 'grazer_merger'

QUEUE_REQUESTED_PACKAGES = 'q_requests'
QUEUE_SCRAPED_PACKAGES = 'q_scrapes'
QUEUE_MERGE_REQUEST = 'q_merges'
ROUTING_IRRELEVANT = 'routing_irrelevant'

EXCHANGE_RAW_DATA = 'ex_raw_data'
