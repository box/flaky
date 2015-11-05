# coding: utf-8

from __future__ import unicode_literals
from unittest import TestCase as _TestCase


# pylint:disable=invalid-name
try:
    # pylint:disable=unused-import
    from unittest import expectedFailure, skip
    # pylint:enable=unused-import
except ImportError:
    # pylint:disable=unused-argument, invalid-name
    def _noop_wrapper(wrapped):
        def noop_wrapped(*args, **kwargs):
            pass
        return noop_wrapped
    expectedFailure = skip = _noop_wrapper
    # pylint:enable=unused-argument


class TestCase(_TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        if not hasattr(self, 'assertIsNotNone'):
            def assertIsNotNone(obj, msg=None):
                self.assertNotEqual(obj, None, msg)
            self.assertIsNotNone = assertIsNotNone
        if not hasattr(self, 'assertDictContainsSubset'):
            def assertDictContainsSubset(expected, actual, msg=None):
                self.assertTrue(
                    set(expected.items()).issubset(set(actual.items())),
                    msg,
                )
            self.assertDictContainsSubset = assertDictContainsSubset
