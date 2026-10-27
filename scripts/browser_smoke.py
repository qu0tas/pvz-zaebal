#!/usr/bin/env python3
"""Optional Playwright smoke test; requires local originals, never run by public CI."""
from pathlib import Path
import argparse,json,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--originals',type=Path,required=True);ap.add_argument('--browser',default=shutil.which('chromium'));args=ap.parse_args()
 try:from playwright.sync_api import sync_playwright
 except ImportError:raise SystemExit('Optional dependency: install Python Playwright in your test environment first.')
 files=[args.originals/n for n in ['AISpawnGrid.bin','GardenOps_WaveTree.bin','GardenOps_WaveLogic.bin']]
 for p in files:
  if not p.is_file():raise SystemExit('Missing local original: '+str(p))
 fixture=json.loads((ROOT/'reference/builder-regression-plan.json').read_text());out=ROOT/'artifacts/browser-smoke';out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as pw:
  kwargs={'headless':True}
  if args.browser:kwargs['executable_path']=args.browser
  browser=pw.chromium.launch(**kwargs);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto((ROOT/'index.html').as_uri());page.locator('#binOpen').click();page.locator('#binInputs').set_input_files([str(p.resolve()) for p in files]);page.wait_for_function('binSources.size===3');page.evaluate('(p)=>{plan=validate(p);renderWave();renderMap()}',fixture);page.locator('#binConsent').check()
  with page.expect_download() as download:page.locator('#binBuild').click()
  download.value.save_as(out/'generated.zip');assert not errors,errors;browser.close()
 hashes=json.loads((ROOT/'reference/builder-golden-hashes.json').read_text())['files']
 with zipfile.ZipFile(out/'generated.zip') as z:
  assert z.testzip() is None;assert len(z.namelist())==6
  for name,digest in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
 print('PASS: browser ZIP CRC and three historical BIN hashes. This is NOT runtime proof.')
if __name__=='__main__':main()
