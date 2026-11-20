"""数值出现位置与JSON来源核查。未知退出3，错误1，用法2。

不展开TeX宏，不读取图像数字，不认证测量/统计/元数据语义。
派生数值应先保存真实分析输出，再引用其中字段；旧全局白名单不能认证结果。
"""
import hashlib
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from _common import Report, find_main_tex, read_lines, relpath, scan_tex_files, hit

NUMBER = re.compile(r'(?<![\w.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?(?:\s*\\%)?(?!\w|\.\d)')
# 保持字符位置，用空格代替引用/标签/路径及结构参数，扫描公式与caption里的数字。
STRUCTURAL = re.compile(r'\\(?:cite\w*|parencite|textcite|autocite|ref|eqref|autoref|cref|Cref|label|input|include|subfile|url|href|includegraphics|documentclass|usepackage|begin|end)\*?(?:\s*\[[^\]]*\]){0,2}\s*\{[^{}]*\}')
COMMAND = re.compile(r'\\[A-Za-z@]+\*?')


def number_tokens(line):
    text = STRUCTURAL.sub(lambda m: ' '*len(m.group()), line)
    text = COMMAND.sub(lambda m: ' '*len(m.group()), text)
    return [m.group().strip() for m in NUMBER.finditer(text)]


def location_key(loc):
    if not isinstance(loc,dict):
        raise ValueError('缺location')
    path,line,token,occ = (loc.get(k) for k in ('path','line','token','occurrence'))
    if not isinstance(path,str) or not path or not isinstance(line,int) or isinstance(line,bool) or line<1 or not isinstance(token,str) or not token or not isinstance(occ,int) or isinstance(occ,bool) or occ<1:
        raise ValueError('location须含path、正整数line/occurrence、数值token')
    return os.path.normpath(path),line,token,occ


def decimal_token(token):
    return Decimal(token.replace(r'\%','').strip())


def pointer_value(data,pointer):
    if not isinstance(pointer,str) or (pointer and not pointer.startswith('/')):
        raise ValueError('json_pointer须为JSON Pointer')
    for part in pointer.split('/')[1:] if pointer else []:
        part=part.replace('~1','/').replace('~0','~')
        if isinstance(data,list):
            if not re.fullmatch(r'0|[1-9]\d*',part):raise ValueError('数组JSON Pointer索引无效')
            data=data[int(part)]
        else:
            data=data[part]
    if isinstance(data,bool) or not isinstance(data,(int,float,Decimal)):
        raise ValueError('来源字段不是有限数值')
    value=Decimal(str(data))
    if not value.is_finite():raise ValueError('来源字段不是有限数值')
    return value


def source_value(root,entry):
    for key in ('id','experiment_id','metric','condition_ref'):
        if not isinstance(entry.get(key),str) or not entry[key].strip():
            raise ValueError('缺'+key)
    condition=entry['condition_ref'].split('#',1)[0]
    if not os.path.isfile(os.path.join(root,condition)):
        raise ValueError('条件记录不可得: '+condition)
    src=entry.get('source')
    if not isinstance(src,dict) or not isinstance(src.get('path'),str):
        raise ValueError('缺source.path')
    path=os.path.join(root,src['path'])
    with open(path,'rb') as f:raw=f.read()
    if src.get('sha256')!=hashlib.sha256(raw).hexdigest():
        raise ValueError('来源校验值不匹配或缺失')
    data=json.loads(raw,parse_float=Decimal)
    value=pointer_value(data,src.get('json_pointer'))
    if isinstance(src.get('scale',1),bool):raise ValueError('scale无效')
    scale=Decimal(str(src.get('scale',1)))
    if not scale.is_finite():raise ValueError('scale非有限值')
    return value*scale


