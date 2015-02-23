# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from odm.document import BaseDocument


def csv_header(model_klass):
    assert issubclass(model_klass, BaseDocument)
    return ','.join(model_klass._get_fields())


def csv_line(model_instance):
    assert isinstance(model_instance, BaseDocument)

    json_object = model_instance.to_json()
    values = []
    for column in model_instance._fields:
        if column in json_object and json_object[column] is not None:
            value = json_object[column]
            if not isinstance(value, basestring):
                value = str(value)

            value = value.replace("\'", "''")
            values.append("'" + value + "'")
        else:
            values.append("''")

    return ','.join(values)
