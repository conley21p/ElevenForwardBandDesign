import sys,copy,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'3d-rendering/scripts'))
from model import load,shape,cut,bounds
from allowances import expand

class RenderAllowanceTests(unittest.TestCase):
 def piece(self,k):
  s=load();pts=shape(s,k);verts=[(x,y,0) for x,y in pts]
  return s,expand(s,k,verts,[],[(x*.0254,y*.0254) for x,y in pts],list(range(len(pts))))
 def test_cut_envelopes_match_real_patterns(self):
  for k in ['1','2a','2b','3','4']:
   s,r=self.piece(k)
   self.assertTrue(r['ring'])
   self.assertLess(max(abs(a-b) for a,b in zip(bounds([v[:2] for v in r['verts']]),bounds(cut(s,k))))*25.4,.5)
 def test_free_flange_edges_do_not_gain_an_allowance(self):
  for k in ['2a','2b']:
   _,r=self.piece(k);self.assertLess(len(r['ring']),r['base_count']);self.assertGreater(len(r['ring']),0)
   for face in r['faces']:
    area2=abs(sum(r['verts'][a][0]*r['verts'][b][1]-r['verts'][a][1]*r['verts'][b][0] for a,b in zip(face,face[1:]+face[:1])))
    self.assertGreater(area2,1e-12)
 def test_band_and_insert_returns_preserve_join_direction(self):
  s,r=self.piece('3');i=r['ring'][0];self.assertAlmostEqual(r['turned'][i][0],s['seam_allowance']);self.assertLess(r['turned'][i][1],0)
  s,r=self.piece('4');i=r['ring'][0];self.assertLess(r['turned'][i][0],0);self.assertAlmostEqual(r['turned'][i][1],s['back_hem_allowance'])
 def test_unimplemented_finishing_change_fails(self):
  s=load();s['seam_finishing']['back_join']='toward_insert';pts=shape(s,'4')
  with self.assertRaisesRegex(AssertionError,'Finishing change'):
   expand(s,'4',[(x,y,0) for x,y in pts],[],pts,list(range(len(pts))))
 def test_subdivided_insert_uses_edge_specific_hem_allowance(self):
  s=load();s['back_hem_allowance']=.5;pts=[(0,0),(1,0),(2,0),(2,5.5),(2,11),(1,11),(0,11),(0,5.5)]
  r=expand(s,'4',[(x,y,0) for x,y in pts],[],pts,list(range(len(pts))))
  self.assertEqual(bounds([v[:2] for v in r['verts']]),bounds(cut(s,'4')))
