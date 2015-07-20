# coding: utf-8

from __future__ import unicode_literals

# This is an end-to-end example of the flaky package in action. Consider it
# a live tutorial, showing the various features in action.

from genty import genty, genty_dataset

from flaky import flaky
from test.base_test_case import TestCase, expectedFailure, skip


class ExampleTests(TestCase):
    _threshold = -1

    def test_non_flaky_thing(self):
        """Flaky will not interact with this test"""
        pass

    @expectedFailure
    def test_non_flaky_failing_thing(self):
        """Flaky will also not interact with this test"""
        self.assertEqual(0, 1)

    @flaky(3, 2)
    def test_flaky_thing_that_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will fail once and then succeed twice.
        """
        self._threshold += 1
        if self._threshold < 1:
            raise Exception("Threshold is not high enough: {0} vs {1}.".format(
                self._threshold, 1),
            )

    @flaky(3, 2)
    def test_flaky_thing_that_succeeds_then_fails_then_succeeds(self):
        """
        Flaky will run this test 3 times.
        It will succeed once, fail once, and then succeed one more time.
        """
        self._threshold += 1
        if self._threshold == 1:
            self.assertEqual(0, 1)

    @flaky(2, 2)
    def test_flaky_thing_that_always_passes(self):
        """Flaky will run this test twice.  Both will succeed."""
        pass

    @skip("This really fails! Remove this decorator to see the test failure.")
    @flaky()
    def test_flaky_thing_that_always_fails(self):
        """Flaky will run this test twice.  Both will fail."""
        self.assertEqual(0, 1)


@flaky
class ExampleFlakyTests(TestCase):
    _threshold = -1

    def test_flaky_thing_that_fails_then_succeeds(self):
        """
        Flaky will run this test twice.
        It will fail once and then succeed.
        """
        self._threshold += 1
        if self._threshold < 1:
            raise Exception("Threshold is not high enough: {0} vs {1}.".format(
                self._threshold, 1),
            )


def test_function():
    """
    Nose will import this function and wrap it in a :class:`FunctionTestCase`.
    It's included in the example to make sure flaky handles it correctly.
    """
    pass


@flaky
def test_flaky_function(param=[]):
    # pylint:disable=dangerous-default-value
    param_length = len(param)
    param.append(None)
    assert param_length == 1


@flaky
@genty
class ExampleFlakyTestsWithTrickyTestNames(TestCase):
    _threshold = -1

    _unicode_string = 'Plain Hello'
    _byte_string = str(_unicode_string)
    _unicode_string_non_ascii = 'ńőń ȁŝćȉȉ ŝƭȕƒƒ'
    _byte_string_non_ascii = _unicode_string_non_ascii.encode('utf-8')
    _byte_string_windows_encoded = 'Hèllö'.encode('windows-1252')

    @genty_dataset(
        _unicode_string,
        _byte_string,
        _unicode_string_non_ascii,
        _byte_string_non_ascii,
        _byte_string_windows_encoded,
    )
    def test_tricky_strings_in_test_method_name(self, message):
        # pylint:disable=unused-argument
        self._threshold += 1
        if self._threshold < 1:
            # Raise an exception with a message that is also tricky. To ensure
            # that any logging by flaky works correctly
            raise Exception(message)
