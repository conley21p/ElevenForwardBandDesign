import sys,json,tempfile,shutil,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from model import *
from build import source_hash,build
from verify import verify,review_guard

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for path in ['design/design-spec.json','manual/source/steps.json','manual/source/references.json','docs/changes/R2.json']:
   dest=self.root/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
  shutil.copytree(ROOT/'scripts',self.root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
  shutil.copyfile(ROOT/'requirements.txt',self.root/'requirements.txt')
  self.s=load(self.root)
 def tearDown(self):self.tmp.cleanup()
 def write(self): (self.root/'design/design-spec.json').write_text(json.dumps(self.s))
 def reject(self):
  self.write()
  with self.assertRaisesRegex(AssertionError,'Unreviewed source change'):review_guard(self.root,self.s)
 def test_01_height_requires_review(self):
  self.s['parts']['1']['max_height']=11;self.reject();self.assertEqual(derived(self.s)['extra'],2)
 def test_02_material_requires_review(self):
  self.s['materials']['band']['name']='Test replacement material';self.reject()
 def test_03_insert_width_requires_review(self):
  self.s['parts']['4']['width']=3;self.reject();self.assertEqual(derived(self.s)['circ'],37)
 def test_04_cutout_requires_review(self):
  self.s['parts']['2a']['notch_width']=2.5;self.reject();self.assertNotEqual(shape(self.s,'2a'),shape(load(),'2a'))
 def test_05_quantity_requires_review_and_count(self):
  self.s['parts']['3']['qty']=1;self.reject()
  with self.assertRaisesRegex(AssertionError,'Textile count'):validate(self.s,json.loads((ROOT/'manual/source/steps.json').read_text()))
 def test_06_thread_operation_requires_review(self):
  self.s['operations']['JOIN']['stitch']='changed stitch';self.reject()
 def test_07_direct_svg_edit_rejected(self):
  build(self.root,self.root)
  p=self.root/'design/ostomy-band-scaled-layout.svg';p.write_bytes(p.read_bytes()+b'\n<!-- unreviewed -->')
  with self.assertRaisesRegex(AssertionError,'directly edited'):verify(self.root)
 def test_08_physical_evidence_required(self):
  self.s['physical_checks']['pouch_depth']['status']='physically verified'
  with self.assertRaisesRegex(AssertionError,'Missing evidence'):validate(self.s,json.loads((ROOT/'manual/source/steps.json').read_text()))
 def test_09_back_height_and_open_band_cut(self):
  d=derived(self.s);self.assertEqual(d['back_h'],11);self.assertEqual(d['back_cut_h'],11.5);self.assertEqual(d['band_cut_w'],34.5);self.assertEqual(d['band_cut_h'],4.5)
 def test_10_offsets_and_orientation(self):
  b=bounds(cut(self.s,'4'));self.assertAlmostEqual(b[2]-b[0],2.5);self.assertAlmostEqual(b[3]-b[1],11.5)
  lo=shape(self.s,'2a');hi=shape(self.s,'2b');self.assertEqual(hi,[(x,3-y) for x,y in reversed(lo)])
  self.assertAlmostEqual(bounds(shape(self.s,'1'))[3],10);self.assertGreater(derived(self.s)['edge_length'],34)
 def test_11_approved_change_regenerates_both(self):
  self.s['parts']['1']['max_height']=11;self.write()
  impact=json.loads((self.root/'docs/changes/R2.json').read_text());impact['reviewed_source_hash']=source_hash(self.root);(self.root/'docs/changes/R2.json').write_text(json.dumps(impact))
  build(self.root,self.root);verify(self.root)
  self.assertIn('11 in max',(self.root/'design/ostomy-band-scaled-layout.svg').read_text())
  self.assertIn('11 max',(self.root/'docs/DESIGN_SPEC.md').read_text())
if __name__=='__main__':unittest.main()
