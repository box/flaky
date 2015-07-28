# coding: utf-8

from __future__ import unicode_literals

# pylint:disable=invalid-name
try:
    unicode_type = unicode
    binary_type = str
except NameError:
    unicode_type = str
    binary_type = bytes


def ensure_unicode_string(string):
    try:
        return unicode_type(string)
    except UnicodeDecodeError:
        return string.decode('utf-8', 'replace')


def ensure_byte_string(string):
    try:
        return binary_type(string)
    except UnicodeEncodeError:
        return string.encode('utf-8', 'replace')
