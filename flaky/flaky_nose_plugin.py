# coding: utf-8

from __future__ import unicode_literals
import logging
from nose.failure import Failure

from nose.plugins import Plugin
from nose.result import TextTestResult

from flaky._flaky_plugin import _FlakyPlugin


class FlakyPlugin(_FlakyPlugin, Plugin):
    """
    Plugin for nosetests that allows retrying flaky tests.
    """
    name = 'flaky'

    def __init__(self):
        super(FlakyPlugin, self).__init__()
        self._logger = logging.getLogger('nose.plugins.flaky')
        self._flaky_result = TextTestResult(self._stream, [], 0)

    def handleError(self, test, err):
        """
        Baseclass override. Called when a test raises an exception.
        :param test:
            The test that has raised an error
        :type test:
            :class:`nose.case.Test`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :return:
            True, if the test will be rerun; False, if nose should handle it.
        :rtype:
            `bool`
        """
        # pylint:disable=invalid-name
        return self._handle_test_error_or_failure(test, err)

    def handleFailure(self, test, err):
        """
        Baseclass override. Called when a test fails.
        :param test:
            The test that has raised an error
        :type test:
            :class:`nose.case.Test`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :return:
            True, if the test will be rerun; False, if nose should handle it.
        :rtype:
            `bool`
        """
        # pylint:disable=invalid-name
        return self._handle_test_error_or_failure(test, err)

    def addSuccess(self, test):
        """
        Baseclass override. Called when a test succeeds.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.

        Returning True from this method keeps the test runner from reporting
        the test as a success; this way we can retry and only report as a
        success if we have achieved the required number of successes.
        :param test:
            The test that has succeeded
        :type test:
            :class:`nose.case.Test`
        :return:
            True, if the test will be rerun; False, if nose should handle it.
        :rtype:
            `bool`
        """
        # pylint:disable=invalid-name
        return self._handle_test_success(test)

    def _add_flaky_report(self, stream):
        """
        Baseclass override. Write details about flaky tests to the test report.
        :param stream:
            The test stream to which the report can be written.
        :type stream:
            `file`
        """
        stream.write('===Flaky Test Report===\n\n')
        stream.write(self._stream.getvalue())
        stream.write('\n===End Flaky Test Report===\n')

    def report(self, stream):
        """
        Baseclass override. Write details about flaky tests to the test report.
        :param stream:
            The test stream to which the report can be written.
        :type stream:
            `file`
        """
        self._add_flaky_report(stream)

    def prepareTestCase(self, test):
        """
        Baseclass override. Called right before a test case is run.

        If the test class is marked flaky and the test method is not, copy the
        flaky attributes from the test class to the test method.
        :param test:
            The test that is being prepared to run
        :type test:
            :class:`nose.case.Test`
        """
        # pylint:disable=invalid-name
        if not isinstance(test.test, Failure):
            test_class = test.test
            self._copy_flaky_attributes(test, test_class)

    def _rerun_test(self, test):
        """Base class override. Rerun a flaky test."""
        test.run(self._flaky_result)

    @staticmethod
    def _get_test_method_name(test):
        """
        Get the name of the test method from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`nose.case.Test`
        :return:
            The name of the test method that is being run by the test
        :rtype:
            `unicode`
        """
        _, _, class_and_method_name = test.address()
        first_dot_index = class_and_method_name.index('.')
        test_method_name = class_and_method_name[first_dot_index + 1:]
        return test_method_name

    @classmethod
    def _get_test_method_and_name(cls, test):
        """
        Get the test method and test method name from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`nose.case.Test`
        :return:
            The test method (and its name) that is being run by the test
        :rtype:
            `tuple` of `callable`, `unicode`
        """
        method_name = cls._get_test_method_name(test)
        return getattr(test.test, method_name), method_name
