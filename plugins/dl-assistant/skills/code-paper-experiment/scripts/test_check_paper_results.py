import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_paper_results as checker


REFERENCES = Path(__file__).resolve().parents[1] / "references/templates"
PLAN = REFERENCES.parents[2] / "writing-paper/references/templates/paper-experiment-plan-template.json"


def write(root, name, obj):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return {"path": name, "sha256": checker.digest(path)}


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = checker.load(PLAN)
        self.plan["approval"]["ref"] = "approved-plan-record"
        self.spec = checker.load(REFERENCES / "run-spec-template.json")
        self.spec["approval_ref"] = "approved-launch-record"
        for row in self.spec["experiments"]:
            row["git_commit"] = "a" * 40
            row["command"] = "python bench.py"
        self.result = checker.load(REFERENCES / "paper-results-template.json")

    def package(self, revision, previous=None):
        directory = self.root / f"rev-{revision}"
        self.result["revision"] = revision
        self.result["previous_sha256"] = previous
        self.spec["plan"] = write(directory, "plan-v1.json", self.plan)
        self.result["plan"] = self.spec["plan"]
        self.result["run_spec"] = write(directory, "run-spec.json", self.spec)
        for row in self.result["experiments"]:
            for attempt in row["execution"]["attempts"]:
                meta = {**attempt, "batch_id": self.result["batch_id"], "exp_id": row["exp_id"],
                        "run_spec_ref": self.result["run_spec"], "git_commit": "a" * 40, "command": "python bench.py"}
                write(directory, attempt["meta_ref"], meta)
                if attempt["metrics_ref"]:
                    raw = attempt["_fixture_readouts"]
                    write(directory, attempt["metrics_ref"], {"attempt_id": attempt["attempt_id"],
                          "measurements": {"latency": {"unit": "ms", "values": raw}}})
        payload = copy.deepcopy(self.result)
        for row in payload["experiments"]:
            for attempt in row["execution"]["attempts"]:
                attempt.pop("_fixture_readouts", None)
        write(directory, "paper-results.json", payload)
        return directory

    def attempt(self, row, number, readouts, *, aid=None, retry_of=None, status="completed"):
        aid = aid or f"attempt-{number}"
        prefix = f"evidence/{row['exp_id']}/{aid}"
        row["execution"]["attempts"].append({
            "attempt_id": aid, "replicate_id": f"pair-{number}", "seed": None,
            "run_spec_revision": 1, "status": status,
            "data_validity": "valid" if status == "completed" else "unassessed",
            "meta_ref": f"{prefix}/meta.json", "metrics_ref": f"{prefix}/metrics.json" if readouts else None,
            "retry_of": retry_of, "_fixture_readouts": readouts,
        })

    def complete(self, row, values):
        row["execution"].update(status="completed", reason="")
        row["measurement"]["validity"] = "valid"
        for number, (baseline, combined) in enumerate(values, start=1):
            self.attempt(row, number, {"baseline": baseline, "combined": combined})
        row["statistics"].append({
            "id": "paired-latency-difference", "measurement_id": "latency", "unit": "ms",
            "method": "mean_paired_difference", "minuend": "combined", "subtrahend": "baseline",
            "value": -1.8, "attempt_ids": ["attempt-1", "attempt-2", "attempt-3"],
        })

    def test_partial_then_complete_package(self):
        first, second = self.result["experiments"]
        self.complete(first, [(12.5, 10.7), (12.6, 10.8), (12.7, 10.9)])
        self.attempt(second, 1, {"combined": 13.2}, aid="partial-1", status="partial")
        old_dir = self.package(1)
        old_path, _, _ = checker.check_package(old_dir)
        self.complete(second, [(15.0, 13.2), (15.1, 13.3), (15.2, 13.4)])
        second["execution"]["attempts"][1]["retry_of"] = "partial-1"
        new_dir = self.package(2, checker.digest(old_path))
        updated = checker.check_package(new_dir)
        checker.check_revision(updated, old_dir)
        script = REFERENCES.parents[1] / "scripts/check-run-artifacts.sh"
        subprocess.run(["bash", script, "--pkgdir", new_dir, "--previous", old_dir], check=True,
                       capture_output=True, text=True)

        first["statistics"][0]["value"] = -1.7
        with self.assertRaisesRegex(ValueError, "does not match"):
            checker.check_package(self.package(2, checker.digest(old_path)))

    def test_duplicate_replicate_is_rejected_even_with_new_attempt_id(self):
        first = self.result["experiments"][0]
        self.complete(first, [(12.5, 10.7), (12.6, 10.8), (12.7, 10.9)])
        self.attempt(first, 1, {"baseline": 12.5, "combined": 10.7}, aid="retry-1", retry_of="attempt-1")
        first["statistics"][0]["attempt_ids"].append("retry-1")
        with self.assertRaisesRegex(ValueError, "repeated independent replicate"):
            checker.check_package(self.package(1))


if __name__ == "__main__":
    unittest.main()
