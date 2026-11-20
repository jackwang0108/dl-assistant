"""Offline CLI regressions for missing records and honest non-positive outcomes."""
import copy
import json
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check-exp-artifacts.sh')


class ArtifactCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="experiment check '")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exp = self.root / 'exp-001-evaluation'
        self.exp.mkdir()
        self.meta = {
            'schema_version': 2, 'experiment_id': self.exp.name,
            'type': 'evaluation', 'design_mode': 'confirmation',
            'status': 'completed', 'data_validity': 'valid',
            'inference_status': 'contradicted', 'purpose': 'Check predicted error reduction',
            'design_record': {'path': 'design.json'},
            'interpretation_plan': 'Compare paired errors; report uncertainty and alternative explanations',
            'git_commit': '0123456789', 'code_dirty': False,
            'attempts': [{'attempt_id': 'a1', 'replicate_id': 'main', 'status': 'completed', 'command': 'python eval.py', 'exit_code': 0}],
            'required_artifacts': [{'path': 'results.json', 'format': 'json', 'required_for': ['completed']}],
        }
        self.write('design.json', {'prediction': 'Error decreases', 'analysis': 'paired difference'})
        self.write('results.json', {'difference': 0.02, 'unit': 'error fraction'})
        (self.exp / '报告.md').write_text('Observed error increased; evidence contradicts the prediction.\n')
        self.save()

    def write(self, path, data):
        (self.exp / path).write_text(json.dumps(data), encoding='utf-8')

    def save(self):
        self.write('meta.json', self.meta)
        row = {key: self.meta[key] for key in ('experiment_id', 'status', 'data_validity', 'inference_status')}
        self.rows = [row]
        self.ledger()

    def ledger(self):
        (self.root / 'index.json').write_text(json.dumps({'schema_version': 2, 'experiments': self.rows}))

    def run_check(self, *args, expected=0):
        result = subprocess.run(['bash', str(SCRIPT), *map(str, args)], text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def test_completed_negative_evaluation_without_training_log(self):
        self.run_check('--all', self.root)

    def test_missing_meta_fails(self):
        (self.exp / 'meta.json').unlink()
        self.run_check('--expdir', self.exp, expected=1)

    def test_empty_collection_fails(self):
        with tempfile.TemporaryDirectory() as empty:
            Path(empty, 'index.json').write_text('{"schema_version":2,"experiments":[]}')
            self.run_check('--all', empty, expected=1)

    def test_failed_blocked_cancelled_need_no_success_metrics(self):
        for status in ('failed', 'blocked', 'cancelled'):
            with self.subTest(status=status):
                self.meta.update(status=status, status_reason='No usable GPU memory',
                                 data_validity='unassessed', inference_status='pending')
                self.meta['required_artifacts'] = [{'path': 'error.log', 'format': 'text', 'required_for': [status]}]
                (self.exp / 'error.log').write_text('OOM, no scientific result obtained\n')
                self.save()
                result = self.run_check('--all', self.root)
                self.assertIn('WARN', result.stdout)

    def test_failure_reason_required(self):
        self.meta.update(status='failed', status_reason=None)
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_exploration_does_not_require_effect_threshold(self):
        self.meta.update(design_mode='exploration', interpretation_plan=None,
                         analysis_plan='Inspect conditional error distributions', decision_rule=None,
                         inference_status='not_identifiable')
        self.save()
        self.run_check('--all', self.root)

    def test_confirmation_requires_interpretation_plan(self):
        self.meta['interpretation_plan'] = None
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_completed_requires_declared_result(self):
        self.meta['required_artifacts'] = []
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_invalid_missing_empty_or_ambiguous_json_fails(self):
        for content in ('', '{', '{"x":1,"x":2}', '{"x":NaN}'):
            with self.subTest(content=content):
                (self.exp / 'results.json').write_text(content)
                self.run_check('--all', self.root, expected=1)
        (self.exp / 'results.json').unlink()
        self.run_check('--all', self.root, expected=1)

    def test_json_arrays_are_valid_results(self):
        self.write('results.json', [{'sample': 1, 'error': 0.2}])
        self.run_check('--all', self.root)

    def test_ledger_duplicate_or_mismatch_fails(self):
        self.rows.append(dict(self.rows[0]))
        self.ledger()
        self.run_check('--all', self.root, expected=1)
        self.rows = [dict(self.rows[0], status='failed')]
        self.ledger()
        self.run_check('--all', self.root, expected=1)

    def test_orphan_and_unstarted_plan_are_distinguished(self):
        self.rows.append({'experiment_id': 'exp-002-plan', 'status': 'completed'})
        self.ledger()
        self.run_check('--all', self.root, expected=1)
        self.rows[-1].update(status='not_started', status_reason='Waiting for dataset')
        self.ledger()
        self.assertIn('WARN', self.run_check('--all', self.root).stdout)

    def test_dirty_code_requires_saved_diff(self):
        self.meta.update(code_dirty=True, code_diff_path='code.diff')
        self.save()
        self.run_check('--all', self.root, expected=1)
        (self.exp / 'code.diff').write_text('diff --git a/eval.py b/eval.py\n')
        self.run_check('--all', self.root)

    def test_artifact_cannot_escape_experiment_directory(self):
        (self.root / 'external.json').write_text('{}')
        self.meta['required_artifacts'][0]['path'] = '../external.json'
        self.save()
        self.run_check('--all', self.root, expected=1)
        (self.exp / 'link.json').symlink_to(self.root / 'external.json')
        self.meta['required_artifacts'][0]['path'] = 'link.json'
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_malformed_fields_fail_without_traceback(self):
        for field in ('status', 'type', 'data_validity', 'inference_status', 'design_mode'):
            with self.subTest(field=field):
                original = self.meta[field]
                self.meta[field] = []
                self.save()
                self.run_check('--all', self.root, expected=1)
                self.meta[field] = original
        self.meta['required_artifacts'][0]['format'] = {}
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_unassessed_data_cannot_support_or_contradict(self):
        self.meta['data_validity'] = 'unassessed'
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_legacy_schema_is_not_silently_upgraded(self):
        self.meta['schema_version'] = 1
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_declared_tracking_cannot_bypass_shared_check(self):
        self.meta['tracking'] = {'provider': 'wandb', 'base_url': 'https://api.wandb.ai'}
        self.save()
        result = self.run_check('--all', self.root, expected=1)
        self.assertIn('W&B', result.stdout)

    def test_tracking_init_failure_does_not_change_experiment_status(self):
        self.meta.update(status='failed', status_reason='Initialization failed')
        self.meta['tracking'] = None
        self.save()
        result = self.run_check('--all', self.root)
        self.assertIn('执行状态=failed', result.stdout)

    def test_attempt_fields_and_duplicate_ids_are_checked(self):
        original = copy.deepcopy(self.meta['attempts'])
        for attempts in ([{}], ['bad'], [dict(original[0], status='unknown')],
                         [dict(original[0], command='')], [dict(original[0], exit_code=1)],
                         [dict(original[0], exit_code=True)], original * 2):
            with self.subTest(attempts=attempts):
                self.meta['attempts'] = attempts
                self.save()
                self.run_check('--all', self.root, expected=1)

    def test_resume_requires_earlier_same_replicate(self):
        self.meta['attempts'][0]['resume_from'] = 'a2'
        self.save()
        self.run_check('--all', self.root, expected=1)
        a2 = dict(self.meta['attempts'][0], attempt_id='a2', resume_from='a1', replicate_id='other')
        self.meta['attempts'][0]['resume_from'] = None
        self.meta['attempts'].append(a2)
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_running_attempt_has_no_fake_terminal_exit(self):
        self.meta.update(status='in_progress', data_validity='unassessed', inference_status='pending')
        self.meta['attempts'][0].update(status='in_progress', exit_code=None)
        self.save()
        self.run_check('--all', self.root)
        self.meta['attempts'][0]['exit_code'] = 0
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_completed_experiment_needs_a_completed_attempt(self):
        self.meta['attempts'][0].update(status='failed', exit_code=1)
        self.save()
        self.run_check('--all', self.root, expected=1)

    def test_standalone_install_without_wandb(self):
        scripts = self.root / 'installed/code-idea-execution/scripts'
        scripts.mkdir(parents=True)
        source = SCRIPT.with_name('check_exp_artifacts.py')
        shutil.copy(source, scripts / source.name)
        command = [sys.executable, str(scripts / source.name)]
        self.assertEqual(subprocess.run(command + ['--help'], capture_output=True).returncode, 0)
        result = subprocess.run(command + ['--all', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.meta['tracking'] = {'provider': 'wandb'}
        self.save()
        result = subprocess.run(command + ['--all', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('wandb', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_cli_usage_errors(self):
        for args in ((), ('--all',), ('--all', self.root, '--expdir', self.exp), ('--all', self.root / 'missing')):
            with self.subTest(args=args):
                self.run_check(*args, expected=2)


if __name__ == '__main__':
    unittest.main()
