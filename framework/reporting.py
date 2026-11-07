"""Custom unittest result class + JSON/HTML report writers."""
import html
import json
import time
import unittest
from datetime import datetime
from pathlib import Path


class ReportingResult(unittest.TextTestResult):
    """Records every outcome with duration, tags and failure detail."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self._started = {}

    def startTest(self, test):
        self._started[test.id()] = time.perf_counter()
        super().startTest(test)

    def _record(self, test, outcome, detail="", name=None):
        duration = time.perf_counter() - self._started.get(test.id(), time.perf_counter())
        method = getattr(test, getattr(test, "_testMethodName", ""), None)
        self.records.append({
            "name": name or test.id(),
            "outcome": outcome,
            "duration_s": round(duration, 4),
            "tags": sorted(getattr(method, "tags", [])),
            "detail": detail,
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._record(test, "failed", self._exc_info_to_string(err, test),
                         name=f"{test.id()} {subtest._subDescription()}")


def write_reports(records, out_dir, duration_s):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {k: sum(1 for r in records if r["outcome"] == k)
              for k in ("passed", "failed", "error", "skipped")}
    total = len(records)
    rate = round(100 * counts["passed"] / total, 1) if total else 0.0
    summary = {"generated": datetime.now().isoformat(timespec="seconds"),
               "duration_s": round(duration_s, 3), "total": total,
               "pass_rate_pct": rate, **counts}

    (out / "results.json").write_text(json.dumps({"summary": summary, "results": records}, indent=2))

    colors = {"passed": "#1a7f37", "failed": "#cf222e", "error": "#9a6700", "skipped": "#6e7781"}
    rows = "".join(
        f"<tr><td>{html.escape(r['name'])}</td>"
        f"<td style='color:{colors[r['outcome']]};font-weight:600'>{r['outcome'].upper()}</td>"
        f"<td>{r['duration_s']}</td><td>{html.escape(', '.join(r['tags']))}</td>"
        f"<td><pre>{html.escape(r['detail'])}</pre></td></tr>"
        for r in records)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Validation Report</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;color:#1f2328}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d0d7de;padding:6px 10px;text-align:left;vertical-align:top}}
th{{background:#f6f8fa}}pre{{margin:0;white-space:pre-wrap;font-size:12px}}
.card{{display:inline-block;margin-right:1.5rem;font-size:1.1rem}}</style></head><body>
<h1>System Validation Report</h1><p>{summary['generated']} &middot; {summary['duration_s']}s</p>
<p><span class="card">Total: <b>{total}</b></span><span class="card">Pass rate: <b>{rate}%</b></span>
<span class="card">Passed: <b>{counts['passed']}</b></span><span class="card">Failed: <b>{counts['failed']}</b></span>
<span class="card">Errors: <b>{counts['error']}</b></span><span class="card">Skipped: <b>{counts['skipped']}</b></span></p>
<table><tr><th>Test</th><th>Result</th><th>Time (s)</th><th>Tags</th><th>Details</th></tr>{rows}</table>
</body></html>"""
    (out / "report.html").write_text(page)
    return summary
