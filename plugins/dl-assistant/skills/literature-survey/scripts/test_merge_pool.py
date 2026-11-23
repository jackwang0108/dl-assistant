"""Offline regression tests: python3 -B -m unittest discover -s <scripts>."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import merge_pool as mod


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "search").mkdir()

    def write(self, name, **data):
        path = self.root / "search" / f"{name}.json"
        path.write_text(json.dumps({"query_group": name, **data}), encoding="utf-8")
        return path

    def pool(self):
        return mod.build_pool(sorted((self.root / "search").glob("*.json")))

    def test_bridge_arxiv_and_doi_across_groups(self):
        self.write("a", included=[{"title": "Work", "arxiv": "https://arxiv.org/abs/2601.00001v2"}])
        self.write("b", included=[{"doi": "https://doi.org/10.1/work", "arxiv": "2601.00001"}])
        self.write("c", included=[{"doi": "DOI:10.1/WORK"}])
        pool = self.pool()
        self.assertEqual(len(pool["papers"]), 1)
        paper = pool["papers"][0]
        self.assertEqual(len(paper["observations"]), 3)
        self.assertEqual(paper["source_groups"], ["a", "b", "c"])
        self.assertEqual(paper["arxiv"], "2601.00001")
        self.assertEqual(paper["doi"], "10.1/work")

    def test_same_title_is_review_candidate_not_merge(self):
        self.write("a", included=[{"title": "Same title", "authors": ["A"]},
                                    {"title": "Same title", "authors": ["B"]}])
        pool = self.pool()
        self.assertEqual(len(pool["papers"]), 2)
        self.assertEqual(len(pool["possible_duplicates"]), 1)

    def test_conflicting_strong_identifiers_remain_pending(self):
        self.write("a", included=[{"arxiv": "2601.00001", "doi": "10.1/x"},
                                    {"arxiv": "2601.00002", "doi": "10.1/x"}])
        pool = self.pool()
        self.assertEqual(len(pool["papers"]), 0)
        self.assertEqual(len(pool["pending"]), 2)
        self.assertEqual(len(pool["identity_conflicts"]), 1)

    def test_inclusion_exclusion_conflict_not_silenced(self):
        self.write("a", included=[{"arxiv": "2601.00001", "reason": "Relevant"}])
        self.write("b", excluded=[{"arxiv": "2601.00001", "reason": "Not relevant"}])
        pool = self.pool()
        self.assertEqual(pool["papers"], [])
        self.assertEqual(pool["excluded"], [])
        self.assertTrue(pool["pending"][0]["decision_conflict"])
        self.assertEqual(len(pool["pending"][0]["observations"]), 2)

    def test_citations_keep_source_time_and_zero_without_maximum(self):
        self.write("a", included=[{"doi": "10.1/x", "citations": 0, "source": "A", "observed_at": "2026-01-01"}])
        self.write("b", included=[{"doi": "10.1/x", "citations": 30, "source": "B", "observed_at": "2026-02-01"}])
        paper = self.pool()["papers"][0]
        self.assertIsNone(paper["citations"])
        self.assertEqual([x["value"] for x in paper["citation_observations"]], [0, 30])
        self.assertEqual(paper["citation_observations"][1]["source"], "B")

    def test_versions_and_field_conflicts_are_preserved(self):
        self.write("a", included=[{"arxiv": "2601.00001v1", "title": "Old", "version": "v1"},
                                    {"arxiv": "2601.00001v2", "title": "New", "version": "v2"}])
        paper = self.pool()["papers"][0]
        self.assertIsNone(paper["title"])
        self.assertIn("version", [c["field"] for c in paper["field_conflicts"]])
        self.assertEqual(paper["observations"][0]["record"]["arxiv"], "2601.00001v1")

    def test_partial_request_and_new_hit_are_separate(self):
        call = {"source": "arxiv", "status": "partial", "truncated": True, "complete": False}
        self.write("a", requests=[call], included=[{"title": "Recent", "published": "2026-07"}])
        pool = self.pool()
        self.assertEqual(pool["stats"]["latest_published"], "2026-07")
        self.assertEqual(pool["requests"][0]["requests"], [call])
        self.assertNotIn("coverage_complete", pool["stats"])

    def test_old_inputs_have_unknown_coverage(self):
        self.write("old", included=[{"title": "Legacy"}])
        self.assertFalse(self.pool()["requests"][0]["coverage_known"])

    def test_unknown_decision_is_pending(self):
        self.write("a", pending=[{"title": "Need abstract"}])
        self.assertEqual(len(self.pool()["pending"]), 1)

    def test_url_identity_and_arxiv_url_alias(self):
        self.write("a", included=[{"url": "https://arxiv.org/pdf/2601.00001v2"},
                                    {"arxiv": "2601.00001"},
                                    {"url": "https://example.org/paper/one"},
                                    {"url": "https://example.org/paper/one"}])
        self.assertEqual(len(self.pool()["papers"]), 2)

    def test_malformed_inputs_do_not_replace_existing_pool(self):
        target = self.root / "pool.json"
        target.write_text('{"existing": true}')
        (self.root / "search" / "bad.json").write_text('{"included": [')
        result = subprocess.run([sys.executable, "-B", str(Path(mod.__file__)), str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bad.json", result.stderr)
        self.assertEqual(json.loads(target.read_text()), {"existing": True})

    def test_invalid_shapes_report_input_file(self):
        self.write("bad", included="not an array")
        with self.assertRaisesRegex(ValueError, "bad.json"):
            self.pool()

    def test_cli_produces_pool_and_preserves_input(self):
        path = self.write("a", included=[{"doi": "10.1/x"}])
        before = path.read_bytes()
        result = subprocess.run([sys.executable, "-B", str(Path(mod.__file__)), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(json.loads((self.root / "pool.json").read_text())["papers"]), 1)
        self.assertEqual(list(self.root.glob('.pool-*')), [])


if __name__ == "__main__":
    unittest.main()
