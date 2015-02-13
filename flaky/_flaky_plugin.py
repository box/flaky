# coding: utf-8

from __future__ import unicode_literals
from io import StringIO
from flaky import defaults
from flaky.names import FlakyNames
from flaky.utils import ensure_unicode_string


# pylint:disable=R0921
class _FlakyPlugin(object):
    _retry_failure_message = ' failed ({0} runs remaining out of {1}).'
    _failure_message = ' failed; it passed {0} out of the required {1} times.'

    def __init__(self):
        super(_FlakyPlugin, self).__init__()
        self._stream = StringIO()

    def _log_test_failure(self, test_callable_name, err, message):
        """
        Add messaging about a test failure to the stream, which will be
        printed by the plugin's report method.
        """
        self._stream.writelines([
            ensure_unicode_string(test_callable_name),
            message,
            '\n\t',
            ensure_unicode_string(err[0]),
            '\n\t',
            ensure_unicode_string(err[1]),
            '\n\t',
            ensure_unicode_string(err[2]),
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
        try:
            test_callable, name = self._get_test_callable_and_name(
                test,
            )
        except AttributeError:
            return False
        current_runs = self._get_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_RUNS,
        )
        if current_runs is None:
            return False
        current_runs += 1
        self._set_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )
        self._add_flaky_test_failure(test_callable, err)
        flaky = self._get_flaky_attributes(test_callable)

        if not self._has_flaky_test_failed(flaky):
            max_runs = flaky[FlakyNames.MAX_RUNS]
            runs_left = max_runs - flaky[FlakyNames.CURRENT_RUNS]
            message = self._retry_failure_message.format(
                runs_left,
                max_runs,
            )
            self._log_test_failure(name, err, message)
            self._rerun_test(test)
            return True
        else:
            min_passes = flaky[FlakyNames.MIN_PASSES]
            current_passes = flaky[FlakyNames.CURRENT_PASSES]
            message = self._failure_message.format(
                current_passes,
                min_passes,
            )
            self._log_test_failure(name, err, message)
            return False

    def _rerun_test(self, test):
        """
        Rerun a flaky test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`Function`
        """
        raise NotImplementedError

    def _handle_test_success(self, test):
        """
        Handle a flaky test success.
        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.

        Returning True from this method keeps the test runner from reporting
        the test as a success; this way we can retry and only report as a
        success if the test has passed the required number of times.
        :param test:
            The test that has raised an error
        :type test:
            :class:`nose.case.Test`
        :return:
            True, if the test will be rerun; False, if nose should handle it.
        :rtype:
            `bool`
        """
        test_callable, test_callable_name = self._get_test_callable_and_name(
            test,
        )
        current_runs = self._get_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_RUNS
        )
        if current_runs is None:
            return False
        current_runs += 1
        current_passes = self._get_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_PASSES
        )
        current_passes += 1
        self._set_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_RUNS,
            current_runs
        )
        self._set_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_PASSES,
            current_passes
        )
        flaky = self._get_flaky_attributes(test_callable)
        min_passes = flaky[FlakyNames.MIN_PASSES]
        self._stream.writelines([
            ensure_unicode_string(test_callable_name),
            ' passed {0} out of the required {1} times. '.format(
                current_passes,
                min_passes,
            ),
        ])
        if not self._has_flaky_test_succeeded(flaky):
            self._stream.write(
                'Running test again until it passes {0} times.\n'.format(
                    min_passes,
                )
            )
            self._rerun_test(test)
            return True
        else:
            self._stream.write('Success!\n')
            return False

    @staticmethod
    def add_report_option(add_option):
        """
        Add an option to the test runner to suppress the flaky report.
        :param add_option:
            A function that can add an option to the test runner.
            Its argspec should equal that of argparse.add_option.
        :type add_option:
            `callable`
        """
        add_option(
            '--no-flaky-report',
            action='store_false',
            dest='flaky_report',
            default=True,
            help="Suppress the report at the end of the "
                 "run detailing flaky test results.",
        )

    @staticmethod
    def add_force_flaky_options(add_option):
        """
        Add options to the test runner that force all tests to be flaky.
        :param add_option:
            A function that can add an option to the test runner.
            Its argspec should equal that of argparse.add_option.
        :type add_option:
            `callable`
        """
        add_option(
            '--force-flaky',
            action="store_true",
            dest="force_flaky",
            default=False,
            help="If this option is specified, we will treat all tests as "
                 "flaky."
        )
        add_option(
            '--max-runs',
            action="store",
            dest="max_runs",
            type="int",
            default=2,
            help="If --force-flaky is specified, we will run each test at "
                 "most this many times (unless the test has its own flaky "
                 "decorator)."
        )
        add_option(
            '--min-passes',
            action="store",
            dest="min_passes",
            type="int",
            default=1,
            help="If --force-flaky is specified, we will run each test at "
                 "least this many times (unless the test has its own flaky "
                 "decorator)."
        )

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

    @classmethod
    def _copy_flaky_attributes(cls, test, test_class):
        """
        Copy flaky attributes from the test class to the test callable, but
        only if the attributes aren't already on the test callable.
        :param test:
            The test that is being prepared to run
        :type test:
            :class:`nose.case.Test`
        """
        test_callable, _ = cls._get_test_callable_and_name(test)
        for attr, value in cls._get_flaky_attributes(test_class).items():
            if value is not None:
                already_set = hasattr(test_callable, attr)
                if not already_set or getattr(test_callable, attr) is None:
                    cls._set_flaky_attribute(test_callable, attr, value)

    @staticmethod
    def _get_flaky_attribute(test_callable, flaky_attribute):
        """
        Gets an attribute describing the flaky test.
        :param test_callable:
            The test method from which to get the attribute
        :type test_callable:
            `callable`
        :param flaky_attribute:
            The name of the attribute to get
        :type flaky_attribute:
            `unicode`
        :return:
            The test callable's attribute, or None if the test
            callable doesn't have that attribute.
        :rtype:
            varies
        """
        return getattr(
            test_callable,
            flaky_attribute,
            None,
        )

    @staticmethod
    def _set_flaky_attribute(test_callable, flaky_attribute, value):
        """
        Sets an attribute on a flaky test. Uses magic __dict__ since setattr
        doesn't work for bound methods.
        :param test_callable:
            The test callable on which to set the attribute
        :type test_callable:
            `callable`
        :param flaky_attribute:
            The name of the attribute to set
        :type flaky_attribute:
            `unicode`
        :param value:
            The value to set the test callable's attribute to.
        :type value:
            varies
        """
        test_callable.__dict__[flaky_attribute] = value

    @classmethod
    def _has_flaky_attributes(cls, test):
        """
        Returns true if the test callable in question is marked as flaky.
        :param test:
            The test that is being prepared to run
        :type test:
            :class:`Function`
        :return:
        :rtype:
            `bool`
        """
        test_callable, _ = cls._get_test_callable_and_name(test)
        current_runs = cls._get_flaky_attribute(
            test_callable,
            FlakyNames.CURRENT_RUNS,
        )
        return current_runs is not None

    @classmethod
    def _get_flaky_attributes(cls, test_callable):
        """
        Get all the flaky related attributes from the test callable.
        :param test_callable:
            The test callable from which to get the flaky related attributes.
        :type test_callable:
            `callable`
        :return:
        :rtype:
            `dict` of `unicode` to varies
        """
        return dict((
            (attr, cls._get_flaky_attribute(
                test_callable,
                attr,
            )) for attr in FlakyNames()
        ))

    @classmethod
    def _add_flaky_test_failure(cls, test_callable, err):
        """
        Store test error information on the test callable.
        :param test_callable:
            The test callable from which to get the flaky related attributes.
        :type test_callable:
            `callable`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        """
        if not hasattr(test_callable, FlakyNames.CURRENT_ERRORS):
            errs = []
            cls._set_flaky_attribute(
                test_callable,
                FlakyNames.CURRENT_ERRORS,
                errs,
            )
        else:
            errs = getattr(test_callable, FlakyNames.CURRENT_ERRORS)
        errs.append(err)

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

    @classmethod
    def _get_test_callable_and_name(cls, test):
        """
        Get the test callable and test callable name from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :return:
            The test callable (and its name) that is being run by the test
        :rtype:
            `tuple` of `callable`, `unicode`
        """
        raise NotImplementedError

    @classmethod
    def _make_test_callable_flaky(cls, test, max_runs, min_passes):
        """
        Make a given test callable flaky.
        :param test:
            The test in question.
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :param max_runs:
            The value of the FlakyNames.MAX_RUNS attribute to use.
        :type max_runs:
            `int`
        :param min_passes:
            The value of the FlakyNames.MIN_PASSES attribute to use.
        :type min_passes:
            `int`
        """
        attrib_dict = defaults.default_flaky_attributes(max_runs, min_passes)
        test_callable, _ = cls._get_test_callable_and_name(test)
        if test_callable is not None:
            for attr, value in attrib_dict.items():
                cls._set_flaky_attribute(test_callable, attr, value)
