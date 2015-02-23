# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from grazer.model.model_constants import *
from odm.document import BaseDocument
from odm.fields import StringField


class ScrapeContent(BaseDocument):
    entry_id = StringField(FIELD_ENTRY_ID)
    content_url = StringField(FIELD_CONTENT_URL)
    title = StringField(FIELD_TITLE)
    category = StringField(FIELD_CATEGORY)
    category_path = StringField(FIELD_CATEGORY_PATH)
    release_date = StringField(FIELD_RELEASE_DATE)
    version = StringField(FIELD_VERSION)
    rating = StringField(FIELD_RATING)
    rating_count = StringField(FIELD_RATING_COUNT)
    description = StringField(FIELD_DESCRIPTION)
    price = StringField(FIELD_PRICE)
    developer = StringField(FIELD_DEVELOPER)
    seller = StringField(FIELD_SELLER)
    cover_url = StringField(FIELD_COVER_URL)
