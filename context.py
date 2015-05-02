# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from synergy.system.time_qualifier import *
from synergy.scheduler.scheduler_constants import *
from synergy.db.model.queue_context_entry import queue_context_entry
from synergy.db.model.daemon_process_entry import daemon_context_entry
from synergy.db.model.managed_process_entry import managed_context_entry
from synergy.db.model.timetable_tree_entry import timetable_tree_entry

from constants import *


mq_queue_context = {
    QUEUE_REQUESTED_PACKAGES: queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_REQUESTED_PACKAGES),

    QUEUE_SCRAPED_PACKAGES: queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_SCRAPED_PACKAGES),

    QUEUE_MERGE_REQUEST: queue_context_entry(
        exchange=EXCHANGE_RAW_DATA,
        queue_name=QUEUE_MERGE_REQUEST),
}

process_context = {
    PROCESS_LAUNCH_PY: daemon_context_entry(
        process_name=PROCESS_LAUNCH_PY,
        classname='',
        token=TOKEN_LAUNCH_PY,
        routing=ROUTING_IRRELEVANT,
        exchange=EXCHANGE_UTILS),

    PROCESS_GRAZER_HATCHERY: managed_context_entry(
        process_name=PROCESS_GRAZER_HATCHERY,
        classname='grazer.workers.grazer_hatchery.GrazerHatchery.start',
        token=TOKEN_GRAZER_HATCHERY,
        time_qualifier=QUALIFIER_DAILY,
        exchange=EXCHANGE_MANAGED_WORKER,
        process_type=TYPE_MANAGED),

    PROCESS_GRAZER_MANAGER: daemon_context_entry(
        process_name=PROCESS_GRAZER_MANAGER,
        classname='grazer.workers.grazer_manager.GrazerManager.start',
        token=TOKEN_GRAZER_MANAGER,
        exchange=EXCHANGE_FREERUN_WORKER,
        sink=QUEUE_REQUESTED_PACKAGES),

    PROCESS_GRAZER_CONTENT_SCRAPER: daemon_context_entry(
        process_name=PROCESS_GRAZER_CONTENT_SCRAPER,
        classname='grazer.workers.content_scraper.ContentScraper.start',
        token=TOKEN_GRAZER_CONTENT_SCRAPER,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_REQUESTED_PACKAGES,
        sink=QUEUE_SCRAPED_PACKAGES),

    PROCESS_GRAZER_SCRAPE_REDUCER: daemon_context_entry(
        process_name=PROCESS_GRAZER_SCRAPE_REDUCER,
        classname='grazer.workers.scrape_reducer.ScrapeReducer.start',
        token=TOKEN_GRAZER_SCRAPE_REDUCER,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_SCRAPED_PACKAGES,
        sink=QUEUE_MERGE_REQUEST),

    PROCESS_GRAZER_MERGER: daemon_context_entry(
        process_name=PROCESS_GRAZER_MERGER,
        classname='grazer.workers.grazer_merger.GrazerMerger.start',
        token=TOKEN_GRAZER_MERGER,
        exchange=EXCHANGE_FREERUN_WORKER,
        source=QUEUE_MERGE_REQUEST),
}

timetable_context = {
}
