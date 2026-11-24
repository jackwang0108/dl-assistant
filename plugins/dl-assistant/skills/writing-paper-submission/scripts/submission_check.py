"""可选的PDF/日志观察，不能代替官方要求、上下文核查或人工提交。

0所请求观察/有限比较完成；1局部问题或输入/工具错误；2用法；3未完成检查。
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

CHECKS=('pages','references','labels','fonts','metadata')
REFERENCE_WARNING = re.compile(
    r'^(?:LaTeX|Package (?:natbib|biblatex)) Warning:[ \t]+'
    r'(?:There were undefined (?:references|citations)\b'
    r'|(?:Citation|Reference)\b'
    # TeX may wrap inside a quoted label. Stop at a blank line or a new log entry.
    r"(?:[ \t]+[\x60'][^'\r\n]*(?:\r?\n(?![ \t]*(?:$|(?:LaTeX|Package|Class)\b|!))[^'\r\n]*){0,2}')?"
    r'[^\r\n]*?'
    r'(?:\r?\n[ \t]*(?:\((?:natbib|biblatex)\)[ \t]*)?on (?:page|input line)\b[^\r\n]*?){0,2}'
    r'(?:[ \t]+|\r?\n[ \t]*(?:\((?:natbib|biblatex)\)[ \t]*)?)'
    r'undefined\b(?=[ \t]*(?:[.!]|on\b|$)))',
    re.IGNORECASE | re.MULTILINE,
)


def positive(value):
    if not re.fullmatch(r'[0-9]+',value) or int(value)<=0:
        raise argparse.ArgumentTypeError('须为正整数，不能使用负数、小数或表达式')
    return int(value)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def row(check,status,observation,**details):
    return {'check':check,'status':status,'observation':observation,**details}


class Observer:
    def __init__(self,args):
        self.args=args;self.inputs={};self.cache={}
        for key in ('pdf','log'):
            path=getattr(args,key)
            if path is not None:
                try:self.inputs[key]={'path':str(path.resolve()),'sha256':sha(path)}
                except OSError as e:self.inputs[key]={'path':str(path.resolve()),'error':str(e)}

    def tool(self,name):
        if name in self.cache:return self.cache[name]
        pdf=self.inputs.get('pdf')
        if not pdf:
            result={'status':'unverified','reason':'未提供PDF'}
        elif 'error' in pdf:
            result={'status':'error','reason':'PDF不可读取：'+pdf['error']}
        else:
            try:
                p=subprocess.run([name,pdf['path']],capture_output=True,text=True,errors='replace',timeout=30)
                result={'status':'observed' if p.returncode==0 else 'error','returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr[:3000]}
                if p.returncode!=0:result['reason']=name+'执行失败，不把空输出当通过'
            except FileNotFoundError:
                result={'status':'unverified','reason':'缺少工具 '+name+'；未自动安装'}
            except subprocess.TimeoutExpired:
                result={'status':'unverified','reason':name+'超时，未自动重试'}
            except OSError as e:
                result={'status':'error','reason':str(e)}
        self.cache[name]=result;return result

    def info(self):
        result=self.tool('pdfinfo')
        if result['status']!='observed':return result
        fields={}
        for line in result['stdout'].splitlines():
            if ':' in line:
                key,value=line.split(':',1);fields[key.strip()]=value.strip()
        if not re.fullmatch(r'[0-9]+',fields.get('Pages','')) or int(fields['Pages'])<=0:
            return {'status':'unverified','reason':'pdfinfo未返回可解析的正整数页数','stdout':result['stdout'][:3000]}
        return {**result,'fields':fields,'pages':int(fields['Pages'])}

    def pages(self):
        info=self.info()
        if info['status']!='observed':return row('pages',info['status'],info.get('reason','PDF信息不可用'),tool=info)
        a=self.args;total=info['pages']
        if a.main_pages is not None and a.main_pages>total:
            return row('pages','error','声明正文页数超过PDF总页数，不能继续比较',total_pages=total,declared_main_pages=a.main_pages)
        scope=a.page_scope or ('main' if a.main_pages is not None else None)
        details={'total_pages':total,'declared_scope':scope,'declared_limit':a.page_limit,'declared_main_pages':a.main_pages,'count_basis':a.main_pages_basis,'rule_ref':a.rule_ref}
        if a.page_limit is None:return row('pages','observed','仅取得PDF总页数，未判断官方篇幅要求',**details)
        if scope is None or not a.rule_ref:
            return row('pages','unverified','比较缺明确计数口径或规则来源；不默认用总页数',**details)
        if scope=='main' and (a.main_pages is None or not a.main_pages_basis):
            return row('pages','unverified','正文计数缺实际页数或定位/计数依据，不从参考文献起始页推算',**details)
        count=total if scope=='total' else a.main_pages
        status='issue_found' if count>a.page_limit else 'meets_declared_rule'
        return row('pages',status,'仅比较所声明范围与上限，不认证官方口径或人工计数依据',judged_pages=count,**details)

    def fonts(self):
        result=self.tool('pdffonts')
        if result['status']!='observed':return row('fonts',result['status'],result.get('reason','工具不可用'),tool=result)
        lines=result['stdout'].splitlines();header=next((i for i,x in enumerate(lines) if re.search(r'\bemb\s+sub\s+uni\b',x)),None)
        if header is None:return row('fonts','unverified','字体输出缺可识别表头，不能当作全嵌',tool=result)
        fonts=[];unparsed=[]
        for line in lines[header+1:]:
            if not line.strip() or set(line.strip())<={'-',' '}:continue
            m=re.fullmatch(r'(.+?)\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+(\d+)\s+(\d+)\s*',line)
            if m:fonts.append({'name':m.group(1).split()[0],'embedded':m.group(2)=='yes','subset':m.group(3)=='yes','unicode':m.group(4)=='yes'})
            else:unparsed.append(line)
        unembedded=[f['name'] for f in fonts if not f['embedded']]
        details={'fonts':fonts,'unembedded':unembedded,'unparsed_rows':unparsed,'rule_ref':self.args.rule_ref}
        if self.args.require_embedded_fonts and self.args.rule_ref and unembedded:
            return row('fonts','issue_found','所声明嵌入要求下发现未嵌字体；另核适用规则',**details)
        if unparsed:return row('fonts','unverified','部分字体行无法解析，不据缺失结果宣布全嵌',**details)
        if not fonts:return row('fonts','observed','工具未列出字体；不代表文本正确、可搜索或整体合规',**details)
        if self.args.require_embedded_fonts:
            if not self.args.rule_ref:return row('fonts','unverified','请求嵌入规则比较但缺规则来源',**details)
            return row('fonts','meets_declared_rule','所列字体符合声明的嵌入要求，不认证其他字体/版式要求',**details)
        return row('fonts','observed','记录所列字体嵌入情况，是否不符合要求需结合官方指南',**details)

    def metadata(self):
        info=self.info()
        if info['status']!='observed':return row('metadata',info['status'],info.get('reason','PDF信息不可用'),tool=info)
        fields={k:v for k,v in info['fields'].items() if k!='Pages'}
        return row('metadata','unverified' if self.args.double_blind else 'observed',
                   '保留工具所见字段；需按适用规则读上下文，不由Author非空/空或tex等子串决定匿名；camera-ready不默认必须填Author',
                   fields=fields,stage_hint='camera-ready' if self.args.camera_ready else None,identity_context_review_required=self.args.double_blind)

    def log_check(self,kind):
        source=self.inputs.get('log')
        if not source:return row(kind,'unverified','未提供日志，不认证当前PDF的构建或引用')
        if 'error' in source:return row(kind,'error','日志不可读取：'+source['error'])
        try:content=Path(source['path']).read_text(errors='replace')
        except OSError as e:return row(kind,'error',str(e))
        if not content.strip():return row(kind,'unverified','空日志不能说明引用/label正确')
        if kind == 'references':
            matches = [match.group().strip() for match in REFERENCE_WARNING.finditer(content)]
        else:
            matches = [match.group().strip() for match in re.finditer(r'[^\n]*multiply[-\s]+defined[^\n]*', content, re.I)]
        details={'warning_count':len(matches),'warnings':matches[:20],'scope':'仅扫描所识别日志警告，不覆盖宏、图像、实际引用内容或页面显示'}
        if re.search(r'Fatal error occurred|Emergency stop|No pages of output|^!.*(?:Error|Undefined control sequence)',content,re.I|re.M):
            return row(kind,'error','日志包含构建失败，不能用来证明PDF引用正确',**details)
        if not re.search(r'This is (?:pdfTeX|LuaHBTeX|LuaTeX|XeTeX|TeX)',content) or not re.search(r'Output written on [^\n]+\.pdf\b',content):
            return row(kind,'unverified','未识别完整成功的PDF构建日志，仍保留观察到的警告',**details)
        if not self.args.build_record:return row(kind,'unverified','日志未绑定当前PDF；不能将旧日志当成当前证据',**details)
        try:
            record_path=self.args.build_record
            with record_path.open() as f:build=json.load(f)
            details['build_record']={'path':str(record_path.resolve()),'sha256':sha(record_path)}
            if not isinstance(build,dict):raise ValueError('构建记录须为对象')
            pdf=self.inputs.get('pdf')
            if not pdf or 'error' in pdf:return row(kind,'unverified','缺当前PDF，无法核日志对应关系',**details)
            if build.get('pdf_sha256')!=pdf['sha256'] or build.get('log_sha256')!=source['sha256']:
                return row(kind,'error','构建记录与当前PDF/日志校验值不符',**details)
            if type(build.get('exit_code')) is not int or build['exit_code']!=0:
                return row(kind,'error','构建记录未声明实际成功退出',**details)
        except (OSError,ValueError,TypeError) as e:return row(kind,'error','构建记录不可核：'+str(e),**details)
        return row(kind,'issue_found' if matches else 'observed','发现所识别警告' if matches else '绑定日志中未发现所识别警告；不认证完整正确',**details)


def render(report):
    def cell(value):return str(value).replace('|',r'\|').replace('\n',' ')
    lines=['## 材料观察与有限比较','','| 检查项 | 状态 | 观察与范围 |','| --- | --- | --- |']
    for result in report['results']:
        lines.append('| '+ ' | '.join(cell(result[k]) for k in ('check','status','observation'))+' |')
        if result['check']=='pages' and 'total_pages' in result:lines.append(f"| 页数数据 | observed | 总页数={result.get('total_pages','未知')}；声明正文页数={result.get('declared_main_pages','未给')} |")
        if 'fields' in result:
            for k,v in result['fields'].items():lines.append('| metadata '+cell(k)+' | observed | '+cell(v)+' |')
        if result.get('unembedded'):lines.append('| 未嵌字体 | observed | '+cell(', '.join(result['unembedded']))+' |')
        for warning in result.get('warnings',[]):lines.append('| 日志观察 | observed | '+cell(warning)+' |')
    lines+=['','输入快照：']+[f"- {k}: {cell(v['path'])} · {v.get('sha256','不可读取')}" for k,v in report['inputs'].items()]
    lines+=['']+report['limits']
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',type=Path);parser.add_argument('--log',type=Path)
    parser.add_argument('--checks',help='逗号分隔：'+','.join(CHECKS))
    parser.add_argument('--page-limit',type=positive);parser.add_argument('--page-scope',choices=('total','main'))
    parser.add_argument('--main-pages',type=positive);parser.add_argument('--main-pages-basis')
    parser.add_argument('--rule-ref');parser.add_argument('--require-embedded-fonts',action='store_true')
    parser.add_argument('--double-blind',action='store_true');parser.add_argument('--camera-ready',action='store_true')
    parser.add_argument('--build-record',type=Path);parser.add_argument('--format',choices=('markdown','json'),default='markdown')
    args=parser.parse_args()
    if not args.pdf and not args.log:parser.error('需要PDF或日志；只查指南时无需调用本脚本')
    if args.page_scope=='total' and args.main_pages is not None:parser.error('total口径与main-pages矛盾，请选择实际口径')
    checks=args.checks.split(',') if args.checks else ((['pages','fonts','metadata'] if args.pdf else [])+(['references','labels'] if args.log else []))
    if not checks or len(checks)!=len(set(checks)) or any(c not in CHECKS for c in checks):parser.error('checks含未知/重复项目')
    observer=Observer(args);results=[]
    for kind in checks:
        results.append(observer.log_check(kind) if kind in {'references','labels'} else getattr(observer,kind)())
    for kind,source in observer.inputs.items():
        if 'sha256' not in source:continue
        try:changed=sha(Path(source['path']))!=source['sha256']
        except OSError:changed=True
        if changed:results.append(row(kind+'_changed','error','检查期间输入变化，结果不能沿用为当前版本'))
    code=1 if any(r['status'] in {'issue_found','error'} for r in results) else (3 if any(r['status']=='unverified' for r in results) else 0)
    report={'schema_version':2,'checked_at':datetime.now(timezone.utc).isoformat(),'requested_checks':checks,'inputs':observer.inputs,'results':results,'exit_code':code,
            'limits':['这些是局部观察或声明规则下的比较，不是整体合规、匿名合格、科学内容或平台接受认证。','未进行任何在线填写、上传或提交；官方要求和人工待办需另外核对。']}
    print(json.dumps(report,ensure_ascii=False,indent=2) if args.format=='json' else render(report),end='\n')
    return code


if __name__=='__main__':sys.exit(main())
