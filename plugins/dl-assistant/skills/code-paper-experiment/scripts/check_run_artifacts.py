"""共用execution的记录检查，增加批次、重复身份、来源与有限汇总复核。

0声明记录核对完成（可以含失败记录）；1错误；2用法；3来源/记录/复算未完成。
不启动实验，不认证科学判断、授权真实性或数据有效性。
"""
import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ENGINE_PATH=Path(__file__).resolve().parents[2]/'code-idea-execution/scripts/check_exp_artifacts.py'
SPEC=importlib.util.spec_from_file_location('shared_experiment_artifacts',ENGINE_PATH)
ENGINE=importlib.util.module_from_spec(SPEC)
if ENGINE_PATH.is_file():SPEC.loader.exec_module(ENGINE)


def require(test,message):
    if not test:raise ValueError(message)


def text(v,name):require(isinstance(v,str) and bool(v.strip()),name+'须为非空文字')


def seq(v,name):require(isinstance(v,list),name+'须为数组');return v


def obj(v,name):require(isinstance(v,dict),name+'须为对象');return v


def indexed(items,key,name):
    out={}
    for item in seq(items,name):
        obj(item,name);text(item.get(key),name+'.'+key);require(item[key] not in out,name+'重复ID');out[item[key]]=item
    return out


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path,object_required=True):
    checker=ENGINE.Checks();value=checker.load(path,str(path),object_required=object_required)
    require(not any(x[1]=='FAIL' for x in checker.rows),'; '.join(x[2] for x in checker.rows));return value


def local(root,value):
    text(value,'相对路径');require(not Path(value).is_absolute(),'需目录内相对路径')
    p=(root/value).resolve();require(p.is_relative_to(root.resolve()),'路径超出声明目录');return p


