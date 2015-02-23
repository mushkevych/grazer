# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from odm.document import BaseDocument
from odm.fields import StringField
from grazer.model.model_constants import *


class ScrapeState(BaseDocument):
    package_name = StringField(FIELD_PACKAGE_NAME)
    platform = StringField(FIELD_PLATFORM)
    scrape_state = StringField(field_name=FIELD_SCRAPE_STATE,
                               choices=[STATE_EMBRYO, STATE_FAILURE, STATE_SUCCESS, STATE_RESCRAPE_FAILURE])
    scrape_url = StringField(FIELD_SCRAPE_URL)
    scrape_http_code = StringField(FIELD_SCRAPE_HTTP_CODE)
    last_updated = StringField(FIELD_LAST_UPDATED)
    store_url = StringField(FIELD_STORE_URL)
