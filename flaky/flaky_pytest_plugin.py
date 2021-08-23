from _pytest import runner  # pylint:disable=import-error

from flaky.flaky_plugin import FlakyPlugin


def _get_worker_output(item):
    worker_output = None
    if hasattr(item, 'workeroutput'):
        worker_output = item.workeroutput
    elif hasattr(item, 'slaveoutput'):
        worker_output = item.slaveoutput
    return worker_output


class FlakyXdist:

    def __init__(self, plugin):
        super().__init__()
        self._plugin = plugin

    def pytest_testnodedown(self, node, error):
        """
        Pytest hook for responding to a test node shutting down.
        Copy worker flaky report output so it's available on the master flaky report.
        """
        # pylint: disable=unused-argument, no-self-use
        worker_output = _get_worker_output(node)
        if worker_output is not None and 'flaky_report' in worker_output:
            self._plugin.stream.write(worker_output['flaky_report'])


def pytest_addoption(parser):
    """
    Pytest hook to add an option to the argument parser.

    :param parser:
        Parser for command line arguments and ini-file values.
    :type parser:
        :class:`Parser`
    """
    parser.addoption(
        '--no-flaky-report',
        action='store_false',
        dest='flaky_report',
        default=True,
        help="Suppress the report at the end of the "
             "run detailing flaky test results.",
    )
    parser.addoption(
        '--no-success-flaky-report',
        action='store_false',
        dest='flaky_success_report',
        default=True,
        help="Suppress reporting flaky test successes"
             "in the report at the end of the "
             "run detailing flaky test results.",
    )

    group = parser.getgroup(
        "Force flaky", "Force all tests to be flaky.")

    group.addoption(
        '--force-flaky',
        action="store_true",
        dest="force_flaky",
        default=False,
        help="If this option is specified, we will treat all tests as "
             "flaky."
    )
    group.addoption(
        '--max-runs',
        action="store",
        dest="max_runs",
        type=int,
        default=2,
        help="If --force-flaky is specified, we will run each test at "
             "most this many times (unless the test has its own flaky "
             "decorator)."
    )
    group.addoption(
        '--min-passes',
        action="store",
        dest="min_passes",
        type=int,
        default=1,
        help="If --force-flaky is specified, we will run each test at "
             "least this many times (unless the test has its own flaky "
             "decorator)."
    )


def pytest_configure(config):
    """
    Pytest hook to get information about how the test run has been configured.

    :param config:
        The pytest configuration object for this test run.
    :type config:
        :class:`Configuration`
    """
    plugin = FlakyPlugin()
    plugin.flaky_report = config.option.flaky_report
    plugin.flaky_success_report = config.option.flaky_success_report
    plugin.force_flaky = config.option.force_flaky
    plugin.max_runs = config.option.max_runs
    plugin.min_passes = config.option.min_passes

    config.pluginmanager.register(plugin, name='flaky.base')

    if config.pluginmanager.hasplugin('xdist'):
        config.pluginmanager.register(FlakyXdist(plugin), name='flaky.xdist')
    worker_output = _get_worker_output(config)
    if worker_output is not None:
        worker_output['flaky_report'] = ''

    config.addinivalue_line('markers', 'flaky: marks tests to be automatically retried upon failure')


def pytest_runtest_setup(item):
    """
    Pytest hook to modify the test before it's run.

    :param item:
        The test item.
    """
    plugin = item.config.pluginmanager.getplugin('flaky.base')
    found_marker = False
    if hasattr(item, 'iter_markers'):
        for marker in item.iter_markers(name='flaky'):
            plugin.make_test_flaky(item, *marker.args, **marker.kwargs)
            found_marker = True
            break
    elif hasattr(item, 'get_marker'):
        marker = item.get_marker('flaky')
        if marker:
            plugin.make_test_flaky(item, *marker.args, **marker.kwargs)
            found_marker = True
    if not found_marker and plugin.force_flaky:
        plugin.make_test_flaky(
            item,
            plugin.max_runs,
            plugin.min_passes,
        )


