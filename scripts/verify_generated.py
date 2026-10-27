#!/usr/bin/env python3
"""Independent semantic comparison of a generated 5-BIN package, using the EBX diagnostic reader."""
from pathlib import Path
import argparse,json,copy,struct
from ebx_inspect import read
ROOT=Path(__file__).resolve().parents[1]
def signed(v):return v if v<2**31 else v-2**32
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);args=ap.parse_args();folder=args.folder
 reportpath=folder/'build-report.json'
 if not reportpath.exists():reportpath=folder/'report.json'
 report=json.loads(reportpath.read_text());mode=report['mode'];s=json.loads((ROOT/f'data/{mode}-profile.json').read_text());original={name:read(ROOT/'originals'/(name+'.bin')) for name in s['files']};actual={name:read(folder/(name+'.bin')) for name in s['files']}
 # Tree: only composition pointers, chosen IDs/distances, delays and explicit min/max.
 tn=s['treeFile'];expected=copy.deepcopy(original[tn]);idx={o['guid']:i for i,o in enumerate(expected['objects']) if o['guid']}
 for w in report['waves']:
  o=expected['objects'][idx[w['groupGuid']]]['fields'];o['StartDelayTime']=f32(w['delay'])
  if w['composition']!='auto':o['Waves']=[x for x in o['Waves'] if x['internal']==w['composition']];assert len(o['Waves'])==1
 for entry in report['assignments']:
  if entry['point']=='auto':continue
  f=expected['objects'][idx[entry['guid']]]['fields'];f.update(UseSpecificSpawnID=entry['spawnID'],MinSpawnDistanceFromBase=0.0,MaxSpawnDistanceFromBase=10000.0,MinDistanceFromPlayer=0.0,MaxDistanceFromPlayer=10000.0);f['NumMainSpawnPoints']=[1]*len(f['NumMainSpawnPoints'])
 for guid,entries in report['enemyLimitsApplied'].items():
  for key,v in entries.items():expected['objects'][idx[guid]]['fields']['WaveSpawnTypeSet'][int(key)].update(MinSpawnLimit=v['min'],MaxSpawnLimit=v['max'])
 assert actual[tn]==expected,'Unexpected semantic tree change'
 # Logic: compare every connection and every object, not only requested routes.
 ln=s['logicFile'];expected=copy.deepcopy(original[ln]);a=s['logic']['connections'];wavegroups={w['wave']:next(g for g in s['tree']['groups'] if g['guid']==w['groupGuid']) for w in report['waves']};te=(next(iter(s['logic']['routes']))['offset']-a['offset'])%a['stride']
 for route in s['logic']['routes']:
  if route['wave'] not in wavegroups:continue
  i=(route['offset']-a['offset']-te)//a['stride'];expected['objects'][0]['fields']['EventConnections'][i]['TargetEvent']['Id']=signed(wavegroups[route['wave']]['startEvent'])
 assert actual[ln]==expected,'Unexpected semantic WaveLogic change'
 # Selector lifecycle and all other objects remain unchanged.
 name='CoOps_ChallengeSelector';expected=copy.deepcopy(original[name]);a=s['shared']['challenge']['connections'];choice=report['shared']['challenge']
 if choice!='vanilla':
  c=s['shared']['challenge']['choices'][choice];target={'internal':expected['objects'][c['target']-1]['guid'],'index':c['target']-1}
  for row in s['shared']['challenge']['routes']:
   i=(row['targetOffset']-a['offset'])//a['stride'];e=expected['objects'][0]['fields']['EventConnections'][i];e['Target']=target;e['TargetEvent']['Id']=signed(c['event'])
 assert actual[name]==expected,'Unexpected selector lifecycle/object change'
 # Rewards: only two UniformDistribution flags and their weight arrays.
 name='CoOps_SlotMachine_RewardSpin';expected=copy.deepcopy(original[name])
 for row,dist in zip(s['shared']['reward']['selectors'],report['shared']['distributions']):
  f=expected['objects'][row['object']]['fields'];f['UniformDistribution']=False;f['RandomEventWeight']=[f32(v) for v in dist['weights']]
 assert actual[name]==expected,'Unexpected reward event or property change'
 # Grid: originals/imports preserved; expected interface/property suffix only.
 name='AISpawnGrid';a=original[name];b=actual[name];assert a['imports']==b['imports'];assert len(a['objects'])==len(b['objects']);iface=a['objects'][0]['fields']['Interface']['index'];expected=copy.deepcopy(a)
 sf=a['objects'][iface]['fields']['Fields'];sp=a['objects'][0]['fields']['PropertyConnections'];nf=b['objects'][iface]['fields']['Fields'];np=b['objects'][0]['fields']['PropertyConnections'];points=report['registeredPoints'];assert nf[:len(sf)]==sf and np[:len(sp)]==sp;assert len(nf)==len(sf)+len(points) and len(np)==len(sp)+len(points)
 for k,id in enumerate(points):
  reg=next(p for p in s['grid']['registry'] if p['id']==id);field=nf[len(sf)+k];prop=np[len(sp)+k];assert field['Value']=='Int32 '+str(reg['spawnID']) and field['Id']&0xffffffff==reg['sourceField'];assert prop['Target']['external'][1]==reg['guid'] and prop['TargetFieldId']&0xffffffff==s['grid']['targetField'] and prop['Flags']==17
 expected['objects'][iface]['fields']['Fields']=nf;expected['objects'][0]['fields']['PropertyConnections']=np;assert b==expected,'Unexpected grid semantic change'
 print('PASS:',mode,'all five BIN semantic diffs match the requested changes. NOT runtime proof.')
if __name__=='__main__':main()
