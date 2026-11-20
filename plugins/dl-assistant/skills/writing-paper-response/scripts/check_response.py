"""核意见覆盖、版本、行动状态和回复声明，生成不覆盖历史的交接。

0当前阶段记录检查完成，1错误，2用法错误，3草稿/部分完成。
不认证自然语言真实性、证据充分性、官方合规或已发送。
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

FINDINGS={'confirmed','partially_supported','unsupported','unverified'}
STAGES={'plan','handoff','final'}
OWNERS={'writing-paper','code-idea-iterate','writing-paper-submission','writing-paper-response'}
KINDS={'text_edit','visual_edit','supplementary_evidence','research_decision','compliance_check','reply_only'}
STATUSES={'proposed','approved','in_progress','completed','verified','blocked','cancelled'}
SOURCE_KINDS={'review','comments','manuscript','evidence','research_record','execution_record','policy','authorization','verification','analysis'}


def require(test,message):
    if not test:raise ValueError(message)


def text(value,name):
    require(isinstance(value,str) and bool(value.strip()),name+'须为非空文字')


def seq(value,name):
    require(isinstance(value,list),name+'须为数组');return value


def obj(value,name):
    require(isinstance(value,dict),name+'须为对象');return value


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with path.open(encoding='utf-8') as f:return json.load(f)


def snapshot(record,root,name):
    obj(record,name);text(record.get('path'),name+'.path')
    path=(root/record['path']).resolve();require(path.is_file(),name+'文件不可得: '+str(path))
    require(isinstance(record.get('sha256'),str) and sha(path)==record['sha256'],name+'校验值缺失或版本已变化')
    return path


def indexed(items,name,key='id'):
    out={}
    for item in seq(items,name):
        obj(item,name);text(item.get(key),name+'.'+key)
        require(item[key] not in out,name+'ID重复');out[item[key]]=item
    return out


def refs(values,known,name):
    seen=set()
    for value in seq(values,name):
        require(isinstance(value,str) and value in known,name+'引用未知ID: '+str(value))
        require(value not in seen,name+'引用重复');seen.add(value)
    return seen


def evidence(values,sources,name):
    for item in seq(values,name):
        obj(item,name);require(item.get('source_id') in sources,name+'引用未知来源')
        text(item.get('location'),name+'.location');text(item.get('observation'),name+'.observation')


def check(value,name):
    obj(value,name);require(value.get('status') in {'clear','limited','needs_revision'},name+'状态无效')
    text(value.get('basis'),name+'.basis');text(value.get('effect'),name+'.effect')
    for x in seq(value.get('unknowns'),name+'.unknowns'):text(x,name+'.unknown')
    return value['status']=='needs_revision'


def validate(path):
    root=path.parent;state=obj(load(path),'response-state')
    require(state.get('schema_version')==2,'需要schema_version=2记录')
    text(state.get('response_id'),'response_id');stage=state.get('stage');require(stage in STAGES,'阶段无效')
    paper=snapshot(state.get('paper'),root,'paper')
    current=state.get('current_paper');current_path=snapshot(current,root,'current_paper') if current is not None else paper
    current_hash=current['sha256'] if current else state['paper']['sha256']
    sources=indexed(state.get('sources'),'sources');source_paths={}
    for sid,s in sources.items():
        require(s.get('kind') in SOURCE_KINDS,'来源kind无效')
        source_paths[sid]=snapshot(s,root,'source '+sid)
    comments=indexed(state.get('comments'),'comments');require(comments,'缺原意见')
    for c in comments.values():
        require(c.get('source_id') in sources,'原意见引用未知来源');require(sources[c['source_id']]['kind'] in {'review','comments'},'原意见来源须标明review/comments');text(c.get('location'),'comment.location');text(c.get('text'),'comment.text')
    # 审查来源全部登记，再选择本轮范围，避免只导入希望回应的问题。
    for sid,source in sources.items():
        if source['kind']!='review':continue
        review=obj(load(source_paths[sid]),'review source');require(review.get('schema_version')==2,'旧review需明确重核，不自动升级')
        require(isinstance(review.get('paper'),dict) and review['paper'].get('sha256')==state['paper']['sha256'],'review与被评论论文版本不符')
        problems=indexed(review.get('problems'),'review.problems')
        linked=[c for c in comments.values() if c['source_id']==sid]
        require(len(linked)==len(problems) and {c.get('source_item_id') for c in linked}==set(problems),'未完整登记原review意见或有重复/未知ID')
        for c in linked:
            require(c['text']==problems[c['source_item_id']].get('description'),'原意见文字与指定review记录不符，原文和改写须分开')
    scope=refs(state.get('scope_comment_ids'),comments,'scope_comment_ids');require(scope,'本轮未声明处理范围')
    units=indexed(state.get('units'),'units');actions=indexed(state.get('actions'),'actions');replies=indexed(state.get('replies'),'replies','unit_id')
    covered=set();scope_units=set()
    for uid,u in units.items():
        linked=refs(u.get('comment_ids'),comments,'unit.comment_ids');require(linked,'关切未对应原意见')
        require(linked<=scope,'本轮关切混入未选原意见，先明确处理范围');covered|=linked;scope_units.add(uid)
        for k in ('concern','rationale'):text(u.get(k),'unit.'+k)
        a=obj(u.get('assessment'),'assessment');require(a.get('finding_status') in FINDINGS,'意见判断无效')
        for k in ('reasoning','prior_belief','observation','updated_belief'):text(a.get(k),'assessment.'+k)
        evidence(a.get('evidence_refs'),sources,'assessment.evidence_refs');seq(a.get('unknowns'),'assessment.unknowns')
        if a['finding_status']!='unverified':require(a['evidence_refs'],'对意见作支持/反对判断须有实际依据')
        require(type(a.get('core_unresolved')) is bool,'core_unresolved须为布尔值')
        require(u.get('disposition') in {'clarify','edit','supplement','research','not_adopt','defer'},'处理方式无效')
        if a['core_unresolved']:require(u['disposition'] in {'research','defer'},'核心研究未决不能仅按改稿关闭')
        require(u.get('coverage_status') in {'unaddressed','partially_addressed','addressed','unresolved'},'回应覆盖状态无效')
        require(type(u.get('scope_change')) is bool,'scope_change须为布尔值')
        if u['scope_change']:text(u.get('value_reassessment'),'范围变化后的价值重评')
        refs(u.get('action_ids'),actions,'unit.action_ids')
    require(covered==scope,'遗漏指定原意见的关切，不能因讨论过或合并而消失')
    for aid,a in actions.items():
        linked=refs(a.get('unit_ids'),units,'action.unit_ids');require(linked,'行动未关联关切')
        for uid in linked:require(aid in units[uid]['action_ids'],'行动和关切对应不一致')
        for k in ('description','target','acceptance_criterion'):text(a.get(k),'action.'+k)
        require(a.get('owner') in OWNERS and a.get('kind') in KINDS,'行动owner/kind无效')
        if a['kind']=='research_decision':require(a['owner']=='code-idea-iterate','核心研究判断必须交iterate')
        if a['kind'] in {'text_edit','visual_edit'}:require(a['owner']=='writing-paper','正文/图表修改必须交writing-paper')
        if a['kind']=='reply_only':require(a['owner']=='writing-paper-response','回复处理归response')
        if a['kind']=='supplementary_evidence':
            require(a['owner']=='writing-paper','明确补充设计交writing-paper')
            require(not any(units[x]['assessment']['core_unresolved'] for x in linked),'核心取证不能伪装普通论文补实验')
        deps=refs(a.get('depends_on'),actions,'action.depends_on');require(aid not in deps,'行动依赖自身')
        approval=obj(a.get('approval'),'approval');require(approval.get('status') in {'pending','approved','declined'},'批准状态无效')
        text(approval.get('basis'),'approval.basis');refs(approval.get('source_refs'),sources,'approval.source_refs')
        require(a.get('status') in STATUSES,'行动状态无效')
        if a['status'] in {'approved','in_progress','completed','verified'}:require(approval['status']=='approved','未批准不能标已批准/执行/完成')
        if a['status'] in {'blocked','cancelled'}:text(a.get('reason'),'阻塞/取消原因')
        outputs=refs(a.get('outputs'),sources,'action.outputs')
        v=obj(a.get('verification'),'verification');require(v.get('status') in {'pending','passed','failed'},'核查状态无效')
        vrefs=refs(v.get('source_refs'),sources,'verification.source_refs');text(v.get('basis'),'verification.basis')
        if v['status']=='passed':require(vrefs and all(sources[x]['kind']=='verification' for x in vrefs),'核查通过须有实际verification记录')
        if a['status'] in {'completed','verified'}:require(outputs,'已完成行动缺实际产物')
        if a['status']=='verified':require(v['status']=='passed','未核查通过不能标verified')
        if a['status'] in {'in_progress','completed','verified'}:
            require(all(actions[x].get('status')=='verified' for x in deps),'执行中的行动有未核实前置依赖')
    for uid,u in units.items():
        for aid in u['action_ids']:require(uid in actions[aid]['unit_ids'],'关切和行动对应不一致')
        if u['disposition']=='research':require(any(actions[x]['kind']=='research_decision' for x in u['action_ids']),'返回研究缺明确研究判断任务')
    # 核有向依赖，数组顺序不是执行/批准证据。
    active=set();done=set()
    def visit(aid):
        require(aid not in active,'行动依赖存在循环')
        if aid in done:return
        active.add(aid)
        for dep in actions[aid]['depends_on']:visit(dep)
        active.remove(aid);done.add(aid)
    for aid in actions:visit(aid)
    policy=obj(state.get('policy'),'policy');require(policy.get('status') in {'verified','unknown','not_applicable'},'规则核查状态无效')
    text(policy.get('reason'),'policy.reason');require(type(policy.get('planned_actions_allowed')) is bool,'planned_actions_allowed须为布尔值')
    prefs=refs(policy.get('source_refs'),sources,'policy.source_refs')
    if policy['status']=='verified':require(prefs and all(sources[x]['kind']=='policy' for x in prefs),'已核规则缺实际policy来源')
    partial=stage=='plan';checks=obj(state.get('self_checks'),'self_checks');needed=['plan']+(['handoff'] if stage in {'handoff','final'} else [])+(['final'] if stage=='final' else [])
    check_pending=False
    for name in needed:check_pending|=check(checks.get(name),'self_checks.'+name)
    partial|=check_pending
    statement_ids=set()
    for uid,reply in replies.items():
        require(uid in scope_units,'回复引用未知/范围外关切');require(reply.get('status') in {'draft','checked'},'回复状态无效')
        partial_check=check(reply.get('check'),'reply.check')
        statements=seq(reply.get('statements'),'reply.statements');require(statements,'回复无实际陈述')
        for st in statements:
            obj(st,'statement');text(st.get('id'),'statement.id');require(st['id'] not in statement_ids,'回复语句ID重复');statement_ids.add(st['id']);text(st.get('text'),'statement.text')
            require(st.get('kind') in {'position','evidence_statement','completed_action','planned_action','limitation'},'回复陈述类型无效')
            evidence(st.get('evidence_refs'),sources,'statement.evidence_refs');linked=refs(st.get('action_ids'),actions,'statement.action_ids')
            require(linked<=set(units[uid]['action_ids']),'回复引用不属于该关切的行动')
            if st['kind']=='evidence_statement':require(st['evidence_refs'],'事实/证据陈述缺实际来源')
            if st['kind']=='completed_action':require(linked and all(actions[x]['status']=='verified' for x in linked),'完成陈述不能引用未核查行动')
            if st['kind']=='planned_action':
                require(linked and all(actions[x]['approval']['status']=='approved' and actions[x]['status'] in {'approved','in_progress','blocked'} for x in linked),'未批准/已取消/已完成行动不能伪装未来承诺')
                if stage=='final':require(policy['status']!='unknown' and policy['planned_actions_allowed'],'适用规则未明确允许未来承诺')
        if stage=='final':partial|=reply['status']!='checked' or partial_check
    if stage=='final':
        partial|=set(replies)!=scope_units or any(u['coverage_status']=='unaddressed' for u in units.values()) or policy['status']=='unknown'
    impacts=indexed(state.get('impact_checks'),'impact_checks');changed=set();impact_pending=False;impacted_actions=set()
    for item in impacts.values():
        triggers=refs(item.get('trigger_unit_ids'),units,'impact.trigger_unit_ids');require(triggers,'影响检查缺触发关切');changed|=triggers
        this_pending=check(item.get('check'),'impact.check');impact_pending|=this_pending
        affected=seq(item.get('affected'),'impact.affected');require(affected,'影响检查无具体检查对象')
        for a in affected:
            obj(a,'affected');require(a.get('kind') in {'reply','action','paper_section','claim','visual','research_record'},'影响对象类型无效')
            text(a.get('id'),'affected.id');text(a.get('reason'),'affected.reason')
            if a['kind']=='reply':require(a['id'] in units,'影响检查引用未知回复关切')
            if a['kind']=='action':require(a['id'] in actions,'影响检查引用未知行动')
            require(a.get('status') in {'pending','reviewed','updated','not_affected'},'影响处理状态无效')
            evidence(a.get('evidence_refs'),sources,'affected.evidence_refs');impact_pending|=a['status']=='pending'
            this_pending|=a['status']=='pending'
            if a['status']=='pending' and a['kind']=='action':impacted_actions.add(a['id'])
        if this_pending:
            for uid in triggers:impacted_actions.update(units[uid]['action_ids'])
    require(all(uid in changed for uid,u in units.items() if u['scope_change']),'范围/主张变化未检查跨意见影响')
    conflicts=indexed(state.get('conflicts'),'conflicts');unresolved_actions=set()
    for c in conflicts.values():
        cunits=refs(c.get('unit_ids'),units,'conflict.unit_ids');linked=refs(c.get('action_ids'),actions,'conflict.action_ids')
        text(c.get('description'),'conflict.description');require(c.get('status') in {'unresolved','resolved'},'冲突状态无效')
        evidence(c.get('evidence_refs'),sources,'conflict.evidence_refs')
        if c['status']=='resolved':text(c.get('decision'),'冲突决定');require(c['evidence_refs'],'冲突关闭缺实际决定依据')
        else:
            unresolved_actions|=linked
            for uid in cunits:unresolved_actions.update(units[uid]['action_ids'])
    if stage=='final':partial|=impact_pending or any(c['status']=='unresolved' for c in conflicts.values())
    # 修改完成陈述还需对应实际当前稿，而不是旧稿/旧定位。
    if stage=='final':
        for reply in replies.values():
            for st in reply['statements']:
                if st['kind']!='completed_action':continue
                for aid in st['action_ids']:
                    a=actions[aid]
                    if a['kind'] in {'text_edit','visual_edit'}:
                        require(any(source_paths[x]==current_path and sources[x]['sha256']==current_hash for x in a['outputs']),'完成改稿陈述未对应实际当前稿版本')
    eligible={aid for aid,a in actions.items() if a['owner']=='writing-paper' and a['approval']['status']=='approved' and a['status'] in {'approved','in_progress'} and aid not in unresolved_actions and aid not in impacted_actions}
    while True:
        filtered={aid for aid in eligible if all(dep in eligible or actions[dep]['status']=='verified' for dep in actions[aid]['depends_on'])}
        if filtered==eligible:break
        eligible=filtered
    if stage=='plan' or check_pending:eligible=set()
    if stage=='handoff':
        candidates={aid for aid,a in actions.items() if a['owner']=='writing-paper' and a['approval']['status']=='approved' and a['status'] in {'approved','in_progress'}}
        partial|=bool(candidates-eligible)
    paper_root=state.get('paper_root')
    if eligible:
        require(isinstance(paper_root,str) and (root/paper_root).is_dir(),'交付改稿前须明确实际paper_root，不能猜PDF所在目录')
    items=[]
    for aid,a in actions.items():
        if aid not in eligible:continue
        kind={'text_edit':'局部改','visual_edit':'补图表','supplementary_evidence':'补实验项'}.get(a['kind'],'局部改')
        item={'id':aid,'unit_ids':a['unit_ids'],'section':a['target'],'改动类型':kind,'具体要求':a['description'],'关闭判据':a['acceptance_criterion'],'涉及claim':[],'触发意见':[cid for uid in a['unit_ids'] for cid in units[uid]['comment_ids']],'approval':a['approval'],'status':a['status'],'depends_on':a['depends_on']}
        if a['kind']=='supplementary_evidence':item['补实验目的']=a['description']
        items.append(item)
    brief={'schema_version':2,'任务':state['response_id'],'来源':'writing-paper-response','论文草稿路径':str((root/paper_root).resolve()) if paper_root else None,'response_ref':{'path':str(path),'sha256':sha(path)},'response_id':state['response_id'],'stage':stage,'paper':{'path':str(current_path),'sha256':current_hash},'items':items,'excluded_actions':[{'id':aid,'status':a['status'],'approval':a['approval']['status'],'owner':a['owner'],'reason':('已核查完成，不重复交执行' if a['status']=='verified' else '本轮未就绪、非写作任务或不在当前批准批次；见原记录依赖/冲突/自查')} for aid,a in actions.items() if aid not in eligible]}
    summary={'response_id':state['response_id'],'stage':stage,'completion':'partial' if partial else 'records_complete','record_ref':{'path':str(path),'sha256':sha(path)},'scope_comment_ids':sorted(scope),'not_checked_comment_ids':[cid for cid in comments if cid not in scope],'ready_action_ids':[aid for aid in actions if aid in eligible],'limits':['仅核结构、快照和声明状态，不认证自然语言真实性、科学判断、官方合规或已提交/发送']}
    return state,brief,summary,3 if partial else 0


def render(state,brief,summary):
    comments={c['id']:c for c in state['comments']};units={u['id']:u for u in state['units']};actions={a['id']:a for a in state['actions']};replies={r['unit_id']:r for r in state['replies']}
    ready=state['stage']=='final' and summary['completion']=='records_complete'
    letter=['# Response' if ready else '# 回复草稿','']
    if not ready:letter += ['这是待完成核对的草稿；实际状态与未决见response-map.md和validation.json。','']
    mapping=['# 意见与处理结果对应表','',f"本轮：{state['response_id']}；范围外意见：{', '.join(summary['not_checked_comment_ids']) or '无'}",'']
    for cid in state['scope_comment_ids']:
        c=comments[cid];letter += [f"## {cid}",'',c['text'],'']
        for uid,u in units.items():
            if cid not in u['comment_ids']:continue
            mapping += [f"## {cid} → {uid}",'','关切：'+u['concern'],'','判断：'+u['assessment']['finding_status']+'；'+u['assessment']['reasoning'],'','变化：'+u['assessment']['prior_belief']+' → '+u['assessment']['observation']+' → '+u['assessment']['updated_belief'],'','处理：'+u['disposition']+'；'+u['rationale'],'','回应状态：'+u['coverage_status'],'']
            for aid in u['action_ids']:
                a=actions[aid];mapping += [f"- {aid}：{a['owner']}；批准={a['approval']['status']}；执行={a['status']}；核查={a['verification']['status']}；{a['description']}"]
            for ev in u['assessment']['evidence_refs']:mapping += [f"- 依据 {ev['source_id']} · {ev['location']}：{ev['observation']}"]
            for aid in u['action_ids']:mapping += [f"- {aid}产物：{', '.join(actions[aid]['outputs']) or '尚无'}；核查材料：{', '.join(actions[aid]['verification']['source_refs']) or '尚无'}"]
            mapping += ['']
            letter += [f"### {uid}",'']
            if uid not in replies:letter += ['待形成具体回复。',''];continue
            for st in replies[uid]['statements']:letter += [st['text'],'']
            # 明确列实际状态，不替作者生成虚构的过去时Changes。
            if u['action_ids'] and not ready:
                letter += ['行动状态：']+[f"- {aid}：{actions[aid]['status']}（{actions[aid]['target']}）" for aid in u['action_ids']]+['']
    mapping += ['## 跨意见影响与冲突','']
    for impact in state['impact_checks']:
        for a in impact['affected']:mapping += [f"- {impact['id']}：{a['kind']}/{a['id']}；{a['status']}；{a['reason']}"]
    for c in state['conflicts']:mapping += [f"- {c['id']}：{c['status']}；{c['description']}；{c.get('decision','')}"]
    return '\n'.join(letter)+'\n','\n'.join(mapping)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    try:
        require(not args.output_dir.exists(),'输出目录已存在，不覆盖历史')
        record_path=args.record.resolve()
        state,brief,summary,code=validate(record_path)
        # 交接引用不可变的输出快照，之后更新当前状态不会使已交任务失去原批准版本。
        frozen={**state,'paper':{**state['paper'],'path':str((record_path.parent/state['paper']['path']).resolve())},
                'sources':[{**source,'path':str((record_path.parent/source['path']).resolve())} for source in state['sources']]}
        if state.get('current_paper'):
            frozen['current_paper']={**state['current_paper'],'path':str((record_path.parent/state['current_paper']['path']).resolve())}
        if state.get('paper_root'):
            frozen['paper_root']=str((record_path.parent/state['paper_root']).resolve())
        frozen_text=json.dumps(frozen,ensure_ascii=False,indent=2)+'\n'
        frozen_ref={'path':str((args.output_dir/'response-state.json').resolve()),'sha256':hashlib.sha256(frozen_text.encode('utf-8')).hexdigest()}
        brief['response_ref']=frozen_ref
        summary['input_record_ref']=summary['record_ref'];summary['record_ref']=frozen_ref
        letter,mapping=render(frozen,brief,summary)
        args.output_dir.mkdir(parents=True,exist_ok=False)
        (args.output_dir/'response-state.json').write_text(frozen_text)
        for name,value in [('revision-brief.json',brief),('validation.json',{**summary,'checked_at':datetime.now(timezone.utc).isoformat(),'exit_code':code})]:
            (args.output_dir/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        (args.output_dir/'rebuttal-letter.md').write_text(letter);(args.output_dir/'response-map.md').write_text(mapping)
        print(('PARTIAL' if code else 'RECORDS_COMPLETE')+': '+str(args.output_dir));print(summary['limits'][0]);return code
    except (OSError,ValueError,TypeError,KeyError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
