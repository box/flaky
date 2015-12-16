# coding: utf-8

from __future__ import unicode_literals
import pytest

# pylint:disable=import-error
from _pytest.runner import CallInfo
# pylint:enable=import-error

from flaky._flaky_plugin import _FlakyPlugin


class FlakyXdist(object):

    def __init__(self, plugin):
        super(FlakyXdist, self).__init__()
        self._plugin = plugin

    def pytest_testnodedown(self, node, error):
        """
        Pytest hook for responding to a test node shutting down.
        Copy slave flaky report output so it's available on the master flaky report.
        """
        # pylint: disable=unused-argument, no-self-use
        if hasattr(node, 'slaveoutput') and 'flaky_report' in node.slaveoutput:
            self._plugin.stream.write(node.slaveoutput['flaky_report'])


class FlakyPlugin(_FlakyPlugin):
    """
    Plugin for py.test that allows retrying flaky tests.

    """
    runner = None
    flaky_report = True
    force_flaky = False
    max_runs = None
    min_passes = None
    config = None
    _call_infos = {}
    _PYTEST_WHEN_CALL = 'call'
    _PYTEST_OUTCOME_PASSED = 'passed'
    _PYTEST_OUTCOME_FAILED = 'failed'
    _PYTEST_EMPTY_STATUS = ('', '', '')

    def pytest_runtest_protocol(self, item, nextitem):
        """
        Pytest hook to override how tests are run.

        Runs a test collected by py.test.
        - First, monkey patches the builtin runner module to call back to
        FlakyPlugin.call_runtest_hook rather than its own.
        - Then defers to the builtin runner module to run the test,
        and repeats the process if the test needs to be rerun.
        - Reports test results to the flaky report.

        :param item:
            py.test wrapper for the test function to be run
        :type item:
            :class:`Function`
        :param nextitem:
            py.test wrapper for the next test function to be run
        :type nextitem:
            :class:`Function`
        :return:
            True if no further hook implementations should be invoked.
        :rtype:
            `bool`
        """
        test_instance = self._get_test_instance(item)
        self._copy_flaky_attributes(item, test_instance)
        if self.force_flaky and not self._has_flaky_attributes(item):
            self._make_test_flaky(
                item,
                self.max_runs,
                self.min_passes,
            )
        original_call_runtest_hook = self.runner.call_runtest_hook
        self._call_infos[item] = {}
        should_rerun = True
        try:
            self.runner.call_runtest_hook = self.call_runtest_hook
            while should_rerun:
                self.runner.pytest_runtest_protocol(item, nextitem)
                run = self._call_infos.get(item, {}).get(self._PYTEST_WHEN_CALL, None)
                if run is None:
                    return False
                passed = run.excinfo is None
                if passed:
                    should_rerun = self.add_success(item)
                else:
                    should_rerun = self.add_failure(item, run.excinfo)
                    if not should_rerun:
                        item.excinfo = run.excinfo
        finally:
            self.runner.call_runtest_hook = original_call_runtest_hook
            del self._call_infos[item]
        return True

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """
        Pytest hook to intercept the report for reruns.

        Change the report's outcome to 'passed' if flaky is going to handle the test run.
        That way, pytest will not mark the run as failed.
        """
        outcome = yield
        if call.when == self._PYTEST_WHEN_CALL:
            report = outcome.get_result()
            report.item = item
            report.original_outcome = report.outcome
            if report.failed:
                if self._will_handle_test_error_or_failure(item, None, None):
                    report.outcome = self._PYTEST_OUTCOME_PASSED

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_report_teststatus(self, report):
        """
        Pytest hook to only add final runs to the report.

        Given a test report, get the correpsonding test status.
        For tests that flaky is handling, return the empty status
        so it isn't reported; otherwise, don't change the status.
        """
        outcome = yield
        if report.when == self._PYTEST_WHEN_CALL:
            item = report.item
            if report.original_outcome == self._PYTEST_OUTCOME_PASSED:
                if self._should_handle_test_success(item):
                    outcome.force_result(self._PYTEST_EMPTY_STATUS)
            elif report.original_outcome == self._PYTEST_OUTCOME_FAILED:
                if self._will_handle_test_error_or_failure(item, None, None):
                    outcome.force_result(self._PYTEST_EMPTY_STATUS)
            delattr(report, 'item')

    def pytest_terminal_summary(self, terminalreporter):
        """
        Pytest hook to write details about flaky tests to the test report.

        Write details about flaky tests to the test report.

        :param terminalreporter:
            Terminal reporter object. Supports stream writing operations.
        :type terminalreporter:
            :class: `TerminalReporter`
        """
        if self.flaky_report:
            self._add_flaky_report(terminalreporter)

    def pytest_addoption(self, parser):
        """
        Pytest hook to add an option to the argument parser.

        :param parser:
            Parser for command line arguments and ini-file values.
        :type parser:
            :class:`Parser`
        """
        self.add_report_option(parser.addoption)

        group = parser.getgroup(
            "Force flaky", "Force all tests to be flaky.")
        self.add_force_flaky_options(group.addoption)

    def pytest_configure(self, config):
        """
        Pytest hook to get information about how the test run has been configured.

        :param config:
            The pytest configuration object for this test run.
        :type config:
            :class:`Configuration`
        """
        self.flaky_report = config.option.flaky_report
        self.flaky_success_report = config.option.flaky_success_report
        self.force_flaky = config.option.force_flaky
        self.max_runs = config.option.max_runs
        self.min_passes = config.option.min_passes
        self.runner = config.pluginmanager.getplugin("runner")
        if config.pluginmanager.hasplugin('xdist'):
            config.pluginmanager.register(FlakyXdist(self))
            self.config = config
        if hasattr(config, 'slaveoutput'):
            config.slaveoutput['flaky_report'] = ''

    def pytest_sessionfinish(self):
        """
        Pytest hook to take a final action after the session is complete.
        Copy flaky report contents so that the master process can read it.
        """
        if hasattr(self.config, 'slaveoutput'):
            self.config.slaveoutput['flaky_report'] += self.stream.getvalue()

    @property
    def stream(self):
        return self._stream

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

    @staticmethod
    def _get_test_instance(item):
        """
        Get the object containing the test. This might be `test.instance`
        or `test.parent.obj`.
        """
        test_instance = getattr(item, 'instance', None)
        if test_instance is None:
            if hasattr(item, 'parent') and hasattr(item.parent, 'obj'):
                test_instance = item.parent.obj
        return test_instance

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
        call_info = CallInfo(
            lambda: ihook(item=item, **kwds),
            when=when,
        )
        self._call_infos[item][when] = call_info
        return call_info

    def add_success(self, item):
        """
        Called when a test succeeds.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.

        :param item:
            py.test wrapper for the test function that has succeeded
        :type item:
            :class:`Function`
        """
        return self._handle_test_success(item)

    def add_failure(self, item, err):
        """
        Called when a test fails.

        Count remaining retries and compare with number of required successes
        that have not yet been achieved; retry if necessary.

        :param item:
            py.test wrapper for the test function that has succeeded
        :type item:
            :class:`Function`
        :param err:
            Information about the test failure
        :type err:
            :class: `ExceptionInfo`
        """
        if err is not None:
            error = (err.type, err.value, err.traceback)
        else:
            error = (None, None, None)
        return self._handle_test_error_or_failure(item, error)

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
    def _get_test_declaration_callable_and_name(cls, test):
        """
        Base class override.

        :param test:
            The test that has raised an error or succeeded
        :type test:
            :class:`Function`
        :return:
            The test declaration, callable and name that is being run
        :rtype:
            `tuple` of `object`, `callable`, `unicode`
        """
        callable_name = cls._get_test_callable_name(test)
        if callable_name.endswith(']') and '[' in callable_name:
            unparametrized_name = callable_name[:callable_name.index('[')]
        else:
            unparametrized_name = callable_name
        test_instance = cls._get_test_instance(test)
        if hasattr(test_instance, callable_name):
            # Test is a method of a class
            def_and_callable = getattr(test_instance, callable_name)
            return def_and_callable, def_and_callable, callable_name
        elif hasattr(test_instance, unparametrized_name):
            # Test is a parametrized method of a class
            def_and_callable = getattr(test_instance, unparametrized_name)
            return def_and_callable, def_and_callable, callable_name
        elif hasattr(test, 'runner') and hasattr(test.runner, 'run'):
            # Test is a doctest
            return test, test.runner.run, callable_name
        elif hasattr(test.module, callable_name):
            # Test is a function in a module
            def_and_callable = getattr(test.module, callable_name)
            return def_and_callable, def_and_callable, callable_name
        elif hasattr(test.module, unparametrized_name):
            # Test is a parametrized function in a module
            def_and_callable = getattr(test.module, unparametrized_name)
            return def_and_callable, def_and_callable, callable_name
        else:
            return None, None, callable_name

    def _mark_test_for_rerun(self, test):
        """Base class override. Rerun a flaky test."""


PLUGIN = FlakyPlugin()
# pytest only processes hooks defined on the module
# find all hooks defined on the plugin class and copy them to the module globals
for _pytest_hook in dir(PLUGIN):
    if _pytest_hook.startswith('pytest_'):
        globals()[_pytest_hook] = getattr(PLUGIN, _pytest_hook)
