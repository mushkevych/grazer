# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from grazer.model.model_constants import *
from odm.document import BaseDocument
from odm.fields import StringField, IntegerField


class MqMergerRequest(BaseDocument):
    s3_file_scrape_content = StringField(FIELD_FILE_SCRAPE_CONTENT)
    s3_file_scrape_state = StringField(FIELD_FILE_SCRAPE_STATE)
    stat_android_success = IntegerField(STAT_ANDROID_SUCCESS, default=0)
    stat_android_failure = IntegerField(STAT_ANDROID_FAILURE, default=0)
