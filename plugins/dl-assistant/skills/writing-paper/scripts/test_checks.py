"""CLI回归：误判、来源错配、缺失材料、跨文件引用与汇总退出码。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parent


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.put('main.tex',r'\documentclass{article}'+'\n'+r'\begin{document}'+'\n'+r'\input{sections/results}'+'\n'+r'\end{document}'+'\n')
        self.put('sections/results.tex','Results are available.\n')
        self.json('_draft/venue-contract.json',{'mandatory_sections':[]})

    def put(self,name,text):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);return p

    def json(self,name,data):
        return self.put(name,json.dumps(data))

    def run_check(self,name,code,*args):
        p=subprocess.run([sys.executable,str(SCRIPTS/(name+'.py')),str(self.root),*args],capture_output=True,text=True)
        self.assertEqual(p.returncode,code,p.stdout+'\n'+p.stderr)
        return p.stdout

    def registry(self,token='87.3',source=87.31,line=1,location='sections/results.tex',**changes):
        p=self.json('data.json',{'score':source})
        self.put('conditions.md','Actual conditions and evidence limits.\n')
        e={'id':'n1','experiment_id':'exp-A','metric':'accuracy','condition_ref':'conditions.md','source':{'path':'data.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'json_pointer':'/score'},'location':{'path':location,'line':line,'token':token,'occurrence':1}}
        e.update(changes)
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[e],'exemptions':[]})
        return e

    def cite(self,text=r'Prior work \cite{a}.'):
        self.put('sections/results.tex',text+'\n')
        self.put('refs.bib','@article{a, title={Real title}, author={A}, year={2024}}\n')
        self.json('_draft/references.json',[{'cite_key':'a','claim':'Prior related work','section':'results'}])

    def test_honest_qualification_warns_without_blocking(self):
        self.put('sections/results.tex','The method achieves limited improvement and still lags behind the reference.\n')
        out=self.run_check('check_ai_tells',0)
        self.assertIn('[WARN]',out);self.assertNotIn('[FAIL]',out)

    def test_filler_is_suggestion(self):
        self.put('sections/results.tex','It is worth noting the observation.\n')
        self.assertIn('[WARN]',self.run_check('check_ai_tells',0))

    def test_number_specific_source_and_rounding(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n');self.registry()
        self.assertIn('[PASS] number_locations',self.run_check('check_numbers',0))

    def test_wrong_source_cannot_borrow_global_equal_number(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n');self.registry(source=12.0)
        self.assertIn('来源不一致',self.run_check('check_numbers',1))

    def test_source_modified_after_registration(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n');self.registry();self.json('data.json',{'score':88})
        self.assertIn('校验值不匹配',self.run_check('check_numbers',1))

    def test_missing_condition_record_fails(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n');self.registry(condition_ref='missing.md')
        self.assertIn('条件记录不可得',self.run_check('check_numbers',1))

    def test_unregistered_table_not_blessed_by_registry(self):
        self.put('sections/results.tex',r'\input{tables/results}'+'\n')
        self.put('tables/results.tex',r'\begin{tabular}{lc}'+'\n'+r'Ours & 999.9 \\'+'\n'+r'\end{tabular}'+'\n')
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[],'exemptions':[]})
        self.assertIn('999.9',self.run_check('check_numbers',3))

    def test_legacy_global_whitelist_is_unknown(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n')
        self.json('_draft/canonical-values.json',[{'value':87.3}])
        self.assertIn('legacy_number_registry',self.run_check('check_numbers',3))

    def test_caption_and_math_numbers_not_skipped(self):
        self.put('sections/results.tex',r'\begin{figure}\caption{Score is $87.3$.}\end{figure}'+'\n')
        self.registry();self.run_check('check_numbers',0)

    def test_percentage_explicit_conversion(self):
        self.put('sections/results.tex',r'Accuracy is 87.3\%.'+'\n');e=self.registry(token=r'87.3\%',source=.8731)
        e['source']['scale']=100
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[e],'exemptions':[]})
        self.run_check('check_numbers',0)

    def test_integer_results_require_source(self):
        self.put('sections/results.tex','The correct count is 17.\n')
        self.run_check('check_numbers',3)

    def test_non_result_numbers_require_specific_reason(self):
        self.put('sections/results.tex',r'Let $n=2$.'+'\n')
        item={'location':{'path':'sections/results.tex','line':1,'token':'2','occurrence':1},'category':'definition','reason':'Defines the dimension in this example.'}
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[],'exemptions':[item]})
        self.run_check('check_numbers',0)
        item['reason']=''
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[],'exemptions':[item]})
        self.run_check('check_numbers',1)

    def test_location_drift_is_error(self):
        self.put('sections/results.tex','\nAccuracy is 87.3.\n');self.registry()
        self.assertIn('过期',self.run_check('check_numbers',1))

    def test_repeated_same_value_needs_each_location(self):
        self.put('sections/results.tex','Scores are 87.3 and 87.3.\n');self.registry()
        self.run_check('check_numbers',3)

    def test_json_pointer_escaped_keys(self):
        self.put('sections/results.tex','Accuracy is 87.3.\n');e=self.registry()
        p=self.json('data.json',{'a/b':{'~x':[87.31]}})
        e['source'].update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),json_pointer='/a~1b/~0x/0')
        self.json('_draft/canonical-values.json',{'schema_version':2,'entries':[e],'exemptions':[]})
        self.run_check('check_numbers',0)

    def test_boolean_source_is_not_number(self):
        self.put('sections/results.tex','Score is 1.\n');self.registry(token='1',source=True)
        self.run_check('check_numbers',1)

    def test_invalid_registry_is_error(self):
        self.put('_draft/canonical-values.json','{broken')
        self.run_check('check_numbers',1)

    def test_missing_bibliography_is_error(self):
        self.put('sections/results.tex',r'Prior work \cite{missing}.'+'\n')
        self.assertIn('cite_without_entry',self.run_check('check_citations',1))

    def test_missing_reference_registration_is_unknown(self):
        self.cite();(self.root/'_draft/references.json').unlink()
        self.run_check('check_citations',3)

    def test_custom_bib_and_two_optional_arguments(self):
        self.cite(r'Prior work \citep[see][Sec. 2]{a}.')
        (self.root/'refs.bib').rename(self.root/'literature.bib')
        with (self.root/'main.tex').open('a') as f:f.write(r'\bibliography{literature}'+'\n')
        self.run_check('check_citations',0)

    def test_every_citation_section_must_be_registered(self):
        self.cite()
        with (self.root/'main.tex').open('a') as f:f.write(r'\input{sections/discussion}'+'\n')
        self.put('sections/discussion.tex',r'Prior work \cite{a}.'+'\n')
        self.run_check('check_citations',1)
        self.json('_draft/references.json',[{'cite_key':'a','claim':'Prior work','section':['results','discussion']}])
        self.run_check('check_citations',0)

    def test_duplicate_bibliography_keys_fail(self):
        self.cite()
        with (self.root/'refs.bib').open('a') as f:f.write('@article{a,title={Duplicate}}\n')
        self.run_check('check_citations',1)

    def test_invalid_reference_json_fails(self):
        self.cite();self.put('_draft/references.json','not json')
        self.run_check('check_citations',1)

    def test_numeric_style_does_not_forbid_citet(self):
        self.cite(r'Prior work \citet{a}.')
        self.json('_draft/venue-contract.json',{'mandatory_sections':[],'citation_style':'numeric'})
        self.run_check('run_checks',0,'all')

    def test_empty_section_file_does_not_prove_required_section(self):
        self.put('sections/limitations.tex','')
        self.json('_draft/venue-contract.json',{'mandatory_sections':['limitations']})
        self.assertIn('mandatory_section_missing',self.run_check('run_checks',1,'all'))

    def test_contract_parse_error_is_not_skip_success(self):
        self.put('_draft/venue-contract.json','{broken')
        self.run_check('run_checks',1,'all')

    def test_missing_contract_is_incomplete(self):
        (self.root/'_draft/venue-contract.json').unlink()
        out=self.run_check('run_checks',3,'all');self.assertNotIn('全绿',out)

    def test_no_target_venue_can_be_explicit(self):
        self.json('_draft/venue-contract.json',{'applicability':'not_applicable','reason':'No target venue chosen for this draft.'})
        self.run_check('run_checks',0,'all')

    def test_nested_include_and_cycle(self):
        self.put('sections/results.tex',r'\input{parts/inner}'+'\n')
        self.put('parts/inner.tex',r'See \ref{deep}.\label{deep}\input{sections/results}'+'\n')
        self.run_check('check_labels',0)

    def test_unknown_mode_is_usage_error(self):
        self.run_check('run_checks',2,'unknown')


    def test_leading_decimal_and_scientific_value(self):
        self.put('sections/results.tex','Score is .5.\n');self.registry(token='.5',source=.5)
        self.run_check('check_numbers',0)
        self.put('sections/results.tex','Score is 5e-1.\n');self.registry(token='5e-1',source=.5)
        self.run_check('check_numbers',0)

    def test_stale_main_config_cannot_silently_fallback(self):
        self.json('_draft/config.json',{'main_tex':'missing.tex'})
        self.run_check('run_checks',3,'all')

    def test_bad_config_is_incomplete(self):
        self.put('_draft/config.json','{broken')
        self.run_check('run_checks',3,'all')

    def test_duplicate_labels_are_error(self):
        self.put('sections/results.tex',r'\label{a}\label{a}'+'\n')
        self.run_check('check_labels',1)

    def test_external_figure_mention_is_suggestion(self):
        self.put('sections/results.tex','Figure 3 in prior work is relevant.\n')
        self.assertIn('[WARN] bare_number',self.run_check('check_labels',0))


if __name__=='__main__':unittest.main()
