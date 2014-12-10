# coding: utf-8

from __future__ import unicode_literals
from flaky._flaky_plugin import _FlakyPlugin
from test.base_test_case import TestCase


class TestFlakyPlugin(TestCase):
    def setUp(self):
        super(TestFlakyPlugin, self).setUp()
        self._flaky_plugin = _FlakyPlugin()

    def test_flaky_plugin_handles_non_ascii_byte_string_in_exception(self):
        mock_method_name = 'my_method'
        mock_exception = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'.encode('utf-16')
        mock_message = 'information about retries'
        # pylint:disable=protected-access
        self._flaky_plugin._log_test_failure(
            mock_method_name,
            (ValueError.__name__, mock_exception, ''),
            mock_message
        )
