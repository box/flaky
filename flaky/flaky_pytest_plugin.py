# coding: utf-8

from __future__ import unicode_literals
from time import time
import py

# pylint:disable=import-error
from _pytest.runner import CallInfo, Skipped
# pylint:enable=import-error

from flaky._flaky_plugin import _FlakyPlugin


def pytest_runtest_protocol(item, nextitem):
    """
    Pytest hook to override how tests are run.
    """
    PLUGIN.run_test(item, nextitem)
    return True


def pytest_terminal_summary(terminalreporter):
    """
    Pytest hook to write details about flaky tests to the test report.
    :param terminalreporter:
        Terminal reporter object. Supports stream writing operations.
    :type terminalreporter:
        :class: `TerminalReporter`
    """
    PLUGIN.terminal_summary(terminalreporter)


def pytest_addoption(parser):
    """
    Pytest hook to add an option to the argument parser.
    :param parser:
        Parser for command line arguments and ini-file values.
    :type parser:
        :class:`Parser`
    """
    PLUGIN.add_report_option(parser.addoption)

    group = parser.getgroup(
        "Force flaky", "Force all tests to be flaky.")
    PLUGIN.add_force_flaky_options(group.addoption)


def pytest_configure(config):
    """
    Pytest hook to get information about how the test run has been configured.
    :param config:
        The pytest configuration object for this test run.
    :type config:
        :class:`Configuration`
    """
    PLUGIN.flaky_report = config.option.flaky_report
    PLUGIN.force_flaky = config.option.force_flaky
    PLUGIN.max_runs = config.option.max_runs
    PLUGIN.min_passes = config.option.min_passes
    PLUGIN.runner = config.pluginmanager.getplugin("runner")


class FlakyPlugin(_FlakyPlugin):
    """
    Plugin for py.test that allows retrying flaky tests.

    """
    runner = None
    _info = None
    flaky_report = True
    force_flaky = False
    max_runs = None
    min_passes = None

    def run_test(self, item, nextitem):
        """
        Runs a test collected by py.test. First, monkey patches the builtin
        runner module to call back to FlakyPlugin.call_runtest_hook rather
        than its own. Then defer to the builtin runner module to run the test.
        :param item:
            py.test wrapper for the test function to be run
        :type item:
            :class:`Function`
        :param nextitem:
            py.test wrapper for the next test function to be run
        :type nextitem:
            :class:`Function`
        """
        self._copy_flaky_attributes(item, item.instance)
        if self.force_flaky and not self._has_flaky_attributes(item):
            self._make_test_callable_flaky(
                item,
                self.max_runs,
                self.min_passes,
            )
        patched_call_runtest_hook = self.runner.call_runtest_hook
        try:
            self.runner.call_runtest_hook = self.call_runtest_hook
            self.runner.pytest_runtest_protocol(item, nextitem)
        finally:
            self.runner.call_runtest_hook = patched_call_runtest_hook

    def call_runtest_hook(self, item, when, **kwds):
        """
        Monkey patched from the runner plugin. Responsible for running
        the test. Had to be patched to pass additional info to the
        CallInfo so the tests can be rerun if necessary.
        :param item:
            py.test wrapper for the test function to be run
        :type item:
            :class:`Function`
        """
        hookname = "pytest_runtest_" + when
        ihook = getattr(item.ihook, hookname)
        return FlakyCallInfo(
            self,
            item,
            lambda: ihook(item=item, **kwds),
            when=when
        )

    def add_success(self, info, item):
        """
        Called when a test succeeds.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.
        :param info:
            Information about the test call.
        :type info:
            :class: `FlakyCallInfo`
        :param item:
            py.test wrapper for the test function that has succeeded
        :type item:
            :class:`Function`
        """
        self._info = info
        return self._handle_test_success(item)

    def add_failure(self, info, item, err):
        """
        Called when a test fails.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.
        :param info:
            Information about the test call.
        :type info:
            :class: `FlakyCallInfo`
        :param item:
            py.test wrapper for the test function that has succeeded
        :type item:
            :class:`Function`
        :param err:
            Information about the test failure
        :type err:
            :class: `ExceptionInfo`
        """
        self._info = info
        if err is not None:
            error = (err.type, err.value, err.traceback)
        else:
            error = (None, None, None)
        return self._handle_test_error_or_failure(item, error)

    def terminal_summary(self, stream):
        """
        Write details about flaky tests to the test report.
        :param stream:
            The test stream to which the report can be written.
        :type stream:
            :class: `TerminalReporter`
        """
        if self.flaky_report:
            self._add_flaky_report(stream)

    @staticmethod
    def _get_test_callable_name(test):
        """
        Get the name of the test callable from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`Function`
        :return:
            The name of the test callable that is being run by the test
        :rtype:
            `unicode`
        """
        return test.name

    @classmethod
    def _get_test_callable_and_name(cls, test):
        """
        Get the test callable and test callable name from the test.
        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`Function`
        :return:
            The test callable (and its name) that is being run by the test
        :rtype:
            `tuple` of `callable`, `unicode`
        """
        callable_name = cls._get_test_callable_name(test)
        if hasattr(test.instance, callable_name):
            return getattr(test.instance, callable_name), callable_name
        elif hasattr(test.module, callable_name):
            return getattr(test.module, callable_name), callable_name
        else:
            return None, callable_name

    def _rerun_test(self, test):
        """Base class override. Rerun a flaky test."""
        self._info.call(test.runtest, self)


class FlakyCallInfo(CallInfo):
    """
    Subclass of pytest default runner's CallInfo.
    This subclass has an extracted call method to support
    calling the test function again in the case of a rerun.
    """
    excinfo = None
    result = None

    def __init__(self, plugin, item, func, when):
        # pylint:disable=super-init-not-called
        #: context of invocation: one of "setup", "call",
        #: "teardown", "memocollect"
        self.when = when
        self.start = time()
        self._item = item
        try:
            self.call(func, plugin)
        finally:
            self.stop = time()

    def call(self, func, plugin):
        """
        Call the test function, handling success or failure.
        :param func:
            The test function to run.
        :type func:
            `callable`
        :param plugin:
            Plugin class for flaky that can handle test success or failure.
        :type plugin:
            :class: `FlakyPlugin`
        """
        is_call = self.when == 'call'
        try:
            self.result = func()
        except KeyboardInterrupt:
            raise
        except Skipped:
            # pylint:disable=no-member
            err = py.code.ExceptionInfo()
            # pylint:enable=no-member
            self.excinfo = err
        # pylint:disable=bare-except
        except:
            # pylint:disable=no-member
            err = py.code.ExceptionInfo()
            # pylint:enable=no-member
            if is_call:
                handled_failure = plugin.add_failure(
                    self,
                    self._item,
                    err
                )
                if not handled_failure:
                    self.excinfo = err
        else:
            if is_call:
                handled_success = plugin.add_success(
                    self,
                    self._item
                )
                if not handled_success:
                    self.excinfo = None


PLUGIN = FlakyPlugin()
