# coding: utf-8

from __future__ import unicode_literals
from io import StringIO
from mock import Mock, patch
# pylint:disable=import-error
import pytest
# pylint:enable=import-error
from flaky import flaky
from flaky import _flaky_plugin
from flaky.flaky_pytest_plugin import (
    CallInfo,
    FlakyPlugin,
    FlakyXdist,
    PLUGIN,
)
from flaky.names import FlakyNames
from flaky.utils import unicode_type


@pytest.fixture
def mock_io(monkeypatch):
    mock_string_io = StringIO()

    def string_io():
        return mock_string_io
    monkeypatch.setattr(_flaky_plugin, 'StringIO', string_io)
    return mock_string_io


@pytest.fixture
def string_io():
    return StringIO()


@pytest.fixture
def flaky_plugin(mock_io):
    # pylint:disable=unused-argument
    return FlakyPlugin()


@pytest.fixture
def mock_plugin_rerun(monkeypatch, flaky_plugin):
    calls = []

    def rerun_test(test):
        calls.append(test)
    monkeypatch.setattr(flaky_plugin, '_mark_test_for_rerun', rerun_test)

    def get_calls():
        return calls

    return get_calls


@pytest.fixture(params=['instance', 'module', 'parent'])
def flaky_test(request):
    def test_function():
        pass
    test_owner = Mock()
    setattr(test_owner, 'test_method', test_function)
    setattr(test_owner, 'obj', test_owner)
    kwargs = {request.param: test_owner}
    test = MockTestItem(**kwargs)
    setattr(test, 'owner', test_owner)
    return test


@pytest.fixture
def call_info(flaky_test):
    return MockFlakyCallInfo(flaky_test, 'call')


@pytest.fixture
def mock_error():
    return MockError()


class MockError(object):
    def __init__(self):
        super(MockError, self).__init__()
        self.type = Mock()
        self.value = Mock()
        self.value.message = 'failed'
        self.traceback = Mock()


class MockTestItem(object):
    name = 'test_method'
    instance = None
    module = None
    parent = None

    def __init__(self, instance=None, module=None, parent=None):
        if instance is not None:
            self.instance = instance
        if module is not None:
            self.module = module
        if parent is not None:
            self.parent = parent

    def runtest(self):
        pass


class MockFlakyCallInfo(CallInfo):
    def __init__(self, item, when):
        # pylint:disable=super-init-not-called
        # super init not called because it has unwanted side effects
        self.when = when
        self._item = item


def test_flaky_plugin_report(flaky_plugin, mock_io, string_io):
    flaky_report = 'Flaky tests passed; others failed. ' \
                   'No more tests; that ship has sailed.'
    expected_string_io = StringIO()
    expected_string_io.write('===Flaky Test Report===\n\n')
    expected_string_io.write(flaky_report)
    expected_string_io.write('\n===End Flaky Test Report===\n')
    mock_io.write(flaky_report)
    flaky_plugin.pytest_terminal_summary(string_io)
    assert string_io.getvalue() == expected_string_io.getvalue()


@pytest.fixture(params=(
    {},
    {'flaky_report': ''},
    {'flaky_report': 'ŝȁḿҏľȅ ƭȅхƭ'},
))
def mock_xdist_node_slaveoutput(request):
    return request.param


@pytest.fixture(params=(None, object()))
def mock_xdist_error(request):
    return request.param


@pytest.mark.parametrize('assign_slaveoutput', (True, False))
def test_flaky_xdist_nodedown(
        mock_xdist_node_slaveoutput,
        assign_slaveoutput,
        mock_xdist_error
):
    flaky_xdist = FlakyXdist(PLUGIN)
    node = Mock()
    if assign_slaveoutput:
        node.slaveoutput = mock_xdist_node_slaveoutput
    else:
        delattr(node, 'slaveoutput')
    mock_stream = Mock(StringIO)
    with patch.object(PLUGIN, '_stream', mock_stream):
        flaky_xdist.pytest_testnodedown(node, mock_xdist_error)
    if assign_slaveoutput and 'flaky_report' in mock_xdist_node_slaveoutput:
        mock_stream.write.assert_called_once_with(
            mock_xdist_node_slaveoutput['flaky_report'],
        )
    else:
        assert not mock_stream.write.called


_REPORT_TEXT1 = 'Flaky report text'
_REPORT_TEXT2 = 'Ḿőŕȅ ƒľȁƙŷ ŕȅҏőŕƭ ƭȅхƭ'


