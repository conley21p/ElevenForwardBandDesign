#!/usr/bin/env python3
"""Read-only verification: regenerate in a temporary directory and compare."""
import json,hashlib,tempfile,sys,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from model import *
from build import build,read_all,source_hash

def physical_source_hash(root):
 facts={p:json.loads((root/p).read_text()) for p in ['design/design-spec.json','manual/source/steps.json','manual/source/references.json']}
 facts['design/design-spec.json'].pop('physical_checks',None)
 return digest(facts)

def review_guard(root,s):
 entries=[]
 for path in (root/'docs/changes').glob('*.json'):
  v=json.loads(path.read_text())
  if v.get('revision')==s['revision']:entries.append(v)
 assert len(entries)==1,'Need exactly one impact entry for current revision'
 e=entries[0]
 required=['request','question','answer','direct_parts','dependent_parts','operations','outputs','invalidated_checks','decisions','status','verification']
 assert all(e.get(k) for k in required),'Incomplete change-impact record'
 assert e.get('reviewed_source_hash')==source_hash(root),'Unreviewed source change: evaluate dependent parts/operations and update impact record'
 assert e.get('unresolved_updates')==[] and e['status']=='complete','Dependent updates unresolved'
 for k in e['direct_parts']+e['dependent_parts']:assert k in s['parts'],'Impact refers to unknown part'
 assert all(k in s['operations'] for k in e['operations'])
 assert set(e['invalidated_checks'])==set(s['physical_checks']),'Impact review must address every physical check'
 for k,v in s['physical_checks'].items():
  if v['status']=='physically verified':
   assert v['evidence'].get('source_hash')==physical_source_hash(root),f'Stale manual/setup evidence for {k}'
   record=root/v['evidence']['record'];assert record.is_file(),f'Missing physical record: {record}'
 return e

def verify(root=ROOT):
 root=Path(root);s,steps,refs=read_all(root);review_guard(root,s)
 manifest=json.loads((root/'design/generated-manifest.json').read_text())
 assert manifest['source_hash']==source_hash(root),'Generated manifest is stale'
 assert manifest['revision']==s['revision'],'Layout/manual revision mismatch'
 with tempfile.TemporaryDirectory() as td:
  expected=build(root,Path(td))
  for rel,data in expected.items():
   actual=root/rel
   assert actual.exists(),f'Missing generated output: {rel}'
   assert actual.read_bytes()==data,f'Stale or directly edited output: {rel}; reconcile source and rebuild'
  current={str(p.relative_to(root)) for p in (root/'manual/pages').glob('*.svg')}
  wanted={p for p in expected if p.startswith('manual/pages/')}
  assert current==wanted,'Stale or extra manual SVG pages'
 pages=json.loads((root/'manual/page-manifest.json').read_text())['pages']
 assert len(pages)==31
 for page in pages:
  file=root/'manual'/page['file'];doc=ET.parse(file)
  assert doc.getroot().get('data-design-revision')==s['revision']
  for node in doc.iter():
   url=node.get('href')
   if url:assert (file.parent/url).exists(),f'Broken page link: {url}'
 pdf=PdfReader(root/'manual/assembly-manual.pdf')
 assert len(pdf.pages)==len(pages) and len(pdf.outline)==len(pages),'PDF pages/bookmarks mismatch'
 assert all(abs(float(p.mediabox.width)-792)<.1 and abs(float(p.mediabox.height)-612)<.1 for p in pdf.pages)
 text='\n'.join(p.extract_text() or '' for p in pdf.pages)
 assert s['revision'] in text and 'STEP 20' in text
 assert all(v['status']!='physically verified' or v.get('evidence') for v in s['physical_checks'].values())
 from cad_bridge import validate as check_cad
 check_cad(root)
 from pipeline_verify import verify_pipeline
 verify_pipeline(root)
 print('PASS: source review, deterministic outputs, 31 SVG pages, 31 PDF bookmarks, geometry and evidence status.')
 return True
if __name__=='__main__':
 try:verify()
 except (AssertionError,ValueError,KeyError) as e:print('FAIL:',e);sys.exit(1)
