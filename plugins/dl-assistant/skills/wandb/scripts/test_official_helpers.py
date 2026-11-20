"""Exercise the selected upstream helpers without a W&B service or dependencies."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "upstream/wandb-primary/scripts/wandb_helpers_impl.py"
SPEC = importlib.util.spec_from_file_location("official_wandb_helpers", SOURCE)
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)


class OfficialHelpersTests(unittest.TestCase):
    def test_scan_requires_explicit_metric_keys(self):
        with self.assertRaises(ValueError):
            HELPERS.scan_history(None, keys=[])

    def test_scan_obeys_positive_row_budget_and_passes_keys(self):
        class Run:
            def scan_history(self, **kwargs):
                self.request = kwargs
                yield from ({"_step": i, "loss": 1 / (i + 1)} for i in range(20))
        run = Run()
        rows = HELPERS.scan_history(run, keys=["loss"], max_rows=3)
        self.assertEqual([r["_step"] for r in rows], [0, 1, 2])
        self.assertEqual(run.request["keys"], ["loss"])

    def test_history_does_not_invent_missing_metrics(self):
        class Run:
            def scan_history(self, **kwargs):
                yield {"_step": 4, "val_loss": 0.4}
        rows = HELPERS.scan_history(Run(), keys=["val_loss"], max_rows=10)
        self.assertEqual(rows, [{"_step": 4, "val_loss": 0.4}])

    def test_distinct_display_names_config_comparison_selects_fields(self):
        a = SimpleNamespace(name="baseline", config={"lr": 0.01, "seed": 0})
        b = SimpleNamespace(name="method", config={"lr": 0.02, "seed": 1})
        self.assertEqual(HELPERS.compare_configs(a, b, keys=["lr"]),
                         [{"key": "lr", "baseline": 0.01, "method": 0.02}])


if __name__ == "__main__":
    unittest.main()
