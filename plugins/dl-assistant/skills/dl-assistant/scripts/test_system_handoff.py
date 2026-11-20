"""Cross-skill file/CLI integration, not autonomous research-quality evaluation.

The same synthetic records flow through research self-checks, execution, paper
experiments, a copied offline package and the writing number checker. Research
assessments in this fixture are prescribed; actual agent evaluation is separate.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILLS = Path(__file__).resolve().parents[2]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


FIXTURES = module(SKILLS/'code-paper-experiment/scripts/test_check_run_artifacts.py', 'batch_fixtures')
SELF_CHECK = module(SKILLS/'dl-assistant/scripts/check_research_self_check.py', 'research_checks')


class SystemHandoff(unittest.TestCase):
    def setUp(self):
        self.case = FIXTURES.ArtifactChecks('test_package_consistent')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root, self.exp = self.case.root, self.case.exp
        self.case.put(self.root/'question.md', 'Synthetic Q1: what is the mean of the two prescribed measurements?\n')
        claims = json.loads((SKILLS/'dl-assistant/references/claims-template.json').read_text())
        claims['paper_claim'] = None
        claims['claims'] = []  # A measurement question need not invent a directional hypothesis.
        self.case.write(self.root/'claims.json', claims)
        self.case.meta['research_question_ids'] = ['Q1']
        self.case.meta['hypothesis_ids'] = []
        self.case.meta['claim_cids'] = []

    def cli(self, script, *args, code=0):
        result = subprocess.run([sys.executable, str(SKILLS/script), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def self_check(self, skill, stage, inputs, action):
        record = {'schema_version':1, 'skill':skill, 'stage':stage, 'subject':'Synthetic Q1, fixed two-measurement protocol',
                  'checked_at':'2026-11-20T12:00:00Z', 'inputs':[self.case.ref(self.root/p, self.root) for p in inputs],
                  'checks':[{'id':cid, 'status':'limited', 'finding':'Fixed synthetic boundary test, no real research finding or user authorization',
                             'basis_refs':inputs, 'unknowns':['No claim about real scientific value'],
                             'effect':action} for cid in sorted(SELF_CHECK.REQUIRED[(skill, stage)])],
                  'decision':'continue_with_limits', 'next_action':action}
        path = self.case.write(self.root/'self-checks'/f'{skill}-{stage}.json', record)
        self.cli('dl-assistant/scripts/check_research_self_check.py', '--root', self.root, '--record', path,
                 '--skill', skill, '--stage', stage)
        return path

    def execution(self):
        self.case.save()
        row = {k:self.case.meta[k] for k in ('experiment_id','status','data_validity','inference_status')}
        self.case.write(self.exp.parent/'index.json', {'schema_version':2,'experiments':[row]})
        return self.cli('code-idea-execution/scripts/check_exp_artifacts.py', '--all', self.exp.parent)

    def writing(self, package):
        paper = package/'paper'
        self.case.put(paper/'main.tex', '\\documentclass{article}\n\\begin{document}\n\\input{sections/results}\n\\end{document}\n')
        self.case.put(paper/'sections/results.tex', 'The synthetic measured mean is 2.0.\n')
        source = package/'experiments/exp-A/results.json'
        item = {'id':'q1-mean', 'experiment_id':'exp-A', 'metric':'score mean',
                'condition_ref':'../experiments/exp-A/conditions.md',
                'source':{'path':'../experiments/exp-A/results.json', 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                          'json_pointer':'/metrics/score/mean'},
                'location':{'path':'sections/results.tex','line':1,'token':'2.0','occurrence':1}}
        self.case.write(paper/'_draft/canonical-values.json', {'schema_version':2,'entries':[item],'exemptions':[]})
        self.cli('writing-paper/scripts/check_numbers.py', paper)
        return paper

    def test_complete_chain_uses_one_record_set(self):
        self.self_check('idea-find','handoff',['question.md','claims.json'], 'Check the prescribed measurement design only')
        self.case.save()
        self.self_check('code-idea-execution','pre_run',['question.md','plan.json','experiments/exp-A/scripts/run.py'], 'Check synthetic source identity')
        self.execution()
        self.self_check('code-idea-execution','handoff',['question.md','experiments/exp-A/meta.json','experiments/exp-A/results.json'], 'Hand over actual synthetic readings')
        self.case.put(self.root/'assessment.md', 'Synthetic Q1 mean is 2.0 from the two declared readings; no performance or novelty claim.\n')
        self.self_check('code-idea-iterate','transition',['question.md','assessment.md','experiments/exp-A/results.json'], 'Preserve the fixed fixture assessment for number tracing only')
        self.case.audit(package=True)
        self.writing(self.root)
        self.assertIsNone(json.loads((self.root/'claims.json').read_text())['paper_claim'])

    def test_offline_package_is_checked_after_real_directory_copy(self):
        self.case.enable_tracking()
        self.execution()
        self.case.audit(package=True)
        with tempfile.TemporaryDirectory() as target:
            copied = Path(target)/'received'
            shutil.copytree(self.root, copied, ignore=shutil.ignore_patterns('wandb'))
            result = self.cli('code-paper-experiment/scripts/check_run_artifacts.py', '--pkgdir', copied, code=3)
            self.assertIn('UNCHECKED', result.stdout)
            self.assertNotIn('FAIL', result.stdout)
            self.writing(copied)
            meta = json.loads((copied/'experiments/exp-A/meta.json').read_text())
            self.assertEqual(meta['status'], 'completed')
            self.assertTrue(all(a['wandb']['sync_status']=='offline' for a in meta['attempts']))

    def test_recovery_keeps_failed_attempt_and_does_not_add_a_replicate(self):
        previous = copy.deepcopy(self.case.meta['attempts'][0])
        previous.update(attempt_id='failed-first', status='failed', exit_code=1)
        self.case.meta['attempts'].insert(0, previous)
        self.case.meta['attempts'][1]['resume_from'] = 'failed-first'
        self.execution()
        self.case.audit(package=True)
        self.writing(self.root)
        self.assertEqual(self.case.result['n_replicates'], 2)
        self.assertEqual(len(self.case.meta['attempts']), 3)

    def test_changed_source_invalidates_previous_pre_run_check(self):
        self.case.save()
        record = self.self_check('code-idea-execution','pre_run',['question.md','experiments/exp-A/scripts/run.py'], 'Check this exact source before execution')
        self.case.put(self.exp/'scripts/run.py', '# changed source after review\n')
        self.cli('dl-assistant/scripts/check_research_self_check.py', '--root', self.root, '--record', record,
                 '--skill','code-idea-execution','--stage','pre_run', code=1)
        self.case.audit(1)

    def test_later_result_change_breaks_package_and_paper_trace(self):
        self.case.audit(package=True)
        paper = self.writing(self.root)
        altered = copy.deepcopy(self.case.result)
        altered['metrics']['score']['mean'] = 99
        self.case.write(self.exp/'results.json', altered)
        self.cli('code-paper-experiment/scripts/check_run_artifacts.py', '--pkgdir', self.root, code=1)
        self.cli('writing-paper/scripts/check_numbers.py', paper, code=1)


if __name__ == '__main__':
    unittest.main()