class Audit:
    def __init__(self):self.rows=[];self.partial=False;self.manifest={};self.states={}
    def note(self,name,status,message):
        self.rows.append((name,status,message));self.partial|=status=='UNCHECKED'
    def check(self,value,name):
        obj(value,name);require(value.get('status') in {'clear','limited','needs_revision'},name+'状态无效')
        text(value.get('basis'),name+'.basis');text(value.get('effect'),name+'.effect');seq(value.get('unknowns'),name+'.unknowns')
        if value['status']=='needs_revision':self.note(name,'UNCHECKED','自查记录尚待修正：'+value['effect'])
    def ref(self,root,record,name,exp_id=None):
        obj(record,name);p=local(root,record.get('path'));text(record.get('sha256'),name+'.sha256')
        require(len(record['sha256'])==64 and all(c in '0123456789abcdef' for c in record['sha256']),name+'sha256格式无效')
        if not p.is_file() and exp_id is not None:
            m=self.manifest.get((exp_id,record['path']))
            if m:
                require(m['sha256']==record['sha256'],name+'与包清单校验值不一致');p=m['_resolved']
                if m['availability']!='accessible':self.note(name,'UNCHECKED',m['missing_effect']);return None
        if not p.is_file():
            if exp_id is not None and (exp_id,record['path']) in self.manifest:
                self.note(name,'UNCHECKED','外部引用不可取得，不能当已取得数据');return None
            raise ValueError(name+'文件不存在: '+str(p))
        require(sha(p)==record['sha256'],name+'校验值/版本不符');return p
    def spec(self,path):
        spec=load(path);require(spec.get('schema_version')==2,'run-spec须schema_version=2，旧记录先明确核对')
        text(spec.get('batch_id'),'batch_id');plan_path=self.ref(path.parent,spec.get('plan_ref'),'plan')
        plan=load(plan_path);require(plan.get('schema_version')==2,'plan须schema_version=2')
        approval=obj(plan.get('approval'),'plan.approval');require(approval.get('status')=='approved' and approval.get('record_ref'),'计划缺实际批准记录引用')
        # record_ref是明确记录位置而非自动授权认证；可用文件快照形式核存在与版本。
        if isinstance(approval['record_ref'],dict):self.ref(path.parent,approval['record_ref'],'plan approval')
        else:text(approval['record_ref'],'plan approval ref')
        planned=indexed(plan.get('experiments'),'exp_id','plan experiments');entries=indexed(spec.get('experiments'),'exp_id','run-spec experiments')
        require(planned and set(planned)==set(entries),'计划与run-spec实验集合不一致（含遗漏/额外实验）')
        active=set();done=set()
        def visit(eid):
            require(eid not in active,'实验依赖有循环')
            if eid in done:return
            active.add(eid)
            e=entries[eid];p=planned[eid]
            require(eid.startswith('exp-') and Path(eid).name==eid and '/' not in eid and '\\' not in eid,'实验ID不能是路径')
            require(e.get('type') in ENGINE.TYPES,'实际操作type无效；论文角色不能代替操作')
            require(e.get('type')==p.get('execution_type',p.get('type')),'计划与实际操作类型不一致')
            for field in ('design_mode','purpose'):
                require(e.get(field)==p.get(field),'plan/run-spec的'+field+'不一致')
            require(e['design_mode'] in {'exploration','confirmation'},'设计类型无效');text(e['purpose'],'purpose')
            mode_field='analysis_plan' if e['design_mode']=='exploration' else 'interpretation_plan'
            require(bool(p.get(mode_field)),'计划缺'+mode_field)
            require(e.get('approval',{}).get('status')=='approved','执行项未声明实际批准');text(e['approval'].get('basis'),'execution approval basis')
            reps=indexed(e.get('expected_replicates'),'id','expected_replicates');require(reps,'至少明确一次实际操作身份')
            approved_reps=indexed(p.get('expected_replicates'),'id','plan expected_replicates')
            require(set(reps)==set(approved_reps),'run-spec与批准计划的重复身份不一致')
            for rid,rep in approved_reps.items():
                require(rep.get('seed') is None or type(rep['seed']) is int,'计划seed须为整数或null')
                require(reps[rid].get('seed')==rep.get('seed'),'run-spec与批准计划的seed身份不符')
            for rep in reps.values():require(rep.get('seed') is None or type(rep['seed']) is int,'seed须为整数或null')
            sources=seq(e.get('source_snapshots'),'source_snapshots')
            for source in sources:obj(source,'source snapshot');text(source.get('role'),'source role')
            obj(e.get('condition_review_ref'),'condition_review_ref');obj(e.get('design_record'),'design_record')
            deps=seq(e.get('depends_on'),'depends_on');require(len(deps)==len(set(deps)) and all(x in entries for x in deps),'未知/重复实验依赖')
            require(deps==p.get('depends_on',[]),'plan/run-spec依赖不一致')
            for dep in deps:visit(dep)
            active.remove(eid);done.add(eid)
        for eid in entries:visit(eid)
        return spec,entries
    def experiment(self,root,spec,e,portable=False):
        eid=e['exp_id'];require(root.name==eid and eid.startswith('exp-'),'实验目录与exp_id不符')
        meta=load(root/'meta.json');require(meta.get('batch_id')==spec['batch_id'],'meta批次不符')
        base=ENGINE.Checks();ledger={k:meta.get(k) for k in ('status','data_validity','inference_status')}
        base.experiment(root,ledger,check_artifacts=not portable,portable=portable)
        self.rows.extend(base.rows);require(not any(row[1]=='FAIL' for row in base.rows),'共享实验记录检查失败')
        self.partial |= any(row[1]=='UNCHECKED' for row in base.rows)
        require(isinstance(meta.get('design_record'),dict) and all(meta['design_record'].get(k)==e['design_record'].get(k) for k in ('path','sha256')),'设计副本与批准执行版本不一致');self.ref(root,meta['design_record'],eid+' design snapshot',eid)
        require(meta.get('type')==e['type'] and meta.get('design_mode')==e['design_mode'] and meta.get('purpose')==e['purpose'],'设计类型/目的与执行记录不符')
        self.states[eid]=meta['status']
        if meta['status'] in {'not_started','in_progress'}:self.note(eid,'UNCHECKED','本项尚未完成，保存真实进度')
        require(meta.get('source_snapshots')==e['source_snapshots'],'实际来源快照与本次run-spec不一致；变更须保留批准版本')
        for source in meta['source_snapshots']:self.ref(root,source,eid+' source',eid)
        require(meta.get('condition_review_ref')==e['condition_review_ref'],'研究条件引用版本不符');self.ref(root,meta['condition_review_ref'],eid+' conditions',eid)
        checks=obj(meta.get('paper_self_checks'),'paper_self_checks');self.check(checks.get('acceptance'),eid+' acceptance')
        if meta['status'] in {'in_progress','completed','failed'}:self.check(checks.get('pre_run'),eid+' pre_run')
        self.check(checks.get('handoff'),eid+' handoff')
        deviations={}
        for deviation in seq(meta.get('deviations'),'deviations'):
            obj(deviation,'deviation');text(deviation.get('id'),'deviation.id');require(deviation['id'] not in deviations,'deviation ID重复');deviations[deviation['id']]=deviation
            if deviation.get('affects_conditions'):self.check(deviation.get('condition_check'),eid+' condition change')
        attempts=indexed(meta.get('attempts'),'attempt_id','attempts');reps=indexed(meta.get('replicates'),'id','replicates');expected=indexed(e['expected_replicates'],'id','expected_replicates')
        require(set(reps)==set(expected),'实际重复身份不符，不能仅按seed数量判断')
        prior=set()
        for aid,a in attempts.items():
            require(a.get('replicate_id') in reps,'attempt引用未知重复');require(a.get('status') in ENGINE.STATUSES,'attempt状态无效');text(a.get('command'),'实际操作/命令')
            seq(a.get('source_refs'),'attempt.source_refs')
            for source in a['source_refs']:self.ref(root,source,aid+' actual source',eid)
            if a['source_refs']!=meta['source_snapshots']:
                deviation=deviations.get(a.get('deviation_ref'));require(deviation is not None,'尝试来源变化缺明确偏差记录')
                require(deviation.get('approval',{}).get('status')=='approved' and deviation.get('approval',{}).get('basis'),'尝试调整缺既有授权/批准依据')
                require(deviation.get('changes_scientific_design') is False,'科学设计变化需新版批准计划/批次，不能改写旧尝试')
            if a['status']=='completed':
                if meta.get('type')=='theory' and meta.get('execution_basis')=='manual':
                    require(a.get('exit_code') is None,'人工核查不补造进程退出码');self.ref(root,a.get('manual_record_ref'),aid+' manual observation',eid)
                else:require(type(a.get('exit_code')) is int and a['exit_code']==0,'完成代码尝试需真实成功退出')
            if a.get('resume_from'):
                require(a['resume_from'] in prior and attempts[a['resume_from']]['replicate_id']==a['replicate_id'],'恢复源不是本重复更早的尝试')
            prior.add(aid)
        successes={};selected=set()
        for rid,r in reps.items():
            require(r.get('seed')==expected[rid].get('seed') and (r.get('seed') is None or type(r['seed']) is int),'seed身份不符')
            require(r.get('status') in ENGINE.STATUSES,'重复状态无效');text(r.get('selection_reason'),'重复选择/未完成原因')
            if r['status']=='completed':
                aid=r.get('selected_attempt_id');require(aid in attempts and attempts[aid]['replicate_id']==rid and attempts[aid]['status']=='completed','选中尝试不属于该重复或未完成')
                require(aid not in selected,'同一次尝试不能算多个独立重复');selected.add(aid);successes[rid]=r
                if r.get('metrics_ref') is not None:self.ref(root,r['metrics_ref'],rid+' metrics',eid)
            else:require(r.get('selected_attempt_id') is None,'未完成重复不能选成功尝试')
        if meta['status']=='completed':require(len(successes)==len(expected),'未完成所声明操作不能标整体completed')
        if portable:
            for artifact in meta['required_artifacts']:
                if meta['status'] in artifact['required_for']:
                    require((eid,artifact['path']) in self.manifest,'包清单遗漏当前状态必需产物: '+artifact['path'])
                    require(self.manifest[(eid,artifact['path'])]['format']==artifact['format'],'产物格式声明与包清单不一致')
            if meta.get('tracking') is not None:
                for attempt in meta['attempts']:
                    refs=[attempt.get('configuration_ref',meta.get('configuration_ref'))]
                    if attempt.get('code_dirty',meta.get('code_dirty')):
                        path=attempt.get('code_diff_path',meta.get('code_diff_path'))
                        refs.append({'path':path,'sha256':attempt['wandb']['identity']['code_diff_sha256']})
                    if attempt['wandb']['sync_status']=='synced':refs.append(attempt['wandb']['snapshot_ref'])
                    for ref in refs:
                        manifest=self.manifest.get((eid,ref['path']))
                        require(manifest is not None and manifest['sha256']==ref['sha256'],'包清单遗漏或错配W&B来源文件')
                        require(manifest['disposition']=='copy' and manifest['availability']=='accessible'
                                and manifest['_resolved']==local(root,ref['path']),'W&B小型来源文件须随包复制并保持相对路径')
        result_path=root/'results.json'
        if not result_path.is_file():
            require(meta['status']!='completed','完成项缺实际结果记录');return meta,None
        result=load(result_path)
        require(result.get('schema_version')==2 and result.get('batch_id')==spec['batch_id'] and result.get('exp_id')==eid,'结果身份/批次错误')
        for k in ('status','data_validity','inference_status'):require(result.get(k)==meta.get(k),'结果与meta的'+k+'不一致')
        ids=seq(result.get('replicate_ids'),'result.replicate_ids');require(len(ids)==len(set(ids)) and set(ids)==set(successes),'结果重复ID/选择集合错误')
        require(type(result.get('n_replicates')) is int and result['n_replicates']==len(successes),'n_replicates与实际身份不符')
        if 'n_seeds' in result:require(type(result['n_seeds']) is int and result['n_seeds']==sum(r.get('seed') is not None for r in successes.values()),'n_seeds与实际成功seed不符')
        obj(result.get('metrics'),'metrics');seq(result.get('observations'),'observations');seq(result.get('limitations'),'limitations')
        self.summaries(root,result,successes,eid)
        return meta,result
    def pointer(self,data,path):
        require(isinstance(path,str) and (path=='' or path.startswith('/')),'JSON Pointer无效')
        for part in path.split('/')[1:] if path else []:
            part=part.replace('~1','/').replace('~0','~')
            if isinstance(data,list):require(part.isdecimal() and (part=='0' or not part.startswith('0')),'JSON Pointer数组下标无效');data=data[int(part)]
            else:data=data[part]
        require(type(data) in (int,float),'汇总字段须为有限数值，不把bool当数字')
        value=Decimal(str(data));require(value.is_finite(),'汇总字段非有限数值');return value
    def summaries(self,root,result,reps,eid):
        checks=indexed(result.get('summary_checks'),'id','summary_checks');covered=set()
        for c in checks.values():
            pointer=c.get('reported');require(isinstance(pointer,str) and pointer.startswith('/metrics/'),'reported须指本结果metrics数值')
            require(pointer not in covered,'同一汇总字段重复声明');covered.add(pointer);observed=self.pointer(result,pointer)
            inputs=seq(c.get('inputs'),'summary.inputs');ids=seq(c.get('replicate_ids'),'summary.replicate_ids')
            require(len(ids)==len(set(ids)) and all(x in reps for x in ids),'汇总引用未选中/重复/未知操作')
            if ids:
                require(len(ids)==len(inputs),'重复与来源数量不符')
                if c.get('operation') in {'mean','std','sum'}:require(len({x.get('json_pointer') for x in inputs})==1,'同一重复统计不能混用不同源字段')
            values=[];missing=False
            for i,source in enumerate(inputs):
                if ids:
                    metric_ref=reps[ids[i]].get('metrics_ref');require(metric_ref and all(source.get(k)==metric_ref.get(k) for k in ('path','sha256')),'汇总来源不是该重复实际选中读数')
                require(local(root,source.get('path'))!=(root/'results.json').resolve(),'不能用结果自身认证汇总')
                p=self.ref(root,source,eid+' summary input',eid)
                if p is None:missing=True;continue
                values.append(self.pointer(load(p,False),source.get('json_pointer')))
            if missing:continue
            operation=c.get('operation');decimals=c.get('decimals');require(type(decimals) is int and decimals>=0,'需明确非负展示小数位')
            require(values,'汇总缺实际输入；零计数等应指实际分析输出')
            with localcontext() as ctx:
                ctx.prec=max(50,decimals+30,max((len(v.as_tuple().digits)+abs(v.as_tuple().exponent)+10 for v in values),default=0))
                if operation=='mean':computed=sum(values)/len(values)
                elif operation=='sum':computed=sum(values)
                elif operation=='count':computed=Decimal(len(values))
                elif operation=='direct':require(len(values)==1,'direct须指一个实际分析输出');computed=values[0]
                elif operation=='std':
                    ddof=c.get('ddof');require(type(ddof) is int and ddof>=0 and len(values)>ddof,'std的ddof/重复数不合法，不伪填单样本std=0')
                    mean=sum(values)/len(values);computed=(sum((v-mean)**2 for v in values)/(len(values)-ddof)).sqrt()
                else:self.note(pointer,'UNCHECKED','未支持自动复算的运算，保留实际分析及人工核查');continue
                require(Decimal(computed).quantize(Decimal(1).scaleb(-decimals),rounding=ROUND_HALF_UP)==observed,'汇总值与声明输入/计算不一致: '+pointer)
            self.note(pointer,'PASS','声明的有限运算与读数一致；不认证统计设计/来源语义')
        def leaves(value,path):
            if type(value) in (int,float):yield path
            elif isinstance(value,dict):
                for k,v in value.items():yield from leaves(v,path+'/'+str(k).replace('~','~0').replace('/','~1'))
            elif isinstance(value,list):
                for i,v in enumerate(value):yield from leaves(v,path+'/'+str(i))
        for path in leaves(result['metrics'],'/metrics'):
            if path not in covered:self.note(path,'UNCHECKED','此数值尚未关联自动复算/分析来源，不能当已核')
    def package(self,root):
        actual=load(root/'experiments-actual.json');results=load(root/'results.json');package=load(root/'pkg-meta.json')
        files=(actual,results,package)
        for data in files:require(data.get('schema_version')==2,'包格式须schema_version=2')
        for key in ('batch_id','plan_ref','run_spec_ref'):require(all(d.get(key)==actual.get(key) for d in files),'包各索引的'+key+'不一致')
        spec_path=self.ref(root,actual.get('run_spec_ref'),'package run-spec');spec,entries=self.spec(spec_path)
        require(spec['batch_id']==actual.get('batch_id') and spec['plan_ref']==actual.get('plan_ref'),'包与run-spec/plan版本不符')
        require((root/actual['plan_ref']['path']).resolve()==(spec_path.parent/spec['plan_ref']['path']).resolve(),'plan相对路径解析到不同文件')
        rows=indexed(actual.get('experiments_actual'),'exp_id','actual');summaries=indexed(results.get('experiments'),'exp_id','package results');meta_rows=indexed(package.get('experiments'),'exp_id','pkg-meta experiments')
        require(set(rows)==set(entries)==set(meta_rows),'包与全部计划项集合不一致')
        seq(actual.get('deviations'),'actual.deviations');seq(package.get('resources'),'resources')
        for m in seq(package.get('artifact_manifest'),'artifact_manifest'):
            obj(m,'artifact manifest');require(m.get('exp_id') in rows,'清单未知实验');local(root,m.get('artifact_path'))
            key=(m['exp_id'],m['artifact_path']);require(key not in self.manifest,'清单重复逻辑产物');text(m.get('purpose'),'artifact purpose')
            require(type(m.get('required_for_interpretation')) is bool,'需明确产物解释用途');require(m.get('disposition') in {'copy','reference'} and m.get('availability') in {'accessible','unavailable','not_checked'},'产物复制/可用状态无效')
            text(m.get('path'),'artifact path');text(m.get('sha256'),'artifact sha256');require(m.get('format') in {'file','text','json'},'artifact format无效')
            p=local(root,m['path']) if m['disposition']=='copy' else (root/m['path']).resolve()
            self.manifest[key]={**m,'_resolved':p}
            if m['availability']!='accessible' or not p.is_file():
                text(m.get('missing_effect'),'缺失/未知产物的影响');self.note(m['path'],'UNCHECKED',m['missing_effect']);continue
            require(sha(p)==m['sha256'],'包产物版本/校验值不符')
            require(p.stat().st_size>0,'清单产物为空，不能视为完整声明产物')
            if m['format']=='json':load(p,False)
        expected_results=set()
        for eid,row in rows.items():
            require(row.get('status') in ENGINE.STATUSES,'actual状态无效');require(meta_rows[eid].get('status')==row['status'],'pkg-meta与actual状态不符');self.states[eid]=row['status']
            if row.get('results_ref') is not None:expected_results.add(eid)
            if row.get('meta_ref') is None:
                require(row['status'] in {'not_started','blocked','cancelled'} and row.get('results_ref') is None,'实际运行/有结果却无meta')
                text(row.get('reason'),'未执行/阻塞/取消原因');self.note(eid,'UNCHECKED','尚无实际运行记录：'+row['reason']);continue
            exp=root/'experiments'/eid;require(exp.resolve().is_relative_to(root.resolve()),'实验目录越界')
            p=self.ref(root,row['meta_ref'],eid+' meta');require(p==(exp/'meta.json').resolve(),'meta_ref未对应本实验')
            meta,result=self.experiment(exp,spec,entries[eid],portable=True)
            for k in ('status','data_validity','inference_status'):require(row.get(k)==meta.get(k),'actual与实际meta的'+k+'不一致')
            if row.get('results_ref') is None:require(result is None,'实际结果未登记进包索引')
            else:
                rp=self.ref(root,row['results_ref'],eid+' results');require(rp==(exp/'results.json').resolve(),'results_ref未对应本实验');require(result is not None and eid in summaries and result==summaries[eid],'汇总副本与实际results不一致')
        require(set(summaries)==expected_results,'包结果有遗漏/多出记录，不能用单向集合认证')
        self.note('package','PASS','计划—实际—结果—包元数据逐项对应；失败/部分状态仍按实际显示')


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--expdir',type=Path);group.add_argument('--pkgdir',type=Path)
    parser.add_argument('--spec',type=Path);parser.add_argument('--exp-id');args=parser.parse_args()
    if bool(args.spec)!=bool(args.exp_id):parser.error('--spec与--exp-id同时提供')
    if args.pkgdir and args.spec:parser.error('包模式从包记录核版本，不另传spec')
    if not ENGINE_PATH.is_file():print('UNCHECKED: 缺少code-idea-execution共享检查器');return 3
    audit=Audit()
    try:
        if args.pkgdir:audit.package(args.pkgdir.resolve())
        elif not args.spec:audit.note('run-spec','UNCHECKED','未提供具体spec/exp-id，不能认证本次计划对应关系')
        else:
            spec,entries=audit.spec(args.spec.resolve());require(args.exp_id in entries,'指定实验不在本批计划');audit.experiment(args.expdir.resolve(),spec,entries[args.exp_id])
    except (OSError,ValueError,TypeError,KeyError,IndexError,InvalidOperation) as error:audit.note('validation','FAIL',str(error))
    print('| 检查项 | 状态 | 说明 |\n| --- | --- | --- |')
    for name,status,message in audit.rows:
        clean=lambda x:str(x).replace('|','／').replace('\n',' ')
        print('| '+' | '.join(map(clean,(name,status,message)))+' |')
    print('实际执行状态：'+json.dumps(audit.states,ensure_ascii=False))
    print('仅核声明记录、来源及有限复算；不认证预登记时间、授权、数据有效性或科学判断。')
    return 1 if any(r[1]=='FAIL' for r in audit.rows) else (3 if audit.partial else 0)


if __name__=='__main__':sys.exit(main())
