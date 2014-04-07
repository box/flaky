# coding: utf-8

from __future__ import unicode_literals
import logging
from io import StringIO

from nose.plugins import Plugin
from nose.result import TextTestResult

from box.test.flaky.names import FlakyNames


class FlakyPlugin(Plugin):
    """
    Plugin for nosetests that allows retrying flaky tests.
    """
    name = 'flaky'
    _retry_failure_message = ' failed ({} runs remaining out of {}).'
    _failure_message = ' failed; it passed {} out of the required {} times.'

    def __init__(self):
        super(FlakyPlugin, self).__init__()
        self._logger = logging.getLogger('nose.plugins.flaky')
        self._flaky_tests = []
        self._stream = StringIO()
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
        test_method, test_method_name = self._get_test_method_and_name(test)
        current_runs = self._get_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_RUNS
        )
        if current_runs is None:
            return False
        current_runs += 1
        current_passes = self._get_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_PASSES
        )
        current_passes += 1
        self._set_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_RUNS,
            current_runs
        )
        self._set_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_PASSES,
            current_passes
        )
        flaky = self._get_flaky_attributes(test_method)
        min_passes = flaky[FlakyNames.MIN_PASSES]
        self._stream.writelines([
            unicode(test_method_name),
            ' passed {} out of the required {} times. '.format(
                current_passes,
                min_passes,
            ),
        ])
        if not self._has_flaky_test_succeeded(flaky):
            self._stream.write(
                'Running test again until it passes {} times.\n'.format(
                    min_passes,
                )
            )
            test.run(self._flaky_result)
            return True
        else:
            self._stream.write('Success!\n')
            return False

    def report(self, stream):
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

    def prepareTestCase(self, test):
        """
        Baseclass override. Called right before a test case is run.

        If the test is marked flaky and the test method is not, copy the
        flaky attributes from the test to the test method.
        :param test:
            The test that has succeeded
        :type test:
            :class:`nose.case.Test`
        """
        # pylint:disable=invalid-name
        test_method, _ = self._get_test_method_and_name(test)
        for attr, value in self._get_flaky_attributes(test.test).iteritems():
            if value is not None:
                if not hasattr(
                        test_method,
                        attr,
                ) or getattr(
                        test_method,
                        attr,
                ) is None:
                    self._set_flaky_attribute(test_method, attr, value)

    def _log_test_failure(self, test_method_name, err, message):
        """
        Add messaging about a test failure to the stream, which will be
        printed by the plugin's report method.
        """
        self._stream.writelines([
            unicode(test_method_name),
            message,
            '\n\t',
            unicode(err[0]),
            '\n\t',
            unicode(err[1].message),
            '\n\t',
            unicode(err[2]),
            '\n',
        ])

    def _handle_test_error_or_failure(self, test, err):
        """
        Handle a flaky test error or failure.
        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.

        Returning True from this method keeps the test runner from reporting
        the test as a failure; this way we can retry and only report as a
        failure if we are out of retries.
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
        test_method, test_method_name = self._get_test_method_and_name(test)
        current_runs = self._get_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_RUNS,
        )
        if current_runs is None:
            return False
        current_runs += 1
        self._set_flaky_attribute(
            test_method,
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )
        self._add_flaky_test_failure(test_method, err)
        flaky = self._get_flaky_attributes(test_method)

        if not self._has_flaky_test_failed(flaky):
            max_runs = flaky[FlakyNames.MAX_RUNS]
            runs_left = max_runs - flaky[FlakyNames.CURRENT_RUNS]
            message = self._retry_failure_message.format(
                runs_left,
                max_runs,
            )
            self._log_test_failure(test_method_name, err, message)
            test.run(self._flaky_result)
            return True
        else:
            min_passes = flaky[FlakyNames.MIN_PASSES]
            current_passes = flaky[FlakyNames.CURRENT_PASSES]
            message = self._failure_message.format(
                current_passes,
                min_passes,
            )
            self._log_test_failure(test_method_name, err, message)
            return False

    @staticmethod
    def _get_flaky_attribute(test_method, flaky_attribute):
        """
        Gets an attribute describing the flaky test.
        :param test_method:
            The test method from which to get the attribute
        :type test_method:
            `callable`
        :param flaky_attribute:
            The name of the attribute to get
        :type flaky_attribute:
            `unicode`
        :return:
            The test method's attribute, or None if the test method doesn't
            have that attribute.
        :rtype:
            varies
        """
        return getattr(
            test_method,
            flaky_attribute,
            None
        )

    @staticmethod
    def _set_flaky_attribute(test_method, flaky_attribute, value):
        """
        Sets an attribute on a flaky test. Uses magic __dict__ since setattr
        doesn't work for bound methods.
        :param test_method:
            The test method on which to set the attribute
        :type test_method:
            `callable`
        :param flaky_attribute:
            The name of the attribute to set
        :type flaky_attribute:
            `unicode`
        :param value:
            The value to set the test method's attribute to.
        :type value:
            varies
        """
        test_method.__dict__[flaky_attribute] = value

    @classmethod
    def _get_flaky_attributes(cls, test_method):
        """
        Get all the flaky related attributes from the test method.
        :param test_method:
            The test method from which to get the flaky related attributes.
        :type test_method:
            `callable`
        :return:
        :rtype:
            `dict` of `unicode` to varies
        """
        return {
            attr: cls._get_flaky_attribute(
                test_method,
                attr,
            ) for attr in FlakyNames()
        }

    @classmethod
    def _add_flaky_test_failure(cls, test_method, err):
        """
        Store test error information on the test method.
        :param test_method:
            The test method from which to get the flaky related attributes.
        :type test_method:
            `callable`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        """
        if not hasattr(test_method, FlakyNames.CURRENT_ERRORS):
            errs = []
            cls._set_flaky_attribute(
                test_method,
                FlakyNames.CURRENT_ERRORS,
                errs,
            )
        else:
            errs = getattr(test_method, FlakyNames.CURRENT_ERRORS)
        errs.append(err)

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

    @classmethod
    def _has_flaky_test_failed(cls, flaky):
        """
        Whether or not the flaky test has failed
        :param flaky:
            Dictionary of flaky attributes
        :type flaky:
            `dict` of `unicode` to varies
        :return:
            True if the flaky test should be marked as failure; False if
            it should be rerun.
        :rtype:
            `bool`
        """
        no_retry = flaky[FlakyNames.CURRENT_RUNS] >= flaky[FlakyNames.MAX_RUNS]
        return no_retry and not cls._has_flaky_test_succeeded(flaky)

    @staticmethod
    def _has_flaky_test_succeeded(flaky):
        """
        Whether or not the flaky test has succeeded
        :param flaky:
            Dictionary of flaky attributes
        :type flaky:
            `dict` of `unicode` to varies
        :return:
            True if the flaky test should be marked as success; False if
            it should be rerun.
        :rtype:
            `bool`
        """
        return flaky[FlakyNames.CURRENT_PASSES] >= flaky[FlakyNames.MIN_PASSES]
