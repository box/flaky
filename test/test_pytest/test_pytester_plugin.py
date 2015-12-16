# coding: utf-8

from __future__ import unicode_literals, absolute_import

pytest_plugins = str('pytester')  # pylint:disable=invalid-name

TESTSUITE = """
def test_a_thing():
    pass

"""


def test_output_without_capture(testdir):
    """
    Test for Issue #82. Flaky was breaking tests using the pytester plugin.
    """
    script = testdir.makepyfile(TESTSUITE)
    result = testdir.runpytest(script, '--verbose', '--capture', 'fd')
    assert result.ret == 0
