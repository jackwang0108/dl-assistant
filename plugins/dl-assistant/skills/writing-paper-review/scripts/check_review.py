"""核审查记录与实际产物，生成不覆盖历史的有限/完整交接。

0结构记录完整，1错误，2用法，3部分完成。不能认证科学判断或真实隔离。
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

FINDINGS={'confirmed','partially_supported','unsupported','unverified'}
SEVERITIES={'critical','major','minor','suggestion','undetermined'}
ROLES={'reviewer','counter_evidence','compliance','synthesis'}
KINDS={'text','figure','table','equation','cross_reference','absence','external','author_response'}
CHECKS={'clear','limited','needs_revision'}
RECHECKS={'resolved','partially_resolved','unresolved','not_checked'}


def require(test,message):
    if not test:raise ValueError(message)


def text(value,name):
    require(isinstance(value,str) and bool(value.strip()),name+'须为非空文字')


def seq(value,name):
    require(isinstance(value,list),name+'须为数组')
    return value


def obj(value,name):
    require(isinstance(value,dict),name+'须为对象')
    return value


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with path.open(encoding='utf-8') as f:return json.load(f)


def snapshot(record,root,name):
    obj(record,name);text(record.get('path'),name+'.path')
    path=(root/record['path']).resolve()
    require(path.is_file(),name+'文件不可得: '+str(path))
    require(re.fullmatch('[a-f0-9]{64}',str(record.get('sha256',''))) is not None,name+'缺真实sha256')
    require(digest(path)==record['sha256'],name+'版本/校验值不匹配')
    return path


def check_record(value,name):
    obj(value,name);require(value.get('status') in CHECKS,name+'状态无效')
    text(value.get('basis'),name+'.basis');text(value.get('effect'),name+'.effect')
    for x in seq(value.get('unknowns'),name+'.unknowns'):text(x,name+'.unknown')
    return value['status']=='needs_revision'


def evidence(items,materials,name):
    for item in seq(items,name):
        obj(item,name);require(item.get('kind') in KINDS,name+'证据类型无效')
        require(item.get('material_id') in materials,name+'引用未知材料ID')
        text(item.get('location'),name+'.location');text(item.get('observation'),name+'.observation')
        require(item.get('excerpt') is None or isinstance(item['excerpt'],str),name+'.excerpt须为文字或null')


def issue(item,materials,name):
    obj(item,name)
    for k in ('id','description','target_claim','impact'):text(item.get(k),name+'.'+k)
    require(item.get('finding_status') in FINDINGS,name+'finding_status无效')
    require(item.get('severity') in SEVERITIES,name+'severity无效')
    evidence(item.get('evidence'),materials,name+'.evidence')
    if item['finding_status'] in {'confirmed','partially_supported','unsupported'}:
        require(bool(item['evidence']),name+'已作支持/反对判断但无可定位证据')
    for field in ('uncertainty','suggested_actions'):
        for x in seq(item.get(field),name+'.'+field):text(x,name+'.'+field)
    require(isinstance(item.get('clarification_needed'),str),name+'缺clarification_needed（可空）')
    return check_record(item.get('self_check'),name+'.self_check')


def source_ref(item,known,name):
    obj(item,name);key=(item.get('task_id'),item.get('issue_id'))
    require(key in known,name+'引用未知原意见: '+str(key))
    return key


def validate(run_path,workflow_path):
    root=run_path.parent;run=obj(load(run_path),'run');wf=obj(load(workflow_path),'workflow')
    require(run.get('schema_version')==2 and wf.get('schema_version')==2,'需要schema_version=2')
    text(run.get('run_id'),'run_id');require(run.get('mode') in {'independent','revision_check'},'模式无效')
    require(wf.get('run_id')==run['run_id'] and wf.get('run_sha256')==digest(run_path),'workflow与本轮输入版本不符')
    paper_path=snapshot(run.get('paper'),root,'paper')
    materials={}
    allowed_material_roles={'paper','supplement','public_resource','venue_standard','prior_review','author_response'}
    for m in seq(run.get('materials'),'materials'):
        obj(m,'material');text(m.get('id'),'material.id');require(m['id'] not in materials,'材料ID重复')
        snapshot(m,root,'material '+m['id']);require(m.get('role') in allowed_material_roles,'材料角色无效')
        if run['mode']=='independent':require(m['role'] not in {'prior_review','author_response'},'独立预审夹带旧意见/回应')
        materials[m['id']]=m
    require(any((root/m['path']).resolve()==paper_path and m['sha256']==run['paper']['sha256'] for m in materials.values()),'主材料未列入materials')
    iso=obj(run.get('isolation'),'isolation');require(iso.get('status') in {'context_separated','shared','unknown'},'隔离状态无效')
    seq(iso.get('limitations'),'isolation.limitations')
    needs_revision=check_record(run.get('preparation_check'),'preparation_check')
    require(not needs_revision,'准备自查尚有影响启动的缺陷')
    venue=obj(run.get('venue'),'venue');require(venue.get('form_status') in {'verified','unverified','not_requested'},'表单状态无效')
    sources=seq(venue.get('sources'),'venue.sources');dimensions={}
    for d in seq(venue.get('dimensions'),'venue.dimensions'):
        obj(d,'dimension');text(d.get('name'),'dimension.name');require(d['name'] not in dimensions,'评分维度重复')
        values=seq(d.get('allowed_values'),'allowed_values');require(values,'评分维度缺允许刻度')
        require(all(type(v) in (str,int,float) for v in values),'评分刻度须为数字/文字值')
        dimensions[d['name']]=values
    if venue['form_status']=='verified':
        require(sources,'已核实表单缺来源')
        for source in sources:
            obj(source,'venue source')
            for k in ('ref','checked_at','scope','location'):text(source.get(k),'venue source.'+k)
    tasks={}
    for t in seq(run.get('tasks'),'tasks'):
        obj(t,'task');require(re.fullmatch('[A-Za-z0-9_-]+',str(t.get('id',''))) is not None,'任务ID无效')
        require(t['id'] not in tasks and t.get('role') in ROLES,'任务重复或角色无效')
        text(t.get('focus'),'task.focus');tasks[t['id']]=t
    require(any(t['role']=='reviewer' for t in tasks.values()),'缺reviewer任务')
    require(sum(t['role']=='synthesis' for t in tasks.values())<=1,'多个synthesis')
    envelopes={}
    for entry in seq(wf.get('tasks'),'workflow.tasks'):
        obj(entry,'task envelope');tid=entry.get('task_id')
        require(tid in tasks and tid not in envelopes,'返回任务未知或重复')
        require(entry.get('role')==tasks[tid]['role'],'返回角色不符')
        require(entry.get('status') in {'returned','failed','invalid'},'返回状态无效')
        if entry['status']!='returned':text(entry.get('error'),'失败/无效任务原因')
        envelopes[tid]=entry
    require(set(envelopes)==set(tasks),'任务集合不完整，不能静默删除缺失任务')
    reports={};statuses=[];partial=False;all_materials=dict(materials)
    # 先收集实际检索新增来源快照，再核跨任务证据引用；不改写初始材料快照。
    for tid,env in envelopes.items():
        if env['status']!='returned':continue
        report=obj(env.get('result'),'report '+tid)
        require(report.get('task_id')==tid and report.get('run_id')==run['run_id'] and report.get('paper_sha256')==run['paper']['sha256'],'任务返回身份/论文版本不符')
        for m in seq(report.get('external_sources'),'external_sources'):
            obj(m,'external source');text(m.get('id'),'source.id')
            require(m['id'].startswith(tid+':') and m['id'] not in all_materials,'外部来源ID须以任务ID:开头且唯一')
            snapshot(m,root,'外部来源 '+m['id']);text(m.get('url'),'source.url');seq(m.get('read_locations'),'read_locations')
            all_materials[m['id']]={**m,'role':'public_resource'}
        reports[tid]=report
    known={}
    for tid,env in envelopes.items():
        state={'task_id':tid,'role':tasks[tid]['role'],'status':env['status'],'error':env.get('error'),'artifact_status':'not_checked','artifact_path':str((root/'tasks'/(tid+'.json')).resolve()),'artifact_sha256':None}
        statuses.append(state)
        if env['status']!='returned':partial=True;continue
        report=reports[tid]
        contribution=obj(report.get('contribution'),'contribution')
        for k in ('problem','prior_knowledge','new_knowledge','evidence_scope','significance'):text(contribution.get(k),'contribution.'+k)
        reading=obj(report.get('reading'),'reading');seq(reading.get('locations'),'reading.locations');seq(reading.get('missing_materials'),'reading.missing_materials')
        for strength in seq(report.get('strengths'),'strengths'):
            obj(strength,'strength');text(strength.get('statement'),'strength.statement');evidence(strength.get('evidence'),all_materials,'strength evidence')
        seen=set()
        for item in seq(report.get('issues'),'issues'):
            needs_revision|=issue(item,all_materials,tid+' issue')
            require(item['id'] not in seen,'同任务issue ID重复');seen.add(item['id']);known[(tid,item['id'])]=item
        for search in seq(report.get('searches'),'searches'):
            obj(search,'search');text(search.get('query'),'search.query');text(search.get('conclusion'),'search.conclusion')
            for k in ('sources','read_locations','limitations'):seq(search.get(k),'search.'+k)
        used=set()
        for score in seq(report.get('scores'),'scores'):
            obj(score,'score');text(score.get('reason'),'score.reason')
            require(venue['form_status']=='verified','未核实表单不能给官方评分')
            dim=score.get('dimension');require(dim in dimensions and dim not in used,'未知/重复评分维度');used.add(dim)
            value=score.get('value')
            require(value is None or (type(value) is not bool and value in dimensions[dim]),'评分不在适用允许刻度')
        needs_revision|=check_record(report.get('self_check'),'report self_check')
        artifact=root/'tasks'/(tid+'.json')
        if not artifact.is_file():
            state['artifact_status']='missing';partial=True
        else:
            require(load(artifact)==report,'实际任务文件与结构化返回不一致: '+tid)
            state['artifact_status']='matched';state['artifact_sha256']=digest(artifact)
    synthesis=next((reports[t] for t in reports if tasks[t]['role']=='synthesis'),None)
    prior=None;scope=[]
    if run['mode']=='revision_check':
        prior_path=snapshot(run.get('prior_round'),root,'prior_round');prior=obj(load(prior_path),'prior problem-list')
        require(prior.get('schema_version')==2,'旧schema需先明确转换与范围，不能伪装新版已核实')
        text(prior.get('run_id'),'prior.run_id')
        require(isinstance(prior.get('paper'),dict) and re.fullmatch('[a-f0-9]{64}',str(prior['paper'].get('sha256',''))) is not None,'旧问题清单未绑定具体论文版本')
        old={}
        for p in seq(prior.get('problems'),'prior.problems'):
            obj(p,'prior problem');text(p.get('id'),'prior id');require(p['id'] not in old,'旧问题ID重复');old[p['id']]=p
        scope=seq(run.get('revision_scope'),'revision_scope');require(len(scope)==len(set(scope)) and all(x in old for x in scope),'复查范围含重复/未知旧ID')
    else:
        require(run.get('prior_round') in (None,{}) and run.get('revision_scope') in (None,[]),'独立预审不接收旧轮次范围')
    problems=[];dispositions=[];disputes=[];rechecks=[]
    recommendation={'judgment':'undetermined','rationale':'尚未完成综合，只提供明确来源的候选意见','limits':['不是官方评审或录用预测']}
    if synthesis is not None:
        final={}
        for item in seq(synthesis.get('problems'),'problems'):
            needs_revision|=issue(item,all_materials,'final problem')
            require(item['id'] not in final,'最终问题ID重复')
            refs=seq(item.get('source_refs'),'source_refs');require(refs,'问题缺原意见来源')
            keys=[source_ref(x,known,'problem source') for x in refs];require(len(keys)==len(set(keys)),'问题来源重复')
            final[item['id']]=item
        done=set();covered_sources={pid:set() for pid in final}
        for d in seq(synthesis.get('dispositions'),'dispositions'):
            key=source_ref(d,known,'disposition');require(key not in done,'原意见处理重复');done.add(key)
            require(d.get('outcome') in {'included','merged','not_supported','needs_check'},'原意见处理结果无效')
            text(d.get('reason'),'disposition.reason');evidence(d.get('evidence'),all_materials,'disposition evidence')
            if d['outcome']=='not_supported':
                require(d['evidence'],'不支持须有核查依据');require(d.get('problem_id') is None,'不支持项不能关联仍纳入的问题')
            else:
                pid=d.get('problem_id');require(pid in final,'原意见未对应最终问题')
                refs={(x['task_id'],x['issue_id']) for x in final[pid]['source_refs']}
                require(key in refs,'合并/纳入丢失原意见来源');covered_sources[pid].add(key)
                if d['outcome']=='needs_check':require(final[pid]['finding_status'] in {'unverified','partially_supported'},'待核查不能写成已确认')
        require(done==set(known),'综合遗漏原意见的处理，不能按缺字段静默丢弃')
        for pid,item in final.items():
            require(covered_sources[pid]=={(x['task_id'],x['issue_id']) for x in item['source_refs']},'最终问题存在无对应处理的来源')
        dispositions=synthesis['dispositions'];problems=list(final.values())
        for d in seq(synthesis.get('disputes'),'disputes'):
            obj(d,'dispute');text(d.get('topic'),'dispute.topic');text(d.get('basis'),'dispute.basis');require(d.get('judgment') in FINDINGS,'争议判断无效')
            refs=seq(d.get('source_refs'),'dispute refs');require(refs,'争议缺具体意见来源')
            for x in refs:source_ref(x,known,'dispute source')
            evidence(d.get('evidence'),all_materials,'dispute evidence')
            seq(d.get('remaining_unknowns'),'remaining_unknowns');seq(d.get('next_actions'),'next_actions')
        disputes=synthesis['disputes'];rec=obj(synthesis.get('recommendation'),'recommendation')
        require(rec.get('judgment') in {'positive','mixed','negative','undetermined'},'综合建议无效');text(rec.get('rationale'),'recommendation.rationale');seq(rec.get('limits'),'recommendation.limits');recommendation=rec
        checked=set()
        for c in seq(synthesis.get('rechecks'),'rechecks'):
            obj(c,'recheck');pid=c.get('prior_problem_id')
            require(prior is not None and pid in scope and pid not in checked,'复查引用未知/重复/范围外旧ID');checked.add(pid)
            require(c.get('status') in RECHECKS,'复查状态无效');text(c.get('reason'),'recheck.reason');evidence(c.get('evidence'),all_materials,'recheck evidence')
            if c['status']!='not_checked':require(c['evidence'],'解决/未解决判断须有本轮证据')
            require(all(x in final for x in seq(c.get('new_problem_ids'),'new_problem_ids')),'复查引用未知新问题')
        require(checked==set(scope),'复查未覆盖指定旧问题；无法检查须明记not_checked')
        rechecks=synthesis['rechecks']
    else:
        partial=True
        for (tid,iid),item in known.items():
            problems.append({**item,'id':'candidate-'+tid+'-'+iid,'source_refs':[{'task_id':tid,'issue_id':iid}],'needs_synthesis':True})
    if prior is not None:
        checked={x['prior_problem_id'] for x in rechecks}
        for p in prior['problems']:
            if p['id'] not in checked:
                rechecks.append({'prior_problem_id':p['id'],'status':'not_checked','reason':'不在本轮指定范围或本轮尚未完成综合','evidence':[],'new_problem_ids':[]})
    partial|=needs_revision
    package={
        'schema_version':2,'run_id':run['run_id'],'run_sha256':digest(run_path),'mode':run['mode'],
        'paper':{'path':str(paper_path),'sha256':run['paper']['sha256']},
        'input_refs':{'run':{'path':str(run_path),'sha256':digest(run_path)},'workflow':{'path':str(workflow_path),'sha256':digest(workflow_path)}},
        'materials':[{**m,'path':str((root/m['path']).resolve())} for m in all_materials.values()],
        'prior_round':({'path':str(prior_path),'sha256':run['prior_round']['sha256']} if prior is not None else None),'revision_scope':scope,
        'venue':venue,'isolation':iso,'completion':'partial' if partial else 'complete','task_statuses':statuses,
        'contributions':{tid:report['contribution'] for tid,report in reports.items()},
        'recommendation':recommendation,'problems':problems,'dispositions':dispositions,'disputes':disputes,'rechecks':rechecks,
        'limits':['结构校验不认证科学判断、引文/图像真实性或真实上下文隔离','只审声明的材料和实际取得的来源，不预测官方录用'],
    }
    return package,3 if partial else 0


def render(package):
    lines=['# 本轮问题清单','',f"运行：{package['run_id']}；模式：{package['mode']}；完成状态：{package['completion']}",'']
    for p in package['problems']:
        lines += [f"## {p['id']} · {p['finding_status']} · {p['severity']}",'',p['description'],'','影响主张：'+p['target_claim'],'','影响：'+p['impact'],'']
        for e in p['evidence']:lines += [f"- {e['material_id']} · {e['location']}：{e['observation']}"]
        lines += ['','未知：'+'；'.join(p['uncertainty']),'','澄清需求：'+p['clarification_needed'],'']
    summary=['# 本轮审查结果','',f"运行：{package['run_id']}；模式：{package['mode']}；状态：{package['completion']}",'',f"论文版本：{package['paper']['sha256']}",'','这是预审记录，不是官方同行评审或录用预测。','', '## 贡献理解','']
    for tid,c in package['contributions'].items():
        summary += [f"### {tid}",'']+[label+'：'+c[key]+'\n' for label,key in [('问题','problem'),('已有认识','prior_knowledge'),('实际新增','new_knowledge'),('证据范围','evidence_scope'),('意义','significance')]]
    summary += ['## 综合建议','',package['recommendation']['judgment']+'：'+package['recommendation']['rationale'],'','## 任务状态','']
    summary += [f"- {t['task_id']}：{t['status']}；文件={t['artifact_status']}；{t['error'] or ''}" for t in package['task_statuses']]
    summary += ['','## 分歧与待核实','']
    for d in package['disputes']:summary += [f"- {d['topic']}：{d['judgment']}；{d['basis']}；未知：{'；'.join(d['remaining_unknowns'])}"]
    for p in package['problems']:
        if p['finding_status'] in {'unverified','partially_supported'}:summary += [f"- {p['id']}：{p['description']}"]
    summary += ['','## 修改复查','']+[f"- {c['prior_problem_id']}：{c['status']}；{c['reason']}" for c in package['rechecks']]
    summary += ['','## 文件与交接','', 'problem-list.json 保存本轮结构化意见；problem-清单.md 保存具体问题；validation.json 保存文件核查范围。', '', 'response须按本轮确切路径和论文校验值核对；核心研究未决建议iterate，不按严重程度自动安排实验。','']
    summary += ['- '+x for x in package['limits']+package['recommendation']['limits']]
    return '\n'.join(lines)+'\n','\n'.join(summary)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True,type=Path);parser.add_argument('--workflow',required=True,type=Path);parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    try:
        require(not args.output_dir.exists(),'输出目录已存在，不覆盖历史；指定新的交接目录')
        package,code=validate(args.run.resolve(),args.workflow.resolve())
        problem_md,summary_md=render(package)
        args.output_dir.mkdir(parents=True,exist_ok=False)
        for name,value in [('problem-list.json',package),('validation.json',{'checked_at':datetime.now(timezone.utc).isoformat(),'exit_code':code,'completion':package['completion'],'run_sha256':package['run_sha256'],'limits':package['limits']})]:
            (args.output_dir/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        (args.output_dir/'problem-清单.md').write_text(problem_md)
        (args.output_dir/'审稿总报告.md').write_text(summary_md)
        print(('PARTIAL' if code else 'RECORDS_COMPLETE')+': '+str(args.output_dir))
        print('仅核记录与声明一致；不认证科学判断、引用真实性或录用预测')
        return code
    except (OSError,ValueError,TypeError,KeyError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
