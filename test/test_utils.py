import sys
from unittest import TestCase

from flaky.utils import ensure_unicode_string, unicode_type

from genty import genty, genty_dataset


@genty
class TestEnsureUnicodeString(TestCase):
    _unicode_string = 'Plain Hello'
    _byte_string = b'Plain Hello'
    _unicode_string_non_ascii = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'
    _byte_string_non_ascii = _unicode_string_non_ascii.encode('utf-8')
    _hello = 'Hèllö'
    _mangled_hello = 'H\ufffdll\ufffd'
    _byte_string_windows_encoded = _hello.encode('windows-1252')

    def test_ensure_unicode_string_handles_nonascii_exception_message(self):
        message = '\u2013'
        encoded_message = message.encode('utf-8')
        ex = Exception(encoded_message)

        string = ensure_unicode_string(ex)
        if sys.version_info.major >= 3:
            message = unicode_type(encoded_message)
        self.assertEqual(string, message)

    @genty_dataset(
        (_unicode_string, _unicode_string),
        (_byte_string, _unicode_string),
        (_unicode_string_non_ascii, _unicode_string_non_ascii),
        (_byte_string_non_ascii, _unicode_string_non_ascii),
        (_byte_string_windows_encoded, _mangled_hello),
    )
    def test_ensure_unicode_string_handles_various_strings(
            self,
            string,
            expected_unicode_string,
    ):
        unicode_string = ensure_unicode_string(string)
        if sys.version_info.major >= 3:
            expected_unicode_string = unicode_type(string)
        self.assertIsInstance(unicode_string, unicode_type)
        self.assertIn(expected_unicode_string, unicode_string)
