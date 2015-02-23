# coding=utf-8
__author__ = 'Bohdan Mushkevych'

import random
import string
from datetime import datetime

from grazer.model.scrape_content import ScrapeContent
from grazer.model.scrape_state import ScrapeState
from grazer.model.model_constants import *


def name_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def unicode_name_generator(size=6):
    return u''.join(unichr(random.choice(range(0x300, 0x370) + range(0x20d0, 0x2100))) for _ in range(size))


def create_scrape_content():
    scrape = ScrapeContent()
    scrape.content_url = 'http://' + name_generator(12) + '.package.com'
    scrape.category = random.choice(['Sports', 'Action', 'Games', 'Video'])
    scrape.category_path = name_generator(32) + '.path'
    scrape.rating = str(random.uniform(0.0, 9.9))
    scrape.rating_count = str(random.randint(0, 987654321))
    scrape.title = name_generator() + '.title'
    scrape.release_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    scrape.description = name_generator(32) + '.descr'
    scrape.developer = name_generator(16) + '.developer'
    scrape.seller = name_generator(16) + '.seller'
    scrape.cover_url = 'http://' + name_generator(12) + '.cover.com'
    scrape.version = '.'.join([str(random.randint(0, 5)), str(random.randint(0, 5)), str(random.randint(0, 5))])
    scrape.price = str(random.uniform(0.99, 99.99))
    return scrape


def create_scrape_state():
    scrape_state = ScrapeState()
    scrape_state.package_name = random.choice(['com.appgeneration.setimaapp',
                                               'com.cptandroid',
                                               'org.skinmonitor',
                                               'com.rhamesgames.atoz',
                                               'com.webclap.sweetstyle.sweetDigitalClockHappy'])
    scrape_state.platform = random.choice([PLATFORM_ANDROID])
    scrape_state.scrape_state = random.choice([STATE_SUCCESS, STATE_FAILURE])
    scrape_state.scrape_url = 'http://' + name_generator(12) + '.app.com'
    scrape_state.last_updated = name_generator() + '.name'
    scrape_state.scrape_http_code = 200
    scrape_state.store_url = 'http://' + name_generator(12) + '.store.com'
    return scrape_state
