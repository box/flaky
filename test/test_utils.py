# coding: utf-8

from __future__ import unicode_literals

from genty import genty, genty_dataset

from flaky.utils import ensure_byte_string, ensure_unicode_string
from test.base_test_case import TestCase


@genty
class TestUtils(TestCase):
    @genty_dataset(
        unicode_string=(u'test', u'test'),
        byte_string=(b'test', u'test'),
        byte_string_with_non_ascii=(
            b'ƭȅŝƭ',
            u'\u01ad\u0205\u015d\u01ad',
        ),
    )
    def test_ensure_unicode_string(self, string, expected_result):
        result = ensure_unicode_string(string)
        self.assertEqual(result, expected_result)

    @genty_dataset(
        unicode_string=(u'test', b'test'),
        byte_string=(b'test', b'test'),
        unicode_string_with_non_ascii=(
            u'ƭȅŝƭ',
            b'\xc6\xad\xc8\x85\xc5\x9d\xc6\xad',
        ),
    )
    def test_ensure_byte_string(self, string, expected_result):
        result = ensure_byte_string(string)
        self.assertEqual(result, expected_result)
