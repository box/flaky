# coding: utf-8

from __future__ import unicode_literals

from io import StringIO

from genty import genty, genty_dataset

from test.test_case_base import TestCase


@genty
class TestMultiprocessStringIO(TestCase):
    _unicode_string = 'Plain Hello'
    _unicode_string_non_ascii = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'

    def setUp(self):
        super(TestMultiprocessStringIO, self).setUp()
        from flaky.multiprocess_string_io import MultiprocessingStringIO
        self._string_io = StringIO()
        self._mp_string_io = MultiprocessingStringIO()
        del self._mp_string_io.proxy[:]
        self._string_ios = (self._string_io, self._mp_string_io)

    @genty_dataset(
        no_writes=([], ''),
        one_write=([_unicode_string], _unicode_string),
        two_writes=(
            [_unicode_string, _unicode_string_non_ascii],
            '{0}{1}'.format(_unicode_string, _unicode_string_non_ascii),
        )
    )
    def test_write_then_read(self, writes, expected_value):
        for string_io in self._string_ios:
            for item in writes:
                string_io.write(item)
            self.assertEqual(string_io.getvalue(), expected_value)

    @genty_dataset(
        no_writes=([], ''),
        one_write=([_unicode_string], _unicode_string),
        two_writes=(
            [_unicode_string, _unicode_string_non_ascii],
            '{0}{1}'.format(_unicode_string, _unicode_string_non_ascii),
        )
    )
    def test_writelines_then_read(self, lines, expected_value):
        for string_io in self._string_ios:
            string_io.writelines(lines)
            self.assertEqual(string_io.getvalue(), expected_value)
