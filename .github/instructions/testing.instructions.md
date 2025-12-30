---
applyTo: "**/tests/**"
---


# Testing

Our test directories have four subdirectories for tests

* `tests/dev/` Dev tests are used while implementing an update. Once the update
  is completed, they are considered obsolete, although they should be deleted
  only just before releases, not after the update. 
* `test/smoke` Smoke tests are a small number of tests of basic use cases. They
  are meant to be very fast to run and designed to catch major problems like
  seriously broken code, import errors, or catastrophic configuration errors. 
* `test/unit` Unit tests exercise a subsystem, and collectively they can be used
  for coverage testing. Unit tests may involve mock objects, calling private
  methods, or other invasive techniques. 
* `test/system` System tests are involve running major use cases and typically
  will delete the database, reload it completely or load it from backup, and
  perform many end-to-end tests from the major interfaces. 




