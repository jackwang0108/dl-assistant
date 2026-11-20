"""运行可执行文件检查。0未发现硬错误，1错误，2用法，3检查未完成。

不认证研究结论、原文支持、实际版式/页数/匿名。WARN是建议，SKIP不是通过。
"""
import json
import os
import re
import subprocess
import sys
from _common import Report, find_main_tex, read_lines, scan_tex_files, norm

HERE=os.path.dirname(os.path.abspath(__file__))
CHECKS={name:'check_'+name+'.py' for name in ('labels','citations','ai_tells','numbers')}
SECTION_RE=re.compile(r'\\(?:section|subsection)\*?(?:\[[^\]]*\])?\s*\{([^{}]+)\}')


def venue_check(root):
    rep=Report('venue')
    path=os.path.join(root,'_draft','venue-contract.json')
    if not os.path.isfile(path):
        rep.unchecked('venue_contract','缺适用要求记录，不推导已合规');return rep
    try:
        with open(path,encoding='utf-8') as f:data=json.load(f)
        if not isinstance(data,dict):raise ValueError('投稿要求须为对象')
        if data.get('applicability')=='not_applicable':
            if not isinstance(data.get('reason'),str) or not data['reason'].strip():raise ValueError('不适用须说明理由')
            rep.skip('venue_contract',data['reason']);return rep
        main,problems=find_main_tex(root)
        if main is None:
            rep.unchecked('main_tex','; '.join(problems));return rep
        files=scan_tex_files(root,main)
        sections={norm(m.group(1)) for p in files for m in SECTION_RE.finditer('\n'.join(read_lines(p) or []))}
        required=data.get('mandatory_sections')
        if not isinstance(required,list):
            rep.unchecked('mandatory_sections','未明确适用强制章节，不能按空数组默认通过')
        else:
            for name in required:
                if not isinstance(name,str) or not name.strip():raise ValueError('mandatory_sections须为非空名称数组')
                if norm(name) not in sections:rep.fail('mandatory_section_missing',[name+'：未在可解析章节标题中找到，需核实际要求/模板'])
            if not any(x[0]=='FAIL' for x in rep.items):rep.pass_('mandatory_section_headings','只核已声明标题，不认证章节内容满足要求')
        rep.skip('pdf_and_policy_checks','页数计数范围、匿名、样式/引用显示与其他政策需实际官方材料、编译/PDF和内容核查；不由cite命令推定引用风格')
    except (OSError,ValueError,TypeError) as e:
        rep.fail('venue_contract_invalid',[str(e)])
    return rep


def main():
    if len(sys.argv) not in (2,3):
        print('用法: python3 run_checks.py <论文根> [all|labels|citations|ai_tells|numbers]');return 2
    root=os.path.abspath(sys.argv[1]);mode=sys.argv[2] if len(sys.argv)==3 else 'all'
    if mode not in CHECKS and mode!='all':print('未知检查: '+mode);return 2
    if not os.path.isdir(root):print('[UNCHECKED] 论文根不存在或不是目录');return 3
    codes=[];counts={k:0 for k in ('PASS','FAIL','WARN','SKIP','UNCHECKED')}
    for name in CHECKS if mode=='all' else [mode]:
        p=subprocess.run([sys.executable,os.path.join(HERE,CHECKS[name]),root],capture_output=True,text=True)
        print(p.stdout,end='')
        if p.stderr:print(p.stderr,end='',file=sys.stderr)
        codes.append(p.returncode)
        found=False
        for line in p.stdout.splitlines():
            m=re.match(r'^\[(PASS|FAIL|WARN|SKIP|UNCHECKED)\]',line)
            if m:counts[m.group(1)]+=1;found=True
        if p.returncode not in (0,1,3) or (p.returncode and not found):
            print('[FAIL] check_execution: '+name);counts['FAIL']+=1;codes.append(1)
    rep=venue_check(root);codes.append(rep.emit())
    for status,*_ in rep.items:counts[status]+=1
    rc=1 if 1 in codes or any(x not in (0,1,3) for x in codes) else (3 if 3 in codes else 0)
    print('[OVERALL] '+' '.join(k+'='+str(v) for k,v in counts.items())+' => '+{0:'所执行规则未发现硬错误；不认证内容或未检查项目',1:'发现错误',3:'存在无法完成的检查'}[rc])
    return rc


if __name__=='__main__':sys.exit(main())
