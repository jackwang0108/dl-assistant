"""CLI regressions: records cannot silently bypass missing or stale checks.

These tests assess record enforcement, not whether an agent reasons correctly.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check_research_self_check.py')


class SelfCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="research check '")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.notes = self.root / 'research.md'
        self.notes.write_text('Q1: Does a fixed-budget intervention change errors on rare events?\n'
                              'H1 is untested; selection effects remain an alternative.\n')
        self.path = self.root / 'self-check.json'
        findings = {
            'problem': 'The object, budget and rare-event outcome are defined in Q1.',
            'hypothesis': 'H1 predicts a conditional error change; this is not a measured result.',
            'reasoning': 'The intervention targets the stated constraint; effectiveness remains unknown.',
            'value': 'An answer would distinguish a resource limit from a representation limit.',
            'alternatives': 'Sample selection could also produce a difference; use a fixed held-out cohort.',
        }
        self.record = {
            'schema_version': 1, 'skill': 'idea-find', 'stage': 'candidate',
            'subject': 'Q1/H1, revision 1', 'checked_at': '2026-11-19T10:00:00+08:00',
            'inputs': [{'path': 'research.md', 'sha256': self.digest()}],
            'checks': [{'id': cid, 'status': 'clear', 'finding': finding,
                        'basis_refs': ['research.md#Q1'], 'unknowns': [],
                        'effect': 'Proceed to a bounded value discussion, not experimental launch.'}
                       for cid, finding in findings.items()],
            'decision': 'continue', 'next_action': 'Discuss Q1 and H1 with the user',
        }

    def digest(self):
        return hashlib.sha256(self.notes.read_bytes()).hexdigest()

    def run_check(self, expected=0, skill='idea-find', stage='candidate', write=True):
        if write:
            self.path.write_text(json.dumps(self.record, ensure_ascii=False))
        result = subprocess.run([sys.executable, str(SCRIPT), '--record', str(self.path),
                                 '--root', str(self.root), '--skill', skill, '--stage', stage],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def test_complete_record_allows_only_its_declared_action(self):
        self.run_check()

    def test_missing_check_fails(self):
        self.record['checks'].pop()
        self.run_check(expected=1)

    def test_check_without_basis_or_action_effect_fails(self):
        for field, value in (('basis_refs', []), ('finding', ''), ('effect', '')):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                self.record['checks'][0][field] = value
                self.run_check(expected=1)
                self.record = record

    def test_missing_source_file_fails(self):
        self.record['checks'][0]['basis_refs'] = ['not-obtained.pdf#p1']
        self.run_check(expected=1)

    def test_changed_input_invalidates_prior_check(self):
        self.notes.write_text(self.notes.read_text() + 'Revision: now a narrower question.\n')
        self.run_check(expected=1)

    def test_missing_input_fails(self):
        self.notes.unlink()
        self.run_check(expected=1)

    def test_needs_revision_cannot_authorize_continuation(self):
        self.record['checks'][0].update(status='needs_revision',
                                       finding='Q1 is still a topic, not a defined problem.',
                                       unknowns=['Object and conditions'], effect='Clarify before any launch.')
        self.run_check(expected=1)
        self.record['decision'] = 'revise'
        self.record['next_action'] = 'Save the defect and clarify Q1'
        self.run_check(expected=1)  # Honest revision is still not permission for the blocked action.

    def test_unknown_effect_can_continue_as_limited_exploration(self):
        self.record['checks'][2].update(status='limited', unknowns=['No effect estimate yet'],
                                       effect='Continue discussing a bounded exploratory estimate, not claiming efficacy.')
        self.run_check(expected=1)
        self.record['decision'] = 'continue_with_limits'
        self.run_check()

    def test_limited_requires_explanation(self):
        self.record['checks'][0]['status'] = 'limited'
        self.record['decision'] = 'continue_with_limits'
        self.run_check(expected=1)

    def test_wrong_checkpoint_or_skill_cannot_reuse_record(self):
        self.run_check(expected=1, stage='handoff')
        self.run_check(expected=1, skill='code-idea-iterate', stage='next_step')

    def test_duplicate_ids_and_json_keys_fail(self):
        self.record['checks'].append(copy.deepcopy(self.record['checks'][0]))
        self.run_check(expected=1)
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        self.run_check(expected=1, write=False)

    def test_invalid_json_and_values_fail_without_traceback(self):
        for value in ('', '{', '[]', '{"value":NaN}'):
            with self.subTest(value=value):
                self.path.write_text(value)
                self.run_check(expected=1, write=False)
        for field in ('checks', 'inputs', 'decision'):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                self.record[field] = None
                self.run_check(expected=1)
                self.record = record

    def test_empty_snapshots_or_self_reference_fail(self):
        self.record['inputs'] = []
        self.run_check(expected=1)
        self.record['inputs'] = [{'path': 'self-check.json', 'sha256': 'not-real'}]
        self.run_check(expected=1)

    def test_url_reference_is_not_a_scientific_validation(self):
        self.record['checks'][0]['basis_refs'] = ['https://example.org/paper']
        result = self.run_check()
        self.assertIn('不证明', result.stdout)

    def test_partial_execution_can_handoff_honestly(self):
        self.record.update(skill='code-idea-execution', stage='handoff',
                           decision='continue_with_limits', next_action='Report incomplete data to iterate')
        self.notes.write_text('Run blocked by memory limits; no valid comparison exists. All attempts retained.\n')
        self.record['inputs'][0]['sha256'] = self.digest()
        self.record['checks'] = [
            {'id': cid, 'status': 'limited', 'finding': finding,
             'basis_refs': ['research.md'], 'unknowns': ['Comparison remains unmeasured'],
             'effect': 'Handoff reports a blocked run, without treating it as a hypothesis refutation.'}
            for cid, finding in (
                ('execution_state', 'Run blocked; comparison not completed.'),
                ('data_validity', 'No usable comparative result, not a negative effect.'),
                ('inference', 'Cannot infer support or contradiction.'),
                ('deviations', 'Memory failure and all attempts recorded.'),
                ('traceability', 'Execution record and missing result are explicitly located.'))]
        self.run_check(skill='code-idea-execution', stage='handoff')

    def test_stopping_with_unknowns_is_not_paper_readiness(self):
        self.record.update(skill='code-idea-iterate', stage='transition',
                           decision='continue_with_limits', next_action='Save a stop decision, do not handoff to writing')
        self.notes.write_text('Question narrowed to a minor known setting; user declines further budget. Mechanism unresolved.\n')
        self.record['inputs'][0]['sha256'] = self.digest()
        self.record['checks'] = [
            {'id': cid, 'status': 'limited', 'finding': finding,
             'basis_refs': ['research.md'], 'unknowns': ['Core mechanism remains unresolved'],
             'effect': 'Save limits and stop investment; neither paper readiness nor scientific refutation is asserted.'}
            for cid, finding in (
                ('knowledge', 'The current study has not established a worthwhile new answer.'),
                ('evidence', 'Evidence is insufficient for the original claim.'),
                ('novelty_value', 'Remaining narrow difference has no justified significance.'),
                ('remaining_work', 'More core experiments would be needed; none are authorized.'),
                ('recommendation', 'User declines further budget after the stop recommendation.'))]
        self.run_check(skill='code-idea-iterate', stage='transition')

    def test_invalid_cli_usage(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.run_check(expected=2, stage='unknown')


if __name__ == '__main__':
    unittest.main()
