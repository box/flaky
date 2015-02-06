# coding: utf-8

from __future__ import unicode_literals

from flaky import defaults


def flaky(max_runs=None, min_passes=None):
    """
    Decorator used to mark a test as "flaky". When used in conjuction with
    the flaky nosetests plugin, will cause the decorated test to be retried
    until min_passes successes are achieved out of up to max_runs test runs.
    :param max_runs:
        The maximum number of times the decorated test will be run.
    :type max_runs:
        `int`
    :param min_passes:
        The minimum number of times the test must pass to be a success.
    :type min_passes:
        `int`
    :return:
        A wrapper function that includes attributes describing the flaky test.
    :rtype:
        `callable`
    """
    if max_runs is None:
        max_runs = 2
    if min_passes is None:
        min_passes = 1
    if min_passes <= 0:
        raise ValueError('min_passes must be positive')
    # In case @flaky is applied to a function or class without arguments
    # (and without parentheses), max_runs will refer to the wrapped object.
    # In this case, the default value can be used.
    wrapped = None
    if hasattr(max_runs, '__call__'):
        wrapped = max_runs
        max_runs = 2
    if max_runs < min_passes:
        raise ValueError('min_passes cannot be greater than max_runs!')

    attrib = defaults.default_flaky_attributes(max_runs, min_passes)

    def wrapper(wrapped_object):
        for name, value in attrib.items():
            setattr(wrapped_object, name, value)
        return wrapped_object

    return wrapper(wrapped) if wrapped is not None else wrapper
