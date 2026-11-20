"""CLI回归：工具失败、计数口径、日志身份、metadata及有限观察边界。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('submission_check.py')
WRAPPER=Path(__file__).with_name('submission-check.sh')


def minimal_pdf():
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    stream=b'BT /F1 12 Tf 20 240 Td (Fixture) Tj ET\n';objects.append(b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'endstream')
    data=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):offsets.append(len(data));data+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(data);data+=f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    for offset in offsets[1:]:data+=f'{offset:010d} 00000 n \n'.encode()
    return data+f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()


class Observations(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.bin=self.root/'bin';self.bin.mkdir()
        self.pdf=self.root/'paper.pdf';self.pdf.write_bytes(b'Synthetic tool fixture, not a real paper')
        self.log=self.root/'output.log';self.log.write_text('This is pdfTeX\nOutput written on paper.pdf (10 pages, 100 bytes).\n')
        self.stub('pdfinfo','Pages: 10\nAuthor: Alex Texley: Example Lab\nTitle: Fixture title\nCreator: pdfTeX\nProducer: Example\n')
        self.stub('pdffonts','name type encoding emb sub uni object ID\n----\nFixture Type 1 Custom yes yes no 1 0\n')
        self.env={**os.environ,'PATH':str(self.bin)}

    def stub(self,name,out,code=0):
        p=self.bin/name;p.write_text('#!/bin/sh\nprintf %s '+"'"+out.replace("'","'\\''")+"'\nexit "+str(code)+'\n');p.chmod(0o755)

    def invoke(self,*args,code=0,real=False):
        p=subprocess.run([sys.executable,str(SCRIPT),*map(str,args),'--format','json'],capture_output=True,text=True,env=None if real else self.env)
        self.assertEqual(p.returncode,code,p.stdout+'\n'+p.stderr)
        return json.loads(p.stdout) if code!=2 else p

    def pdfcheck(self,*args,code=0):return self.invoke('--pdf',self.pdf,*args,code=code)

    def bind(self):
        p=self.root/'build.json';p.write_text(json.dumps({'pdf_sha256':hashlib.sha256(self.pdf.read_bytes()).hexdigest(),'log_sha256':hashlib.sha256(self.log.read_bytes()).hexdigest(),'exit_code':0}));return p

    def test_default_only_observes_and_does_not_claim_compliance(self):
        r=self.pdfcheck();self.assertEqual(r['requested_checks'],['pages','fonts','metadata']);self.assertTrue(all(x['status']=='observed' for x in r['results']))

    def test_pdfinfo_failure_not_clean_metadata_or_pages(self):
        self.stub('pdfinfo','',1);r=self.pdfcheck('--checks','pages,metadata',code=1);self.assertTrue(all(x['status']=='error' for x in r['results']))

    def test_pdffonts_failure_not_all_embedded(self):
        self.stub('pdffonts','',1);self.assertEqual(self.pdfcheck('--checks','fonts',code=1)['results'][0]['status'],'error')

    def test_empty_font_output_is_unverified(self):
        self.stub('pdffonts','');self.assertEqual(self.pdfcheck('--checks','fonts',code=3)['results'][0]['status'],'unverified')

    def test_header_without_fonts_is_only_observation(self):
        self.stub('pdffonts','name type encoding emb sub uni object ID\n-----\n');r=self.pdfcheck('--checks','fonts');self.assertEqual(r['results'][0]['fonts'],[]);self.assertEqual(r['results'][0]['status'],'observed')

    def test_malformed_font_row_not_silently_passed(self):
        self.stub('pdffonts','name type encoding emb sub uni object ID\n----\nunrecognized row\n');self.pdfcheck('--checks','fonts',code=3)

    def test_unembedded_font_without_rule_is_observation(self):
        self.stub('pdffonts','name type encoding emb sub uni object ID\n----\nFixture Type 1 Custom no no no 1 0\n');r=self.pdfcheck('--checks','fonts');self.assertEqual(r['results'][0]['unembedded'],['Fixture'])

    def test_declared_embedding_requirement_detects_local_violation(self):
        self.stub('pdffonts','name type encoding emb sub uni object ID\n----\nFixture Type 1 Custom no no no 1 0\n');self.pdfcheck('--checks','fonts','--require-embedded-fonts','--rule-ref','fixture-rule',code=1)

    def test_declared_embedding_requirement_needs_source(self):
        self.pdfcheck('--checks','fonts','--require-embedded-fonts',code=3)

    def test_tex_substring_does_not_hide_author(self):
        r=self.pdfcheck('--checks','metadata','--double-blind',code=3);self.assertEqual(r['results'][0]['fields']['Author'],'Alex Texley: Example Lab')

    def test_camera_ready_empty_author_not_automatic_violation(self):
        self.stub('pdfinfo','Pages: 10\nAuthor:\nTitle: Anonymous communication study\n');r=self.pdfcheck('--checks','metadata','--camera-ready');self.assertEqual(r['results'][0]['status'],'observed')

    def test_stage_hint_does_not_override_declared_identity_review(self):
        r=self.pdfcheck('--checks','metadata','--camera-ready','--double-blind',code=3)
        self.assertEqual(r['results'][0]['stage_hint'],'camera-ready');self.assertTrue(r['results'][0]['identity_context_review_required'])

    def test_pages_over_limit_without_scope_not_assumed_violation(self):
        self.pdfcheck('--checks','pages','--page-limit','8','--rule-ref','fixture-rule',code=3)

    def test_total_counting_rule_requires_source(self):
        self.pdfcheck('--checks','pages','--page-limit','8','--page-scope','total',code=3)

    def test_total_limit_violation_has_nonzero_exit(self):
        r=self.pdfcheck('--checks','pages','--page-limit','8','--page-scope','total','--rule-ref','fixture-rule',code=1);self.assertEqual(r['results'][0]['judged_pages'],10)

    def test_main_count_needs_basis(self):
        self.pdfcheck('--checks','pages','--page-limit','8','--main-pages','8','--rule-ref','fixture-rule',code=3)

    def test_main_count_with_basis_compares_only_declared_rule(self):
        r=self.pdfcheck('--checks','pages','--page-limit','8','--main-pages','8','--main-pages-basis','fixture manually checked pages','--rule-ref','fixture-rule');self.assertEqual(r['results'][0]['status'],'meets_declared_rule')

    def test_main_count_above_total_rejected(self):
        self.pdfcheck('--checks','pages','--page-limit','100','--main-pages','99','--rule-ref','fixture-rule',code=1)

    def test_page_integer_validation(self):
        for value in ('-1','0','abc','2+2','1.5','1e2'):
            with self.subTest(value=value):self.pdfcheck('--checks','pages','--page-limit',value,code=2)

    def test_conflicting_page_scope_arguments(self):
        self.pdfcheck('--checks','pages','--page-scope','total','--main-pages','8',code=2)

    def test_empty_log_never_passes_reference_check(self):
        self.log.write_text('');self.invoke('--log',self.log,'--checks','references,labels',code=3)

    def test_missing_log_does_not_inherit_pdf_success(self):
        self.pdfcheck('--checks','references',code=3)

    def test_unbound_success_log_stays_unverified(self):
        self.invoke('--log',self.log,'--checks','references',code=3)

    def test_bound_success_log_has_limited_observation(self):
        r=self.pdfcheck('--log',self.log,'--checks','references,labels','--build-record',self.bind());self.assertTrue(all(x['status']=='observed' for x in r['results']))

    def test_log_pdf_identity_mismatch_rejected(self):
        p=self.bind();self.pdf.write_bytes(b'changed paper');self.pdfcheck('--log',self.log,'--checks','references','--build-record',p,code=1)

    def test_bound_undefined_reference_is_detected(self):
        self.log.write_text("This is pdfTeX\nLaTeX Warning: Reference `x' on page 1\n undefined on input line 3.\nOutput written on paper.pdf (10 pages, 100 bytes).\n")
        r=self.pdfcheck('--log',self.log,'--checks','references','--build-record',self.bind(),code=1);self.assertGreater(r['results'][0]['warning_count'],0)

    def test_unbound_warning_not_claimed_as_current_pdf_defect(self):
        self.log.write_text("This is pdfTeX\nLaTeX Warning: Reference `x' undefined.\nOutput written on paper.pdf (10 pages, 100 bytes).\n")
        r=self.pdfcheck('--log',self.log,'--checks','references',code=3);self.assertGreater(r['results'][0]['warning_count'],0);self.assertEqual(r['results'][0]['status'],'unverified')

    def test_bound_duplicate_label_is_detected(self):
        self.log.write_text("This is pdfTeX\nLaTeX Warning: Label `x' multiply defined.\nOutput written on paper.pdf (10 pages, 100 bytes).\n")
        self.pdfcheck('--log',self.log,'--checks','labels','--build-record',self.bind(),code=1)

    def test_failed_build_log_not_passed(self):
        self.log.write_text('This is pdfTeX\n! Emergency stop.\nNo pages of output.\n');self.invoke('--log',self.log,'--checks','references',code=1)

    def test_incomplete_log_is_unverified(self):
        self.log.write_text('This is pdfTeX\nworking...');self.invoke('--log',self.log,'--checks','references',code=3)

    def test_bad_build_record_not_ignored(self):
        p=self.root/'build.json';p.write_text('{broken');self.pdfcheck('--log',self.log,'--checks','references','--build-record',p,code=1)

    def test_false_is_not_successful_exit_code(self):
        p=self.bind();d=json.loads(p.read_text());d['exit_code']=False;p.write_text(json.dumps(d));self.pdfcheck('--log',self.log,'--checks','references','--build-record',p,code=1)

    def test_missing_tools_are_unverified(self):
        (self.bin/'pdfinfo').unlink();self.pdfcheck('--checks','pages',code=3)

    def test_invalid_page_output_not_success(self):
        self.stub('pdfinfo','Pages: unknown\nAuthor: Name\n');self.pdfcheck('--checks','pages,metadata',code=3)

    def test_missing_input_file_reports_error(self):
        self.pdf.unlink();self.pdfcheck('--checks','pages',code=1)

    def test_input_change_during_observation_invalidates_record(self):
        p=self.bin/'pdfinfo';p.write_text('#!/bin/sh\nprintf changed >> "$1"\nprintf "Pages: 10\\n"\n');p.chmod(0o755)
        r=self.pdfcheck('--checks','pages',code=1);self.assertEqual(r['results'][-1]['check'],'pdf_changed')

    def test_only_selected_tools_run(self):
        self.stub('pdffonts','must not be read',1);self.pdfcheck('--checks','pages')

    def test_unknown_checks_and_missing_flag_value(self):
        self.pdfcheck('--checks','unknown',code=2);self.invoke('--pdf',code=2)

    def test_legacy_wrapper_help(self):
        p=subprocess.run(['/bin/bash',str(WRAPPER),'--help'],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertIn('--checks',p.stdout)

    @unittest.skipUnless(shutil.which('pdfinfo') and shutil.which('pdffonts'),'真实Poppler不可用')
    def test_actual_poppler_valid_pdf_smoke(self):
        self.pdf.write_bytes(minimal_pdf());r=self.invoke('--pdf',self.pdf,'--checks','pages,fonts,metadata',real=True)
        self.assertEqual(r['results'][0]['total_pages'],1);self.assertEqual(r['results'][1]['status'],'observed')

    @unittest.skipUnless(shutil.which('pdfinfo') and shutil.which('pdffonts'),'真实Poppler不可用')
    def test_actual_poppler_invalid_pdf_not_false_pass(self):
        r=self.invoke('--pdf',self.pdf,'--checks','pages,fonts,metadata',real=True,code=1);self.assertTrue(all(x['status']=='error' for x in r['results']))


if __name__=='__main__':unittest.main()
