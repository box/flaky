# coding: utf-8

from flaky.utils import ensure_unicode_string
from test.base_test_case import TestCase


class UtilsTestCase(TestCase):
    def test_ensure_unicode_string_handles_nonascii_exception_message(self):
        ex = Exception('\xe2\x80\x93')

        string = ensure_unicode_string(ex)
        self.assertEqual(string, u'\u2013')
