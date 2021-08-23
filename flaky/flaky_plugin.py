from collections import defaultdict
from io import StringIO

from flaky import defaults
from flaky.names import FlakyNames


class FlakyPlugin:
    """
    Plugin for pytest that allows retrying flaky tests.

    """
    runner = None
    flaky_report = True
    force_flaky = False
    max_runs = None
    min_passes = None
    config = None
    call_infos = {}
    flaky_attributes = defaultdict(dict)
    _PYTEST_WHEN_SETUP = 'setup'
    _PYTEST_WHEN_CALL = 'call'
    PYTEST_WHENS = (_PYTEST_WHEN_SETUP, _PYTEST_WHEN_CALL)
    PYTEST_OUTCOME_PASSED = 'passed'
    PYTEST_OUTCOME_FAILED = 'failed'
    _PYTEST_EMPTY_STATUS = ('', '', '')

    _retry_failure_message = ' failed ({0} runs remaining out of {1}).'
    _failure_message = ' failed; it passed {0} out of the required {1} times.'
    _not_rerun_message = ' failed and was not selected for rerun.'

    def __init__(self):
        super().__init__()
        self._stream = StringIO()
        self._flaky_success_report = True
        self._had_flaky_tests = False

    @property
    def stream(self):
        """
        Returns the stream used for building the flaky report.
        Anything written to this stream before the end of the test run
        will be written to the flaky report.

        :return:
            The stream used for building the flaky report.
        :rtype:
            :class:`StringIO`
        """
        return self._stream

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

    def _should_handle_test_error_or_failure(self, test):
        """
        Whether or not flaky should handle a test error or failure.
        Only handle tests marked flaky.
        Count remaining retries and compare with number of required successes that have not yet been achieved.

        This method may be called multiple times for the same test run, so it has no side effects.

        :param test:
            The test that has raised an error
        :type test:
            :class:`Function`
        :return:
            True, if the test needs to be rerun; False, otherwise.
        :rtype:
            `bool`
        """
        if not self._is_test_marked_flaky(test):
            return False
        flaky_attributes = self.get_flaky_attributes(test)
        flaky_attributes[FlakyNames.CURRENT_RUNS] += 1
        has_failed = self.has_flaky_test_failed(flaky_attributes)
        return not has_failed

    def will_handle_test_error_or_failure(self, test, name, err):
        """
        Whether or not flaky will handle a test error or failure.
        Returns True if the plugin should handle the test result, and
        the `rerun_filter` returns True.

        :param test:
            The test that has raised an error
        :type test:
            :class:`Item`
        :param name:
            The name of the test that has raised an error
        :type name:
            `unicode`
        :param err:
            Information about the test failure (from sys.exc_info())
        :type err:
            `tuple` of `type`, :class:`Exception`, `traceback`
        :return:
            True, if the test will be rerun by flaky; False, otherwise.
        :rtype:
            `bool`
        """
        return self._should_handle_test_error_or_failure(test) and self._should_rerun_test(test, name, err)

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
           :class:`Item`
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

    def should_handle_test_success(self, test):
        if not self._is_test_marked_flaky(test):
            return False
        flaky = self.get_flaky_attributes(test)
        flaky[FlakyNames.CURRENT_PASSES] += 1
        flaky[FlakyNames.CURRENT_RUNS] += 1
        return not self._has_flaky_test_succeeded(flaky)

    def add_flaky_report(self, stream):
        """
        Baseclass override. Write details about flaky tests to the test report.

        :param stream:
            The test stream to which the report can be written.
        :type stream:
            `file`
        """
        value = self._stream.getvalue()

        # Do not print report if there were no tests marked 'flaky' at all.
        if not self._had_flaky_tests and not value:
            return

        # If everything succeeded and --no-success-flaky-report is specified
        # don't print anything.
        if not self._flaky_success_report and not value:
            return

        stream.write('===Flaky Test Report===\n\n')

        # Python 2 will write to the stderr stream as a byte string, whereas
        # Python 3 will write to the stream as text. Only encode into a byte
        # string if the write tries to encode it first and raises a
        # UnicodeEncodeError.
        try:
            stream.write(value)
        except UnicodeEncodeError:
            stream.write(value.encode('utf-8', 'replace'))

        stream.write('\n===End Flaky Test Report===\n')

    @classmethod
    def _get_flaky_attribute(cls, test_item, flaky_attribute):
        """
        Gets an attribute describing the flaky test.

        :param test_item:
            The test method from which to get the attribute
        :type test_item:
            `callable` or :class:`Item`
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
        return cls.flaky_attributes[test_item].get(flaky_attribute)

    @classmethod
    def set_flaky_attribute(cls, test_item, flaky_attribute, value):
        """
        Sets an attribute on a flaky test. Uses magic __dict__ since setattr
        doesn't work for bound methods.

        :param test_item:
            The test callable on which to set the attribute
        :type test_item:
            `callable` or :class:`Function`
        :param flaky_attribute:
            The name of the attribute to set
        :type flaky_attribute:
            `unicode`
        :param value:
            The value to set the test callable's attribute to.
        :type value:
            varies
        """
        cls.flaky_attributes[test_item][flaky_attribute] = value

    @classmethod
    def _increment_flaky_attribute(cls, test_item, flaky_attribute):
        """
        Increments the value of an attribute on a flaky test.

        :param test_item:
            The test callable on which to set the attribute
        :type test_item:
            `callable` or :class:`Item`
        :param flaky_attribute:
            The name of the attribute to set
        :type flaky_attribute:
            `unicode`
        """
        cls.set_flaky_attribute(test_item, flaky_attribute, cls._get_flaky_attribute(test_item, flaky_attribute) + 1)

    @classmethod
    def _is_test_marked_flaky(cls, test):
        """
        Returns True if the test callable in question is marked as flaky.

        :param test:
            The test that is being prepared to run
        :type test:
            :class:`Function`
        :return:
        :rtype:
            `bool`
        """
        return test in cls.flaky_attributes

    @classmethod
    def get_flaky_attributes(cls, test_item):
        """
        Get all the flaky related attributes from the test.

        :param test_item:
            The test callable from which to get the flaky related attributes.
        :type test_item:
            `callable` or :class:`Item`
        :return:
        :rtype:
            `dict` of `unicode` to varies
        """
        return {
            attr: cls._get_flaky_attribute(
                test_item,
                attr,
            ) for attr in FlakyNames()
        }

    @classmethod
    def has_flaky_test_failed(cls, flaky):
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
    def make_test_flaky(cls, test, max_runs=None, min_passes=None, rerun_filter=None):
        """
        Make a given test flaky.

        :param test:
            The test in question.
        :type test:
            :class:`Item`
        :param max_runs:
            The value of the FlakyNames.MAX_RUNS attribute to use.
        :type max_runs:
            `int`
        :param min_passes:
            The value of the FlakyNames.MIN_PASSES attribute to use.
        :type min_passes:
            `int`
        :param rerun_filter:
            Filter function to decide whether a test should be rerun if it fails.
            Function signature is as follows:
                (err, name, test, plugin) -> should_rerun
            - err (`tuple` of `class`, :class:`Exception`, `traceback`):
                Information about the test failure (from sys.exc_info())
            - name (`unicode`):
                The test name
            - test (:class:`Item`):
                The test that has raised an error
            - plugin (:class:`FlakyPlugin`):
                The flaky plugin. Has a :prop:`stream` that can be written to in
                order to add to the Flaky Report.
        :type rerun_filter:
            `callable`
        """
        if cls._is_test_marked_flaky(test):
            return
        attrib_dict = defaults.default_flaky_attributes(max_runs, min_passes, rerun_filter)
        for attr, value in attrib_dict.items():
            cls.set_flaky_attribute(test, attr, value)

    def _log_test_failure(self, test_callable_name, err, message):
        """
        Add messaging about a test failure to the stream, which will be
        printed by the plugin's report method.
        """
        self._stream.writelines([
            str(test_callable_name),
            message,
            '\n\t',
            str(err[0]),
            '\n\t',
            str(err[1]),
            '\n\t',
            str(err[2]),
            '\n',
        ])

    @property
    def flaky_success_report(self):
        """
        Property for setting whether or not the plugin will print results about
        flaky tests that were successful.

        :return:
            Whether or not flaky will report on test successes.
        :rtype:
            `bool`
        """
        return self._flaky_success_report

    @flaky_success_report.setter
    def flaky_success_report(self, value):
        """
        Property for setting whether or not the plugin will print results about
        flaky tests that were successful.

        :param value:
            Whether or not flaky will report on test successes.
        :type value:
            `bool`
        """
        self._flaky_success_report = value

    def add_success(self, item):
        """
        Called when a test succeeds.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved.

        :param item:
            pytest wrapper for the test function that has succeeded
        :type item:
            :class:`Function`
        """
        try:
            name = item.name
        except AttributeError:
            return False
        need_reruns = self.should_handle_test_success(item)

        if self._is_test_marked_flaky(item):
            self._had_flaky_tests = True
            flaky = self.get_flaky_attributes(item)
            min_passes = flaky[FlakyNames.MIN_PASSES]
            passes = flaky[FlakyNames.CURRENT_PASSES] + 1
            self.set_flaky_attribute(item, FlakyNames.CURRENT_PASSES, passes)
            self._increment_flaky_attribute(item, FlakyNames.CURRENT_RUNS)

            if self._flaky_success_report:
                self._stream.writelines([
                    str(name),
                    ' passed {} out of the required {} times. '.format(
                        passes,
                        min_passes,
                    ),
                ])
                if need_reruns:
                    self._stream.write(
                        'Running test again until it passes {} times.\n'.format(
                            min_passes,
                        )
                    )
                else:
                    self._stream.write('Success!\n')

        return need_reruns

    def add_failure(self, item, err):
        """
        Called when a test fails.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved.

        :param item:
            pytest wrapper for the test function that has succeeded
        :type item:
            :class:`Item`
        :param err:
            Information about the test failure
        :type err:
            :class: `ExceptionInfo`
        """
        if err is not None:
            error = (err.type, err.value, err.traceback)
        else:
            error = (None, None, None)

        try:
            name = item.name
        except AttributeError:
            return False

        if self._is_test_marked_flaky(item):
            self._had_flaky_tests = True
            errs = self._get_flaky_attribute(item, FlakyNames.CURRENT_ERRORS) or []
            self.set_flaky_attribute(item, FlakyNames.CURRENT_ERRORS, errs)
            errs.append(error)
            should_handle = self._should_handle_test_error_or_failure(item)
            self._increment_flaky_attribute(item, FlakyNames.CURRENT_RUNS)
            if should_handle:
                flaky_attributes = self.get_flaky_attributes(item)
                if self._should_rerun_test(item, name, error):
                    self._log_intermediate_failure(error, flaky_attributes, name)
                    return True
                self._log_test_failure(name, error, self._not_rerun_message)
                return False
            flaky_attributes = self.get_flaky_attributes(item)
            self._report_final_failure(error, flaky_attributes, name)
        return False
