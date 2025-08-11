# Changelog

## v0.4.3 (2025/07/25)
* Add E2ETask class to handle end-to-end (E2E) testing with async task execution and schema validation.

## v0.4.2 (2022/04/04)
* Fix issues on Documentation
* Remove Travis CI and add Github Actions
* Fix output value for rollback issue

## v0.4.1 (2021/09/20)
* Fix token argument type hint

## v0.4.0 (2021/02/01)
* Add capabilty to stop test execution if some elements are present on "fail_on" definition ([#11](https://github.com/societe-generale/spintest/pull/11))

## v0.3.0 (2020/06/26)
* Add capability to generate spintest report, this report contains all needed information about your tested API routes ([#8](https://github.com/societe-generale/spintest/pull/8))

## v0.2.1 (2020/06/26)
* Fix version httpretty to 0.9.7 to fix tests execution ([#9](https://github.com/societe-generale/spintest/pull/9))
* Set environment proxy to '', to avoid error when tests execution


## v0.2.0 (2020/02/10)

Enhancement : 
* UUID Token are not visible in the log to avoid security violation, when spintest is used during the CI/CD tools ([#6](https://github.com/societe-generale/spintest/pull/6))

