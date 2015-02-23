# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from synergy.system.time_qualifier import *
from synergy.scheduler.scheduler_constants import *
from synergy.db.model.queue_context_entry import _queue_context_entry
from synergy.db.model.process_context_entry import _process_context_entry

from constants import *


mq_queue_context = {
    QUEUE_REQUESTED_PACKAGES: _queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_REQUESTED_PACKAGES),

    QUEUE_SCRAPED_PACKAGES: _queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_SCRAPED_PACKAGES),

    QUEUE_MERGE_REQUEST: _queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_MERGE_REQUEST),
}

process_context = {
    PROCESS_LAUNCH_PY: _process_context_entry(
        process_name=PROCESS_LAUNCH_PY,
        classname='',
        token=TOKEN_LAUNCH_PY,
        time_qualifier=QUALIFIER_REAL_TIME,
        routing=ROUTING_IRRELEVANT,
        exchange=EXCHANGE_UTILS),

    PROCESS_GRAZER_HATCHERY: _process_context_entry(
        process_name=PROCESS_GRAZER_HATCHERY,
        classname='grazer.workers.grazer_hatchery.GrazerHatchery.start',
        token=TOKEN_GRAZER_HATCHERY,
        time_qualifier=QUALIFIER_DAILY,
        exchange=EXCHANGE_MANAGED_WORKER,
        process_type=TYPE_MANAGED),

    PROCESS_GRAZER_MANAGER: _process_context_entry(
        process_name=PROCESS_GRAZER_MANAGER,
        classname='grazer.workers.grazer_manager.GrazerManager.start',
        token=TOKEN_GRAZER_MANAGER,
        time_qualifier=QUALIFIER_REAL_TIME,
        exchange=EXCHANGE_FREERUN_WORKER,
        sink=QUEUE_REQUESTED_PACKAGES),

    PROCESS_GRAZER_CONTENT_SCRAPER: _process_context_entry(
        process_name=PROCESS_GRAZER_CONTENT_SCRAPER,
        classname='grazer.workers.content_scraper.ContentScraper.start',
        token=TOKEN_GRAZER_CONTENT_SCRAPER,
        time_qualifier=QUALIFIER_REAL_TIME,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_REQUESTED_PACKAGES,
        sink=QUEUE_SCRAPED_PACKAGES),

    PROCESS_GRAZER_SCRAPE_REDUCER: _process_context_entry(
        process_name=PROCESS_GRAZER_SCRAPE_REDUCER,
        classname='grazer.workers.scrape_reducer.ScrapeReducer.start',
        token=TOKEN_GRAZER_SCRAPE_REDUCER,
        time_qualifier=QUALIFIER_REAL_TIME,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_SCRAPED_PACKAGES,
        sink=QUEUE_MERGE_REQUEST),

    PROCESS_GRAZER_MERGER: _process_context_entry(
        process_name=PROCESS_GRAZER_MERGER,
        classname='grazer.workers.grazer_merger.GrazerMerger.start',
        token=TOKEN_GRAZER_MERGER,
        time_qualifier=QUALIFIER_REAL_TIME,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_MERGE_REQUEST),
}

timetable_context = {
}
