#!/usr/bin/env python3
"""Entry point: discover tests, run them (optionally by tag), write reports.

Usage:
    python run_tests.py                 # run everything
    python run_tests.py --tag smoke     # only smoke tests
    python run_tests.py --tag fault --tag performance
"""
import argparse
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from framework.reporting import ReportingResult, write_reports  # noqa: E402


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def build_suite(tags):
    discovered = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    if not tags:
        return discovered
    suite = unittest.TestSuite()
    for test in iter_tests(discovered):
        method = getattr(test, getattr(test, "_testMethodName", ""), None)
        if set(tags) & set(getattr(method, "tags", [])):
            suite.addTest(test)
    return suite


def main():
    parser = argparse.ArgumentParser(description="System validation test runner")
    parser.add_argument("--tag", action="append", default=[], help="run only tests with this tag")
    parser.add_argument("--out", default=str(ROOT / "reports"), help="report output directory")
    args = parser.parse_args()

    runner = unittest.TextTestRunner(resultclass=ReportingResult, verbosity=2)
    start = time.perf_counter()
    result = runner.run(build_suite(args.tag))
    summary = write_reports(result.records, args.out, time.perf_counter() - start)

    print(f"\nPass rate: {summary['pass_rate_pct']}%  ({summary['passed']}/{summary['total']})")
    print(f"Reports: {Path(args.out) / 'report.html'}, {Path(args.out) / 'results.json'}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
