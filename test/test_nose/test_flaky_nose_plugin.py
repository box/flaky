# coding: utf-8

from __future__ import unicode_literals
from genty import genty, genty_dataset
import mock
from mock import MagicMock, Mock, patch
from flaky import defaults
from flaky.flaky_decorator import flaky
from flaky import flaky_nose_plugin
from flaky.names import FlakyNames
from flaky.utils import unicode_type
from test.test_case_base import TestCase


@genty
class TestFlakyNosePlugin(TestCase):
    def setUp(self):
        super(TestFlakyNosePlugin, self).setUp()

        self._mock_test_result = MagicMock()
        self._mock_stream = None
        self._flaky_plugin = flaky_nose_plugin.FlakyPlugin()
        self._mock_nose_result = Mock(flaky_nose_plugin.TextTestResult)
        self._flaky_plugin.prepareTestResult(self._mock_nose_result)
        self._mock_test = MagicMock(name='flaky_plugin_test')
        self._mock_test_case = MagicMock(
            name='flaky_plugin_test_case',
            spec=TestCase
        )
        self._mock_test_case.address = MagicMock()
        self._mock_test_case.test = self._mock_test
        self._mock_test_module_name = 'test_module'
        self._mock_test_class_name = 'TestClass'
        self._mock_test_method_name = 'test_method'
        self._mock_test_names = '{0}:{1}.{2}'.format(
            self._mock_test_module_name,
            self._mock_test_class_name,
            self._mock_test_method_name
        )
        self._mock_exception = Exception('Error in {0}'.format(
            self._mock_test_method_name)
        )
        self._mock_stack_trace = ''
        self._mock_exception_type = Exception
        self._mock_error = (
            self._mock_exception_type,
            self._mock_exception,
            self._mock_stack_trace
        )
        self._mock_test_method = MagicMock(
            name=self._mock_test_method_name,
            spec=['__call__'] + list(FlakyNames().items()),
        )
        setattr(
            self._mock_test,
            self._mock_test_method_name,
            self._mock_test_method,
        )

    def _assert_flaky_plugin_configured(self):
        options = Mock()
        options.multiprocess_workers = 0
        conf = Mock()
        self._flaky_plugin.enabled = True
        with patch.object(flaky_nose_plugin, 'TextTestResult') as flaky_result:
            flaky_result.return_value = self._mock_test_result
            from io import StringIO
            self._mock_stream = MagicMock(spec=StringIO)
            with patch.object(self._flaky_plugin, '_get_stream') as get_stream:
                get_stream.return_value = self._mock_stream
                self._flaky_plugin.configure(options, conf)

    def test_flaky_plugin_report(self):
        flaky_report = 'Flaky tests passed; others failed. ' \
                       'No more tests; that ship has sailed.'
        self._test_flaky_plugin_report(flaky_report)

    def test_flaky_plugin_handles_success_for_test_method(self):
        self._test_flaky_plugin_handles_success()

    def test_flaky_plugin_handles_success_for_test_instance(self):
        self._test_flaky_plugin_handles_success(is_test_method=False)

    def test_flaky_plugin_handles_success_for_needs_rerun(self):
        self._test_flaky_plugin_handles_success(min_passes=2)

    def test_flaky_plugin_ignores_success_for_non_flaky_test(self):
        self._expect_test_not_flaky()
        self._flaky_plugin.addSuccess(self._mock_test_case)
        self._assert_test_ignored()

    def test_flaky_plugin_ignores_error_for_non_flaky_test(self):
        self._expect_test_not_flaky()
        self._flaky_plugin.handleError(self._mock_test_case, None)
        self._assert_test_ignored()

    def test_flaky_plugin_ignores_failure_for_non_flaky_test(self):
        self._expect_test_not_flaky()
        self._flaky_plugin.handleFailure(self._mock_test_case, None)
        self._assert_test_ignored()

    def test_flaky_plugin_ignores_error_for_nose_failure(self):
        self._mock_test_case.address.return_value = (
            None,
            self._mock_test_module_name,
            None,
        )
        self._flaky_plugin.handleError(self._mock_test_case, None)
        self._assert_test_ignored()

    def test_flaky_plugin_handles_error_for_test_method(self):
        self._test_flaky_plugin_handles_failure_or_error()

    def test_flaky_plugin_handles_error_for_test_instance(self):
        self._test_flaky_plugin_handles_failure_or_error(is_test_method=False)

    def test_flaky_plugin_handles_failure_for_test_method(self):
        self._test_flaky_plugin_handles_failure_or_error(is_failure=True)

    def test_flaky_plugin_handles_failure_for_test_instance(self):
        self._test_flaky_plugin_handles_failure_or_error(
            is_failure=True,
            is_test_method=False
        )

    def test_flaky_plugin_handles_failure_for_no_more_retries(self):
        self._test_flaky_plugin_handles_failure_or_error(
            is_failure=True,
            max_runs=1
        )

    def test_flaky_plugin_handles_additional_errors(self):
        self._test_flaky_plugin_handles_failure_or_error(
            current_errors=[self._mock_error]
        )

    def test_flaky_plugin_handles_bare_test(self):
        self._mock_test_names = self._mock_test_method_name
        self._mock_test.test = Mock()
        self._expect_call_test_address()
        attrib = defaults.default_flaky_attributes(2, 1)
        for name, value in attrib.items():
            setattr(
                self._mock_test.test,
                name,
                value,
            )
        delattr(self._mock_test, self._mock_test_method_name)
        self._flaky_plugin.prepareTestCase(self._mock_test_case)
        self.assertTrue(self._flaky_plugin.handleError(
            self._mock_test_case,
            self._mock_error,
        ))
        self.assertFalse(self._flaky_plugin.handleError(
            self._mock_test_case,
            self._mock_error,
        ))

    def _expect_call_test_address(self):
        self._mock_test_case.address.return_value = (
            None,
            None,
            self._mock_test_names
        )

    def _expect_test_flaky(self, is_test_method, max_runs, min_passes):
        self._expect_call_test_address()
        if is_test_method:
            mock_test_method = getattr(
                self._mock_test,
                self._mock_test_method_name
            )
            for flaky_attr in FlakyNames():
                setattr(self._mock_test, flaky_attr, None)
                setattr(mock_test_method, flaky_attr, None)
            flaky(max_runs, min_passes)(mock_test_method)
        else:
            flaky(max_runs, min_passes)(self._mock_test)
            mock_test_method = getattr(
                self._mock_test,
                self._mock_test_method_name
            )
            for flaky_attr in FlakyNames():
                setattr(mock_test_method, flaky_attr, None)

    def _expect_test_not_flaky(self):
        self._expect_call_test_address()
        for test_object in (
            self._mock_test,
            getattr(self._mock_test, self._mock_test_method_name)
        ):
            for flaky_attr in FlakyNames():
                setattr(test_object, flaky_attr, None)

    def _assert_test_ignored(self):
        self._mock_test_case.address.assert_called_with()
        self.assertEqual(
            self._mock_test_case.mock_calls,
            [mock.call.address()],
        )
        self.assertEqual(self._mock_test.mock_calls, [])
        self.assertEqual(self._mock_nose_result.mock_calls, [])

    def _get_flaky_attributes(self):
        actual_flaky_attributes = dict((
            (
                attr,
                getattr(
                    self._mock_test_case,
                    attr,
                    None,
                )
            ) for attr in FlakyNames()
        ))
        for key, value in actual_flaky_attributes.items():
            if isinstance(value, list):
                actual_flaky_attributes[key] = tuple(value)
        return actual_flaky_attributes

    def _set_flaky_attribute(self, attr, value):
        setattr(self._mock_test, attr, value)

    def _assert_flaky_attributes_contains(
        self,
        expected_flaky_attributes,
    ):
        actual_flaky_attributes = self._get_flaky_attributes()
        self.assertDictContainsSubset(
            expected_flaky_attributes,
            actual_flaky_attributes,
            'Unexpected flaky attributes. Expected {0} got {1}'.format(
                expected_flaky_attributes,
                actual_flaky_attributes
            )
        )

    def _test_flaky_plugin_handles_failure_or_error(
        self,
        current_errors=None,
        current_passes=0,
        current_runs=0,
        is_failure=False,
        is_test_method=True,
        max_runs=2,
        min_passes=1,
    ):
        self._assert_flaky_plugin_configured()
        self._expect_test_flaky(is_test_method, max_runs, min_passes)
        if current_errors is None:
            current_errors = [self._mock_error]
        else:
            current_errors.append(self._mock_error)
        self._set_flaky_attribute(
            FlakyNames.CURRENT_ERRORS,
            current_errors,
        )
        self._set_flaky_attribute(
            FlakyNames.CURRENT_PASSES,
            current_passes,
        )
        self._set_flaky_attribute(
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )

        retries_remaining = current_runs + 1 < max_runs
        too_few_passes = current_passes < min_passes
        expected_plugin_handles_failure = too_few_passes and retries_remaining
        did_plugin_retry_test = max_runs > 1

        self._flaky_plugin.prepareTestCase(self._mock_test_case)
        if is_failure:
            actual_plugin_handles_failure = self._flaky_plugin.handleFailure(
                self._mock_test_case,
                self._mock_error,
            )
        else:
            actual_plugin_handles_failure = self._flaky_plugin.handleError(
                self._mock_test_case,
                self._mock_error,
            )

        self.assertEqual(
            expected_plugin_handles_failure or None,
            actual_plugin_handles_failure,
            'Expected plugin{0} to handle the test run, but it did{1}.'.format(
                ' to' if expected_plugin_handles_failure else '',
                '' if actual_plugin_handles_failure else ' not'
            ),
        )
        self._assert_flaky_attributes_contains(
            {
                FlakyNames.CURRENT_RUNS: current_runs + 1,
                FlakyNames.CURRENT_ERRORS: tuple(current_errors),
            },
        )
        expected_test_case_calls = [mock.call.address(), mock.call.address()]
        expected_result_calls = []
        if expected_plugin_handles_failure:
            expected_test_case_calls.append(('__hash__',))
            expected_stream_calls = [mock.call.writelines([
                self._mock_test_method_name,
                ' failed ({0} runs remaining out of {1}).'.format(
                    max_runs - current_runs - 1, max_runs
                ),
                '\n\t',
                unicode_type(self._mock_error[0]),
                '\n\t',
                unicode_type(self._mock_error[1]),
                '\n\t',
                unicode_type(self._mock_error[2]),
                '\n',
            ])]
        else:
            if did_plugin_retry_test:
                if is_failure:
                    expected_result_calls.append(
                        mock.call.addFailure(
                            self._mock_test_case,
                            self._mock_error,
                        ),
                    )
                else:
                    expected_result_calls.append(mock.call.addError(
                        self._mock_test_case,
                        self._mock_error,
                    ))
            expected_stream_calls = [mock.call.writelines([
                self._mock_test_method_name,
                ' failed; it passed {0} out of the required {1} times.'.format(
                    current_passes,
                    min_passes
                ),
                '\n\t',
                unicode_type(self._mock_error[0]),
                '\n\t',
                unicode_type(self._mock_error[1]),
                '\n\t',
                unicode_type(self._mock_error[2]),
                '\n'
            ])]
        self.assertEqual(
            self._mock_nose_result.mock_calls,
            expected_result_calls,
        )
        self.assertEqual(
            self._mock_test_case.mock_calls,
            expected_test_case_calls,
            'Unexpected TestCase calls: {0} vs {1}'.format(
                self._mock_test_case.mock_calls,
                expected_test_case_calls
            )
        )
        self.assertEqual(self._mock_stream.mock_calls, expected_stream_calls)

    def _test_flaky_plugin_handles_success(
        self,
        current_passes=0,
        current_runs=0,
        is_test_method=True,
        max_runs=2,
        min_passes=1
    ):
        self._assert_flaky_plugin_configured()
        self._expect_test_flaky(is_test_method, max_runs, min_passes)
        self._set_flaky_attribute(
            FlakyNames.CURRENT_PASSES,
            current_passes,
        )
        self._set_flaky_attribute(
            FlakyNames.CURRENT_RUNS,
            current_runs,
        )

        retries_remaining = current_runs + 1 < max_runs
        too_few_passes = current_passes + 1 < min_passes
        expected_plugin_handles_success = too_few_passes and retries_remaining

        self._flaky_plugin.prepareTestCase(self._mock_test_case)
        actual_plugin_handles_success = self._flaky_plugin.addSuccess(
            self._mock_test_case,
        )

        self.assertEqual(
            expected_plugin_handles_success or None,
            actual_plugin_handles_success,
            'Expected plugin{0} to handle the test run, but it did{1}.'.format(
                ' not' if expected_plugin_handles_success else '',
                '' if actual_plugin_handles_success else ' not'
            ),
        )
        self._assert_flaky_attributes_contains(
            {
                FlakyNames.CURRENT_RUNS: current_runs + 1,
                FlakyNames.CURRENT_PASSES: current_passes + 1,
            },
        )
        expected_test_case_calls = [mock.call.address(), mock.call.address()]
        expected_stream_calls = [mock.call.writelines([
            self._mock_test_method_name,
            " passed {0} out of the required {1} times. ".format(
                current_passes + 1,
                min_passes,
            ),
        ])]
        if expected_plugin_handles_success:
            _rerun_text = 'Running test again until it passes {0} times.\n'
            expected_test_case_calls.append(('__hash__',))
            expected_stream_calls.append(
                mock.call.write(_rerun_text.format(min_passes)),
            )
        else:
            expected_stream_calls.append(mock.call.write('Success!\n'))
        self.assertEqual(
            self._mock_test_case.mock_calls,
            expected_test_case_calls,
            'Unexpected TestCase calls = {0} vs {1}'.format(
                self._mock_test_case.mock_calls,
                expected_test_case_calls,
            ),
        )
        self.assertEqual(self._mock_stream.mock_calls, expected_stream_calls)

    def _test_flaky_plugin_report(self, expected_stream_value):
        self._assert_flaky_plugin_configured()
        mock_stream = Mock()
        self._mock_stream.getvalue.return_value = expected_stream_value

        self._flaky_plugin.report(mock_stream)

        self.assertEqual(
            mock_stream.mock_calls,
            [
                mock.call.write('===Flaky Test Report===\n\n'),
                mock.call.write(expected_stream_value),
                mock.call.write('\n===End Flaky Test Report===\n'),
            ],
        )

    @genty_dataset(
        multiprocess_plugin_absent=(None, 'StringIO'),
        processes_argument_absent=(0, 'StringIO'),
        processes_equals_one=(1, 'MultiprocessingStringIO'),
        processes_equals_two=(2, 'MultiprocessingStringIO'),
    )
    def test_flaky_plugin_get_stream(self, mp_workers, expected_class_name):
        options = Mock()
        conf = Mock()
        self._flaky_plugin.enabled = True
        options.multiprocess_workers = mp_workers
        if mp_workers is None:
            del options.multiprocess_workers
        self._flaky_plugin.configure(options, conf)
        # pylint:disable=protected-access
        self.assertEqual(
            self._flaky_plugin._stream.__class__.__name__,
            expected_class_name,
        )
