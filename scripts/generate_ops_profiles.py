#!/usr/bin/env python3
"""Generate exact-baseline profiles/catalog from the owner's supplied originals. No network."""
from pathlib import Path
import json,struct,hashlib,re,xml.etree.ElementTree as E,argparse
ROOT=Path(__file__).resolve().parents[1]
def jsave(path,data):return json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
def h(s):
 v=5381
 for c in s:v=((v*33)^ord(c))&0xffffffff
 return v
ns={};src=(ROOT/'scripts/ebx_inspect.py').read_text().split('if __name__')[0].replace("'objects':result}","'objects':result,'layout':{'fields':fs,'classes':cs,'objects':obs,'arrays':ars,'arraybase':so+sl+dl,'stringsbase':so,'stringslen':sl,'datalen':dl}}")
exec(src,ns)
class Resource:
 def __init__(self,name):
  self.name=name;self.path=ROOT/'originals'/(name+'.bin');self.b=self.path.read_bytes();self.r=ns['read'](self.path);self.l=self.r['layout'];self.idx={o['guid']:i for i,o in enumerate(self.r['objects']) if o['guid']}
 def flat(self,ci):
  l=self.l;c=l['classes'][ci];out=[]
  for f in l['fields'][c[1]:c[1]+c[2]]:out.extend(self.flat(f[2])) if f[1]==0 else out.append(f)
  return out
 def fd(self,ci,name):return next(f for f in self.flat(ci) if f[0]==name)
 def field(self,i,name):
  f=self.fd(self.l['objects'][i][0],name);return {'offset':self.l['objects'][i][2]+f[3],'type':f[1],'value':self.r['objects'][i]['fields'][name]}
 def array(self,i,name):
  l=self.l;b=self.b;f=self.fd(l['objects'][i][0],name);ix=struct.unpack_from('<I',b,l['objects'][i][2]+f[3])[0];off,count,cl=l['arrays'][ix];ng=struct.unpack_from('<I',b,12)[0];ni,ne,nu,nc,nf,tn=struct.unpack_from('<6H',b,16);meta=(64+ng*32+tn+nf*16+nc*16+ni*4+15)//16*16;ac=l['classes'][f[2]];et=l['fields'][ac[1]];ec=et[2];stride=l['classes'][ec][4] if et[1]==2 else {3:4,7:4,8:4,15:4,16:4,19:4,10:1}[et[1]]
  return {'index':ix,'meta':meta+ix*12,'offset':l['arraybase']+off,'count':count,'class':cl,'stride':stride,'elementClass':ec}
 def profile(self):return {'filename':self.name+'.bin','size':len(self.b),'sha256':hashlib.sha256(self.b).hexdigest(),'magic':0x0fb2d1ce}
 def event_layout(self):
  a=self.array(0,'EventConnections');c=a['elementClass'];t=self.fd(c,'Target');te=self.fd(c,'TargetEvent');id=self.fd(te[2],'Id');return a,t[3],te[3]+id[3]
