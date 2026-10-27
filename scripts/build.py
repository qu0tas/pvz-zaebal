#!/usr/bin/env python3
"""Build a self-contained GitHub Pages site using Python's standard library."""
from pathlib import Path
import argparse,base64,json,sys
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def compact(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
def render():
 catalog=load('data/catalog.json');photos=load('data/photo-layout.json');placements={p['label']:p for p in load('data/placements.json')};seen=set()
 for z in photos:
  asset=(ROOT/z.pop('asset')).resolve()
  if not asset.is_relative_to(ROOT/'assets/maps'):raise ValueError('Map asset must be in assets/maps')
  z['image']='data:image/jpeg;base64,'+base64.b64encode(asset.read_bytes()).decode('ascii')
  for p in z['points']:
   if p['id'] in seen:raise ValueError('Duplicate point: '+p['id'])
   seen.add(p['id']);src=placements[p['id']]
   if p['guid']!=src['guid'] or p['world']!={k:src[k] for k in ['x','y','z']}:raise ValueError('GUID/world mismatch: '+p['id'])
   if not all(isinstance(p[k],(int,float)) and 0<=p[k]<=1 for k in ['x','y']):raise ValueError('Invalid photo position')
 app='const PHOTOS='+compact(photos)+';\n'+(ROOT/'src/app.js').read_text(encoding='utf-8')
 template=(ROOT/'src/template.html').read_text(encoding='utf-8')
 if template.count('__DATA__')!=1 or template.count('__APP__')!=1:raise ValueError('Invalid template placeholders')
 return template.replace('__DATA__',compact(catalog)).replace('__APP__',app).replace('__BIN_PANEL__',(ROOT/'src/bin-panel.html').read_text(encoding='utf-8')).replace('__BIN_SCHEMA__',compact(load('data/bin-schema.json'))).replace('__BIN_APP__',(ROOT/'src/bin-builder.js').read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'index.html');ap.add_argument('--check',action='store_true');args=ap.parse_args();html=render();output=args.output
 if args.check:
  if not output.exists() or output.read_text(encoding='utf-8')!=html:print('STALE: run python scripts/build.py');return 1
  print('PASS: generated HTML matches sources');return 0
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(html,encoding='utf-8');print('Built',output.name,len(html.encode('utf-8')),'bytes');return 0
if __name__=='__main__':sys.exit(main())
