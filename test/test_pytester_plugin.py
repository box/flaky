pytest_plugins = 'pytester'  # pylint:disable=invalid-name

TESTSUITE = """
import pytest


@pytest.fixture
def my_fixture():
    return 42

def test_a_thing(my_fixture):
    assert my_fixture == 42

"""


def test_output_without_capture(testdir):
    """
    Test for Issue #82. Flaky was breaking tests using the pytester plugin.
    """
    script = testdir.makepyfile(TESTSUITE)
    result = testdir.runpytest(script, '--verbose', '--capture', 'fd')
    assert result.ret == 0
