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
      )
    }

    def setUp(self):
        super().setUp()
        from flaky.multiprocess_string_io import MultiprocessingStringIO
        self._string_io = StringIO()
        self._mp_string_io = MultiprocessingStringIO()
        del self._mp_string_io.proxy[:]
        self._string_ios = (self._string_io, self._mp_string_io)

    def test_write_then_read(self):
        for name in _test_values:
            with self.subTest(name):
                for string_io in self._string_ios:
                    for item in _test_values[name][0]:
                        string_io.write(item)
                    self.assertEqual(string_io.getvalue(), _test_values[name][1])

    def test_writelines_then_read(self):
        for name in _test_values:
            with self.subTest(name):
                for string_io in self._string_ios:
                    string_io.writelines(_test_values[name][0])
                self.assertEqual(string_io.getvalue(), _test_values[name][1])
