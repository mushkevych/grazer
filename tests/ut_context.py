# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from context import ROUTING_IRRELEVANT, EXCHANGE_UTILS
from synergy.conf import context
from synergy.db.model.daemon_process_entry import daemon_context_entry

# process provides <process context> to unit testing: such as logger, queue, etc
PROCESS_UNIT_TEST = 'UnitTest'
TOKEN_UNIT_TEST = 'unit_test'


def register_processes():
    """ Function should be called by #setting.enable_test_mode to register UT classes and functionality """
    process_entry = daemon_context_entry(
        process_name=PROCESS_UNIT_TEST,
        classname='',
        token=TOKEN_UNIT_TEST,
        routing=ROUTING_IRRELEVANT,
        exchange=EXCHANGE_UTILS)
    context.process_context[process_entry.process_name] = process_entry