def pytest_runtest_protocol(item, nextitem):
    """
    Pytest hook to override how tests are run.

    Runs a test collected by pytest.
    - First, monkey patches the builtin runner module to call back to
    FlakyPlugin.call_runtest_hook rather than its own.
    - Then defers to the builtin runner module to run the test,
    and repeats the process if the test needs to be rerun.
    - Reports test results to the flaky report.

    :param item:
        pytest wrapper for the test function to be run
    :type item:
        :class:`Function`
    :param nextitem:
        pytest wrapper for the next test function to be run
    :type nextitem:
        :class:`Function`
    :return:
        True if no further hook implementations should be invoked.
    :rtype:
        `bool`
    """
    plugin = item.config.pluginmanager.getplugin('flaky.base')
    test_runner = item.config.pluginmanager.getplugin("runner")
    original_call_and_report = test_runner.call_and_report
    plugin.call_infos[item] = {}
    should_rerun = True
    try:
        test_runner.call_and_report = call_and_report
        while should_rerun:
            test_runner.pytest_runtest_protocol(item, nextitem)
            call_info = None
            excinfo = None
            for when in plugin.PYTEST_WHENS:
                call_info = plugin.call_infos.get(item, {}).get(when, None)
                excinfo = getattr(call_info, 'excinfo', None)
                if excinfo is not None:
                    break

            if call_info is None:
                return False
            passed = excinfo is None
            if passed:
                should_rerun = plugin.add_success(item)
            else:
                skipped = excinfo.typename == 'Skipped'
                should_rerun = not skipped and plugin.add_failure(item, excinfo)
                if not should_rerun:
                    item.excinfo = excinfo
    finally:
        test_runner.call_and_report = original_call_and_report
        del plugin.call_infos[item]
    return True


def call_and_report(item, when, log=True, **kwds):
    """
    Monkey patched from the runner plugin. Responsible for running
    the test and reporting the outcome.
    Had to be patched to avoid reporting about test retries.

    :param item:
        pytest wrapper for the test function to be run
    :type item:
        :class:`Function`
    :param when:
        The stage of the test being run. Usually one of 'setup', 'call', 'teardown'.
    :type when:
        `str`
    :param log:
        Whether or not to report the test outcome. Ignored for test
        retries; flaky doesn't report test retries, only the final outcome.
    :type log:
        `bool`
    """
    call = runner.call_runtest_hook(item, when, **kwds)
    plugin = item.config.pluginmanager.getplugin('flaky.base')
    plugin.call_infos[item][when] = call
    hook = item.ihook
    report = hook.pytest_runtest_makereport(item=item, call=call)
    # Start flaky modifications
    # only retry on call, not setup or teardown
    if report.when in plugin.PYTEST_WHENS:
        if report.outcome == plugin.PYTEST_OUTCOME_PASSED:
            if plugin.should_handle_test_success(item):
                log = False
        elif report.outcome == plugin.PYTEST_OUTCOME_FAILED:
            name = item.name
            call_info = plugin.call_infos.get(item, {}).get(when, None)
            if call_info is not None and call_info.excinfo:
                err = (call_info.excinfo.type, call_info.excinfo.value, call_info.excinfo.tb)
            else:
                err = (None, None, None)
            if plugin.will_handle_test_error_or_failure(item, name, err):
                log = False
    # End flaky modifications
    if log:
        hook.pytest_runtest_logreport(report=report)
    test_runner = item.config.pluginmanager.getplugin("runner")
    if test_runner.check_interactive_exception(call, report):
        hook.pytest_exception_interact(node=item, call=call, report=report)
    return report


def pytest_terminal_summary(terminalreporter, config):
    """
    Pytest hook to write details about flaky tests to the test report.

    Write details about flaky tests to the test report.

    :param terminalreporter:
        Terminal reporter object. Supports stream writing operations.
    :type terminalreporter:
        :class: `TerminalReporter`
    """
    plugin = config.pluginmanager.getplugin('flaky.base')
    if plugin.flaky_report:
        plugin.add_flaky_report(terminalreporter)


def pytest_sessionfinish(session):
    """
    Pytest hook to take a final action after the session is complete.
    Copy flaky report contents so that the main process can read it.
    """
    worker_output = _get_worker_output(session.config)
    if worker_output is not None:
        worker_output['flaky_report'] += session.config.pluginmanager.getplugin('flaky.base').stream.getvalue()
