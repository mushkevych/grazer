# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from datetime import datetime

from synergy.system.utils import unicode_truncate
from grazer.model.model_constants import *
from grazer.model.scrape_content import ScrapeContent

REPLACEMENT_PAIRS = {' - Android Apps on Google Play': '',
                     '&amp;': '&'}

# structure <date_time_format: example>
DATE_FORMATS = {'%Y-%m-%dT%H:%M:%SZ': '2010-01-06T02:25:59Z',
                '%b %d, %Y': 'Jan 6, 2010',
                '%B %d, %Y': 'January 6, 2010',
                '%Y-%m-%d %H:%M:%S': '2010-01-06 02:25:59'}


def _to_unicode(value):
    if isinstance(value, str):
        unicode_content = unicode(string=value, encoding='UTF-8', errors='strict')
    elif isinstance(value, unicode):
        unicode_content = value
    else:
        unicode_content = unicode(string=str(value), encoding='UTF-8', errors='strict')

    return unicode_content


def _process_field(value, length, replace=True):
    if not value:
        return UNKNOWN_VALUE

    unicode_content = _to_unicode(value)
    if unicode_content.lower() == NULL_VALUE:
        return UNKNOWN_VALUE

    if replace:
        for lookup, replacement in REPLACEMENT_PAIRS.iteritems():
            unicode_content = unicode_content.replace(lookup, replacement)

    unicode_content = unicode_truncate(unicode_content, length)
    unicode_content = unicode_content.strip()
    return unicode_content


def _process_date(value):
    """ returns: string with date formatted as YYYY-mm-dd HH:MM:SS OR 'null' if the date is un-parsable """
    if not value:
        return NULL_VALUE

    unicode_content = _to_unicode(value)
    if unicode_content.lower() == NULL_VALUE:
        return NULL_VALUE

    parsed_value = NULL_VALUE
    for date_format in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, date_format)
            parsed_value = dt.strftime(TIMESTAMP_FORMAT)
            break
        except:
            pass

    return parsed_value


def do_scrape_processing(scrape):
    assert isinstance(scrape, ScrapeContent)

    scrape.entry_id = _process_field(scrape.entry_id, 128)
    scrape.content_url = _process_field(scrape.content_url, 256)
    scrape.title = _process_field(scrape.title, 200)
    scrape.category = _process_field(scrape.category, 128)
    scrape.category_path = _process_field(scrape.category_path, 256)
    scrape.description = _process_field(scrape.description, 1536)
    scrape.developer = _process_field(scrape.developer, 128)
    scrape.seller = _process_field(scrape.seller, 128)
    scrape.cover_url = _process_field(scrape.cover_url, 256)
    scrape.version = _process_field(scrape.version, 32)
    scrape.rating = _process_field(scrape.rating, 32)
    scrape.rating_count = _process_field(scrape.rating_count, 32)
    scrape.price = _process_field(scrape.price, 16)
    scrape.release_date = _process_date(scrape.release_date)

    return scrape
