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


class FlakyXdist(object):

    def pytest_testnodedown(self, node, error):
        # pylint: disable=unused-argument, no-self-use
        if hasattr(node, 'slaveoutput') and 'flaky_report' in node.slaveoutput:
            PLUGIN.stream.write(node.slaveoutput['flaky_report'])


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
    if config.pluginmanager.hasplugin('xdist'):
        config.pluginmanager.register(FlakyXdist())
        PLUGIN.config = config
    if hasattr(config, 'slaveoutput'):
        config.slaveoutput['flaky_report'] = ''


def pytest_sessionfinish():
    if hasattr(PLUGIN.config, 'slaveoutput'):
        PLUGIN.config.slaveoutput['flaky_report'] += PLUGIN.stream.getvalue()


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
    config = None

    @property
    def stream(self):
        return self._stream

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
        test_instance = self._get_test_instance(item)
        self._copy_flaky_attributes(item, test_instance)
        if self.force_flaky and not self._has_flaky_attributes(item):
            self._make_test_flaky(
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
        test_instance = cls._get_test_instance(test)
        if hasattr(test_instance, callable_name):
            def_and_callable = getattr(test_instance, callable_name)
            return def_and_callable, def_and_callable, callable_name
        elif hasattr(test, 'runner') and hasattr(test.runner, 'run'):
            return test, test.runner.run, callable_name
        elif hasattr(test.module, callable_name):
            def_and_callable = getattr(test.module, callable_name)
            return def_and_callable, def_and_callable, callable_name
        else:
            return None, None, callable_name

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
        self._want_rerun = []
        self.excinfo = None
        try:
            self.call(func, plugin)
        finally:
            self.stop = time()

    def _handle_error(self, plugin):
        """
        Handle an error that occurs during test execution.
        If the test is marked flaky and there are reruns remaining,
        don't report the test as failed.
        """
        # pylint:disable=no-member
        err = self.excinfo or py.code.ExceptionInfo()
        # pylint:enable=no-member
        self.excinfo = None
        self._want_rerun.append(plugin.add_failure(
            self,
            self._item,
            err,
        ))
        self.excinfo = None if self._want_rerun[0] else err

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
            # pytest's unittest plugin for some reason doesn't actually raise
            # errors. It just adds them to the unittest result. In order to
            # determine whether or not the test needs to be rerun, this
            # code looks for the _excinfo attribute set by the plugin.
            excinfo = getattr(self._item, '_excinfo', None)
            if isinstance(excinfo, list) and len(excinfo) > 0:
                self.excinfo = excinfo.pop(0)
        except KeyboardInterrupt:
            raise
        except Skipped:
            # pylint:disable=no-member
            err = py.code.ExceptionInfo()
            # pylint:enable=no-member
            self.excinfo = err
            return
        # pylint:disable=bare-except
        except:
            if is_call:
                self._handle_error(plugin)
        else:
            if is_call:
                if self.excinfo is not None:
                    self._handle_error(plugin)
                else:
                    handled_success = plugin.add_success(
                        self,
                        self._item,
                    )
                    if not handled_success:
                        self.excinfo = None


PLUGIN = FlakyPlugin()
