flaky
=====

.. image:: http://opensource.box.com/badges/active.svg
    :target: http://opensource.box.com/badges

.. image:: https://travis-ci.org/box/flaky.svg?branch=master
    :target: https://travis-ci.org/box/flaky

.. image:: https://img.shields.io/pypi/v/flaky.svg
    :target: https://pypi.python.org/pypi/flaky

About
-----

Flaky is a plugin for nose or pytest that automatically reruns flaky tests.

Ideally, tests reliably pass or fail, but sometimes test fixtures must rely on components that aren't 100%
reliable. With flaky, instead of removing those tests or marking them to @skip, they can be automatically
retried.

For more information about flaky, see `this presentation <http://opensource.box.com/flaky/>`_.

Marking tests flaky
~~~~~~~~~~~~~~~~~~~

To mark a test as flaky, simply import flaky and decorate the test with @flaky:

.. code-block:: python

    from flaky import flaky

.. code-block:: python

    @flaky
    def test_something_that_usually_passes(self):
        value_to_double = 21
        result = get_result_from_flaky_doubler(value_to_double)
        self.assertEqual(result, value_to_double * 2, 'Result doubled incorrectly.')

By default, flaky will retry a failing test once, but that behavior can be overridden by passing values to the
flaky decorator. It accepts two parameters: max_runs, and min_passes; flaky will run tests up to max_runs times, until
it has succeeded min_passes times. Once a test passes min_passes times, it's considered a success; once it has been
run max_runs times without passing min_passes times, it's considered a failure.

.. code-block:: python

    @flaky(max_runs=3, min_passes=2)
    def test_something_that_usually_passes(self):
        """This test must pass twice, and it can be run up to three times."""
        value_to_double = 21
        result = get_result_from_flaky_doubler(value_to_double)
        self.assertEqual(result, value_to_double * 2, 'Result doubled incorrectly.')

Marking a class flaky
+++++++++++++++++++++

In addition to marking a single test flaky, entire test cases can be marked flaky:

.. code-block:: python

    @flaky
    class TestMultipliers(TestCase):
        def test_flaky_doubler(self):
            value_to_double = 21
            result = get_result_from_flaky_doubler(value_to_double)
            self.assertEqual(result, value_to_double * 2, 'Result doubled incorrectly.')

        @flaky(max_runs=3)
        def test_flaky_tripler(self):
            value_to_triple = 14
            result = get_result_from_flaky_tripler(value_to_triple)
            self.assertEqual(result, value_to_triple * 3, 'Result tripled incorrectly.')

The @flaky class decorator will mark test_flaky_doubler as flaky, but it won't override the 3 max_runs
for test_flaky_tripler (from the decorator on that test method).

Pytest marker
+++++++++++++

When using ``pytest``, ``@pytest.mark.flaky`` can be used in place of ``@flaky``.

Don't rerun certain types of failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on your tests, some failures are obviously not due to flakiness. Instead of rerunning
after those failures, you can specify a filter function that can tell flaky to fail the test right away.

.. code-block:: python

    def is_not_crash(err, *args):
        return not issubclass(err[0], ProductCrashedError)

    @flaky
    def test_something():
        raise ProductCrashedError

    @flaky(rerun_filter=is_not_crash)
    def test_something_else():
        raise ProductCrashedError

Flaky will run ``test_something`` twice, but will only run ``test_something_else`` once.

It can also be used to incur a delay between test retries:

.. code-block:: python
    
    import time
    
    def delay_rerun(*args):
        time.sleep(1)
        return True
    
    @flaky(rerun_filter=delay_rerun)
    def test_something_else():
        ...

Activating the plugin
~~~~~~~~~~~~~~~~~~~~~

Like any nose plugin, flaky can be activated via the command line:

.. code-block:: console

    nosetests --with-flaky

With pytest, flaky will automatically run. It can, however be disabled via the command line:

.. code-block:: console

    pytest -p no:flaky

Command line arguments
~~~~~~~~~~~~~~~~~~~~~~

No Flaky Report
+++++++++++++++

Pass ``--no-flaky-report`` to suppress the report at the end of the run detailing flaky test results.

Shorter Flaky Report
++++++++++++++++++++

Pass ``--no-success-flaky-report`` to suppress information about successful flaky tests.

Force Flaky
+++++++++++

Pass ``--force-flaky`` to treat all tests as flaky.

Pass ``--max-runs=MAX_RUNS`` and/or ``--min-passes=MIN_PASSES`` to control the behavior of flaky if ``--force-flaky``
is specified. Flaky decorators on individual tests will override these defaults.


*Additional usage examples are in the code - see test/test_nose/test_nose_example.py and test/test_pytest/test_pytest_example.py*

Installation
------------

To install, simply:

.. code-block:: console

    pip install flaky


Compatibility
-------------

Flaky is tested with the following test runners and options:

- Nosetests. Doctests cannot be marked flaky.

- Py.test. Works with ``pytest-xdist`` but not with the ``--boxed`` option. Doctests cannot be marked flaky.


Contributing
------------

See `CONTRIBUTING.rst <https://github.com/box/flaky/blob/master/CONTRIBUTING.rst>`_.


Setup
~~~~~

Create a virtual environment and install packages -

.. code-block:: console

    mkvirtualenv flaky
    pip install -r requirements-dev.txt


Testing
~~~~~~~

Run all tests using -

.. code-block:: console

    tox

The tox tests include code style checks via pycodestyle and pylint.


Copyright and License
---------------------

::

 Copyright 2015 Box, Inc. All rights reserved.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
