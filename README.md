# Automated System Validation & Test Automation Framework

A small Python framework that validates a system (here, a simulated embedded
controller) against a specification: functional, fault-handling and
performance tests, with tagging, data-driven specs and HTML/JSON reports.
Zero third-party dependencies (Python 3.9+).

## Project layout
```
config/spec.json            # requirements as data (limits, expected responses)
framework/dut.py            # Simulated Device Under Test (state machine, sensors, faults)
framework/base.py           # SystemTestCase base class, @tag decorator, spec loader
framework/validators.py     # assert_in_range, timed(), percentile()
framework/reporting.py      # custom result class + HTML/JSON report writer
tests/                      # smoke, regression, fault, performance tests
run_tests.py                # runner with tag filtering and exit codes for CI
```

## Run
```bash
python run_tests.py                  # everything
python run_tests.py --tag smoke      # quick sanity pass
python run_tests.py --tag fault --tag performance
```
Open `reports/report.html` for the results. The exit code is non-zero on any
failure, so it drops straight into a CI pipeline. pytest can also run the
tests: `pytest tests/`.

## What it demonstrates
- Test design: boundary and limit checks, state-machine validation, negative tests
- Fault injection (boot failure, over-temperature, brownout) and recovery checks
- Performance validation (boot time, p95 command latency)
- Data-driven testing: requirements live in `spec.json`, not in test code
- Reproducibility: seeded simulation, guaranteed teardown
- Reporting: pass rate, per-test timing, tags and failure traces

## Extending it
- Replace `SimulatedDevice` with a real driver (pyserial, CAN, SSH) using the same interface
- Add a CI job (GitHub Actions) that runs `python run_tests.py --tag smoke` on each push
- Add requirement IDs to tests for a traceability matrix
