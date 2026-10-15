import sys,json,copy,unittest,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from model import ROOT,load,derived,shape,cut,bounds
from drafting import inputs,variant_spec,seam_manifest,native,INSTANCES
from cad_bridge import validate
class PipelineTests(unittest.TestCase):
 def test_variant_widths_and_baseline(self):
  s=load();w,vs=inputs(ROOT)
  for vid,width in [('baseline',34),('ease-00',32),('ease-05',30.3),('ease-10',28.6)]:
   d=derived(variant_spec(s,w,vs[vid]));self.assertAlmostEqual(d['body_w'],width);self.assertEqual(d['band_w'],d['body_w']);self.assertEqual(d['back_h'],11)
  self.assertEqual(s['parts']['1']['width'],34)
 def test_width_change_propagates(self):
  s=load();w,vs=inputs(ROOT);w['band_center_circumference']['value']=36
  q=variant_spec(s,w,vs['ease-05']);m=seam_manifest(q,'trial');self.assertAlmostEqual(derived(q)['circ'],34.2)
  self.assertAlmostEqual(m['seams'][2]['lengths_in'][1],32.2)
 def test_cad_six_and_free_edges(self):
  s=load();e=ET.fromstring(native(s,'test'));self.assertEqual(len(e.findall('.//piece')),6)
  m=seam_manifest(s,'test');self.assertEqual(m['seams'][0]['free_edges'],['insertion','flange']);self.assertEqual(m['seams'][1]['free_edges'],['insertion','flange'])
 def test_actual_cad_exports(self):
  r=validate(ROOT)
  for v in r['variants'].values():self.assertLessEqual(max(v['errors_mm'].values()),.5)
 def test_allowance_fold(self):
  d=derived(load());self.assertEqual((d['band_cut_w'],d['band_cut_h']),(34.5,4.5));self.assertEqual(d['band_cut_h']/2-d['sa'],2)
 def test_cutout_material_dependency(self):
  s=load();s['parts']['2a']['notch_width']=2.25;m=seam_manifest(s,'test');self.assertEqual(len(m['part_instances']),6)
  self.assertNotEqual(shape(s,'2a'),shape(load(),'2a'));self.assertNotEqual(shape(s,'2b'),shape(load(),'2b'))
 def test_no_physical_promotion(self):
  s=load();self.assertTrue(all(v['status']!='physically verified' for v in s['physical_checks'].values()))
  m=json.loads((ROOT/'3d-rendering/source/materials.json').read_text());self.assertFalse(m['physical_verified']);self.assertIsNone(m['physical_results'])
