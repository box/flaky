from io import StringIO
from unittest import TestCase

from genty import genty, genty_dataset


@genty
class TestMultiprocessStringIO(TestCase):
    _unicode_string = 'Plain Hello'
    _unicode_string_non_ascii = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'

    def setUp(self):
        super().setUp()
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
            '{}{}'.format(_unicode_string, _unicode_string_non_ascii),
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
            '{}{}'.format(_unicode_string, _unicode_string_non_ascii),
        )
    )
    def test_writelines_then_read(self, lines, expected_value):
        for string_io in self._string_ios:
            string_io.writelines(lines)
            self.assertEqual(string_io.getvalue(), expected_value)
