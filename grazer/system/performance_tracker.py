# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from synergy.system.performance_tracker import TickerThread, TrackerPair


class WebScraperTracker(TickerThread):
    TRACKER_GROUP_ANDROID = 'Android'
    TRACKER_GROUP_TOTAL = 'Total'

    def __init__(self, logger):
        super(WebScraperTracker, self).__init__(logger)
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_ANDROID))
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_TOTAL))

    @property
    def android(self):
        return self.get_tracker(self.TRACKER_GROUP_ANDROID)

    @property
    def total(self):
        return self.get_tracker(self.TRACKER_GROUP_TOTAL)


class PackageManagerTracker(TickerThread):
    TRACKER_GROUP_NEW = 'New'
    TRACKER_GROUP_REPROCESS = 'Reprocess'

    def __init__(self, logger):
        super(PackageManagerTracker, self).__init__(logger)
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_NEW))
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_REPROCESS))

    @property
    def new_packages(self):
        return self.get_tracker(self.TRACKER_GROUP_NEW)

    @property
    def reprocess(self):
        return self.get_tracker(self.TRACKER_GROUP_REPROCESS)


class ScrapeReducerTracker(TickerThread):
    TRACKER_GROUP_META = 'Meta'
    TRACKER_GROUP_SCRAPE = 'Scrape'
    TRACKER_GROUP_INBOX = 'Inbox'

    def __init__(self, logger):
        super(ScrapeReducerTracker, self).__init__(logger)
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_META))
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_SCRAPE))
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_INBOX))

    @property
    def meta(self):
        return self.get_tracker(self.TRACKER_GROUP_META)

    @property
    def scrape(self):
        return self.get_tracker(self.TRACKER_GROUP_SCRAPE)

    @property
    def inbox(self):
        return self.get_tracker(self.TRACKER_GROUP_INBOX)


class MergerTracker(TickerThread):
    TRACKER_GROUP_ANDROID = 'Android'
    TRACKER_GROUP_INBOX = 'Inbox'

    def __init__(self, logger):
        super(MergerTracker, self).__init__(logger)
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_ANDROID))
        self.add_tracker(TrackerPair(self.TRACKER_GROUP_INBOX))

    @property
    def android(self):
        return self.get_tracker(self.TRACKER_GROUP_ANDROID)

    @property
    def inbox(self):
        return self.get_tracker(self.TRACKER_GROUP_INBOX)
