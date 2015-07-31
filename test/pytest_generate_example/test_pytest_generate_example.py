# coding: utf-8

from __future__ import unicode_literals
from flaky import flaky


@flaky
def test_something_flaky(dummy_list):
    # pylint:disable=dangerous-default-value
    dummy_list.append(0)
    assert len(dummy_list) > 1


class TestExample(object):
    _threshold = -1

    @flaky
    def test_flaky_thing_that_fails_then_succeeds(self, dummy_list):
        self._threshold += 1
        assert self._threshold >= 1
