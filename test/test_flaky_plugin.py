# coding: utf-8

from __future__ import unicode_literals

from io import StringIO

from genty import genty, genty_dataset

from flaky._flaky_plugin import _FlakyPlugin
from flaky.names import FlakyNames
from test.test_case_base import TestCase


@genty
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
            mock_message,
        )

    @genty_dataset(
        default_not_started=(2, 1, 0, 0, False),
        default_one_failure=(2, 1, 1, 0, False),
        default_one_success=(2, 1, 1, 1, False),
        default_two_failures=(2, 1, 2, 0, True),
        default_one_failure_one_success=(2, 1, 2, 1, False),
        three_two_not_started=(3, 2, 0, 0, False),
        three_two_one_failure=(3, 2, 1, 0, False),
        three_two_one_success=(3, 2, 1, 1, False),
        three_two_two_failures=(3, 2, 2, 0, True),
        three_two_one_failure_one_success=(3, 2, 2, 1, False),
        three_two_two_successes=(3, 2, 2, 2, False),
    )
    def test_flaky_plugin_identifies_failure(
            self,
            max_runs,
            min_passes,
            current_runs,
            current_passes,
            expect_fail,
    ):
        flaky = {
            FlakyNames.CURRENT_PASSES: current_passes,
            FlakyNames.CURRENT_RUNS: current_runs,
            FlakyNames.MAX_RUNS: max_runs,
            FlakyNames.MIN_PASSES: min_passes,
        }
        # pylint:disable=protected-access
        self.assertEqual(
            self._flaky_plugin._has_flaky_test_failed(flaky),
            expect_fail,
        )

    @genty_dataset('ascii stuff', 'ńőń ȁŝćȉȉ ŝƭȕƒƒ')
    def test_write_unicode_to_stream(self, message):
        stream = StringIO()
        stream.write('ascii stuff')
        # pylint:disable=protected-access
        self._flaky_plugin._stream.write(message)
        self._flaky_plugin._add_flaky_report(stream)
