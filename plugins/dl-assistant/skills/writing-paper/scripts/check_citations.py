"""核本地引用身份、BibTeX及登记位置；不认证原文支持关系。"""
import json
import os
import re
import sys
from _common import Report, find_main_tex, hit, read_lines, relpath, scan_tex_files, norm

CITE_RE = re.compile(r"\\(?:citep|citet|citealp|citealt|citeauthor|citeyear|parencite|textcite|autocite|cite)\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]*)\}")
BIB_RE = re.compile(r"@(\w+)\s*[({]\s*([^,\s]+)\s*,")


def extract_cites(root, files):
    cites = {}
    for path in files:
        for i, line in enumerate(read_lines(path) or []):
            for m in CITE_RE.finditer(line):
                for key in m.group(1).split(','):
                    if key.strip():
                        cites.setdefault(key.strip(), []).append((relpath(root, path), i + 1))
    return cites


def bibliography_files(root, files):
    names = []
    cfg = os.path.join(root, '_draft', 'config.json')
    if os.path.isfile(cfg):
        with open(cfg, encoding='utf-8') as f:
            config = json.load(f)
        extra = config.get('bib_files', [])
        if not isinstance(extra, list) or any(not isinstance(x, str) for x in extra):
            raise ValueError('config.bib_files须为路径数组')
        names.extend(extra)
    for path in files:
        for m in re.finditer(r'\\(?:bibliography|addbibresource)(?:\[[^\]]*\])?\s*\{([^}]+)\}', '\n'.join(read_lines(path) or [])):
            names.extend(m.group(1).split(','))
    if not names and os.path.isfile(os.path.join(root, 'refs.bib')):
        names.append('refs.bib')
    return sorted({os.path.join(root, n.strip() if n.strip().endswith('.bib') else n.strip()+'.bib') for n in names if n.strip()})


def main():
    if len(sys.argv) != 2:
        print('用法: python3 check_citations.py <论文根>')
        return 2
    root = os.path.abspath(sys.argv[1])
    rep = Report('citations')
    main_tex, problems = find_main_tex(root)
    if main_tex is None:
        rep.unchecked('main_tex', '; '.join(problems))
        return rep.emit()
    files = scan_tex_files(root, main_tex)
    cites = extract_cites(root, files)
    try:
        paths = bibliography_files(root, files)
        keys = []
        for path in paths:
            lines = read_lines(path)
            if lines is None:
                rep.fail('bibliography_missing', [path])
                continue
            keys.extend(m.group(2) for m in BIB_RE.finditer('\n'.join(lines)) if m.group(1).lower() not in {'comment','preamble','string'})
    except (OSError, ValueError, TypeError) as e:
        rep.fail('bibliography_config', [str(e)])
        keys = []
    missing = sorted(set(cites) - set(keys))
    if missing:
        rep.fail('cite_without_entry', [hit(*cites[k][0], '引用无可得BibTeX条目: '+k) for k in missing])
    else:
        rep.pass_('cite_without_entry', '仅核本地可解析的引用与条目')
    duplicates = sorted({k for k in keys if keys.count(k)>1})
    if duplicates:
        rep.fail('duplicate_bib_key', duplicates)
    orphan = sorted(set(keys)-set(cites))
    if orphan:
        rep.warn('orphan_entry', orphan)
    path = os.path.join(root, '_draft', 'references.json')
    if not os.path.isfile(path):
        if cites:
            rep.unchecked('citation_registration', '缺references.json，不能核具体使用位置/支持关系登记')
        else:
            rep.skip('citation_registration', '无已识别的正文引用')
        return rep.emit()
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get('entries') if isinstance(data, dict) else data
        if not isinstance(entries, list) or any(not isinstance(x, dict) for x in entries):
            raise ValueError('references须为条目数组或{entries:数组}')
        registered = {}
        for e in entries:
            key = e.get('cite_key')
            if not isinstance(key,str) or not key.strip():
                raise ValueError('登记缺cite_key')
            uses = e.get('uses', [e])
            if not isinstance(uses,list) or not uses:
                raise ValueError('uses须为非空数组')
            for use in uses:
                if not isinstance(use,dict) or not isinstance(use.get('claim'),str) or not use['claim'].strip():
                    raise ValueError(key+' 缺具体claim')
                sec = use.get('section')
                secs = sec if isinstance(sec,list) else [sec]
                if not secs or any(not isinstance(x,str) or not x.strip() for x in secs):
                    raise ValueError(key+' 缺section')
                registered.setdefault(key,set()).update(norm(x) for x in secs)
        for key, locations in cites.items():
            if key not in registered:
                rep.fail('cite_without_registration', [key])
                continue
            for path, line in locations:
                section = 'main' if os.path.abspath(os.path.join(root,path))==os.path.abspath(main_tex) else os.path.splitext(os.path.basename(path))[0]
                if norm(section) not in registered[key]:
                    rep.fail('section_mismatch',[hit(path,line,key+' 的该使用位置未登记')])
        rep.pass_('registration_parsed', '位置对应不认证原文支持；原文依据另作内容核查')
    except (OSError, ValueError, TypeError) as e:
        rep.fail('registration_invalid',[str(e)])
    return rep.emit()


if __name__ == '__main__':
    sys.exit(main())
