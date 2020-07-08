.. :changelog:

Release History
---------------

Upcoming
++++++++

3.7.0 (2020-07-07)
++++++++++++++++++

- Flaky now retries tests which fail during setup.

3.6.1 (2019-08-06)
++++++++++++++++++

**Bugfixes**
- Reraise ``KeyboardInterrupt`` when running tests under pytest.


3.6.0 (2019-06-25)
++++++++++++++++++

- Do not print an empty report if no tests marked 'flaky' were run at all (#116).
  NOTE: This change could be breaking if you relied on the flaky report being printed.

3.5.3 (2019-01-16)
++++++++++++++++++

- Add rerun_filter parameter to _make_test_flaky

3.5.2 (2019-01-10)
++++++++++++++++++

**Bugfixes**
- Fall back to old pytest marker API for older pytest version (``get_marker`` vs ``iter_markers``).

3.5.1 (2019-01-09)
++++++++++++++++++

- Officially support and test on Python 3.6 and 3.7.
- Adds a pytest marker that can be used instead of ```@flaky``.
- Replaced references to 'slaveoutput', where possible
  with 'workeroutput', following the convention chosen by pytest.
- Prints formatted tracebacks in the flaky report when using nose.

**Bugfixes**
- Ensure that tests are only reported as successful to the nose runner once.

3.5.0 (2019-01-07)
++++++++++++++++++

- Updated references to pytest instead of py.test.

**Bugfixes**
- Flaky is now compatible with pytest >= 4.1.

3.4.0 (2017-06-15)
++++++++++++++++++

**Bugfixes**
- Flaky for pytest will no longer silently swallow errors that occur during test setup.

3.3.0 (2016-07-28)
++++++++++++++++++

- Flaky for Nose will now rerun tests using the ``afterTest`` plugin hook, rather than the ``stopTest`` hook.
  The ``afterTest`` hook is called slightly later in the test run process; this change allows flaky to be used
  with `TestCase` subclasses that override the test run process, and do teardown after ``stopTest`` is called.
  In particular, this means that flaky is now compatible with Django's ``LiveServerTestCase``.


3.2.0 (2016-07-21)
++++++++++++++++++

- Flaky will completely suppress the flaky report if ``--no-success-flaky-report`` is specified and no tests
  needed to be rerun.

**Bugfixes**
- Flaky will no longer cause ``py.test --pep8`` to fail.


3.1.0 (2016-22-11)
++++++++++++++++++

- Flaky's automated tests now include a run with the ``pytest-xdist`` plugin enabled.
- Flaky for pytest has slightly changed how it patches the runner. This simplifies the plugin code a bit, but,
  more importantly, avoids reporting test retries until flaky is done with them. This *should* improve compatibility
  with other plugins.

3.0.2 (2015-12-21)
++++++++++++++++++

**Bugfixes**

- Flaky for pytest no longer passes None for the first 2 arguments to the optional ``rerun_filter``.


3.0.1 (2015-12-16)
++++++++++++++++++

**Bugfixes**

- Flaky for pytest no longer causes errors with the pytester plugin.

3.0.0 (2015-12-14)
++++++++++++++++++

- Flaky for pytest now reruns test setup and teardown. **This is a possibly breaking change.**

**Bugfixes**

- Bug with nose and multiprocess fixed.

2.4.0 (2015-10-27)
++++++++++++++++++

**Bugfixes**

- The flaky report is now available under nose with the multiprocessing plugin.

2.3.0 (2015-10-15)
++++++++++++++++++

- Added support and testing for Python 3.5
- Fixed tests on Python 2.6 with latest version of py.test

**Bugfixes**

- Flaky will no longer swallow exceptions raised during pytest fixture setup.
  This change is correct, but is a change in behavior.

2.2.0 (2015-08-28)
++++++++++++++++++

- The `@flaky` decorator now accepts a `rerun_filter` parameter.
  This allows for failing certain types of failures/errors immediately instead of rerunning.
- Flaky now accepts a command line option, `--no-success-flaky-report`.
  When that option is present, flaky won't add information about test successes to the flaky report.

2.1.2 (2015-07-30)
++++++++++++++++++

**Bugfixes**

- Flaky will no longer raise a UnicodeEncodeError for flaky tests which raise exceptions
  with non-ascii characters.
- Flaky will no longer cause nose to report non-flaky test failures and errors twice.
- Flaky now works with tests that are parametrized with py.test.


2.1.1 (2015-05-22)
++++++++++++++++++

**Bugfixes**

- Flaky will no longer raise a KeyError for failed flaky tests.


2.1.0 (2015-05-05)
++++++++++++++++++

**Bugfixes**

- Flaky for nose now reruns failed tests *after* calling the `tearDown()` method.
  This change is correct, but is a change in behavior.


2.0.4 (2015-04-20)
++++++++++++++++++

**Bugfixes**

- Flaky now copies flaky attributes to collected tests, rather than modifying them on the test declaration.
  This means that tests collected from classes that inherit tests marked flaky (from a base class) will now
  work correctly.

- Running py.test with doctests will no longer cause the doctests to fail. Doctests cannot, however, be marked flaky.

- Tests marked flaky will now be correctly rerun from pytest when using the pytest-xdist option. However, they
  will not be run if the `--boxed` option is used due to a technical limitation.

**Documentation updates**

- Updated documentation to correctly specify how to suppress the flaky report under py.test.

2.0.3 (2015-03-20)
++++++++++++++++++

**Bugfixes**

- Tests marked flaky that are part of a class inheriting from `unittest.TestCase` will now be rerun when they fail
  under py.test.


2.0.0 (2015-03-01)
++++++++++++++++++

**Bugfixes**

- Tests marked flaky that fail after exhausting reruns will now be reported to the nose test runner.
  This is a *breaking* change, because the exit code of the nose test runner will indicate failure in this case.

- Tests marked flaky will now be marked as failures after they have failed ``max_runs - min_passes + 1`` times.
  This is a *breaking* change as well, because a bug in previous versions was allowing tests with ``min_passes > 0`` to
  run more than ``max_runs`` times.
