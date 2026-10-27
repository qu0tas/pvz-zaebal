import unittest,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));import build
class SiteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.layout=build.load('data/photo-layout.json');cls.old=build.load('reference/original-site/photo-layout.json');cls.placements=build.load('data/placements.json');cls.catalog=build.load('data/catalog.json')
 def test_counts(self):
  self.assertEqual(len(self.catalog),147);self.assertEqual(len(self.placements),60);self.assertEqual(sum(len(z['points']) for z in self.layout),40);self.assertEqual({z['id'] for z in self.layout},{'Egypt','Center','Rome','China'})
 def test_stable_point_identity(self):
  ps={p['label']:p for p in self.placements};seen=set()
  for z in self.layout:
   for p in z['points']:
    self.assertNotIn(p['id'],seen);seen.add(p['id']);self.assertEqual(p['guid'],ps[p['id']]['guid']);self.assertEqual(p['world'],{k:ps[p['id']][k] for k in ['x','y','z']})
 def test_backgrounds_unchanged(self):
  for a in build.load('reference/map-assets.json'):self.assertEqual(hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest(),a['sha256'])
 def test_confirmed_corrections(self):
  old={z['id']:{p['id']:p for p in z['points']} for z in self.old};now={z['id']:{p['id']:p for p in z['points']} for z in self.layout}
  def xy(p):return p['x'],p['y']
  for a,b in [('A10','A15'),('A55','A01'),('A54','A31'),('A47','A24'),('A12','A53'),('A30','A09'),('A18','A11')]:
   self.assertEqual(xy(now['Center'][a]),xy(old['Center'][b]));self.assertEqual(xy(now['Center'][b]),xy(old['Center'][a]))
  self.assertEqual(xy(now['Center']['A22']),xy(old['Center']['A22']))
  self.assertEqual(xy(now['Rome']['A02']),xy(old['Rome']['A49']));self.assertEqual(xy(now['Rome']['A49']),xy(old['Rome']['A02']));self.assertEqual(xy(now['Rome']['A34']),xy(old['Rome']['A34']))
  for k in ['x','y']:self.assertAlmostEqual(now['Rome']['A23'][k],{'x':0.3860085606575012,'y':0.6831969022750854}[k],places=7)
  for zone in ['Egypt','China']:
   for key,p in old[zone].items():self.assertEqual(xy(p),xy(now[zone][key]))
 def test_build_is_current(self):self.assertEqual((ROOT/'index.html').read_text(encoding='utf-8'),build.render())
 def test_source_has_versioned_export(self):
  app=(ROOT/'src/app.js').read_text(encoding='utf-8');self.assertIn('user-screenshots-rome-center-corrected-v3',app);self.assertIn('readyForFrosty=false',app)
 def test_bin_schema_profiles(self):
  schema=build.load('data/bin-schema.json');manifest={m['filename']:m for m in build.load('reference/game-originals-manifest.json')}
  self.assertEqual(set(schema['files']),{'AISpawnGrid','GardenOps_WaveTree','GardenOps_WaveLogic'})
  for f in schema['files'].values():self.assertEqual(f['sha256'],manifest[f['filename']]['sha256']);self.assertEqual(f['size'],manifest[f['filename']]['size'])
  self.assertEqual(len(schema['tree']['groups']),147);self.assertEqual(schema['logic']['connections']['count'],942)
 def test_no_shared_mutated_arrays(self):
  s=build.load('data/bin-schema.json');groups=[g['array']['index'] for g in s['tree']['groups']];main=[g['numMain']['index'] for g in s['tree']['subgroups'].values()];self.assertEqual(len(groups),len(set(groups)));self.assertEqual(len(main),len(set(main)))
 def test_builder_sources_embedded(self):
  html=(ROOT/'index.html').read_text(encoding='utf-8');self.assertIn('id="bin-schema"',html);self.assertIn('id="binInputs"',html);self.assertNotIn('__BIN_',html)
 def test_bundled_originals_allowlist(self):
  manifest=build.load('originals/manifest.json');allowed={ROOT/'originals'/r['filename'] for r in manifest};self.assertEqual(len(allowed),10)
  for r in manifest:
   b=(ROOT/'originals'/r['filename']).read_bytes();self.assertEqual(len(b),r['size']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
  for pattern in ['*.bin','*.xml']:self.assertTrue({p for p in ROOT.rglob(pattern) if not {'artifacts','_site'}.intersection(p.relative_to(ROOT).parts)}.issubset(allowed))
  for pattern in ['*.fbmod','*.fbproject']:self.assertFalse(list(ROOT.rglob(pattern)),pattern)
 def test_deployment_copies_originals(self):
  import tempfile,subprocess
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'index.html';subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),'--output',str(output)],check=True,capture_output=True)
   for row in build.load('originals/manifest.json'):self.assertEqual((Path(tmp)/'originals'/row['filename']).read_bytes(),(ROOT/'originals'/row['filename']).read_bytes())
 def test_embedded_baselines(self):
  import base64
  bundled=build.originals();schema=build.load('data/bin-schema.json');self.assertEqual(len(bundled),3)
  for key,text in bundled.items():self.assertEqual(hashlib.sha256(base64.b64decode(text)).hexdigest(),schema['files'][key]['sha256'])
if __name__=='__main__':unittest.main()
