# coding: utf-8

from flaky.names import FlakyNames


def default_flaky_attributes(max_runs, min_passes):
    """
    Returns the default flaky attributes to set on a flaky test.
    :param max_runs:
        The value of the FlakyNames.MAX_RUNS attribute to use.
    :type max_runs:
        `int`
    :param min_passes:
        The value of the FlakyNames.MIN_PASSES attribute to use.
    :type min_passes:
        `int`
    :return:
    :rtype:
        `dict`
    """
    return {
        FlakyNames.MAX_RUNS: max_runs,
        FlakyNames.MIN_PASSES: min_passes,
        FlakyNames.CURRENT_RUNS: 0,
        FlakyNames.CURRENT_PASSES: 0,
    }