@pytest.mark.parametrize('initial_report,stream_report,expected_report', (
    ('', '', ''),
    ('', _REPORT_TEXT1, _REPORT_TEXT1),
    (_REPORT_TEXT1, '', _REPORT_TEXT1),
    (_REPORT_TEXT1, _REPORT_TEXT2, _REPORT_TEXT1 + _REPORT_TEXT2),
    (_REPORT_TEXT2, _REPORT_TEXT1, _REPORT_TEXT2 + _REPORT_TEXT1),
))
def test_flaky_session_finish_copies_flaky_report(
        initial_report,
        stream_report,
        expected_report,
):
    PLUGIN.stream.seek(0)
    PLUGIN.stream.truncate()
    PLUGIN.stream.write(stream_report)
    PLUGIN.config = Mock()
    PLUGIN.config.slaveoutput = {'flaky_report': initial_report}
    PLUGIN.pytest_sessionfinish()
    assert PLUGIN.config.slaveoutput['flaky_report'] == expected_report


def test_flaky_plugin_can_suppress_success_report(
    flaky_test,
    flaky_plugin,
    call_info,
    string_io,
    mock_io,
):
    flaky()(flaky_test)
    # pylint:disable=protected-access
    flaky_plugin._flaky_success_report = False
    # pylint:enable=protected-access
    call_info.when = 'call'
    actual_plugin_handles_success = flaky_plugin.add_success(flaky_test)

    assert actual_plugin_handles_success is False
    assert string_io.getvalue() == mock_io.getvalue()


def test_flaky_plugin_raises_errors_in_fixture_setup(
        flaky_test,
        flaky_plugin,
        string_io,
        mock_io,
):
    """
    Test for Issue #57 - fixtures which raise an error should show up as
    test errors.

    This test ensures that exceptions occurring when running a test
    fixture are copied into the call info's excinfo field.
    """
    def error_raising_setup_function(item):
        assert item is flaky_test
        item.ran_setup = True
        return 5 / 0

    flaky()(flaky_test)
    flaky_test.ihook = Mock()
    flaky_test.ihook.pytest_runtest_setup = error_raising_setup_function
    flaky_plugin._call_infos[flaky_test] = {}  # pylint:disable=protected-access
    call_info = flaky_plugin.call_runtest_hook(flaky_test, 'setup')
    assert flaky_test.ran_setup
    assert string_io.getvalue() == mock_io.getvalue()
    assert call_info.excinfo.type is ZeroDivisionError


