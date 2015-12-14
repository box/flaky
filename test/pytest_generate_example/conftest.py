# coding: utf-8

from __future__ import unicode_literals


def pytest_generate_tests(metafunc):
    """
    Parameterize a fixture named 'dummy_list' with a list containing one item - 'foo'
    """
    if 'dummy_list' in metafunc.fixturenames:
        metafunc.parametrize("dummy_list", [[]])
