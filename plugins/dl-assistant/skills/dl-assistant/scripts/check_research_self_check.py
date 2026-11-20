#!/usr/bin/env python3
"""Read-only checks for research self-check records; never certifies science."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

REQUIRED = {
    ('idea-find', 'candidate'): {'problem', 'hypothesis', 'reasoning', 'value', 'alternatives'},
    ('idea-find', 'handoff'): {'problem', 'hypothesis', 'reasoning', 'value', 'alternatives', 'design', 'interpretation', 'budget'},
    ('code-idea-execution', 'pre_run'): {'implementation', 'comparison', 'provenance', 'authorization'},
    ('code-idea-execution', 'handoff'): {'execution_state', 'data_validity', 'inference', 'deviations', 'traceability'},
    ('code-idea-iterate', 'next_step'): {'belief_update', 'competing_explanations', 'current_value', 'next_evidence', 'evidence_history'},
    ('code-idea-iterate', 'transition'): {'knowledge', 'evidence', 'novelty_value', 'remaining_work', 'recommendation'},
}


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('invalid JSON constant: ' + value)


def validate(data, root, skill, stage, record):
    errors = []
    if not isinstance(data, dict):
        return ['记录必须为JSON对象']
    if data.get('schema_version') != 1:
        errors.append('需schema_version=1')
    if data.get('skill') != skill or data.get('stage') != stage:
        errors.append('skill/stage与本次目标行动不一致')
    for field in ('subject', 'checked_at', 'next_action'):
        if not nonblank(data.get(field)):
            errors.append(field + '缺失')
    inputs = data.get('inputs')
    if not isinstance(inputs, list) or not inputs:
        errors.append('缺相关输入快照')
    else:
        seen = set()
        for item in inputs:
            if not isinstance(item, dict) or not nonblank(item.get('path')):
                errors.append('输入需path和sha256')
                continue
            path = (root / item['path']).resolve()
            if path == record.resolve():
                errors.append('输入不能为自查记录自身')
                continue
            if path in seen:
                errors.append('重复输入：' + item['path'])
            seen.add(path)
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if item.get('sha256') != digest:
                    errors.append('输入已变化或hash无效：' + item['path'])
            except OSError as exc:
                errors.append('输入无法读取：' + str(exc))
    checks = data.get('checks')
    statuses = []
    ids = set()
    if not isinstance(checks, list):
        errors.append('checks需为数组')
        checks = []
    for item in checks:
        if not isinstance(item, dict) or not nonblank(item.get('id')):
            errors.append('检查项缺id')
            continue
        cid = item['id']
        if cid in ids:
            errors.append('重复检查项：' + cid)
        ids.add(cid)
        status = item.get('status')
        if status not in ('clear', 'limited', 'needs_revision'):
            errors.append(cid + ' status无效')
        statuses.append(status)
        for field in ('finding', 'effect'):
            if not nonblank(item.get(field)):
                errors.append(cid + ' 缺' + field)
        unknowns = item.get('unknowns')
        if not isinstance(unknowns, list) or any(not nonblank(x) for x in unknowns):
            errors.append(cid + ' unknowns需字符串数组，可为空')
        if status == 'limited' and not unknowns:
            errors.append(cid + ' limited需说明未知/限制')
        refs = item.get('basis_refs')
        if not isinstance(refs, list) or not refs:
            errors.append(cid + ' 缺依据引用')
            continue
        for ref in refs:
            if not nonblank(ref):
                errors.append(cid + ' 引用需字符串')
            elif ref.startswith(('https://', 'http://')):
                # Source contents and whether they were read are deliberately not inferred.
                continue
            else:
                path = (root / ref.split('#', 1)[0]).resolve()
                if not path.is_file():
                    errors.append(cid + ' 引用文件缺失：' + ref)
    missing = REQUIRED[(skill, stage)] - ids
    if missing:
        errors.append('缺必需项：' + ', '.join(sorted(missing)))
    decision = data.get('decision')
    if decision not in ('continue', 'continue_with_limits', 'revise'):
        errors.append('decision无效')
    if 'needs_revision' in statuses and decision != 'revise':
        errors.append('需修正项未阻止目标行动')
    if 'limited' in statuses and decision == 'continue':
        errors.append('有限制却声明无条件继续')
    if decision == 'revise':
        errors.append('已声明需修正：保存/报告问题，勿执行受阻的目标行动')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--skill', choices=sorted({key[0] for key in REQUIRED}), required=True)
    parser.add_argument('--stage', required=True)
    args = parser.parse_args()
    if (args.skill, args.stage) not in REQUIRED:
        parser.error('该skill没有指定stage')
    if not args.root.is_dir():
        parser.error('--root需为存在的项目目录')
    try:
        data = json.loads(args.record.read_text(encoding='utf-8'),
                          object_pairs_hook=unique_object, parse_constant=invalid_constant)
        errors = validate(data, args.root, args.skill, args.stage, args.record)
    except (OSError, ValueError, UnicodeError) as exc:
        errors = ['无法读取有效记录：' + str(exc)]
    for error in errors:
        print('FAIL: ' + error)
    if not errors:
        print('PASS: 记录、引用、输入快照与声明的行动一致')
    print('仅作结构与来源文件检查；不证明研究价值、推理、授权或科学结论正确。')
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