def text(x,n,default=''):return x.findtext(n,default) or default
def members(x,n):return [m.text for m in x.find(n)] if x.find(n) is not None else []
def plant_catalog():
 root=E.fromstring('<Export>'+(ROOT/'originals/GraveyardOps_WaveTree.xml').read_text()+'</Export>');by={o.get('Guid'):o for o in root};resolve=lambda ref:by[ref.split()[-1]]
 names={'Weed':'Сорняк','Dandelion':'Одуванчик','PeaShooter':'Горохострел','Peashooter':'Горохострел','Chomper':'Зубастик','Sunflower':'Подсолнух','Sunflowers':'Подсолнухи','Cactus':'Кактус','Rose':'Роза','Citron':'Цитрон','AssaultCorn':'Кукуруза','Hypnoshroom':'Гипногриб','RescueWarden':'Страж задания Rescue','Beetboxer':'Битбоксер','Torchwood':'Факел','GigaTorchwood':'Гига-факел','SuperBean':'Супербоб','Squash':'Кабачок','SunflowerQueen':'Королева подсолнухов','Marigold':'Бархатцы'}
 variants={'Fire':'огненный','Ice':'ледяной','Toxic':'токсичный','Power':'электрический','Electro':'электрический','Champion':'чемпион','AllVariants':'разные варианты','Flag':'с флагом','Pumpkin':'тыква','MetalVase':'металлическая ваза','OrganicShield':'щит','Vase':'ваза','Pot':'горшок','Rock':'каменный','Metal':'металлический','Vampire':'вампир','Mystic':'мистический'}
 icons={'gardenhorde':'Денежный / horde-символ','assorted':'Денежный символ','superbean':'Супербоб','torchwood':'Факел','gigatorch':'Гига-факел','sunflower':'Королева подсолнухов','ninjacarrot':'Битбоксер (ninjacarrot)'}
 specials={'Basic':'Обычная волна','Huge':'Большая волна','Gift':'Подарки','Tombstone':'Надгробия','TreasureYeti':'Сокровищная волна','Rescue':'Спасение','Bounty':'Охота за целью','Tank':'Танк','Race':'Гонка','Fetch':'Доставка','SW_Champs':'Чемпионы','SW_Melee':'Ближний бой','SW_Armor':'Броня','SW_Dandy':'Одуванчики','SW_Hypno':'Гипногрибы','SW_Pumpkins':'Тыквы','SW_Potheads':'Горшки','SW_Freeze':'Ледяные растения','SW_Fire':'Огненные растения','SW_Mystic':'Мистические растения','SW_Metal':'Металлические растения','SW_Toxic':'Токсичные растения','SW_Power':'Электрические растения','SW_Vampire':'Растения-вампиры','SW_FoodFight':'FoodFight','SW_Ambush':'Засада'}
 data=[]
 for ix,ref in enumerate(members(root[0],'WaveGroups')):
  g=resolve(ref);wave=int(text(g,'WaveNumber','0'),0);node=text(g,'NodeName');comps=[]
  for cr in members(g,'Waves'):
   c=resolve(cr);subs=[]
   for sr in members(c,'SubGroups'):
    s=resolve(sr);enemies=[]
    for member in list(s.find('WaveSpawnTypeSet')):
     e=member[0];ref=text(e,'WaveSpawnType');path=ref.split(' [')[0].replace('[Ebx] ','');raw=path.split('/')[-1];m=re.match(r'WSTP?_(\d+)_(.*)',raw);prefix,stem=m.groups() if m else ('?',raw);parts=stem.split('_');kind=parts.pop(0);quality=''
     if parts and parts[-1].lower() in ['hard','crazy']:quality=parts.pop().capitalize()
     name=names.get(kind,kind+' (внутреннее имя)')+(' · '+', '.join(variants.get(p,p) for p in parts) if parts else '')
     enemies.append(dict(name=name,raw=raw,path=path,set=prefix,quality=quality,category=path.split('/')[-2],guid=ref.split('[')[-1].rstrip(']'),min=int(text(e,'MinSpawnLimit','0'),0),max=int(text(e,'MaxSpawnLimit','0'),0)))
    subs.append(dict(name=text(s,'NodeName'),guid=s.get('Guid'),enemies=enemies,params={k:text(s,k) for k in ['SpawnChance','CompletePercentage','ActivationDelay','UseSpecificSpawnID','MinSpawnDistanceFromBase','MaxSpawnDistanceFromBase','MinDistanceFromPlayer','MaxDistanceFromPlayer']},arrays={k:members(s,k) for k in ['MaxTotalCount','MaxHordeCount','MaxHeroCount','MaxBossCount','SpawnPoolSize','NumMainSpawnPoints']},rewardEntries=len(members(s,'RewardInfos')),tombstoneEntries=len(members(s,'TombstoneInfos'))))
   comps.append(dict(name=text(c,'NodeName'),guid=c.get('Guid'),subs=subs,params={k:text(c,k) for k in ['RandomizeSubgroupOrder','IsContinuousSpawn','SpecialWavePercentage','IsHugeWave','IsEpicSpawnWave']}))
  slot=[text(g,'SlotIcon'+str(i)) for i in [1,2,3]];money=sum(v in ['gardenhorde','assorted'] for v in slot);suffix=re.sub(r'^Wave\d+-','',node)
  title=(' + '.join(icons.get(v,v) for v in slot) or node) if wave in [5,10] else specials.get(suffix,'Обычная волна · вариант '+suffix if suffix.isdigit() else suffix)
  typ='Боссовая' if wave in [5,10] else 'Служебная' if wave not in range(1,11) or node=='Wave00' else 'Специальная' if 'SW_' in suffix else 'Задание' if suffix in ['Gift','Tombstone','Rescue','Bounty','Tank','Race','Fetch'] or suffix.startswith('Quest_') else 'Обычная'
  data.append(dict(index=ix,wave=wave,node=node,guid=g.get('Guid'),type=typ,title=title,displayTitle=((('1 босс + 2 денежных слота' if money==2 else '2 босса + 1 денежный слот' if money==1 else 'Суперволна')+' · '+' + '.join(icons.get(v,v) for v in slot if v not in ['gardenhorde','assorted'])) if wave in [5,10] else title),comps=comps,icons=slot,slotlabels=[icons.get(v,v) for v in slot],slotDisplay=[icons.get(v,v) for v in slot],moneySlotCount=money,enemyNames=list(dict.fromkeys(e['name'] for c in comps for s in c['subs'] for e in s['enemies'])),sid=text(g,'IntroSIDOverride'),delay=text(g,'StartDelayTime'),challenge=text(g,'ChallengeName'),subcount=sum(len(c['subs']) for c in comps),nameNote='Названия — справочные переводы внутренних имён.'+(' gardenhorde может давать horde-результат при штатном колесе.' if wave in [5,10] else '')))
 assert len(data)==105
 return data

