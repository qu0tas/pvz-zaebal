from pathlib import Path
import json,struct,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
import argparse
ap=argparse.ArgumentParser(description='Regenerate exact-baseline EBX offset metadata from local original exports.')
ap.add_argument('folder',type=Path,nargs='?',default=ROOT/'local-game-files')
ap.add_argument('--check',action='store_true')
args=ap.parse_args();root=ROOT
src=(ROOT/'scripts/ebx_inspect.py').read_text(encoding='utf-8').split("if __name__")[0]
src=src.replace("'objects':result}","'objects':result,'layout':{'fields':fs,'classes':cs,'objects':obs,'arrays':ars,'arraybase':so+sl+dl,'stringsbase':so,'stringslen':sl,'datalen':dl}}")
ns={};exec(src,ns);read=ns['read']
paths={n:args.folder/(n+'.bin') for n in ['AISpawnGrid','GardenOps_WaveTree','GardenOps_WaveLogic']}
manifest={Path(m['filename']).stem:m for m in json.loads((ROOT/'reference/game-originals-manifest.json').read_text()) if m['filename'].endswith('.bin')}
for name,p in paths.items():
 if not p.is_file():raise SystemExit('Missing original: '+str(p))
 if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest[name]['sha256']:raise SystemExit('Unsupported baseline: '+name)
loaded={n:read(p) for n,p in paths.items()}
def flat(l,ci):
 fs=l['fields'];c=l['classes'][ci];out=[]
 for f in fs[c[1]:c[1]+c[2]]:out.extend(flat(l,f[2])) if f[1]==0 else out.append(f)
 return out

def array(n,i,name):
 r=loaded[n];l=r['layout'];b=paths[n].read_bytes();f=next(f for f in flat(l,l['objects'][i][0]) if f[0]==name);ix=struct.unpack_from('<I',b,l['objects'][i][2]+f[3])[0];off,count,cl=l['arrays'][ix];ng=struct.unpack_from('<I',b,12)[0];ni,ne,nu,nc,nf,tn=struct.unpack_from('<6H',b,16);meta=(64+ng*32+tn+nf*16+nc*16+ni*4+15)//16*16
 ac=l['classes'][f[2]];et=l['fields'][ac[1]];ec=et[2];stride=l['classes'][ec][4] if et[1]==2 else {3:4,7:4,8:4,15:4,16:4,19:4,10:1}[et[1]]
 return {'index':ix,'meta':meta+ix*12,'offset':l['arraybase']+off,'count':count,'class':cl,'stride':stride,'elementClass':ec}
def field(n,i,name):
 r=loaded[n];l=r['layout'];f=next(f for f in flat(l,l['objects'][i][0]) if f[0]==name)
 return {'offset':l['objects'][i][2]+f[3],'type':f[1],'value':r['objects'][i]['fields'][name]}
def h(s):
 v=5381
 for c in s:v=((v*33)^ord(c))&0xffffffff
 return v
spec={'format':'gw2-timepark-bin-schema','version':1,'files':{},'warning':'Exact-baseline EBX patcher, not runtime-verified. No game resource payload is embedded.'}
for n,p in paths.items():spec['files'][n]={'filename':n+'.bin','size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'magic':0x0fb2d1ce}
r=loaded['AISpawnGrid'];l=r['layout'];bf=paths['AISpawnGrid'].read_bytes();iface=r['objects'][0]['fields']['Interface']['index'];fa=array('AISpawnGrid',iface,'Fields');pa=array('AISpawnGrid',0,'PropertyConnections');points=json.load(open(root/'data/placements.json'));imports=r['imports'];registry=[]
for p in points:
 if not p['label'].startswith('A'):continue
 hits=[i for i,im in enumerate(imports) if im[1]==p['guid']];assert len(hits)==1
 registry.append({'id':p['label'],'guid':p['guid'],'importIndex':hits[0],'sourceField':h('TimePark_FixedPoint_'+p['label']),'spawnID':10000+int(p['label'][1:])})
spec['grid']={'stringsBase':l['stringsbase'],'stringsLength':l['stringslen'],'arrayBase':l['arraybase'],'dataLength':l['datalen'],'fields':fa,'properties':pa,'interfacePointer':iface+1,'targetField':0x93fc517f,'bindingFlags':17,'registry':registry}
r=loaded['GardenOps_WaveTree'];l=r['layout'];idx={o['guid']:i for i,o in enumerate(r['objects']) if o['guid']};cat=json.load(open(root/'data/catalog.json'));groups=[];subs={};comps={}
for g in cat:
 i=idx[g['guid']];a=array('GardenOps_WaveTree',i,'Waves');refs=r['objects'][i]['fields']['Waves'];groups.append({'guid':g['guid'],'wave':g['wave'],'node':g['node'],'startEvent':h('Start_'+g['node']),'array':a,'compositions':[{'guid':x['internal'],'pointer':x['index']+1} for x in refs]})
 for c in g['comps']:
  ci=idx[c['guid']];comps[c['guid']]={'subgroups':[s['guid'] for s in c['subs']]}
  for s in c['subs']:
   si=idx[s['guid']];subs[s['guid']]={'fields':{k:field('GardenOps_WaveTree',si,k) for k in ['UseSpecificSpawnID','MinSpawnDistanceFromBase','MaxSpawnDistanceFromBase','MinDistanceFromPlayer','MaxDistanceFromPlayer']},'numMain':array('GardenOps_WaveTree',si,'NumMainSpawnPoints'),'name':s['name']}
spec['tree']={'rootGroups':array('GardenOps_WaveTree',0,'WaveGroups'),'groups':groups,'compositions':comps,'subgroups':subs}
r=loaded['GardenOps_WaveLogic'];l=r['layout'];spawner=next(i for i,o in enumerate(r['objects']) if o['type']=='AIWaveSpawnEntityData');a=array('GardenOps_WaveLogic',0,'EventConnections');ec=a['elementClass'];ef=next(f for f in flat(l,ec) if f[0]=='TargetEvent');idf=next(f for f in flat(l,ef[2]) if f[0]=='Id');byhash={g['startEvent']:g for g in groups};routes=[]
for i,e in enumerate(r['objects'][0]['fields']['EventConnections']):
 if (e.get('Target') or {}).get('index')!=spawner:continue
 event=e['TargetEvent']['Id']&0xffffffff
 if event in byhash:routes.append({'offset':a['offset']+i*a['stride']+ef[3]+idf[3],'wave':byhash[event]['wave'],'original':event})
spec['logic']={'connections':a,'routes':routes}
output=json.dumps(spec,ensure_ascii=False,separators=(',',':'))+'\n'
target=root/'data/bin-schema.json'
if args.check:
 if target.read_text(encoding='utf-8')!=output:raise SystemExit('Schema is stale')
 print('PASS: schema matches local originals')
else:
 target.write_text(output,encoding='utf-8');print('Wrote',target)
