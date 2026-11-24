"""CLI回归：原意见保留、任务失败、证据身份、综合覆盖和复查状态。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('check_review.py')


def check(status='clear'):
    return {'status':status,'basis':'实际材料和检查范围已明确','unknowns':[],'effect':'按声明范围报告，不扩大推断'}


class ReviewChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        paper=self.put('paper.pdf',b'%PDF-1.4\nSynthetic fixture; not a scientific paper.\n')
        self.run={'schema_version':2,'run_id':'round-fixture','mode':'independent','paper':{'path':'paper.pdf','sha256':self.sha(paper)},'materials':[{'id':'paper','path':'paper.pdf','sha256':self.sha(paper),'role':'paper'}],'venue':{'name':None,'form_status':'not_requested','sources':[],'dimensions':[]},'isolation':{'status':'context_separated','limitations':['隔离声明不由本测试认证']},'tasks':[{'id':'r1','role':'reviewer','focus':'研究问题与证据'},{'id':'s1','role':'synthesis','focus':'综合实际意见'}],'preparation_check':check()}
        self.review=self.report('r1');self.review['issues']=[self.issue('I1')]
        self.meta=self.report('s1');self.meta.update(problems=[{**copy.deepcopy(self.review['issues'][0]),'id':'P1','source_refs':[{'task_id':'r1','issue_id':'I1'}]}],dispositions=[{'task_id':'r1','issue_id':'I1','outcome':'included','problem_id':'P1','reason':'核对后保留','evidence':[self.ev()]}],disputes=[],recommendation={'judgment':'mixed','rationale':'有新增，但此项条件仍待核','limits':['不预测录用']},rechecks=[])
        self.envs=[{'task_id':'r1','role':'reviewer','status':'returned','result':self.review,'error':None},{'task_id':'s1','role':'synthesis','status':'returned','result':self.meta,'error':None}]

    def put(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(value if isinstance(value,bytes) else value.encode());return p

    def sha(self,p):return hashlib.sha256(p.read_bytes()).hexdigest()

    def save(self,name,value):return self.put(name,json.dumps(value,ensure_ascii=False))

    def ev(self,kind='text'):
        return {'kind':kind,'material_id':'paper','location':'p2 §3','observation':'实际可定位观察；本测试不认证科学内容','excerpt':None}

    def issue(self,iid='I1'):
        return {'id':iid,'description':'必要条件是否保留需要核查','target_claim':'目标条件下的主张','impact':'若不满足则不能外推','finding_status':'unverified','severity':'major','evidence':[self.ev()],'open_questions':['目标关系未知'],'clarification_needed':'说明实际条件','suggested_actions':[],'self_check':check()}

    def report(self,tid):
        return {'task_id':tid,'run_id':self.run['run_id'],'paper_sha256':self.run['paper']['sha256'],'contribution':{'problem':'具体问题','prior_knowledge':'已有认识','new_knowledge':'当前新增','evidence_scope':'实际条件','significance':'新增为何重要'},'reading':{'locations':['p2 §3'],'missing_materials':[]},'strengths':[],'issues':[],'external_sources':[],'searches':[],'scores':[],'self_check':check()}

    def execute(self,expected=0,missing=(),output='handoff',before=None):
        runp=self.save('review-run.json',self.run)
        wf={'schema_version':2,'run_id':self.run['run_id'],'run_sha256':self.sha(runp),'tasks':self.envs}
        wfp=self.save('workflow-result.json',wf)
        for e in self.envs:
            if e['status']=='returned' and e['task_id'] not in missing:self.save('tasks/'+e['task_id']+'.json',e['result'])
        if before:before(runp,wfp)
        p=subprocess.run([sys.executable,str(SCRIPT),'--run',str(runp),'--workflow',str(wfp),'--output-dir',str(self.root/output)],capture_output=True,text=True)
        self.assertEqual(p.returncode,expected,p.stdout+'\n'+p.stderr)
        return json.loads((self.root/output/'problem-list.json').read_text()) if expected in (0,3) else p

    def test_complete_record_not_science_certification(self):
        p=self.execute();self.assertEqual(p['completion'],'complete');self.assertIn('结构校验',p['limits'][0]);self.assertTrue(Path(p['materials'][0]['path']).is_absolute());self.assertTrue(Path(p['input_refs']['run']['path']).is_file())

    def test_absence_issue_without_quote_is_preserved(self):
        for item in (self.review['issues'][0], self.meta['problems'][0]):
            item['finding_status'] = 'confirmed'
            item['evidence'] = [self.ev('absence')]
            item['open_questions'] = ['实际训练预算是否一致？']
        problem = self.execute()['problems'][0]
        self.assertEqual(problem['finding_status'], 'confirmed')
        self.assertEqual(problem['evidence'][0]['kind'], 'absence')
        self.assertIsNone(problem['evidence'][0]['excerpt'])
        self.assertEqual(problem['open_questions'], ['实际训练预算是否一致？'])

    def test_figure_and_equation_evidence_without_quote(self):
        self.review['issues'][0]['evidence']=[self.ev('figure'),self.ev('equation')]
        self.meta['problems'][0]['evidence']=copy.deepcopy(self.review['issues'][0]['evidence'])
        self.execute()

    def test_unverified_question_can_have_no_evidence_yet(self):
        self.review['issues'][0]['evidence']=[];self.meta['problems'][0]['evidence']=[]
        self.assertEqual(len(self.execute()['problems']),1)

    def test_confirmed_without_locatable_evidence_rejected(self):
        self.review['issues'][0].update(finding_status='confirmed',evidence=[])
        self.execute(1)

    def test_failed_task_retained_without_losing_other_issues(self):
        self.run['tasks'].insert(1,{'id':'r2','role':'reviewer','focus':'对照'})
        self.envs.insert(1,{'task_id':'r2','role':'reviewer','status':'failed','result':None,'error':'tool unavailable'})
        p=self.execute(3);self.assertEqual(len(p['problems']),1);self.assertEqual(p['task_statuses'][1]['status'],'failed')

    def test_missing_task_not_silently_filtered(self):
        self.envs.pop();self.execute(1)

    def test_planned_single_reviewer_completes_without_synthesis(self):
        self.run['tasks'].pop()
        self.envs.pop()
        package = self.execute()
        self.assertEqual(package['completion'], 'complete')
        self.assertEqual(package['synthesis_status'], 'not_planned')
        self.assertFalse(package['problems'][0]['needs_synthesis'])
        self.assertEqual(package['recommendation']['judgment'], 'undetermined')

    def test_synthesis_without_landed_artifact_remains_pending(self):
        package = self.execute(3, missing=('s1',))
        self.assertEqual(package['completion'], 'partial')
        self.assertEqual(package['synthesis_status'], 'pending')
        self.assertTrue(package['problems'][0]['needs_synthesis'])

    def test_resume_keeps_previously_handed_off_records_intact(self):
        synthesis = self.envs.pop()
        self.envs.append({**synthesis, 'status': 'failed', 'result': None, 'error': 'interrupted'})
        first = self.execute(3, output='handoffs/rev-1')
        self.assertEqual(first['synthesis_status'], 'pending')
        self.review['reading']['locations'].append('p6 Table 2')
        self.envs[-1] = synthesis
        second = self.execute(output='handoffs/rev-2')
        self.assertEqual(second['synthesis_status'], 'completed')
        self.assertNotEqual(first['input_refs']['workflow']['sha256'], second['input_refs']['workflow']['sha256'])
        self.assertNotEqual(first['task_statuses'][0]['artifact_sha256'], second['task_statuses'][0]['artifact_sha256'])

        for package, revision in ((first, 'rev-1'), (second, 'rev-2')):
            records = (self.root / 'handoffs' / revision / 'records').resolve()
            refs = [*package['input_refs'].values(), package['paper'], *package['materials']]
            refs.extend(
                {'path': task['artifact_path'], 'sha256': task['artifact_sha256']}
                for task in package['task_statuses'] if task['artifact_status'] == 'matched'
            )
            for ref in refs:
                path = Path(ref['path'])
                self.assertTrue(path.is_relative_to(records))
                self.assertEqual(self.sha(path), ref['sha256'])

    def test_missing_task_artifact_is_partial(self):
        p=self.execute(3,missing=('r1',));self.assertEqual(p['task_statuses'][0]['artifact_status'],'missing')

    def test_artifact_return_mismatch_rejected(self):
        def change(*_):self.save('tasks/r1.json',{'different':True})
        self.execute(1,before=change)

    def test_changed_paper_rejected(self):
        self.put('paper.pdf','changed');self.execute(1)

    def test_changed_run_after_workflow_rejected(self):
        def change(runp,_):runp.write_text(runp.read_text()+' ')
        self.execute(1,before=change)

    def test_undeclared_evidence_material_rejected(self):
        self.review['issues'][0]['evidence'][0]['material_id']='secret-author-notes'
        self.execute(1)

    def test_retrieved_source_snapshot_can_be_used(self):
        path=self.put('sources/r1/source.txt','Actual retrieved excerpt fixture')
        self.review['external_sources']=[{'id':'r1:related','path':'sources/r1/source.txt','sha256':self.sha(path),'url':'https://example.org/paper','read_locations':['abstract only']}]
        e={**self.ev('external'),'material_id':'r1:related'}
        self.review['issues'][0]['evidence']=[e];self.meta['problems'][0]['evidence']=[e]
        p=self.execute();self.assertEqual(p['materials'][-1]['id'],'r1:related')

    def test_stale_retrieved_source_rejected(self):
        self.review['external_sources']=[{'id':'r1:related','path':'paper.pdf','sha256':'0'*64,'url':'https://example.org/paper','read_locations':[]}]
        self.execute(1)

    def test_synthesis_cannot_omit_raw_issue(self):
        self.meta['dispositions']=[];self.execute(1)

    def test_synthesis_cannot_invent_source(self):
        self.meta['problems'][0]['source_refs'][0]['issue_id']='not-real';self.execute(1)

    def test_pending_issue_not_promoted_to_confirmed(self):
        self.meta['dispositions'][0]['outcome']='needs_check';self.meta['problems'][0]['finding_status']='confirmed'
        self.execute(1)

    def test_disagreement_remains_unverified(self):
        self.meta['disputes']=[{'topic':'条件是否足够','source_refs':[{'task_id':'r1','issue_id':'I1'}],'judgment':'unverified','basis':'缺目标条件资料','evidence':[self.ev()],'remaining_unknowns':['目标现象'],'next_actions':['先核资料']}]
        self.assertEqual(self.execute()['disputes'][0]['judgment'],'unverified')

    def test_not_supported_keeps_reason_and_evidence(self):
        self.meta['problems']=[];self.meta['dispositions'][0].update(outcome='not_supported',problem_id=None)
        p=self.execute();self.assertEqual(len(p['dispositions']),1);self.assertEqual(p['problems'],[])

    def test_not_supported_without_evidence_rejected(self):
        self.meta['problems']=[];self.meta['dispositions'][0].update(outcome='not_supported',problem_id=None,evidence=[])
        self.execute(1)

    def test_unverified_form_cannot_issue_official_score(self):
        self.review['scores']=[{'dimension':'overall','value':5,'reason':'judgment'}];self.execute(1)

    def test_verified_discrete_score_and_null_supported(self):
        self.run['venue']={'name':'fixture','form_status':'verified','sources':[{'ref':'https://example.org/form','checked_at':'fixture-date','scope':'test only','location':'rating'}],'dimensions':[{'name':'overall','allowed_values':[1,3,5,6,8,10]}]}
        self.review['scores']=[{'dimension':'overall','value':6,'reason':'fixture only'}];self.meta['scores']=[{'dimension':'overall','value':None,'reason':'unable to judge reliably'}]
        self.execute()

    def test_invalid_score_value_rejected(self):
        self.run['venue']={'name':'fixture','form_status':'verified','sources':[{'ref':'x','checked_at':'x','scope':'x','location':'x'}],'dimensions':[{'name':'overall','allowed_values':[1,3,5,6,8,10]}]}
        self.review['scores']=[{'dimension':'overall','value':7,'reason':'not an allowed value'}];self.execute(1)

    def test_independent_mode_cannot_take_prior_review(self):
        m=copy.deepcopy(self.run['materials'][0]);m.update(id='old',role='prior_review');self.run['materials'].append(m)
        self.execute(1)

    def revision(self):
        path=self.save('prior/problem-list.json',{'schema_version':2,'run_id':'prior-fixture','paper':copy.deepcopy(self.run['paper']),'problems':[{'id':'OLD1'},{'id':'OLD2'}]})
        self.run.update(mode='revision_check',prior_round={'path':'prior/problem-list.json','sha256':self.sha(path)},revision_scope=['OLD1'])

    def test_revision_tracks_out_of_scope_as_not_checked(self):
        self.revision();self.meta['rechecks']=[{'prior_problem_id':'OLD1','status':'resolved','reason':'核实际修改','evidence':[self.ev()],'new_problem_ids':[]}]
        p=self.execute();self.assertEqual(p['rechecks'][-1]['status'],'not_checked');self.assertEqual(p['rechecks'][-1]['prior_problem_id'],'OLD2')
        archived_prior = Path(p['prior_round']['path'])
        self.assertTrue(archived_prior.is_relative_to((self.root / 'handoff/records').resolve()))
        self.assertEqual(self.sha(archived_prior), p['prior_round']['sha256'])

    def test_selected_revision_without_rechecks_is_partial(self):
        self.revision()
        self.run['tasks'].pop()
        self.envs.pop()
        package = self.execute(3)
        self.assertEqual(package['synthesis_status'], 'not_planned')
        self.assertEqual(package['rechecks'][0]['status'], 'not_checked')

    def test_revision_missing_selected_issue_rejected(self):
        self.revision();self.execute(1)

    def test_author_says_fixed_without_evidence_not_resolved(self):
        self.revision();self.meta['rechecks']=[{'prior_problem_id':'OLD1','status':'resolved','reason':'author says fixed','evidence':[],'new_problem_ids':[]}]
        self.execute(1)

    def test_revision_missing_material_can_be_not_checked(self):
        self.revision();self.meta['rechecks']=[{'prior_problem_id':'OLD1','status':'not_checked','reason':'缺所需材料','evidence':[],'new_problem_ids':[]}]
        self.assertEqual(self.execute()['rechecks'][0]['status'],'not_checked')

    def test_new_problem_not_erased_by_old_fix(self):
        self.revision();self.meta['rechecks']=[{'prior_problem_id':'OLD1','status':'partially_resolved','reason':'仍有新问题','evidence':[self.ev()],'new_problem_ids':['P1']}]
        self.assertEqual(self.execute()['rechecks'][0]['new_problem_ids'],['P1'])

    def test_needs_revision_self_check_yields_partial(self):
        self.review['self_check']=check('needs_revision');self.assertEqual(self.execute(3)['completion'],'partial')

    def test_output_never_overwrites_history(self):
        self.execute();original=(self.root/'handoff/problem-list.json').read_bytes();self.execute(1)
        self.assertEqual((self.root/'handoff/problem-list.json').read_bytes(),original)

    def test_bad_json_does_not_create_handoff(self):
        def change(_,wf):wf.write_text('{bad')
        self.execute(1,before=change);self.assertFalse((self.root/'handoff').exists())


if __name__=='__main__':unittest.main()
