# coding: utf-8

from __future__ import unicode_literals
from flaky import flaky


@flaky
def test_something_flaky(dummy_list):
    dummy_list.append(0)
    assert len(dummy_list) > 1


class TestExample(object):
    _threshold = -1

    @flaky
    def test_flaky_thing_that_fails_then_succeeds(self, dummy_list):
        # pylint:disable=unused-argument,no-self-use
        TestExample._threshold += 1
        assert TestExample._threshold >= 1
