# coding: utf-8

from __future__ import unicode_literals

# This is a series of tests that do not use the flaky decorator; the flaky
# behavior is intended to be enabled with the --force-flaky option on the
# command line.

from flaky import flaky


def test_something_flaky(dummy_list=[]):
    # pylint:disable=dangerous-default-value
    dummy_list.append(0)
    assert len(dummy_list) > 1


class TestExample(object):
    _threshold = -2

    @staticmethod
    @flaky(3, 1)
    def test_flaky_thing_that_fails_then_succeeds():
        """
        Flaky will run this test 3 times.
        It will fail twice and then succeed once.
        This ensures that the flaky decorator overrides any command-line
        options we specify.
        """
        TestExample._threshold += 1
        assert TestExample._threshold >= 1


@flaky(3, 1)
class TestExampleFlakyTests(object):
    _threshold = -2

    @staticmethod
    def test_flaky_thing_that_fails_then_succeeds():
        """
        Flaky will run this test 3 times.
        It will fail twice and then succeed once.
        This ensures that the flaky decorator on a test suite overrides any
        command-line options we specify.
        """
        TestExampleFlakyTests._threshold += 1
        assert TestExampleFlakyTests._threshold >= 1
