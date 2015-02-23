# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from constants import ROUTING_IRRELEVANT
from synergy.scheduler.scheduler_constants import EXCHANGE_UTILS
from synergy.system.time_qualifier import QUALIFIER_REAL_TIME
from synergy.conf.process_context import ProcessContext
from synergy.db.model.process_context_entry import _process_context_entry

# process provides <process context> to unit testing: such as logger, queue, etc
PROCESS_UNIT_TEST = 'UnitTest'
TOKEN_UNIT_TEST = 'unit_test'


def register_processes():
    """ Function should be called by #setting.enable_test_mode to register UT classes and functionality """
    process_entry = _process_context_entry(
        process_name=PROCESS_UNIT_TEST,
        classname='',
        token=TOKEN_UNIT_TEST,
        time_qualifier=QUALIFIER_REAL_TIME,
        routing=ROUTING_IRRELEVANT,
        exchange=EXCHANGE_UTILS)
    ProcessContext.put_context_entry(process_entry)
