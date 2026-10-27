#!/usr/bin/env python3
"""Optional Playwright UI/ZIP checks for both editors. No game is launched."""
from pathlib import Path
import json,zipfile,argparse,hashlib,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
def main():
 from playwright.sync_api import sync_playwright
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--browser',default=shutil.which('chromium'));args=ap.parse_args();out=ROOT/'artifacts/browser-ops';out.mkdir(parents=True,exist_ok=True);errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=args.browser);page=browser.new_page(accept_downloads=True);page.on('pageerror',lambda e:errors.append(str(e)))
  for mode,file in [('garden','index.html'),('graveyard','graveyard.html')]:
   page.goto((ROOT/file).as_uri());page.wait_for_function('binSources.size===5&&!binLoading');assert page.evaluate('OPS_CONFIG.id')==mode
   fixture=page.evaluate('''()=>{const p={format:'gw2-timepark-plan',version:1,mode:OPS_CONFIG.id,name:'UI smoke '+OPS_CONFIG.id,waves:{},enemyLimits:{},ops:{challenge:'vanilla',reward:{mode:'vanilla',weights:{silver:1,bag:1,gem:1,horde:0}}}};for(let w=1;w<=10;w++){const options=DATA.filter(g=>g.wave===w&&g.type!=='Служебная'),g=([5,10].includes(w)?options.find(g=>g.moneySlotCount===2):options.find(g=>g.type==='Обычная'))||options[0];p.waves[w]={groupGuid:g.guid,compositionGuid:'auto',assignments:{},ambush:false}}return p}''')
   # JSON editor is the actual application path, not direct state replacement.
   page.locator('#textPanel').evaluate('(e)=>e.open=true');page.locator('#planText').fill(json.dumps(fixture));page.locator('#textApply').click();assert 'применён' in page.locator('#textStatus').text_content()
   before=page.evaluate('JSON.stringify(plan)');bad=dict(fixture,mode='graveyard' if mode=='garden' else 'garden');page.locator('#planText').fill(json.dumps(bad));page.locator('#textApply').click();assert 'Не применено' in page.locator('#textStatus').text_content();assert page.evaluate('JSON.stringify(plan)')==before
   page.locator('#planText').fill('{ broken JSON');page.locator('#textApply').click();assert page.evaluate('JSON.stringify(plan)')==before
   page.locator('#textSnapshot').click();assert json.loads(page.locator('#planText').input_value())['mode']==mode
   # Existing controls: composition, point, limits, delay, shared settings.
   page.locator('[data-wave="1"]').click();comp=page.locator('#composition option').nth(1).get_attribute('value');page.locator('#composition').select_option(comp)
   page.locator('[data-assign]').first.select_option('A22');details=page.locator('.sub details').first;details.evaluate('(e)=>e.open=true');page.locator('[data-bound="min"]').first.fill('1');page.locator('[data-bound="min"]').first.dispatch_event('change');page.locator('[data-bound="max"]').first.fill('2');page.locator('[data-bound="max"]').first.dispatch_event('change');page.locator('#waveDelay').fill('0');page.locator('#waveDelay').dispatch_event('change')
   assert page.evaluate('Object.keys(plan.enemyLimits).length')==1
   page.locator('#rewardMode').select_option('custom');assert page.locator('#rewardWeights').is_visible();page.locator('#weightSilver').fill('4');page.locator('#weightSilver').dispatch_event('change');assert page.evaluate('plan.ops.reward.weights.silver')==4
   page.locator('#rewardMode').select_option('silver');assert not page.locator('#rewardWeights').is_visible();page.locator('#challengeMode').select_option('NoKnockouts')
   page.locator('#binOpen').click();page.locator('#binClear').click();assert page.evaluate('binSources.size')==0;page.locator('#binDefaults').click();page.wait_for_function('binSources.size===5&&!binLoading');page.locator('#binConsent').check()
   dest=out/mode;dest.mkdir(exist_ok=True)
   with page.expect_download() as event:page.locator('#binBuild').click()
   event.value.save_as(dest/'package.zip')
   with zipfile.ZipFile(dest/'package.zip') as z:
    assert z.testzip() is None;assert len(z.namelist())==8;z.extractall(dest)
    report=json.loads(z.read('build-report.json'));assert report['mode']==mode;assert len(report['files'])==5;assert report['shared']['challenge']=='NoKnockouts';assert report['shared']['rewardMode']=='silver';assert report['enemyLimitsApplied'];assert report['waves'][0]['delay']==0
    for name,row in report['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==row['sha256']
   subprocess.run([sys.executable,str(ROOT/'scripts/verify_generated.py'),str(dest)],check=True)
   page.reload();page.wait_for_function('binSources.size===5&&!binLoading');assert page.evaluate('plan.ops.challenge')=='NoKnockouts';assert page.evaluate('plan.ops.reward.mode')=='silver'
   if mode=='graveyard':assert page.evaluate("DATA.filter(g=>g.wave===1&&g.type!=='Служебная').every(g=>g.node!=='Wave00')")
   for width in [390,768,1440]:
    page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(mode,width)
  # Compatibility: historic Garden plan retains the three historical output hashes.
  page.goto((ROOT/'index.html').as_uri());page.wait_for_function('binSources.size===5&&!binLoading');legacy=json.loads((ROOT/'reference/builder-regression-plan.json').read_text());gold=json.loads((ROOT/'reference/builder-golden-hashes.json').read_text())['files'];digests=page.evaluate('''async p=>{const r=await binGenerate(validate(p),Object.fromEntries(binSources));return Object.fromEntries(await Promise.all(Object.entries(r.outputs).map(async([n,b])=>[n+'.bin',await binHash(b)])))}''',legacy)
  for name,digest in gold.items():assert digests[name]==digest,name
  assert not errors,errors;browser.close()
 print('PASS: both UI editors, JSON apply/reject, limits/delay/shared controls, 5-BIN download/CRC/hash/independent semantic checks, storage isolation, responsive widths, legacy Garden hashes. NOT a gameplay test.')
if __name__=='__main__':main()
