# coding: utf-8

from __future__ import unicode_literals
from flaky.flaky_decorator import flaky
from flaky.names import FlakyNames
from test.test_case_base import TestCase


class TestFlakyDecorator(TestCase):
    def test_flaky_raises_for_non_positive_min_passes(self):
        def test_something():
            pass
        self.assertRaises(
            ValueError,
            lambda: flaky(min_passes=0)(test_something),
        )

    def test_flaky_raises_for_max_runs_less_than_min_passes(self):
        def test_something():
            pass
        self.assertRaises(
            ValueError,
            lambda: flaky(max_runs=2, min_passes=3)(test_something),
        )

    def test_flaky_adds_flaky_attributes_to_test_method(self):
        min_passes = 4
        max_runs = 7

        @flaky(max_runs, min_passes)
        def test_something():
            pass

        flaky_attribute = dict((
            (attr, getattr(
                test_something,
                attr,
                None
            )) for attr in FlakyNames()
        ))

        self.assertIsNotNone(flaky_attribute)
        self.assertDictContainsSubset(
            {
                FlakyNames.MIN_PASSES: min_passes,
                FlakyNames.MAX_RUNS: max_runs,
                FlakyNames.CURRENT_PASSES: 0,
                FlakyNames.CURRENT_RUNS: 0,
                FlakyNames.CURRENT_ERRORS: None
            },
            flaky_attribute
        )
