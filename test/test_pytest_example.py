# coding: utf-8

from __future__ import unicode_literals

# This is an end-to-end example of the flaky package in action. Consider it
# a live tutorial, showing the various features in action.

# pylint:disable=import-error
import pytest
# pylint:enable=import-error
from unittest import TestCase
from flaky import flaky


@flaky
def test_something_flaky(dummy_list=[]):
    # pylint:disable=dangerous-default-value
    dummy_list.append(0)
    assert len(dummy_list) > 1


@pytest.fixture(scope='class')
def threshold_provider():
    return {'threshold': -1}


@pytest.fixture(scope='class')
def threshold_provider_2():
    return {'threshold': -1}


class TestExample(object):
    def test_non_flaky_thing(self):
        """Flaky will not interact with this test"""
        pass

    @pytest.mark.xfail
    def test_non_flaky_failing_thing(self):
        """Flaky will also not interact with this test"""
        assert self == 1

    @staticmethod
    @flaky(3, 2)
    def test_flaky_thing_that_fails_then_succeeds(threshold_provider):
        """
        Flaky will run this test 3 times.
        It will fail once and then succeed twice.
        """
        threshold_provider['threshold'] += 1
        assert threshold_provider['threshold'] >= 1

    @staticmethod
    @flaky(3, 2)
    def test_flaky_thing_that_succeeds_then_fails_then_succeeds(threshold_provider_2):
        """
        Flaky will run this test 3 times.
        It will succeed once, fail once, and then succeed one more time.
        """
        threshold_provider_2['threshold'] += 1
        assert threshold_provider_2['threshold'] != 1

    @flaky(2, 2)
    def test_flaky_thing_that_always_passes(self):
        """Flaky will run this test twice.  Both will succeed."""
        pass

    @pytest.mark.skipif(
        'True',
        reason="This really fails! Remove skipif to see the test failure."
    )
    @flaky()
    def test_flaky_thing_that_always_fails(self):
        """Flaky will run this test twice.  Both will fail."""
        assert self is None


@flaky
class TestExampleFlakyTests(object):
    _threshold = -1

    @staticmethod
    def test_flaky_thing_that_fails_then_succeeds():
        """
        Flaky will run this test twice.
        It will fail once and then succeed.
        """
        TestExampleFlakyTests._threshold += 1
        assert TestExampleFlakyTests._threshold >= 1


@flaky
class TestExampleFlakyTestCase(TestCase):
    _threshold = -1

    @staticmethod
    def test_flaky_thing_that_fails_then_succeeds():
        """
        Flaky will run this test twice.
        It will fail once and then succeed.
        """
        TestExampleFlakyTestCase._threshold += 1
        assert TestExampleFlakyTestCase._threshold >= 1


class TestFlakySubclass(TestExampleFlakyTestCase):
    pass


def _test_flaky_doctest():
    """
    Flaky ignores doctests. This test wouldn't be rerun if it failed.
    >>> _test_flaky_doctest()
    True
    """
    return True


@pytest.fixture
def my_fixture():
    return 42


@flaky
def test_requiring_my_fixture(my_fixture, dummy_list=[]):
    # pylint:disable=dangerous-default-value,unused-argument
    dummy_list.append(0)
    assert len(dummy_list) > 1
