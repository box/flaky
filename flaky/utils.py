# coding: utf-8

from __future__ import unicode_literals

# pylint:disable=invalid-name
try:
    unicode_type = unicode
except NameError:
    unicode_type = str


def ensure_unicode_string(string):
    try:
        return unicode_type(string)
    except UnicodeDecodeError:
        return string.decode('utf-8', 'replace')
