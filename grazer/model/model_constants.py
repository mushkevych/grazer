# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

TABLE_SCRAPE_CONTENT = 'tbl_scrape_content'
TABLE_SCRAPE_STATE = 'tbl_scrape_state'
TABLE_TEMP_SCRAPE_CONTENT = 'temp_scrape_content'
TABLE_TEMP_SCRAPE_STATE = 'temp_scrape_state'

FIELD_PACKAGE_NAME = 'package_name'
FIELD_PLATFORM = 'platform'                  # android, apple, blackberry, etc
FIELD_STORE_URL = 'store_url'                # store base URL
FIELD_SCRAPE_URL = 'scrape_url'              # url we have scraped for the package information
FIELD_SCRAPE_HTTP_CODE = 'scrape_http_code'  # HTTP Code: 200, 404, 503, etc
FIELD_SCRAPE_CONTENT = 'scrape_content'
FIELD_SCRAPE_STATE = 'scrape_state'          # enum: STATE_EMBRYO, STATE_SUCCESS, STATE_FAILURE, STATE_RESCRAPE_FAILURE
FIELD_LAST_UPDATED = 'last_updated'
FIELD_FILE_SCRAPE_CONTENT = 'file_scrape_content'
FIELD_FILE_SCRAPE_STATE = 'file_scrape_state'
FIELD_ENTRY_ID = 'entry_id'
FIELD_CONTENT_URL = 'content_url'            # application end url
FIELD_TITLE = 'title'
FIELD_CATEGORY = 'category'
FIELD_CATEGORY_PATH = 'category_path'
FIELD_RELEASE_DATE = 'release_date'
FIELD_VERSION = 'version'
FIELD_RATING = 'rating'
FIELD_RATING_COUNT = 'rating_count'
FIELD_DESCRIPTION = 'description'
FIELD_PRICE = 'price'
FIELD_SELLER = 'seller'
FIELD_DEVELOPER = 'developer'
FIELD_COVER_URL = 'cover_url'

STAT_ANDROID_SUCCESS = 'android_success'
STAT_ANDROID_FAILURE = 'android_failure'

PLATFORM_ANDROID = 'android'
PLATFORM_IOS = 'ios'

STATE_EMBRYO = 'STATE_EMBRYO'
STATE_SUCCESS = 'STATE_SUCCESS'
STATE_FAILURE = 'STATE_FAILURE'
STATE_RESCRAPE_FAILURE = 'STATE_RESCRAPE_FAILURE'

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

MANIFEST_ENTRIES = 'entries'
ENTRY_URL = 'url'
ENTRY_MANDATORY = 'mandatory'

UNKNOWN_VALUE = 'unknown'
NULL_VALUE = u'null'
UNKNOWN_ERROR_CODE = 999