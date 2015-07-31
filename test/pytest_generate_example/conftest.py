# coding: utf-8

from __future__ import unicode_literals


def pytest_generate_tests(metafunc):
    if 'dummy_list' in metafunc.fixturenames:
        metafunc.parametrize("dummy_list", [[]])
