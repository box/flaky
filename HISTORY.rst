.. :changelog:

Release History
---------------

2.0.0 (2015-03-01)
++++++++++++++++++

**Bugfixes**

- Tests marked flaky that fail after exhausting reruns will now be reported to the nose test runner.
  This is a *breaking* change, because the exit code of the nose test runner will indicate failure in this case.

- Tests marked flaky will now be marked as failures after they have failed ``max_runs - min_passes + 1`` times.
  This is a *breaking* change as well, because a bug in previous versions was allowing tests with ``min_passes > 0`` to
  run more than ``max_runs`` times.