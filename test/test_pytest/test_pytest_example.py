# coding: utf-8

from __future__ import unicode_literals

# pylint:disable=import-error
import pytest
# pylint:enable=import-error
from flaky import flaky
from test.test_case_base import TestCase, skip


# This is an end-to-end example of the flaky package in action. Consider it
# a live tutorial, showing the various features in action.


@flaky
def test_something_flaky(dummy_list=[]):
    # pylint:disable=dangerous-default-value
    dummy_list.append(0)
    assert len(dummy_list) > 1


@pytest.fixture(scope='function')
def failing_setup_fixture():
    assert False


@flaky
@pytest.mark.xfail(strict=True)
@pytest.mark.usefixtures("failing_setup_fixture")
def test_something_good_with_failing_setup_fixture():
    assert True


class TestExample(object):
    _threshold = -1

    def test_non_flaky_thing(self):
        """Flaky will not interact with this test"""
        pass

    @pytest.mark.xfail
    def test_non_flaky_failing_thing(self):
        """Flaky will also not interact with this test"""
        assert self == 1

    @flaky(3, 2)
    def test_flaky_thing_that_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will fail once and then succeed twice.
        """
        # pylint:disable=no-self-use
        TestExample._threshold += 1
        assert TestExample._threshold >= 1

    @flaky(3, 2)
    def test_flaky_thing_that_succeeds_then_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will succeed once, fail once, and then succeed one more time.
        """
        # pylint:disable=no-self-use
        TestExample._threshold += 1
        assert TestExample._threshold != 1

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


def _rerun_filter(err, name, test, plugin):
    # pylint:disable=unused-argument
    return issubclass(err[0], AssertionError)


class TestExampleRerunFilter(object):
    _threshold = -1

    @flaky(rerun_filter=_rerun_filter)
    def test_something_flaky(self):
        # pylint:disable=no-self-use
        TestExampleRerunFilter._threshold += 1
        assert TestExampleRerunFilter._threshold >= 1


@skip('This test always fails')
@flaky
def test_something_that_always_fails_but_should_be_skipped():
    assert 0
