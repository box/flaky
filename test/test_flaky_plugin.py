from collections import namedtuple
from io import StringIO
from unittest import TestCase

from flaky._flaky_plugin import _FlakyPlugin
from flaky.names import FlakyNames

TestCaseDataset = namedtuple(
    "TestCaseDataset",
    ['max_runs', 'min_passes', 'current_runs', 'current_passes', 'expect_fail'],
)


class TestFlakyPlugin(TestCase):
    _test_dataset = {
        "default_not_started": TestCaseDataset(2, 1, 0, 0, False),
        "default_one_failure": TestCaseDataset(2, 1, 1, 0, False),
        "default_one_success": TestCaseDataset(2, 1, 1, 1, False),
        "default_two_failures": TestCaseDataset(2, 1, 2, 0, True),
        "default_one_failure_one_success": TestCaseDataset(2, 1, 2, 1, False),
        "three_two_not_started": TestCaseDataset(3, 2, 0, 0, False),
        "three_two_one_failure": TestCaseDataset(3, 2, 1, 0, False),
        "three_two_one_success": TestCaseDataset(3, 2, 1, 1, False),
        "three_two_two_failures": TestCaseDataset(3, 2, 2, 0, True),
        "three_two_one_failure_one_success": TestCaseDataset(3, 2, 2, 1, False),
        "three_two_two_successes": TestCaseDataset(3, 2, 2, 2, False),
    }

    def setUp(self):
        super().setUp()
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

    def test_flaky_plugin_identifies_failure(self):
        for name, test in self._test_dataset:
            with self.subTest(name):
                flaky = {
                    FlakyNames.CURRENT_PASSES: test.current_passes,
                    FlakyNames.CURRENT_RUNS: test.current_runs,
                    FlakyNames.MAX_RUNS: test.max_runs,
                    FlakyNames.MIN_PASSES: test.min_passes,
                }
                # pylint:disable=protected-access
                self.assertEqual(
                    self._flaky_plugin._has_flaky_test_failed(flaky),
                    test.expect_fail,
                )

    def test_write_unicode_to_stream(self):
        for message in ('ascii stuff', 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'):
            with self.subTest(message):
                stream = StringIO()
                stream.write('ascii stuff')
                # pylint:disable=protected-access
                self._flaky_plugin._stream.write(message)
                self._flaky_plugin._add_flaky_report(stream)
