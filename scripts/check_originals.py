#!/usr/bin/env python3
"""Compare local exports to the historical manifest without reading them into Git."""
from pathlib import Path
import argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path,nargs='?',default=ROOT/'local-game-files');a=p.parse_args();manifest=json.loads((ROOT/'reference/game-originals-manifest.json').read_text(encoding='utf-8'));matched=missing=different=0
 for item in manifest:
  path=a.folder/item['filename']
  if not path.exists():print('MISSING',item['filename']);missing+=1;continue
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest==item.get('sha256'):print('MATCH',item['filename']);matched+=1
  else:print('DIFFERENT',item['filename'],'(may be another game/export version)');different+=1
 print(f'Matched {matched}; missing {missing}; different {different}. No files changed.')
 # Diagnostic inventory, not a claim that missing files invalidate the website.
 return 1 if different else 0
if __name__=='__main__':raise SystemExit(main())