class TestFlakyPytestPlugin(object):
    _test_method_name = 'test_method'

    def test_flaky_plugin_handles_success(
        self,
        flaky_test,
        flaky_plugin,
        call_info,
        string_io,
        mock_io,
    ):
        self._test_flaky_plugin_handles_success(
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
        )

    def test_flaky_plugin_handles_success_for_needs_rerun(
        self,
        flaky_test,
        flaky_plugin,
        call_info,
        string_io,
        mock_io,
        mock_plugin_rerun,
    ):
        self._test_flaky_plugin_handles_success(
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
            min_passes=2,
        )
        assert mock_plugin_rerun()[0] == flaky_test

    def test_flaky_plugin_ignores_success_for_non_flaky_test(
        self,
        flaky_plugin,
        flaky_test,
        call_info,
        string_io,
        mock_io,
    ):
        flaky_plugin.add_success(flaky_test)
        self._assert_test_ignored(mock_io, string_io, call_info)

    def test_flaky_plugin_ignores_failure_for_non_flaky_test(
        self,
        flaky_plugin,
        flaky_test,
        call_info,
        string_io,
        mock_io,
    ):
        flaky_plugin.add_failure(flaky_test, None)
        self._assert_test_ignored(mock_io, string_io, call_info)

    def test_flaky_plugin_handles_failure(
        self,
        flaky_test,
        flaky_plugin,
        call_info,
        string_io,
        mock_io,
        mock_error,
        mock_plugin_rerun,
    ):
        self._test_flaky_plugin_handles_failure(
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
            mock_error,
        )
        assert mock_plugin_rerun()[0] == flaky_test

    def test_flaky_plugin_handles_failure_for_no_more_retries(
        self,
        flaky_test,
        flaky_plugin,
        call_info,
        string_io,
        mock_io,
        mock_error,
    ):
        self._test_flaky_plugin_handles_failure(
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
            mock_error,
            max_runs=1,
        )

    def test_flaky_plugin_handles_additional_failures(
        self,
        flaky_test,
        flaky_plugin,
        call_info,
        string_io,
        mock_io,
        mock_error,
        mock_plugin_rerun,
    ):
        self._test_flaky_plugin_handles_failure(
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
            mock_error,
            current_errors=[None],
        )
        assert mock_plugin_rerun()[0] == flaky_test

    def _assert_flaky_attributes_contains(
        self,
        expected_flaky_attributes,
        test,
    ):
        actual_flaky_attributes = self._get_flaky_attributes(test)
        assert all(
            item in actual_flaky_attributes.items()
            for item in expected_flaky_attributes.items()
        )

    def test_flaky_plugin_exits_after_false_rerun_filter(
            self,
            flaky_test,
            flaky_plugin,
            call_info,
            string_io,
            mock_io,
            mock_error,
            mock_plugin_rerun,
    ):
        err_tuple = (mock_error.type, mock_error.value, mock_error.traceback)

        def rerun_filter(err, name, test, plugin):
            assert err == err_tuple
            assert name == flaky_test.name
            assert test is flaky_test
            assert plugin is flaky_plugin
            return False

        flaky(rerun_filter=rerun_filter)(flaky_test)
        call_info.when = 'call'

        actual_plugin_handles_failure = flaky_plugin.add_failure(
            flaky_test,
            mock_error,
        )
        assert actual_plugin_handles_failure is False
        assert not mock_plugin_rerun()

        string_io.writelines([
            self._test_method_name,
            ' failed and was not selected for rerun.',
            '\n\t',
            unicode_type(mock_error.type),
            '\n\t',
            unicode_type(mock_error.value),
            '\n\t',
            unicode_type(mock_error.traceback),
            '\n',
        ])
        assert string_io.getvalue() == mock_io.getvalue()

    @staticmethod
    def _assert_test_ignored(mock_io, string_io, call_info):
        assert call_info
        assert mock_io.getvalue() == string_io.getvalue()

    def _test_flaky_plugin_handles_success(
        self,
        test,
        plugin,
        info,
        stream,
        mock_stream,
        current_passes=0,
        current_runs=0,
        max_runs=2,
        min_passes=1,
    ):
        flaky(max_runs, min_passes)(test)
        setattr(
            test,
            FlakyNames.CURRENT_PASSES,
            current_passes,
        )
        setattr(
            test,
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )

        too_few_passes = current_passes + 1 < min_passes
        retries_remaining = current_runs + 1 < max_runs
        expected_plugin_handles_success = too_few_passes and retries_remaining

        info.when = 'call'
        actual_plugin_handles_success = plugin.add_success(test)

        assert expected_plugin_handles_success == actual_plugin_handles_success
        self._assert_flaky_attributes_contains(
            {
                FlakyNames.CURRENT_PASSES: current_passes + 1,
                FlakyNames.CURRENT_RUNS: current_runs + 1,
            },
            test,
        )
        stream.writelines([
            self._test_method_name,
            " passed {0} out of the required {1} times. ".format(
                current_passes + 1, min_passes,
            ),
        ])
        if expected_plugin_handles_success:
            stream.write(
                'Running test again until it passes {0} times.\n'.format(
                    min_passes,
                ),
            )
        else:
            stream.write('Success!\n')
        assert stream.getvalue() == mock_stream.getvalue()

    def _test_flaky_plugin_handles_failure(
        self,
        test,
        plugin,
        info,
        stream,
        mock_stream,
        mock_error,
        current_errors=None,
        current_passes=0,
        current_runs=0,
        max_runs=2,
        min_passes=1,
        rerun_filter=None,
    ):
        flaky(max_runs, min_passes, rerun_filter)(test)
        if current_errors is None:
            current_errors = [None]
        else:
            current_errors.append(None)
        setattr(
            test,
            FlakyNames.CURRENT_ERRORS,
            current_errors,
        )
        setattr(
            test,
            FlakyNames.CURRENT_PASSES,
            current_passes,
        )
        setattr(
            test,
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )

        too_few_passes = current_passes < min_passes
        retries_remaining = current_runs + 1 < max_runs
        expected_plugin_handles_failure = too_few_passes and retries_remaining

        info.when = 'call'
        actual_plugin_handles_failure = plugin.add_failure(
            test,
            mock_error,
        )

        assert expected_plugin_handles_failure == actual_plugin_handles_failure
        self._assert_flaky_attributes_contains(
            {
                FlakyNames.CURRENT_RUNS: current_runs + 1,
                FlakyNames.CURRENT_ERRORS: current_errors
            },
            test,
        )
        if expected_plugin_handles_failure:
            stream.writelines([
                self._test_method_name,
                ' failed ({0} runs remaining out of {1}).'.format(
                    max_runs - current_runs - 1, max_runs
                ),
                '\n\t',
                unicode_type(mock_error.type),
                '\n\t',
                unicode_type(mock_error.value),
                '\n\t',
                unicode_type(mock_error.traceback),
                '\n',
            ])
        else:
            message = ' failed; it passed {0} out of the required {1} times.'
            stream.writelines([
                self._test_method_name,
                message.format(
                    current_passes,
                    min_passes
                ),
                '\n\t',
                unicode_type(mock_error.type),
                '\n\t',
                unicode_type(mock_error.value),
                '\n\t',
                unicode_type(mock_error.traceback),
                '\n',
            ])
        assert stream.getvalue() == mock_stream.getvalue()

    @staticmethod
    def _get_flaky_attributes(test):
        actual_flaky_attributes = dict((
            (attr, getattr(
                test,
                attr,
                None,
            )) for attr in FlakyNames()
        ))
        return actual_flaky_attributes
