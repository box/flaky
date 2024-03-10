from io import StringIO
from unittest import TestCase


class TestMultiprocessStringIO(TestCase):
    _unicode_string = 'Plain Hello'
    _unicode_string_non_ascii = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'
    _test_values = {
        "no_writes": ([], ''),
        "one_write": ([_unicode_string], _unicode_string),
        "two_writes": (
            [_unicode_string, _unicode_string_non_ascii],
            '{}{}'.format(_unicode_string, _unicode_string_non_ascii),
        ),
    }

    def setUp(self):
        super().setUp()
        from flaky.multiprocess_string_io import MultiprocessingStringIO
        self._string_io = StringIO()
        self._mp_string_io = MultiprocessingStringIO()
        del self._mp_string_io.proxy[:]
        self._string_ios = (self._string_io, self._mp_string_io)

    def test_write_then_read(self):
        for name, value in self._test_values.items():
            with self.subTest(name):
                for string_io in self._string_ios:
                    for item in value[0]:
                        string_io.write(item)
                    self.assertEqual(string_io.getvalue(), value[1])

    def test_writelines_then_read(self):
        for name, value in self._test_values.items():
            with self.subTest(name):
                for string_io in self._string_ios:
                    string_io.writelines(value[0])
                self.assertEqual(string_io.getvalue(), value[1])
