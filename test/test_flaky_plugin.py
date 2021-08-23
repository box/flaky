from io import StringIO

import pytest

from flaky.flaky_pytest_plugin import FlakyPlugin
from flaky.names import FlakyNames


@pytest.fixture
def flaky_plugin():
    return FlakyPlugin()


def genty_dataset(names, **kwargs):
    return pytest.mark.parametrize(names, [pytest.param(*v, id=k) for k, v in kwargs.items()])


def test_flaky_plugin_handles_non_ascii_byte_string_in_exception(flaky_plugin):
    mock_method_name = 'my_method'
    mock_exception = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'.encode('utf-16')
    mock_message = 'information about retries'
    # pylint:disable=protected-access
    flaky_plugin._log_test_failure(
        mock_method_name,
        (ValueError.__name__, mock_exception, ''),
        mock_message,
    )


@genty_dataset(
    'max_runs,min_passes,current_runs,current_passes,expect_fail',
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
        max_runs,
        min_passes,
        current_runs,
        current_passes,
        expect_fail,
        flaky_plugin,
):
    flaky = {
        FlakyNames.CURRENT_PASSES: current_passes,
        FlakyNames.CURRENT_RUNS: current_runs,
        FlakyNames.MAX_RUNS: max_runs,
        FlakyNames.MIN_PASSES: min_passes,
    }
    assert flaky_plugin.has_flaky_test_failed(flaky) == expect_fail


@pytest.mark.parametrize('message', ('ascii stuff', 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'))
def test_write_unicode_to_stream(message, flaky_plugin):
    stream = StringIO()
    stream.write('ascii stuff')
    flaky_plugin.stream.write(message)
    flaky_plugin.add_flaky_report(stream)