def shared_schema():
 c=Resource('CoOps_ChallengeSelector');a,to,te=c.event_layout();iface=next(i for i,o in enumerate(c.r['objects']) if o['type']=='InterfaceDescriptorData');routes=[];choices={}
 labels={'NoKnockouts':'Без потерь (NoKnockouts)','NoBaseDamage':'Без урона базе (NoBaseDamage)','NoPlayerDamage':'Без урона игрокам (NoPlayerDamage)'}
 xml=E.fromstring('<r>'+(ROOT/'originals/CoOps_ChallengeSelector.xml').read_text()+'</r>');names={o.get('Guid'):text(o,'Blueprint') for o in xml}
 for i,e in enumerate(c.r['objects'][0]['fields']['EventConnections']):
  if (e.get('Source') or {}).get('index')!=iface or (e['SourceEvent']['Id']&0xffffffff)==0x34b2d0dd:continue
  target=e['Target']['index'];path=names.get(c.r['objects'][target]['guid'],'');short=path.split(' [')[0].split('_Set03')[-1]
  route={'targetOffset':a['offset']+i*a['stride']+to,'eventOffset':a['offset']+i*a['stride']+te,'originalTarget':target+1,'originalEvent':e['TargetEvent']['Id']&0xffffffff};routes.append(route)
  if short in labels:choices[short]={'label':labels[short],'target':target+1,'event':e['TargetEvent']['Id']&0xffffffff,'resource':path}
 assert len(routes)==20 and len(choices)==3
 r=Resource('CoOps_SlotMachine_RewardSpin');ra,_,_=r.event_layout();switch=next(i for i,o in enumerate(r.r['objects']) if o['type']=='SwitchPropertyStringEntityData');strings=r.r['objects'][switch]['fields']['StringProperties'];assert strings==['coinGem','coinBag','coinSilver',''];selectors=[]
 for i,o in enumerate(r.r['objects']):
  if o['type']!='RandomMultiEventEntityData':continue
  mapping=[]
  for slot in range(10):
   links=[e for e in r.r['objects'][0]['fields']['EventConnections'] if (e.get('Source')or{}).get('index')==i and (e.get('Target')or{}).get('index')==switch and (e['SourceEvent']['Id']&0xffffffff)==h('Out'+str(slot))];assert len(links)==1
   target=links[0]['TargetEvent']['Id']-263676844;assert 0<=target<4;mapping.append(['gem','bag','silver','horde'][target])
  selectors.append({'object':i,'weights':r.array(i,'RandomEventWeight'),'uniform':r.field(i,'UniformDistribution'),'outcomes':mapping})
 assert len(selectors)==2 and selectors[0]['outcomes'][9]=='silver' and selectors[1]['outcomes'][8]=='silver'
 return {'challenge':{'connections':a,'routes':routes,'choices':choices},'reward':{'connections':ra,'selectors':selectors},'files':{n:Resource(n).profile() for n in ['CoOps_ChallengeSelector','CoOps_SlotMachine_RewardSpin']}}

