# coding: utf-8

from __future__ import unicode_literals
from io import StringIO

# pylint:disable=import-error
import pytest
# pylint:enable=import-error
from flaky import flaky
from flaky import _flaky_plugin
from flaky.flaky_pytest_plugin import FlakyPlugin, FlakyCallInfo
from flaky.names import FlakyNames
from flaky.utils import unicode_type


# pylint:disable=redefined-outer-name


@pytest.fixture(autouse=True)
def mock_io(monkeypatch):
    mock_string_io = StringIO()

    def string_io():
        return mock_string_io
    monkeypatch.setattr(_flaky_plugin, 'StringIO', string_io)
    return mock_string_io


@pytest.fixture(autouse=True)
def string_io():
    return StringIO()


@pytest.fixture(autouse=True)
def flaky_plugin(mock_io):
    # pylint:disable=unused-argument
    return FlakyPlugin()


@pytest.fixture
def mock_plugin_rerun(monkeypatch, flaky_plugin):
    calls = []

    def rerun_test(test):
        calls.append(test)
    monkeypatch.setattr(flaky_plugin, '_rerun_test', rerun_test)

    def get_calls():
        return calls

    return get_calls


@pytest.fixture(autouse=True)
def flaky_test():
    def test_function():
        pass
    instance = Mock()
    setattr(instance, 'test_method', test_function)
    return MockTestItem(instance)


@pytest.fixture(autouse=True)
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

    def __init__(self, instance):
        self.instance = instance
        self.module = instance

    def runtest(self):
        pass


class MockFlakyCallInfo(FlakyCallInfo):
    def __init__(self, item, when):
        # pylint:disable=super-init-not-called
        # super init not called because it has unwanted side effects
        self.when = when
        self._item = item


class Mock(object):
    pass


def test_flaky_plugin_report(flaky_plugin, mock_io, string_io):
    flaky_report = 'Flaky tests passed; others failed. ' \
                   'No more tests; that ship has sailed.'
    expected_string_io = StringIO()
    expected_string_io.write('===Flaky Test Report===\n\n')
    expected_string_io.write(flaky_report)
    expected_string_io.write('\n===End Flaky Test Report===\n')
    mock_io.write(flaky_report)
    flaky_plugin.terminal_summary(string_io)
    assert string_io.getvalue() == expected_string_io.getvalue()


class TestFlakyPytestPlugin(object):
    _test_method_name = 'test_method'

    def test_flaky_plugin_handles_success_for_test_method(
        self,
        flaky_plugin,
        flaky_test,
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

    def test_flaky_plugin_handles_success_for_test_instance(
        self,
        flaky_plugin,
        flaky_test,
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
            is_test_method=False
        )

    def test_flaky_plugin_handles_success_for_needs_rerun(
        self,
        flaky_plugin,
        flaky_test,
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
            min_passes=2
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
        flaky_plugin.add_success(call_info, flaky_test)
        self._assert_test_ignored(mock_io, string_io, call_info)

    def test_flaky_plugin_ignores_failure_for_non_flaky_test(
        self,
        flaky_plugin,
        flaky_test,
        call_info,
        string_io,
        mock_io,
    ):
        flaky_plugin.add_failure(call_info, flaky_test, None)
        self._assert_test_ignored(mock_io, string_io, call_info)

    def test_flaky_plugin_handles_failure_for_test_method(
        self,
        flaky_plugin,
        flaky_test,
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

    def test_flaky_plugin_handles_failure_for_test_instance(
        self,
        flaky_plugin,
        flaky_test,
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
            is_test_method=False,
        )
        assert mock_plugin_rerun()[0] == flaky_test

    def test_flaky_plugin_handles_failure_for_no_more_retries(
        self,
        flaky_plugin,
        flaky_test,
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
        flaky_plugin,
        flaky_test,
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
        test_method_name,
    ):
        actual_flaky_attributes = self._get_flaky_attributes(
            True,
            test,
            test_method_name,
        )
        assert all(
            item in actual_flaky_attributes.items()
            for item in expected_flaky_attributes.items()
        )

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
        is_test_method=True,
        max_runs=2,
        min_passes=1,
    ):
        test_owner = test.instance if is_test_method else test.module
        test_object = getattr(test_owner, self._test_method_name)
        flaky(max_runs, min_passes)(test_object)
        self._set_flaky_attribute(
            is_test_method,
            FlakyNames.CURRENT_PASSES,
            current_passes,
            test,
            self._test_method_name,
        )
        self._set_flaky_attribute(
            is_test_method,
            FlakyNames.CURRENT_RUNS,
            current_runs,
            test,
            self._test_method_name,
        )

        too_few_passes = current_passes + 1 < min_passes
        retries_remaining = current_runs + 1 < max_runs
        expected_plugin_handles_success = too_few_passes and retries_remaining

        info.when = 'call'
        actual_plugin_handles_success = plugin.add_success(
            info,
            test,
        )

        assert expected_plugin_handles_success == actual_plugin_handles_success
        self._assert_flaky_attributes_contains(
            {
                FlakyNames.CURRENT_PASSES: current_passes + 1,
                FlakyNames.CURRENT_RUNS: current_runs + 1,
            },
            test,
            self._test_method_name,
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
        is_test_method=True,
        max_runs=2,
        min_passes=1,
    ):
        test_owner = test.instance if is_test_method else test.module
        test_object = getattr(test_owner, self._test_method_name)
        flaky(max_runs, min_passes)(test_object)
        if current_errors is None:
            current_errors = [None]
        else:
            current_errors.append(None)
        self._set_flaky_attribute(
            is_test_method,
            FlakyNames.CURRENT_ERRORS,
            current_errors,
            test,
            self._test_method_name,
        )
        self._set_flaky_attribute(
            is_test_method,
            FlakyNames.CURRENT_PASSES,
            current_passes,
            test,
            self._test_method_name,
        )
        self._set_flaky_attribute(
            is_test_method,
            FlakyNames.CURRENT_RUNS,
            current_runs,
            test,
            self._test_method_name,
        )

        too_few_passes = current_passes < min_passes
        retries_remaining = current_runs + 1 < max_runs
        expected_plugin_handles_failure = too_few_passes and retries_remaining

        info.when = 'call'
        actual_plugin_handles_failure = plugin.add_failure(
            info,
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
            self._test_method_name,
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
    def _get_flaky_attributes(
        is_test_method,
        test,
        test_method_name=None
    ):
        if is_test_method:
            test_owner = test.instance
        else:
            test_owner = test.module
        test_object = getattr(
            test_owner,
            test_method_name,
        )
        actual_flaky_attributes = dict((
            (attr, getattr(
                test_object,
                attr,
                None,
            )) for attr in FlakyNames()
        ))
        return actual_flaky_attributes

    @staticmethod
    def _set_flaky_attribute(
        is_test_method,
        attr,
        value,
        test,
        test_method_name=None
    ):
        if is_test_method:
            test_owner = test.instance
        else:
            test_owner = test.module
        test_object = getattr(
            test_owner,
            test_method_name
        )
        setattr(test_object, attr, value)
