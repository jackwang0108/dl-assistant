"""CLI回归：意见覆盖、真实状态、版本、批准、批次和跨回复一致性记录。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('check_response.py')


def check(status='clear'):
    return {'status':status,'basis':'核对实际输入及本轮范围','unknowns':[],'effect':'只交当前明确的处理行动'}


class ResponseChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.sources=[]
        p=self.put('paper.pdf','Synthetic submitted manuscript fixture')
        self.source('comments','comments','comments.txt','Please clarify the setup.')
        self.source('evidence','evidence','data.json',json.dumps({'count':2}))
        self.s={'schema_version':2,'response_id':'response-fixture','stage':'handoff','paper_root':str(self.root),'paper':{'path':'paper.pdf','sha256':self.sha(p)},'current_paper':None,'sources':self.sources,'scope_comment_ids':['C1'],'comments':[{'id':'C1','source_id':'comments','source_item_id':None,'location':'comment 1','text':'Please clarify the setup.'}],'units':[self.unit('U1',['C1'])],'actions':[self.action('A1',['U1'])],'replies':[self.reply('U1')],'impact_checks':[],'conflicts':[],'self_checks':{'plan':check(),'handoff':check(),'final':check()},'policy':{'status':'not_applicable','source_refs':[],'scope':'internal draft','reason':'Internal response, no venue-specific format','planned_actions_allowed':False}}

    def put(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value);return p

    def sha(self,p):return hashlib.sha256(p.read_bytes()).hexdigest()

    def source(self,sid,kind,path,content):
        p=self.put(path,content);s={'id':sid,'kind':kind,'path':path,'sha256':self.sha(p)};self.sources.append(s);return s

    def ev(self,sid='evidence'):
        return {'source_id':sid,'location':'actual record location','observation':'检查范围内的实际依据；测试不认证语义'}

    def unit(self,uid,cids,action_ids=None):
        return {'id':uid,'comment_ids':cids,'concern':'核清具体设置','assessment':{'finding_status':'confirmed','reasoning':'需要补清定义','evidence_refs':[self.ev()],'unknowns':[],'prior_belief':'原设置可能不明确','observation':'查看当前材料','updated_belief':'有局部表达修正需求','core_unresolved':False},'disposition':'edit','rationale':'不改变研究主张的澄清','action_ids':action_ids if action_ids is not None else ['A1'],'coverage_status':'addressed','scope_change':False}

    def action(self,aid,uids):
        return {'id':aid,'unit_ids':uids,'owner':'writing-paper','kind':'text_edit','description':'在设置段说明定义及条件','target':'Method/setup paragraph','acceptance_criterion':'定义和真实设置一致','depends_on':[],'approval':{'status':'approved','basis':'已有明确授权的局部澄清','source_refs':[]},'status':'approved','outputs':[],'verification':{'status':'pending','source_refs':[],'basis':'尚未执行，不称核查通过'},'reason':''}

    def reply(self,uid,kind='position',aids=None):
        phrase={'position':'The concern is about the definition of the setting.','planned_action':'We plan to clarify the definition under the approved scope.','completed_action':'We have revised the definition in the checked manuscript.','evidence_statement':'The recorded count is two under the stated setup.','limitation':'The available evidence does not answer this question.'}[kind]
        return {'unit_id':uid,'status':'draft','statements':[{'id':'S-'+uid,'kind':kind,'text':phrase,'evidence_refs':[],'action_ids':aids or []}],'check':check()}

    def final(self):
        self.s['stage']='final'
        for r in self.s['replies']:r['status']='checked'

    def verify(self,aid='A1'):
        out=self.source('new-paper','manuscript','updated.pdf','Synthetic actual updated manuscript fixture')
        self.source('verify','verification','verification.json',json.dumps({'checked_action':aid,'scope':'text and conditions'}))
        a=next(a for a in self.s['actions'] if a['id']==aid);a.update(status='verified',outputs=['new-paper'],verification={'status':'passed','source_refs':['verify'],'basis':'实际产物按本次验收核对'})
        self.s['current_paper']={'path':out['path'],'sha256':out['sha256']}

    def execute(self,code=0,output='handoff',before=None):
        p=self.put('response-state.json',json.dumps(self.s,ensure_ascii=False))
        if before:before(p)
        result=subprocess.run([sys.executable,str(SCRIPT),'--record',str(p),'--output-dir',str(self.root/output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,code,result.stdout+'\n'+result.stderr)
        if code not in (0,3):return result
        return json.loads((self.root/output/'revision-brief.json').read_text()),json.loads((self.root/output/'validation.json').read_text())

    def test_handoff_contains_only_ready_actions(self):
        brief,report=self.execute();self.assertEqual([x['id'] for x in brief['items']],['A1']);self.assertEqual(report['ready_action_ids'],['A1'])

    def test_plan_is_not_execution_authorization(self):
        self.s['stage']='plan';brief,report=self.execute(3);self.assertEqual(brief['items'],[]);self.assertEqual(report['completion'],'partial')

    def test_unapproved_action_not_dispatched(self):
        self.s['actions'][0]['status']='proposed';self.s['actions'][0]['approval']['status']='pending'
        brief,_=self.execute();self.assertEqual(brief['items'],[])

    def test_approved_state_without_approval_is_error(self):
        self.s['actions'][0]['approval']['status']='pending';self.execute(1)

    def test_split_comment_and_shared_action_preserve_coverage(self):
        self.s['units'].append(self.unit('U2',['C1']));self.s['actions'][0]['unit_ids'].append('U2');self.s['replies'].append(self.reply('U2'))
        brief,_=self.execute();self.assertEqual(brief['items'][0]['unit_ids'],['U1','U2'])

    def test_omitted_selected_comment_rejected(self):
        self.s['comments'].append({'id':'C2','source_id':'comments','source_item_id':None,'location':'second concern','text':'What about uncertainty?'})
        self.s['scope_comment_ids'].append('C2');self.execute(1)

    def test_out_of_scope_comments_remain_visible(self):
        self.s['comments'].append({'id':'C2','source_id':'comments','source_item_id':None,'location':'second concern','text':'What about uncertainty?'})
        _,r=self.execute();self.assertEqual(r['not_checked_comment_ids'],['C2'])

    def test_missing_action_source_rejected(self):
        self.s['actions'][0]['outputs']=['missing'];self.execute(1)

    def test_completed_without_verification_not_past_fact(self):
        a=self.s['actions'][0];a.update(status='completed',outputs=['evidence'])
        self.s['replies'][0]=self.reply('U1','completed_action',['A1']);self.execute(1)

    def test_verified_action_requires_actual_verification_record(self):
        self.s['actions'][0].update(status='verified',outputs=['evidence']);self.execute(1)

    def test_regular_evidence_not_substitute_for_verification(self):
        self.s['actions'][0].update(status='verified',outputs=['evidence'],verification={'status':'passed','source_refs':['evidence'],'basis':'wrong source kind'});self.execute(1)

    def test_real_verified_change_can_be_claimed(self):
        self.verify();self.s['replies'][0]=self.reply('U1','completed_action',['A1']);self.final()
        _,r=self.execute();self.assertEqual(r['completion'],'records_complete')

    def test_old_paper_cannot_validate_new_change_location(self):
        self.verify();self.s['current_paper']=None;self.s['replies'][0]=self.reply('U1','completed_action',['A1']);self.final();self.execute(1)

    def test_changed_input_snapshot_rejected(self):
        self.put('data.json','changed');self.execute(1)

    def test_missing_reply_in_final_is_partial(self):
        self.s['replies']=[];self.final();self.execute(3)

    def test_unchecked_reply_in_final_is_partial(self):
        self.final();self.s['replies'][0]['status']='draft';self.execute(3)

    def test_evidence_statement_requires_actual_source(self):
        self.s['replies'][0]=self.reply('U1','evidence_statement');self.execute(1)

    def test_evidence_statement_with_source_is_allowed(self):
        self.s['replies'][0]=self.reply('U1','evidence_statement');self.s['replies'][0]['statements'][0]['evidence_refs']=[self.ev()];self.execute()

    def test_future_commitment_needs_approval(self):
        self.s['actions'][0].update(status='proposed');self.s['actions'][0]['approval']['status']='pending';self.s['replies'][0]=self.reply('U1','planned_action',['A1']);self.execute(1)

    def test_future_commitment_needs_applicable_rule_in_final(self):
        self.s['replies'][0]=self.reply('U1','planned_action',['A1']);self.final();self.execute(1)

    def test_explicit_permitted_future_plan_not_faked_as_completed(self):
        self.s['policy']['planned_actions_allowed']=True;self.s['replies'][0]=self.reply('U1','planned_action',['A1']);self.final()
        self.execute();letter=(self.root/'handoff/rebuttal-letter.md').read_text();self.assertIn('We plan to clarify',letter);self.assertNotIn('执行=',letter);self.assertNotIn('行动状态',letter)

    def test_scientific_unresolved_can_be_honestly_replied(self):
        u=self.s['units'][0];u['assessment']['core_unresolved']=True;u['disposition']='defer';u['coverage_status']='unresolved';u['action_ids']=[];self.s['actions']=[]
        self.s['replies'][0]=self.reply('U1','limitation');self.s['replies'][0]['statements'][0]['text']='We cannot answer this under the current conditions.';self.final();self.execute()

    def test_core_unknown_not_closed_as_story_edit(self):
        self.s['units'][0]['assessment']['core_unresolved']=True;self.execute(1)

    def test_core_evidence_not_routed_as_ordinary_supplement(self):
        u=self.s['units'][0];u['assessment']['core_unresolved']=True;u['disposition']='defer';self.s['actions'][0]['kind']='supplementary_evidence';self.execute(1)

    def test_research_task_does_not_enter_writing_brief(self):
        u=self.s['units'][0];u['assessment']['core_unresolved']=True;u['disposition']='research';self.s['actions'][0].update(owner='code-idea-iterate',kind='research_decision')
        brief,_=self.execute();self.assertEqual(brief['items'],[])

    def test_scope_change_requires_value_and_impact_check(self):
        self.s['units'][0]['scope_change']=True;self.execute(1)

    def impact(self,status='updated'):
        return {'id':'X1','trigger_unit_ids':['U1'],'affected':[{'kind':'reply','id':'U1','reason':'范围变化影响回复','status':status,'evidence_refs':[self.ev()]}],'check':check()}

    def test_scope_change_reassessment_and_impact_record(self):
        self.s['units'][0].update(scope_change=True,value_reassessment='缩小后仍有明确可报告新增，其他未知保留');self.s['impact_checks']=[self.impact()];self.execute()

    def test_pending_impact_blocks_related_action(self):
        self.s['impact_checks']=[self.impact('pending')];brief,_=self.execute(3);self.assertEqual(brief['items'],[])

    def test_pending_impact_does_not_block_unrelated_ready_batch(self):
        self.s['comments'].append({'id':'C2','source_id':'comments','source_item_id':None,'location':'second','text':'Second independent edit.'});self.s['scope_comment_ids'].append('C2');self.s['units'].append(self.unit('U2',['C2'],['A2']));self.s['actions'].append(self.action('A2',['U2']));self.s['impact_checks']=[self.impact('pending')]
        brief,_=self.execute(3);self.assertEqual([x['id'] for x in brief['items']],['A2'])

    def conflict(self):
        return {'id':'K1','unit_ids':['U1'],'action_ids':['A1'],'description':'两种处理存在冲突','status':'unresolved','decision':'','evidence_refs':[]}

    def test_unresolved_conflict_blocks_action_handoff(self):
        self.s['conflicts']=[self.conflict()];brief,_=self.execute(3);self.assertEqual(brief['items'],[])

    def test_claimed_resolved_conflict_needs_decision_and_basis(self):
        c=self.conflict();c['status']='resolved';self.s['conflicts']=[c];self.execute(1)

    def test_dependency_cycle_rejected(self):
        self.s['actions'].append(self.action('A2',['U1']));self.s['units'][0]['action_ids'].append('A2');self.s['actions'][0]['depends_on']=['A2'];self.s['actions'][1]['depends_on']=['A1'];self.execute(1)

    def test_in_progress_task_requires_verified_dependencies(self):
        self.s['actions'].append(self.action('A2',['U1']));self.s['units'][0]['action_ids'].append('A2');self.s['actions'][1].update(status='in_progress',depends_on=['A1']);self.execute(1)

    def test_unknown_rule_leaves_final_draft(self):
        self.s['policy']['status']='unknown';self.final();self.execute(3)

    def test_handoff_self_check_blocks_dispatch_when_revision_needed(self):
        self.s['self_checks']['handoff']=check('needs_revision');brief,_=self.execute(3);self.assertEqual(brief['items'],[])

    def test_no_guessing_paper_root_from_pdf_folder(self):
        self.s['paper_root']=None;self.execute(1)

    def review_source(self):
        data={'schema_version':2,'run_id':'review1','paper':copy.deepcopy(self.s['paper']),'completion':'partial','problems':[{'id':'P1','description':'Please clarify the setup.'},{'id':'P2','description':'Another concern.'}]}
        self.source('review','review','review.json',json.dumps(data));self.s['comments']=[{'id':'C1','source_id':'review','source_item_id':'P1','location':'P1','text':'Please clarify the setup.'},{'id':'C2','source_id':'review','source_item_id':'P2','location':'P2','text':'Another concern.'}]
        return data

    def test_review_subset_scope_preserves_all_original_problems(self):
        self.review_source();_,r=self.execute();self.assertEqual(r['not_checked_comment_ids'],['C2'])

    def test_incomplete_import_of_review_rejected(self):
        self.review_source();self.s['comments'].pop();self.execute(1)

    def test_review_wrong_manuscript_version_rejected(self):
        data=self.review_source();data['paper']['sha256']='0'*64;p=self.put('review.json',json.dumps(data));next(x for x in self.sources if x['id']=='review')['sha256']=self.sha(p);self.execute(1)

    def test_original_comment_not_silently_paraphrased(self):
        self.review_source();self.s['comments'][0]['text']='A different claim';self.execute(1)

    def test_no_overwriting_existing_handoff(self):
        self.execute();old=(self.root/'handoff/rebuttal-letter.md').read_bytes();self.execute(1);self.assertEqual(old,(self.root/'handoff/rebuttal-letter.md').read_bytes())

    def test_bad_json_does_not_create_output(self):
        self.execute(1,before=lambda p:p.write_text('{bad'));self.assertFalse((self.root/'handoff').exists())


    def test_export_freezes_approved_record_and_resolves_paths(self):
        brief,_=self.execute();ref=brief['response_ref'];frozen=Path(ref['path'])
        self.assertTrue(frozen.is_file());self.assertEqual(self.sha(frozen),ref['sha256'])
        data=json.loads(frozen.read_text());self.assertTrue(Path(data['sources'][0]['path']).is_absolute())
        self.put('response-state.json','current state changed later')
        self.assertEqual(self.sha(frozen),ref['sha256'])

    def test_two_units_cannot_accidentally_duplicate_statement_id(self):
        self.s['units'].append(self.unit('U2',['C1']));self.s['actions'][0]['unit_ids'].append('U2');self.s['replies'].append(copy.deepcopy(self.s['replies'][0]));self.s['replies'][1]['unit_id']='U2'
        self.execute(1)


if __name__=='__main__':unittest.main()
