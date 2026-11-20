"""Offline regressions for run identity, incomplete sync and saved query snapshots."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("check_tracking.py")
SPEC = importlib.util.spec_from_file_location("tracking_checks", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tracking ' test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "runs/a1/wandb").mkdir(parents=True)
        (self.root / "config.json").write_text('{"frames":16}')
        (self.root / "design.json").write_text('{"purpose":"paired errors"}')
        self.identity = {
            "experiment_id": "exp-001", "replicate_id": "seed-0", "attempt_id": "a1",
            "resume_from_attempt": None,
            "design_sha256": hashlib.sha256((self.root / "design.json").read_bytes()).hexdigest(),
            "git_commit": "abc123", "code_diff_sha256": None, "config_sha256": hashlib.sha256((self.root / "config.json").read_bytes()).hexdigest(),
            "data_refs": ["dataset:v1"], "model_refs": ["weights:v2"], "protocol_ref": "eval:v1",
        }
        self.meta = {
            "git_commit": "abc123", "code_dirty": False,
            "configuration_ref": {"path": "config.json", "sha256": self.identity["config_sha256"]},
            "experiment_id": "exp-001", "design_record": {"path": "design.json"},
            "tracking": {"provider": "wandb", "base_url": "http://wandb.internal:8080",
                         "entity": "team", "project": "audio", "scope_id": "research-v3",
                         "research_round": "v3", "hypothesis_ids": ["H2"]},
            "attempts": [{"attempt_id": "a1", "replicate_id": "seed-0", "resume_from": None,
                          "wandb": {"run_id": "run1", "sync_status": "pending",
                                    "local_dir": "runs/a1/wandb", "identity": self.identity,
                                    "snapshot_ref": None}}],
        }

    def snapshot(self):
        t = self.meta["tracking"]
        self.remote = {
            "schema_version": 1, **{k: t[k] for k in ("base_url", "entity", "project")},
            "run_id": "run1", "queried_at": "2026-11-20T12:00:00Z",
            "query": {"fields": ["config", "summary"], "history": False},
            "coverage": {"history": "not_requested"},
            "config": {"dl_assistant": dict(self.identity, **{k: t[k] for k in (
                "scope_id", "research_round", "hypothesis_ids")})}, "summary": {"eval/error": 0.2},
        }
        self.save_snapshot()
        self.meta["attempts"][0]["wandb"]["sync_status"] = "synced"

    def save_snapshot(self):
        p = self.root / "readback.json"
        p.write_text(json.dumps(self.remote))
        self.meta["attempts"][0]["wandb"]["snapshot_ref"] = {
            "path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    def check(self):
        return CHECKER.check(self.meta, self.root)

    def test_historical_meta_is_not_rewritten(self):
        original = {"status": "failed"}
        self.assertEqual(CHECKER.check(original, self.root), [])
        self.assertEqual(original, {"status": "failed"})

    def test_execution_and_sync_status_are_independent(self):
        for state in ("pending", "offline", "failed", "unknown", "not_created"):
            with self.subTest(state=state):
                self.meta["status"] = "completed" if state != "pending" else "failed"
                self.meta["attempts"][0]["wandb"].update(sync_status=state, reason="Service unreachable")
                self.assertEqual(self.check(), [])

    def test_unsynced_needs_recovery_directory_and_reason(self):
        w = self.meta["attempts"][0]["wandb"]
        w.update(sync_status="offline", reason="Service unreachable")
        w.pop("local_dir")
        self.assertTrue(self.check())
        w["local_dir"] = "runs/a1"
        w.pop("reason")
        self.assertTrue(self.check())

    def test_synced_requires_snapshot(self):
        self.meta["attempts"][0]["wandb"]["sync_status"] = "synced"
        self.assertTrue(self.check())
        self.snapshot()
        self.assertEqual(self.check(), [])

    def test_wrong_remote_identity_rejected(self):
        for field in ("run_id", "project", "entity", "base_url"):
            with self.subTest(field=field):
                self.snapshot()
                self.remote[field] = "https://another.internal" if field == "base_url" else "wrong"
                self.save_snapshot()
                self.assertTrue(self.check())
        self.snapshot()
        self.remote["config"]["dl_assistant"]["git_commit"] = "changed"
        self.save_snapshot()
        self.assertTrue(self.check())

    def test_snapshot_mutation_missing_and_escape(self):
        self.snapshot()
        (self.root / "readback.json").write_text("{}")
        self.assertTrue(self.check())
        (self.root / "readback.json").unlink()
        self.assertTrue(self.check())
        self.meta["attempts"][0]["wandb"]["snapshot_ref"]["path"] = "../outside.json"
        self.assertTrue(self.check())

    def test_same_run_cannot_hide_multiple_attempts(self):
        a2 = copy.deepcopy(self.meta["attempts"][0])
        a2["attempt_id"] = "a2"
        a2["wandb"]["identity"]["attempt_id"] = "a2"
        self.meta["attempts"].append(a2)
        self.assertTrue(self.check())

    def test_resume_uses_new_run_and_same_replicate(self):
        a2 = copy.deepcopy(self.meta["attempts"][0])
        a2.update(attempt_id="a2", resume_from="a1")
        a2["wandb"]["run_id"] = "run2"
        a2["wandb"]["identity"].update(attempt_id="a2", resume_from_attempt="a1")
        self.meta["attempts"].append(a2)
        self.assertEqual(self.check(), [])
        self.assertIsNone(self.meta["attempts"][0]["resume_from"])
        a2["replicate_id"] = "seed-1"
        self.assertTrue(self.check())

    def test_future_resume_and_duplicate_attempt_rejected(self):
        self.meta["attempts"][0]["resume_from"] = "a2"
        self.assertTrue(self.check())
        self.meta["attempts"][0]["resume_from"] = None
        self.meta["attempts"].append(copy.deepcopy(self.meta["attempts"][0]))
        self.assertTrue(self.check())

    def test_design_and_attempt_code_mismatch_detected(self):
        self.meta["attempts"][0]["git_commit"] = "wrong"
        self.assertTrue(self.check())
        self.meta["attempts"][0]["git_commit"] = "abc123"
        (self.root / "design.json").write_text('{"purpose":"new comparison"}')
        self.assertTrue(self.check())

    def test_meta_commit_is_checked_when_attempt_inherits_it(self):
        self.meta['git_commit'] = 'wrong'
        self.assertTrue(self.check())

    def test_explicit_retry_source_needs_recorded_approval(self):
        a = self.meta['attempts'][0]
        self.meta['git_commit'] = 'old'
        a['git_commit'] = 'abc123'
        self.assertTrue(self.check())
        a['deviation_ref'] = 'D1'
        self.meta['deviations'] = [{'id': 'D1', 'approval': {'status': 'approved', 'basis': 'Approved engineering correction'}}]
        self.assertEqual(self.check(), [])

    def test_retry_configuration_override_keeps_both_sources(self):
        a = self.meta['attempts'][0]
        p = self.root/'retry-config.json'
        p.write_text('{"frames":32}')
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        a['configuration_ref'] = {'path':p.name,'sha256':digest}
        self.identity['config_sha256'] = digest
        self.assertTrue(self.check())
        a['deviation_ref'] = 'D1'
        self.meta['deviations'] = [{'id':'D1','approval':{'status':'approved','basis':'Approved scope'}}]
        self.assertEqual(self.check(), [])
        self.assertTrue((self.root/'config.json').is_file())

    def test_config_and_dirty_diff_are_verified_from_files(self):
        self.meta['configuration_ref']['sha256'] = 'b' * 64
        self.assertTrue(self.check())
        self.meta['configuration_ref']['sha256'] = self.identity['config_sha256']
        self.meta.update(code_dirty=True, code_diff_path='code.diff')
        (self.root / 'code.diff').write_text('diff --git a/model.py b/model.py')
        self.assertTrue(self.check())
        self.identity['code_diff_sha256'] = hashlib.sha256((self.root / 'code.diff').read_bytes()).hexdigest()
        self.assertEqual(self.check(), [])
        (self.root / 'code.diff').write_text('different diff')
        self.assertTrue(self.check())

    def test_portable_offline_evidence_reports_missing_recovery_without_failing(self):
        import shutil
        shutil.rmtree(self.root / 'runs')
        self.assertTrue(self.check())  # On the originating machine this is an error.
        unchecked = []
        self.assertEqual(CHECKER.check(self.meta, self.root, portable=True, unchecked=unchecked), [])
        self.assertTrue(unchecked)
        self.assertEqual(self.meta['attempts'][0]['wandb']['sync_status'], 'pending')

    def test_query_scope_and_coverage_required(self):
        for key in ("query", "coverage", "queried_at"):
            self.snapshot()
            self.remote.pop(key)
            self.save_snapshot()
            self.assertTrue(self.check())

    def test_credentials_and_cloud_rejected_without_echo(self):
        for url in ("https://api.wandb.ai", "http://wandb.ai", "http://user:SECRET@host", "http://host?key=SECRET"):
            self.meta["tracking"]["base_url"] = url
            self.assertTrue(self.check())
            self.assertNotIn("SECRET", str(self.check()))
        self.meta["tracking"]["base_url"] = "http://wandb.internal:8080"
        self.meta["attempts"][0]["wandb"]["api_key"] = "SECRET"
        self.assertTrue(self.check())
        self.assertNotIn("SECRET", str(self.check()))

    def test_cli_invalid_json_no_secret_or_traceback(self):
        p = self.root / "meta.json"
        for content in ('{"tracking":null,"tracking":{}}', '{"tracking":NaN}', '{"api_key":"SECRET"'):
            p.write_text(content)
            result = subprocess.run([sys.executable, str(SCRIPT), "--meta", str(p)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("SECRET", result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_cli_valid_snapshot_is_read_only(self):
        self.snapshot()
        p = self.root / "meta.json"
        p.write_text(json.dumps(self.meta))
        before = {str(f.relative_to(self.root)): f.read_bytes() for f in self.root.rglob("*") if f.is_file()}
        result = subprocess.run([sys.executable, str(SCRIPT), "--meta", str(p)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, {str(f.relative_to(self.root)): f.read_bytes() for f in self.root.rglob("*") if f.is_file()})


if __name__ == "__main__":
    unittest.main()
