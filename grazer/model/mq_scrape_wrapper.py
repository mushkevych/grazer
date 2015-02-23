# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from grazer.model.scrape_state import ScrapeState
from grazer.model.scrape_content import ScrapeContent
from grazer.model.model_constants import *

from odm.document import BaseDocument
from odm.fields import NestedDocumentField


class MqScrapeWrapper(BaseDocument):
    scrape_content_doc = NestedDocumentField(FIELD_SCRAPE_CONTENT, ScrapeContent, null=True)
    scrape_state_doc = NestedDocumentField(FIELD_SCRAPE_STATE, ScrapeState, null=True)
