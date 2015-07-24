.. :changelog:

Release History
---------------


2.1.1 (2015-05-22)
++++++++++++++++++

**Bugfixes**

- Flaky will no longer raise a KeyError for failed flaky tests.

- Flaky will no longer raise a UnicodeEncodeError for flaky tests which raise exceptions
  with non-ascii characters.

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