def profile(mode,cat,shared):
 prefix='GardenOps' if mode=='garden' else 'GraveyardOps';tn=prefix+'_WaveTree';ln=prefix+'_WaveLogic';t=Resource(tn);logic=Resource(ln);base=json.loads((ROOT/'data/bin-schema.json').read_text());assert Resource('AISpawnGrid').profile()['sha256']==base['files']['AISpawnGrid']['sha256'],'Unsupported grid baseline';s={'format':base['format'],'version':2,'mode':mode,'title':'Garden Ops' if mode=='garden' else 'Graveyard Ops','treeFile':tn,'logicFile':ln,'files':{'AISpawnGrid':Resource('AISpawnGrid').profile(),tn:t.profile(),ln:logic.profile(),**shared['files']},'grid':base['grid'],'shared':{k:v for k,v in shared.items() if k!='files'}};groups=[];subs={};comps={}
 for g in cat:
  i=t.idx[g['guid']];a=t.array(i,'Waves');refs=t.r['objects'][i]['fields']['Waves'];groups.append({'guid':g['guid'],'wave':g['wave'],'service':g['type']=='Служебная','node':g['node'],'startEvent':h('Start_'+g['node']),'array':a,'delay':t.field(i,'StartDelayTime'),'compositions':[{'guid':x['internal'],'pointer':x['index']+1} for x in refs]})
  for c in g['comps']:
   comps[c['guid']]={'subgroups':[sub['guid'] for sub in c['subs']]}
   for sub in c['subs']:
    si=t.idx[sub['guid']];es=t.array(si,'WaveSpawnTypeSet');mins=t.fd(es['elementClass'],'MinSpawnLimit');maxs=t.fd(es['elementClass'],'MaxSpawnLimit');orig=t.r['objects'][si]['fields']['WaveSpawnTypeSet']
    subs[sub['guid']]={'fields':{k:t.field(si,k) for k in ['UseSpecificSpawnID','MinSpawnDistanceFromBase','MaxSpawnDistanceFromBase','MinDistanceFromPlayer','MaxDistanceFromPlayer']},'numMain':t.array(si,'NumMainSpawnPoints'),'name':sub['name'],'enemies':[{'minOffset':es['offset']+k*es['stride']+mins[3],'maxOffset':es['offset']+k*es['stride']+maxs[3],'min':e['MinSpawnLimit'],'max':e['MaxSpawnLimit']} for k,e in enumerate(orig)]}
 s['tree']={'rootGroups':t.array(0,'WaveGroups'),'groups':groups,'compositions':comps,'subgroups':subs};spawner=next(i for i,o in enumerate(logic.r['objects']) if o['type']=='AIWaveSpawnEntityData');a,_,te=logic.event_layout();byhash={g['startEvent']:g for g in groups};routes=[]
 for i,e in enumerate(logic.r['objects'][0]['fields']['EventConnections']):
  if (e.get('Target')or{}).get('index')!=spawner:continue
  event=e['TargetEvent']['Id']&0xffffffff
  if event in byhash:routes.append({'offset':a['offset']+i*a['stride']+te,'wave':0 if byhash[event]['node']=='Wave00' else byhash[event]['wave'],'service':byhash[event].get('service',False),'original':event})
 assert all(any(r['wave']==w for r in routes) for w in range(1,11));s['logic']={'connections':a,'routes':routes};return s

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args();grave=plant_catalog();shared=shared_schema();outputs={'data/graveyard-catalog.json':grave,'data/garden-profile.json':profile('garden',json.loads((ROOT/'data/catalog.json').read_text()),shared),'data/graveyard-profile.json':profile('graveyard',grave,shared)}
 for path,data in outputs.items():
  content=jsave(path,data);p=ROOT/path
  if args.check:assert p.read_text()==content,'Stale '+path
  else:p.write_text(content)
  print('Checked' if args.check else 'Wrote',path)
if __name__=='__main__':main()
