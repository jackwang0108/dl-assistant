"""CLI回归：身份、原始读数、部分状态、汇总、包集合、复制与引用。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('check_run_artifacts.py')


def check(status='clear'):
    return {'status':status,'basis':'实际设计与证据记录','unknowns':[],'effect':'按声明范围执行或交接'}


class ArtifactChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="cpe test's ");self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.exp=self.root/'experiments'/'exp-A';self.exp.mkdir(parents=True)
        self.put(self.exp/'design.json',json.dumps({'purpose':'测量已定义量','design_mode':'exploration'}));self.put(self.exp/'报告.md','Synthetic run report; does not certify science.\n');self.put(self.exp/'conditions.md','实际目标条件及未知\n');self.put(self.exp/'scripts'/'run.py','# synthetic analysis script snapshot\n')
        self.sources=[{**self.ref(self.exp/'scripts'/'run.py',self.exp),'role':'script'}];self.condition=self.ref(self.exp/'conditions.md',self.exp);self.design=self.ref(self.exp/'design.json',self.exp)
        self.entry={'exp_id':'exp-A','type':'analysis','design_mode':'exploration','purpose':'测量已定义量','expected_replicates':[{'id':'seed-0','seed':0},{'id':'seed-1','seed':1}],'source_snapshots':copy.deepcopy(self.sources),'condition_review_ref':copy.deepcopy(self.condition),'design_record':copy.deepcopy(self.design),'approval':{'status':'approved','basis':'已有批准范围'},'depends_on':[]}
        self.plan={'schema_version':2,'approval':{'status':'approved','record_ref':'recorded user approval'},'experiments':[{'exp_id':'exp-A','type':'analysis','execution_type':'analysis','design_mode':'exploration','purpose':'测量已定义量','analysis_plan':'核实际读数','expected_replicates':copy.deepcopy(self.entry['expected_replicates']),'depends_on':[]}]}
        self.write(self.root/'plan.json',self.plan)
        self.spec={'schema_version':2,'batch_id':'batch-fixture','plan_ref':self.ref(self.root/'plan.json',self.root),'experiments':[self.entry]}
        attempts=[];reps=[];artifacts=[];inputs=[]
        for i,value in enumerate((1.0,3.0)):
            p=self.exp/'runs'/f'seed-{i}'/'metrics.json';self.write(p,{'metrics':{'score':value}});mref=self.ref(p,self.exp)
            attempts.append({'attempt_id':f'a{i}','replicate_id':f'seed-{i}','status':'completed','exit_code':0,'command':'python scripts/run.py','resume_from':None,'source_refs':copy.deepcopy(self.sources)})
            reps.append({'id':f'seed-{i}','seed':i,'status':'completed','selected_attempt_id':f'a{i}','selection_reason':'按预先约定选实际完成尝试','metrics_ref':mref})
            artifacts.append({'path':mref['path'],'format':'json','required_for':['completed']});inputs.append({**mref,'json_pointer':'/metrics/score'})
        self.meta={'schema_version':2,'experiment_id':'exp-A','batch_id':'batch-fixture','type':'analysis','design_mode':'exploration','purpose':'测量已定义量','status':'completed','status_reason':None,'data_validity':'valid','inference_status':'insufficient_evidence','git_commit':'fixture-sha','code_dirty':False,'design_record':copy.deepcopy(self.design),'analysis_plan':'核实际读数','attempts':attempts,'replicates':reps,'required_artifacts':artifacts,'deviations':[],'source_snapshots':copy.deepcopy(self.sources),'condition_review_ref':copy.deepcopy(self.condition),'paper_self_checks':{'acceptance':check(),'pre_run':check(),'handoff':check()}}
        self.result={'schema_version':2,'batch_id':'batch-fixture','exp_id':'exp-A','status':'completed','data_validity':'valid','inference_status':'insufficient_evidence','replicate_ids':['seed-0','seed-1'],'n_replicates':2,'metrics':{'score':{'mean':2.0}},'summary_checks':[{'id':'mean-score','reported':'/metrics/score/mean','operation':'mean','inputs':inputs,'replicate_ids':['seed-0','seed-1'],'decimals':2,'ddof':None}],'observations':['实际合成测试读数'],'limitations':['测试不证明科研判断']}

    def put(self,path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);return path
    def write(self,path,data):return self.put(path,json.dumps(data,ensure_ascii=False))
    def ref(self,path,root):return {'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    def save(self):
        self.write(self.root/'plan.json',self.plan);self.spec['plan_ref']=self.ref(self.root/'plan.json',self.root)
        self.write(self.root/'run-spec.json',self.spec);self.write(self.exp/'meta.json',self.meta);self.write(self.exp/'results.json',self.result)
    def audit(self,code=0,package=False,before=None):
        self.save()
        if package:self.package()
        if before:before()
        cmd=[sys.executable,str(SCRIPT)]+(['--pkgdir',str(self.root)] if package else ['--expdir',str(self.exp),'--spec',str(self.root/'run-spec.json'),'--exp-id','exp-A'])
        p=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(p.returncode,code,p.stdout+'\n'+p.stderr);return p.stdout
    def package(self):
        common={'schema_version':2,'batch_id':'batch-fixture','plan_ref':self.spec['plan_ref'],'run_spec_ref':self.ref(self.root/'run-spec.json',self.root)}
        row={'exp_id':'exp-A','status':self.meta['status'],'data_validity':self.meta['data_validity'],'inference_status':self.meta['inference_status'],'reason':self.meta.get('status_reason'),'meta_ref':self.ref(self.exp/'meta.json',self.root),'results_ref':self.ref(self.exp/'results.json',self.root)}
        self.actual={**copy.deepcopy(common),'experiments_actual':[row],'deviations':[]};self.package_results={**copy.deepcopy(common),'experiments':[copy.deepcopy(self.result)]}
        manifest=[]
        for a in self.meta['required_artifacts']:
            p=self.exp/a['path'];manifest.append({'exp_id':'exp-A','artifact_path':a['path'],'path':str(p.relative_to(self.root)),'sha256':self.ref(p,self.exp)['sha256'],'format':a['format'],'disposition':'copy','availability':'accessible','purpose':'实际读数/必要产物','required_for_interpretation':True,'missing_effect':''})
        self.pkg={**copy.deepcopy(common),'experiments':[{'exp_id':'exp-A','status':self.meta['status']}],'artifact_manifest':manifest,'resources':[]};self.save_package()
    def save_package(self):
        self.write(self.root/'experiments-actual.json',self.actual);self.write(self.root/'results.json',self.package_results);self.write(self.root/'pkg-meta.json',self.pkg)

    def enable_tracking(self):
        config = self.write(self.exp/'config.json', {'setting':'synthetic-fixed'})
        self.meta['configuration_ref'] = self.ref(config, self.exp)
        self.meta['required_artifacts'].append({'path':'config.json','format':'json','required_for':['completed']})
        self.meta['tracking'] = {'provider':'wandb','base_url':'http://wandb.internal:8080',
            'entity':'team','project':'audio','scope_id':self.spec['batch_id'],
            'research_round':None,'hypothesis_ids':[]}
        for a in self.meta['attempts']:
            directory = self.exp/'runs'/a['attempt_id']/'wandb'
            directory.mkdir(parents=True)
            a['wandb'] = {'run_id':a['attempt_id'],'sync_status':'offline',
                'reason':'Service unreachable','local_dir':str(directory.relative_to(self.exp)),
                'recovery_ref':{'path':str(directory),'availability':'not_checked',
                                'reason':'The originating server retains this recovery directory'},
                'snapshot_ref':None,'identity':{'experiment_id':self.meta['experiment_id'],
                'replicate_id':a['replicate_id'],'attempt_id':a['attempt_id'],
                'resume_from_attempt':a.get('resume_from'),'design_sha256':self.design['sha256'],
                'git_commit':self.meta['git_commit'],'code_diff_sha256':None,
                'config_sha256':self.meta['configuration_ref']['sha256'],
                'data_refs':[],'model_refs':[],'protocol_ref':'synthetic-protocol:v1'}}

    def test_offline_package_can_be_copied_without_raw_wandb_directories(self):
        import shutil
        self.enable_tracking()
        self.audit(package=True)
        def remove_recovery():
            for a in self.meta['attempts']:
                shutil.rmtree(self.exp/a['wandb']['local_dir'])
        out = self.audit(3, package=True, before=remove_recovery)
        self.assertIn('UNCHECKED',out)
        self.assertNotIn('FAIL',out)
        self.assertEqual(self.meta['status'],'completed')

    def test_originating_run_still_requires_recovery_directory(self):
        import shutil
        self.enable_tracking()
        self.audit(1,before=lambda:shutil.rmtree(self.exp/self.meta['attempts'][0]['wandb']['local_dir']))

    def test_wandb_source_file_must_be_listed_in_package_manifest(self):
        self.enable_tracking()
        def omit_config():
            self.pkg['artifact_manifest'] = [m for m in self.pkg['artifact_manifest'] if m['artifact_path']!='config.json']
            self.save_package()
        self.audit(1,package=True,before=omit_config)

    def test_wandb_configuration_mutation_is_not_hidden_by_portable_mode(self):
        self.enable_tracking()
        self.audit(1,package=True,before=lambda:self.write(self.exp/'config.json',{'setting':'changed'}))

    def test_analysis_without_train_log_is_valid_record(self):
        self.assertIn('实际执行状态',self.audit());self.assertFalse((self.exp/'train.log').exists())
    def test_spaces_and_apostrophes_in_paths(self):self.audit()
    def test_exact_seed_identity_not_count(self):
        self.meta['replicates'][0]['id']='seed-2';self.audit(1)
    def test_summary_cannot_claim_999_repetitions(self):
        self.result['n_replicates']=999;self.audit(1)
    def test_legacy_seed_count_checked_if_present(self):
        self.result['n_seeds']=999;self.audit(1)
    def test_result_id_mismatch_rejected(self):
        self.result['exp_id']='exp-WRONG';self.audit(1)
    def test_meta_identity_mismatch_rejected(self):
        self.meta['experiment_id']='exp-WRONG';self.audit(1)
    def test_missing_config_or_script_snapshot_rejected(self):
        (self.exp/'scripts'/'run.py').unlink();self.audit(1)
    def test_changed_snapshot_rejected(self):
        self.put(self.exp/'scripts'/'run.py','changed');self.audit(1)
    def test_wrong_mean_rejected(self):
        self.result['metrics']['score']['mean']=20;self.audit(1)
    def test_missing_metric_check_is_unchecked_not_passed(self):
        self.result['summary_checks']=[];self.audit(3)
    def test_source_not_selected_replicate_rejected(self):
        self.result['summary_checks'][0]['inputs'][0]=copy.deepcopy(self.result['summary_checks'][0]['inputs'][1]);self.audit(1)
    def test_repeated_summary_replicate_rejected(self):
        self.result['summary_checks'][0]['replicate_ids']=['seed-0','seed-0'];self.audit(1)
    def test_result_cannot_verify_itself(self):
        self.result['summary_checks'][0].update(operation='direct',replicate_ids=[],inputs=[{'path':'results.json','sha256':'0'*64,'json_pointer':'/metrics/score/mean'}]);self.audit(1)
    def test_sample_std_explicit_ddof(self):
        c=copy.deepcopy(self.result['summary_checks'][0]);c.update(id='std-score',reported='/metrics/score/std',operation='std',ddof=1,decimals=3);self.result['metrics']['score']['std']=1.414;self.result['summary_checks'].append(c);self.audit()
    def test_invalid_std_ddof_rejected(self):
        self.result['summary_checks'][0].update(operation='std',ddof=2);self.audit(1)
    def test_unknown_analysis_operation_is_explicit_unchecked(self):
        self.result['summary_checks'][0]['operation']='bootstrap';self.audit(3)
    def test_actual_analysis_output_can_be_directly_traced(self):
        p=self.write(self.exp/'analysis'/'derived.json',{'value':2});self.result['summary_checks'][0].update(operation='direct',replicate_ids=[],inputs=[{**self.ref(p,self.exp),'json_pointer':'/value'}]);self.audit()
    def test_successful_attempt_cannot_have_failed_exit(self):
        self.meta['attempts'][0]['exit_code']=1;self.audit(1)
    def test_resume_source_must_exist_and_be_earlier(self):
        self.meta['attempts'][0]['resume_from']='a1';self.audit(1)
    def test_retry_not_a_new_independent_replicate(self):
        old=copy.deepcopy(self.meta['attempts'][0]);old.update(attempt_id='failed0',status='failed',exit_code=1)
        self.meta['attempts'].insert(0,old);self.meta['attempts'][1]['resume_from']='failed0';self.audit()
    def test_authorized_engineering_retry_keeps_old_sources(self):
        p=self.put(self.exp/'scripts'/'adjusted.py','# separate retry snapshot');new={**self.ref(p,self.exp),'role':'script'}
        self.meta['deviations']=[{'id':'D1','approval':{'status':'approved','basis':'已有工程调整范围'},'changes_scientific_design':False,'affects_conditions':True,'condition_check':check()}]
        self.meta['attempts'][1].update(source_refs=[new],deviation_ref='D1');self.audit()
    def test_source_change_without_deviation_rejected(self):
        self.meta['attempts'][0]['source_refs']=[];self.audit(1)
    def test_needs_revision_self_check_is_partial(self):
        self.meta['paper_self_checks']['handoff']=check('needs_revision');self.audit(3)
    def test_plan_pending_cannot_be_run_spec(self):
        self.plan['approval']['status']='pending';self.audit(1)
    def test_extra_unplanned_experiment_rejected(self):
        e=copy.deepcopy(self.entry);e['exp_id']='exp-B';self.spec['experiments'].append(e);self.audit(1)
    def test_no_numeric_seed_requirement_for_single_operation(self):
        self.entry['expected_replicates']=[{'id':'main','seed':None}];self.plan['experiments'][0]['expected_replicates']=copy.deepcopy(self.entry['expected_replicates']);self.meta['replicates']=self.meta['replicates'][:1];self.meta['replicates'][0].update(id='main',seed=None);self.meta['attempts']=self.meta['attempts'][:1];self.meta['attempts'][0]['replicate_id']='main';self.result.update(replicate_ids=['main'],n_replicates=1,metrics={},summary_checks=[]);self.audit()
    def test_manual_theory_does_not_need_fake_git_commit(self):
        self.entry.update(type='theory',expected_replicates=[{'id':'main','seed':None}]);self.plan['experiments'][0]['expected_replicates']=copy.deepcopy(self.entry['expected_replicates']);self.plan['experiments'][0].update(type='theory',execution_type='theory')
        p=self.put(self.exp/'analysis'/'proof.md','Actual synthetic written derivation record')
        self.meta.update(type='theory',execution_basis='manual',git_commit=None,attempts=[{'attempt_id':'manual1','replicate_id':'main','status':'completed','exit_code':None,'command':'人工核对推导并保存步骤','resume_from':None,'source_refs':copy.deepcopy(self.sources),'manual_record_ref':self.ref(p,self.exp)}],replicates=[{'id':'main','seed':None,'status':'completed','selected_attempt_id':'manual1','selection_reason':'实际完成核查','metrics_ref':None}],required_artifacts=[{'path':'analysis/proof.md','format':'text','required_for':['completed']}])
        self.result.update(replicate_ids=['main'],n_replicates=1,metrics={},summary_checks=[]);self.audit()
    def test_failed_attempts_kept_without_fake_success(self):
        self.meta.update(status='failed',status_reason='真实执行错误',data_validity='invalid',inference_status='invalid_data')
        for a in self.meta['attempts']:a.update(status='failed',exit_code=1)
        for r in self.meta['replicates']:r.update(status='failed',selected_attempt_id=None,metrics_ref=None,selection_reason='真实失败')
        self.result.update(status='failed',data_validity='invalid',inference_status='invalid_data',replicate_ids=[],n_replicates=0,metrics={},summary_checks=[])
        self.assertIn('failed',self.audit())
    def test_package_consistent(self):self.audit(package=True)
    def test_orphan_result_rejected(self):
        def change():
            r=copy.deepcopy(self.result);r['exp_id']='exp-ORPHAN';self.package_results['experiments'].append(r);self.save_package()
        self.audit(1,True,change)
    def test_different_plan_references_rejected(self):
        def change():self.package_results['plan_ref']={'path':'other-plan.json','sha256':'0'*64};self.save_package()
        self.audit(1,True,change)
    def test_duplicate_package_id_not_deduplicated(self):
        def change():self.actual['experiments_actual'].append(copy.deepcopy(self.actual['experiments_actual'][0]));self.save_package()
        self.audit(1,True,change)
    def test_aggregate_copy_mismatch_rejected(self):
        def change():self.package_results['experiments'][0]['metrics']['score']['mean']=99;self.save_package()
        self.audit(1,True,change)
    def test_package_status_mismatch_rejected(self):
        def change():self.pkg['experiments'][0]['status']='failed';self.save_package()
        self.audit(1,True,change)
    def test_unstarted_item_stays_visible_without_fake_run_directory(self):
        e=copy.deepcopy(self.entry);e['exp_id']='exp-B';self.spec['experiments'].append(e);p=copy.deepcopy(self.plan['experiments'][0]);p['exp_id']='exp-B';self.plan['experiments'].append(p)
        def change():
            self.actual['experiments_actual'].append({'exp_id':'exp-B','status':'not_started','data_validity':'unassessed','inference_status':'pending','reason':'尚未批准本阶段启动','meta_ref':None,'results_ref':None});self.pkg['experiments'].append({'exp_id':'exp-B','status':'not_started'});self.save_package()
        self.audit(3,True,change)
    def test_package_omits_required_artifact_manifest(self):
        def change():self.pkg['artifact_manifest']=[];self.save_package()
        self.audit(1,True,change)
    def test_external_unavailable_artifact_is_partial(self):
        def change():
            a=self.pkg['artifact_manifest'][0];a.update(disposition='reference',availability='unavailable',path='/not/available/metrics.json',missing_effect='此重复原始证据在接收端不可得')
            (self.exp/a['artifact_path']).unlink();self.save_package()
        self.audit(3,True,change)
    def test_accessible_external_reference_and_weights_not_forbidden(self):
        def change():
            p=self.root.parent/(self.root.name+'-fixture.weights');p.write_text('small synthetic external artifact');self.addCleanup(lambda:p.unlink(missing_ok=True))
            self.pkg['artifact_manifest'].append({'exp_id':'exp-A','artifact_path':'weights.pt','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'format':'file','disposition':'reference','availability':'accessible','purpose':'按需要提供的模型引用','required_for_interpretation':False,'missing_effect':''});self.save_package()
        self.audit(0,True,change)
    def test_path_escape_rejected(self):
        self.entry['condition_review_ref']={'path':'../outside','sha256':'0'*64};self.meta['condition_review_ref']=self.entry['condition_review_ref'];self.audit(1)
    def test_invalid_json_returns_error_not_zero(self):
        self.audit(1,before=lambda:self.put(self.exp/'results.json','{bad'))
    def test_missing_spec_is_not_success(self):
        self.save();p=subprocess.run([sys.executable,str(SCRIPT),'--expdir',str(self.exp)],capture_output=True,text=True);self.assertEqual(p.returncode,3,p.stdout+p.stderr)
    def test_mutually_exclusive_modes_and_missing_values(self):
        p=subprocess.run([sys.executable,str(SCRIPT),'--expdir',str(self.exp),'--pkgdir',str(self.root)],capture_output=True,text=True);self.assertEqual(p.returncode,2)


    def test_changed_design_snapshot_is_not_same_approved_design(self):
        self.put(self.exp/'design.json','{"purpose":"changed after approval"}')
        self.audit(1)

    def test_repetition_summary_cannot_mix_source_fields(self):
        p=self.exp/'runs'/'seed-1'/'metrics.json';self.write(p,{'metrics':{'score':3,'other':3}})
        ref=self.ref(p,self.exp);self.meta['replicates'][1]['metrics_ref']=ref
        self.result['summary_checks'][0]['inputs'][1]={**ref,'json_pointer':'/metrics/other'}
        self.audit(1)


    def test_run_spec_cannot_change_approved_seed_identity(self):
        self.entry['expected_replicates'][0]['seed']=99
        self.meta['replicates'][0]['seed']=99
        self.audit(1)


if __name__=='__main__':unittest.main()
