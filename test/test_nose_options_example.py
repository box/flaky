# coding: utf-8

from __future__ import unicode_literals

# This is a series of tests that do not use the flaky decorator; the flaky
# behavior is intended to be enabled with the --force-flaky option on the
# command line.

from flaky import flaky
from test.test_case_base import TestCase


class ExampleTests(TestCase):
    _threshold = -2

    def test_something_flaky(self):
        """
        Flaky will run this test twice.
        It will fail once and then succeed once.
        This ensures that we mark tests as flaky even if they don't have a
        decorator when we use the command-line options.
        """
        self._threshold += 1
        if self._threshold < 0:
            raise Exception("Threshold is not high enough.")

    @flaky(3, 1)
    def test_flaky_thing_that_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will fail twice and then succeed once.
        This ensures that the flaky decorator overrides any command-line
        options we specify.
        """
        self._threshold += 1
        if self._threshold < 1:
            raise Exception("Threshold is not high enough.")


@flaky(3, 1)
class ExampleFlakyTests(TestCase):
    _threshold = -1

    def test_flaky_thing_that_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will fail twice and then succeed once.
        This ensures that the flaky decorator on a test suite overrides any
        command-line options we specify.
        """
        self._threshold += 1
        if self._threshold < 1:
            raise Exception("Threshold is not high enough.")
