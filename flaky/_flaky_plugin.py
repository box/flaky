# coding: utf-8

from __future__ import unicode_literals
import multiprocessing
from flaky import defaults
from flaky.names import FlakyNames
from flaky.utils import ensure_unicode_string

MULTIPROCESS_MANAGER = multiprocessing.Manager()
MP_STREAM = MULTIPROCESS_MANAGER.list()


class _FlakyPlugin(object):
    _retry_failure_message = ' failed ({0} runs remaining out of {1}).'
    _failure_message = ' failed; it passed {0} out of the required {1} times.'
    _not_rerun_message = ' failed and was not selected for rerun.'

    def __init__(self):
        super(_FlakyPlugin, self).__init__()
        self._stream = MP_STREAM
        self._flaky_success_report = True

    @property
    def stream(self):
        """
        Returns the stream used for building the flaky report.
        Anything written to this stream before the end of the test run
        will be written to the flaky report.

        :return:
        :rtype:
        """
        return self._stream

    def _log_test_failure(self, test_callable_name, err, message):
        """
        Add messaging about a test failure to the stream, which will be
        printed by the plugin's report method.
        """
        self._stream.extend([
            ensure_unicode_string(test_callable_name),
            message,
            "\t" + ensure_unicode_string(err[0]),
            "\t" + ensure_unicode_string(err[1]),
            "\t" + ensure_unicode_string(err[2]),
        ])

    def _report_final_failure(self, err, flaky, name):
        """
        Report that the test has failed too many times to pass at
        least min_passes times.

        By default, this means that the test has failed twice.

        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :param flaky:
            Dictionary of flaky attributes
        :type flaky:
            `dict` of `unicode` to varies
        :param name:
            The test name
        :type name:
            `unicode`
        """
        min_passes = flaky[FlakyNames.MIN_PASSES]
        current_passes = flaky[FlakyNames.CURRENT_PASSES]
        message = self._failure_message.format(
            current_passes,
            min_passes,
        )
        self._log_test_failure(name, err, message)

    def _log_intermediate_failure(self, err, flaky, name):
        """
        Report that the test has failed, but still has reruns left.
        Then rerun the test.

        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :param flaky:
            Dictionary of flaky attributes
        :type flaky:
            `dict` of `unicode` to varies
        :param name:
            The test name
        :type name:
            `unicode`
        """
        max_runs = flaky[FlakyNames.MAX_RUNS]
        runs_left = max_runs - flaky[FlakyNames.CURRENT_RUNS]
        message = self._retry_failure_message.format(
            runs_left,
            max_runs,
        )
        self._log_test_failure(name, err, message)

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
            :class:`nose.case.Test` or :class:`Function`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :return:
            True, if the test will be rerun;
            False, if the test runner should handle it.
        :rtype:
            `bool`
        """
        try:
            _, _, name = self._get_test_declaration_callable_and_name(test)
        except AttributeError:
            return False
        current_runs = self._get_flaky_attribute(
            test,
            FlakyNames.CURRENT_RUNS,
        )
        if current_runs is None:
            return False
        current_runs += 1
        self._set_flaky_attribute(
            test,
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )
        self._add_flaky_test_failure(test, err)
        flaky = self._get_flaky_attributes(test)

        if not self._has_flaky_test_failed(flaky):
            if self._should_rerun_test(test, name, err):
                self._log_intermediate_failure(err, flaky, name)
                self._rerun_test(test)
                return True
            else:
                message = self._not_rerun_message
                self._log_test_failure(name, err, message)
                return False
        else:
            self._report_final_failure(err, flaky, name)
            return False

    def _should_rerun_test(self, test, name, err):
        """
        Whether or not a test should be rerun.
        This is a pass-through to the test's rerun filter.

        A flaky test will only be rerun if it hasn't failed too many
        times to succeed at least min_passes times, and if
        this method returns True.

        :param test:
            The test that has raised an error
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :param name:
            The test name
        :type name:
            `unicode`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        :return:
            Whether flaky should rerun this test.
        :rtype:
            `bool`
        """
        rerun_filter = self._get_flaky_attribute(test, FlakyNames.RERUN_FILTER)
        return rerun_filter(err, name, test, self)

    def _rerun_test(self, test):
        """
        Rerun a flaky test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`Function`
        """
        raise NotImplementedError  # pragma: no cover

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
        _, _, name = self._get_test_declaration_callable_and_name(test)
        current_runs = self._get_flaky_attribute(
            test,
            FlakyNames.CURRENT_RUNS
        )
        if current_runs is None:
            return False
        current_runs += 1
        current_passes = self._get_flaky_attribute(
            test,
            FlakyNames.CURRENT_PASSES
        )
        current_passes += 1
        self._set_flaky_attribute(
            test,
            FlakyNames.CURRENT_RUNS,
            current_runs
        )
        self._set_flaky_attribute(
            test,
            FlakyNames.CURRENT_PASSES,
            current_passes
        )
        flaky = self._get_flaky_attributes(test)
        need_reruns = not self._has_flaky_test_succeeded(flaky)
        if self._flaky_success_report:
            min_passes = flaky[FlakyNames.MIN_PASSES]
            success_string = ensure_unicode_string(name) + ' passed {0} out of the required {1} times. '.format(
                current_passes,
                min_passes,
            )
            if need_reruns:
                success_string += 'Running test again until it passes {0} times.'.format(
                    min_passes,
                )
            else:
                success_string += 'Success!'
            self._stream.append(success_string)
        if need_reruns:
            self._rerun_test(test)
        return need_reruns

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
        add_option(
            '--no-success-flaky-report',
            action='store_false',
            dest='flaky_success_report',
            default=True,
            help="Suppress reporting flaky test successes"
                 "in the report at the end of the "
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

        # Python 2 will write to the stderr stream as a byte string, whereas
        # Python 3 will write to the stream as text. Only encode into a byte
        # string if the write tries to encode it first and raises a
        # UnicodeEncodeError.
        value = "\n".join(i for i in self._stream)
        try:
            stream.write(value)
        except UnicodeEncodeError:
            stream.write(value.encode('utf-8', 'replace'))

        stream.write('\n\n===End Flaky Test Report===\n')

    @classmethod
    def _copy_flaky_attributes(cls, test, test_class):
        """
        Copy flaky attributes from the test callable or class to the test.
        :param test:
            The test that is being prepared to run
        :type test:
            :class:`nose.case.Test`
        """
        _, test_callable, _ = cls._get_test_declaration_callable_and_name(test)
        for attr, value in cls._get_flaky_attributes(test_class).items():
            already_set = hasattr(test, attr)
            if already_set:
                continue
            attr_on_callable = getattr(test_callable, attr, None)
            if attr_on_callable is not None:
                cls._set_flaky_attribute(test, attr, attr_on_callable)
            elif value is not None:
                cls._set_flaky_attribute(test, attr, value)

    @staticmethod
    def _get_flaky_attribute(test_item, flaky_attribute):
        """
        Gets an attribute describing the flaky test.
        :param test_item:
            The test method from which to get the attribute
        :type test_item:
            `callable` or :class:`nose.case.Test` or :class:`Function`
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
            test_item,
            flaky_attribute,
            None,
        )

    @staticmethod
    def _set_flaky_attribute(test_item, flaky_attribute, value):
        """
        Sets an attribute on a flaky test. Uses magic __dict__ since setattr
        doesn't work for bound methods.
        :param test_item:
            The test callable on which to set the attribute
        :type test_item:
            `callable` or :class:`nose.case.Test` or :class:`Function`
        :param flaky_attribute:
            The name of the attribute to set
        :type flaky_attribute:
            `unicode`
        :param value:
            The value to set the test callable's attribute to.
        :type value:
            varies
        """
        test_item.__dict__[flaky_attribute] = value

    @classmethod
    def _has_flaky_attributes(cls, test):
        """
        Returns True if the test callable in question is marked as flaky.
        :param test:
            The test that is being prepared to run
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :return:
        :rtype:
            `bool`
        """
        current_runs = cls._get_flaky_attribute(
            test,
            FlakyNames.CURRENT_RUNS,
        )
        return current_runs is not None

    @classmethod
    def _get_flaky_attributes(cls, test_item):
        """
        Get all the flaky related attributes from the test.
        :param test_item:
            The test callable from which to get the flaky related attributes.
        :type test_item:
            `callable` or :class:`nose.case.Test` or :class:`Function`
        :return:
        :rtype:
            `dict` of `unicode` to varies
        """
        return dict((
            (attr, cls._get_flaky_attribute(
                test_item,
                attr,
            )) for attr in FlakyNames()
        ))

    @classmethod
    def _add_flaky_test_failure(cls, test, err):
        """
        Store test error information on the test callable.
        :param test:
            The flaky test on which to update the flaky attributes.
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `class`, :class:`Exception`, `traceback`
        """
        errs = getattr(test, FlakyNames.CURRENT_ERRORS, None) or []
        cls._set_flaky_attribute(
            test,
            FlakyNames.CURRENT_ERRORS,
            errs,
        )
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
        max_runs, current_runs, min_passes, current_passes = (
            flaky[FlakyNames.MAX_RUNS],
            flaky[FlakyNames.CURRENT_RUNS],
            flaky[FlakyNames.MIN_PASSES],
            flaky[FlakyNames.CURRENT_PASSES],
        )
        runs_left = max_runs - current_runs
        passes_needed = min_passes - current_passes
        no_retry = passes_needed > runs_left
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
    def _get_test_declaration_callable_and_name(cls, test):
        """
        Get the test declaration, the test callable,
        and test callable name from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`nose.case.Test` or :class:`Function`
        :return:
            The test declaration, callable and name that is being run
        :rtype:
            `tuple` of `object`, `callable`, `unicode`
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def _make_test_flaky(cls, test, max_runs, min_passes):
        """
        Make a given test flaky.
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
        for attr, value in attrib_dict.items():
            cls._set_flaky_attribute(test, attr, value)