def main():
    if len(sys.argv)!=2:
        print('用法: python3 check_numbers.py <论文根>');return 2
    root=os.path.abspath(sys.argv[1]);rep=Report('numbers')
    main_tex,problems=find_main_tex(root)
    if main_tex is None:
        rep.unchecked('main_tex','; '.join(problems));return rep.emit()
    actual={}
    for path in scan_tex_files(root,main_tex):
        lines=read_lines(path)
        if lines is None:
            rep.unchecked('file_unreadable',path);continue
        for line_no,line in enumerate(lines,1):
            seen={}
            for token in number_tokens(line):
                seen[token]=seen.get(token,0)+1
                actual[(os.path.normpath(relpath(root,path)),line_no,token,seen[token])]=False
    registry=os.path.join(root,'_draft','canonical-values.json')
    if not os.path.isfile(registry):
        if actual:rep.unchecked('number_sources','数值未登记具体来源与位置，含公式/表格/caption，需核来源或说明非结果类别')
        else:rep.skip('number_sources','所扫描文本未识别到数字；不覆盖宏展开和图像')
        return rep.emit()
    try:
        with open(registry,encoding='utf-8') as f:data=json.load(f)
        if isinstance(data,list):
            rep.unchecked('legacy_number_registry','旧全局白名单不能核当前数值来源；按出现位置重新登记，不改写历史读数')
            return rep.emit()
        if not isinstance(data,dict) or data.get('schema_version')!=2:
            raise ValueError('数值记录须为schema_version=2对象')
        entries,exemptions=data.get('entries'),data.get('exemptions')
        if not isinstance(entries,list) or not isinstance(exemptions,list):
            raise ValueError('entries/exemptions须为数组')
        assigned=set();ids=set()
        for entry in entries:
            try:
                if not isinstance(entry,dict):raise ValueError('数值条目须为对象')
                key=location_key(entry.get('location'))
                if key in assigned:raise ValueError('同一数值位置重复登记')
                assigned.add(key)
                if key not in actual:raise ValueError('数值位置已过期或未扫描到: '+str(key))
                if entry.get('id') in ids:raise ValueError('重复数值ID')
                ids.add(entry.get('id'))
                value=source_value(root,entry)
                displayed=decimal_token(key[2])
                if not displayed.is_finite():raise ValueError('显示值非有限值')
                # 明确采用十进制ROUND_HALF_UP，避免浮点误差；不同规则须保存对应显示分析输出。
                quantum=Decimal(1).scaleb(displayed.as_tuple().exponent)
                with localcontext() as ctx:
                    ctx.prec=max(50,len(value.as_tuple().digits)+abs(value.as_tuple().exponent)+20)
                    if value.quantize(quantum,rounding=ROUND_HALF_UP)!=displayed:
                        raise ValueError('显示数值与该位置登记来源不一致')
                actual[key]=True
            except (ValueError,TypeError,KeyError,IndexError,OSError,InvalidOperation) as e:
                rep.fail('number_source_mismatch',[str(e)])
        for item in exemptions:
            try:
                if not isinstance(item,dict):raise ValueError('豁免须为对象')
                key=location_key(item.get('location'))
                if key in assigned:raise ValueError('同一数值位置重复登记/豁免')
                assigned.add(key)
                if key not in actual:raise ValueError('豁免位置过期或未扫描到')
                if item.get('category') not in {'definition','hyperparameter','structural'} or not isinstance(item.get('reason'),str) or not item['reason'].strip():
                    raise ValueError('非结果数值须有类别和具体理由；文献或实验结果不得豁免来源')
                actual[key]=True
            except (ValueError,TypeError) as e:
                rep.fail('number_exemption_invalid',[str(e)])
        for key,checked in actual.items():
            if not checked and key not in assigned:
                rep.unchecked('number_without_source',hit(key[0],key[1],key[2]+' 未关联来源或非结果说明'))
        if actual and all(actual.values()) and not any(x[0]=='FAIL' for x in rep.items):
            rep.pass_('number_locations','仅核数值位置、来源字段/校验值及声明换算；元数据含义、计算方法、图像与宏仍需核查')
        elif not actual:
            rep.skip('number_locations','所扫描文本未识别到数字；不覆盖宏展开和图像')
    except (OSError,ValueError,TypeError) as e:
        rep.fail('number_registry_invalid',[str(e)])
    return rep.emit()


if __name__=='__main__':sys.exit(main())
