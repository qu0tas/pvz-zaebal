/* Exact-baseline, local-only legacy EBX writer. User-requested baseline payloads are embedded at build time. */
const BIN_SCHEMA=JSON.parse(document.querySelector('#bin-schema').textContent);
const BIN_FILES=Object.keys(BIN_SCHEMA.files),binSources=new Map(),BIN_TREE=BIN_SCHEMA.treeFile||'GardenOps_WaveTree',BIN_LOGIC=BIN_SCHEMA.logicFile||'GardenOps_WaveLogic';
const BIN_BUNDLED=JSON.parse(document.querySelector('#bin-originals')?.textContent||'{}');
let binReady=Promise.resolve(),binLoading=false;
function binAssert(ok,message){if(!ok)throw new Error(message)}
function binView(b){return new DataView(b.buffer,b.byteOffset,b.byteLength)}
function binU32(b,p){binAssert(p>=0&&p+4<=b.length,'Чтение за границами BIN');return binView(b).getUint32(p,true)}
function binPut(b,p,v,float=false){binAssert(p>=0&&p+4<=b.length,'Запись за границами BIN');if(float)binView(b).setFloat32(p,v,true);else binView(b).setUint32(p,v>>>0,true)}
function binAlign(n,a){return Math.ceil(n/a)*a}
function binJoin(...parts){const b=new Uint8Array(parts.reduce((s,p)=>s+p.length,0));let i=0;for(const p of parts){b.set(p,i);i+=p.length}return b}
function binWord(v){const b=new Uint8Array(4);binPut(b,0,v);return b}
function binSame(a,b){return a.length===b.length&&a.every((v,i)=>v===b[i])}
async function binHash(b){binAssert(globalThis.crypto?.subtle,'Для SHA-256 открой сайт через HTTPS (GitHub Pages) или localhost.');return [...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('')}
function binStructuralCheck(b){
 const d=binView(b);binAssert(binU32(b,0)===0x0fb2d1ce,'Не поддерживается формат EBX');const so=binU32(b,4);binAssert(so+binU32(b,8)===b.length,'Неверный размер EBX');const ni=d.getUint16(16,true),nc=d.getUint16(22,true),nf=d.getUint16(24,true),tn=d.getUint16(26,true),ng=binU32(b,12),na=binU32(b,32);const meta=binAlign(64+ng*32+tn+nf*16+nc*16+ni*4,16),abase=so+binU32(b,28)+binU32(b,36);binAssert(meta+na*12<=so,'Таблица массивов выходит за границы');
 for(let i=0;i<na;i++){const off=binU32(b,meta+i*12),count=binU32(b,meta+i*12+4);if(count){const p=abase+off;binAssert(p>=abase+4&&p<b.length,'Массив вне файла');binAssert(binU32(b,p-4)===count,'Не совпадает длина массива')}}
 return {bytes:b.length,arrays:na};
}
function binPlan(raw){
 binAssert(!raw.mode||raw.mode===(BIN_SCHEMA.mode||'garden'),'План другого режима.');
 const selected=[],subgroups=new Map(),pointIDs=new Set(),available=new Set(POINTS.map(p=>p.id));
 for(let wave=1;wave<=10;wave++){
  const w=raw.waves?.[wave];binAssert(w,'Выбери вариант для волны '+wave);binAssert(!w.ambush,'AMBUSH!!! для волны '+wave+' пока не поддерживается генератором. Сними этот флажок.');const g=BIN_SCHEMA.tree.groups.find(g=>g.guid===w.groupGuid&&g.wave===wave&&!g.service);binAssert(g,'Неизвестная группа волны '+wave);let compositions=g.compositions;
  if(w.compositionGuid!=='auto'){const c=compositions.find(c=>c.guid===w.compositionGuid);binAssert(c,'Неизвестный состав волны '+wave);compositions=[c]}
  binAssert(w.delay===undefined||(typeof w.delay==='number'&&Number.isFinite(w.delay)&&w.delay>=0&&w.delay<=300),'Неверная задержка волны '+wave);const row={wave,group:g,delay:w.delay,compositionGuid:w.compositionGuid,compositions,assignments:[]};
  for(const c of compositions)for(const guid of BIN_SCHEMA.tree.compositions[c.guid].subgroups){
   const point=w.assignments?.[guid]||'auto';binAssert(point==='auto'||available.has(point),'Недоступная точка '+point);if(subgroups.has(guid))binAssert(subgroups.get(guid).point===point,'Одна общая подгруппа назначена разным точкам: '+guid);
   const placement=POINTS.find(p=>p.id===point),entry={guid,point,wave,name:BIN_SCHEMA.tree.subgroups[guid].name,spawnID:point==='auto'?null:10000+Number(point.slice(1)),placementGuid:placement?.guid??null,world:placement?.world??null};subgroups.set(guid,entry);row.assignments.push(entry);if(point!=='auto')pointIDs.add(point);
  }
  selected.push(row);
 }
 const limits={};for(const [guid,entries]of Object.entries(raw.enemyLimits||{})){const sub=BIN_SCHEMA.tree.subgroups[guid];binAssert(sub&&entries&&typeof entries==='object'&&!Array.isArray(entries),'Неизвестная подгруппа лимитов '+guid);for(const [key,v]of Object.entries(entries)){binAssert(/^\d+$/.test(key)&&sub.enemies?.[Number(key)]&&v&&Number.isInteger(v.min)&&Number.isInteger(v.max)&&v.min>=0&&v.max<=500&&v.min<=v.max,'Неверные min/max '+guid+' / '+key)}if(subgroups.has(guid))limits[guid]=entries}return {selected,subgroups:[...subgroups.values()],points:[...pointIDs].sort(),limits};
}
function binGrid(original,chosen){
 if(!chosen.length)return original.slice();const s=BIN_SCHEMA.grid;const entries=chosen.map(id=>s.registry.find(p=>p.id===id));binAssert(entries.every(Boolean),'Нет привязки размещения');const enc=new TextEncoder();const texts=entries.map(e=>enc.encode('Int32 '+e.spawnID+'\0'));const addedLength=binAlign(s.stringsLength+texts.reduce((n,b)=>n+b.length,0),16)-s.stringsLength;const extra=new Uint8Array(addedLength);let cursor=0;const stringOffsets=[];
 for(const text of texts){stringOffsets.push(s.stringsLength+cursor);extra.set(text,cursor);cursor+=text.length}
 let b=binJoin(original.slice(0,s.stringsBase+s.stringsLength),extra,original.slice(s.stringsBase+s.stringsLength));binPut(b,28,s.stringsLength+extra.length);const abase=s.arrayBase+extra.length;
 const fields=new Uint8Array(s.fields.count*s.fields.stride+entries.length*16);fields.set(original.slice(s.fields.offset,s.fields.offset+s.fields.count*s.fields.stride));const props=new Uint8Array(s.properties.count*s.properties.stride+entries.length*20);props.set(original.slice(s.properties.offset,s.properties.offset+s.properties.count*s.properties.stride));
 entries.forEach((e,i)=>{const f=s.fields.count*16+i*16;[stringOffsets[i],0,e.sourceField,1].forEach((v,j)=>binPut(fields,f+j*4,v));const p=s.properties.count*20+i*20;[s.interfacePointer,(0x80000000|e.importIndex)>>>0,e.sourceField,s.targetField,s.bindingFlags].forEach((v,j)=>binPut(props,p+j*4,v))});
 function relocate(a,count,payload){const padding=new Uint8Array(binAlign(b.length,4)-b.length);b=binJoin(b,padding,binWord(count),payload);const start=b.length-payload.length;binPut(b,a.meta,start-abase);binPut(b,a.meta+4,count);binPut(b,a.meta+8,a.class)}
 relocate(s.fields,s.fields.count+entries.length,fields);relocate(s.properties,s.properties.count+entries.length,props);b=binJoin(b,new Uint8Array(binAlign(b.length,16)-b.length));binPut(b,8,b.length-s.stringsBase);return b;
}
function binTree(original,compiled){
 const b=original.slice(),s=BIN_SCHEMA.tree;
 for(const row of compiled.selected)if(row.compositionGuid!=='auto'){
  const a=row.group.array;binAssert(binU32(original,a.meta+4)===a.count,'Не совпадает исходный Waves');binPut(b,a.meta+4,1);binPut(b,a.offset-4,1);binPut(b,a.offset,row.compositions[0].pointer);
 }
 for(const entry of compiled.subgroups){if(entry.point==='auto')continue;const sub=s.subgroups[entry.guid],id=BIN_SCHEMA.grid.registry.find(p=>p.id===entry.point).spawnID;const values={UseSpecificSpawnID:id,MinSpawnDistanceFromBase:0,MaxSpawnDistanceFromBase:10000,MinDistanceFromPlayer:0,MaxDistanceFromPlayer:10000};for(const [key,value]of Object.entries(values)){const f=sub.fields[key];binPut(b,f.offset,value,f.type===19)}const a=sub.numMain;for(let i=0;i<a.count;i++)binPut(b,a.offset+i*4,1)}
 for(const row of compiled.selected)if(row.delay!==undefined)binPut(b,row.group.delay.offset,row.delay,true);for(const [guid,entries]of Object.entries(compiled.limits||{}))for(const [index,v]of Object.entries(entries)){const e=s.subgroups[guid].enemies[Number(index)];binPut(b,e.minOffset,v.min);binPut(b,e.maxOffset,v.max)}
 const a=s.rootGroups;binAssert(binSame(original.slice(a.offset,a.offset+a.count*4),b.slice(a.offset,a.offset+a.count*4)),'Изменился список корневых групп');return b;
}
function binLogic(original,compiled){const b=original.slice();for(const route of BIN_SCHEMA.logic.routes){binAssert(binU32(original,route.offset)===route.original,'Не совпадает исходная связь WaveLogic');const row=compiled.selected.find(r=>r.wave===route.wave);if(row)binPut(b,route.offset,row.group.startEvent)}return b}
function binCheckResults(outputs,compiled){
 const tree=outputs[BIN_TREE],grid=outputs.AISpawnGrid;
 for(const row of compiled.selected)if(row.compositionGuid!=='auto'){const a=row.group.array;binAssert(binU32(tree,a.meta+4)===1&&binU32(tree,a.offset)===row.compositions[0].pointer,'Состав не записан')}
 for(const row of compiled.subgroups)if(row.point!=='auto'){const p=BIN_SCHEMA.grid.registry.find(p=>p.id===row.point);binAssert(binU32(tree,BIN_SCHEMA.tree.subgroups[row.guid].fields.UseSpecificSpawnID.offset)===p.spawnID,'ID спавна не записан')}
 for(const route of BIN_SCHEMA.logic.routes)binAssert(binU32(outputs[BIN_LOGIC],route.offset)===(compiled.selected.find(r=>r.wave===route.wave)?.group.startEvent??route.original),'Маршрут волны не записан');
 const s=BIN_SCHEMA.grid;binAssert(binU32(grid,s.properties.meta+4)===s.properties.count+compiled.points.length,'Неверное число привязок');
 if(compiled.points.length){const abase=binU32(grid,4)+binU32(grid,28)+binU32(grid,36);const po=abase+binU32(grid,s.properties.meta);const fo=abase+binU32(grid,s.fields.meta);
  compiled.points.forEach((id,i)=>{const p=s.registry.find(p=>p.id===id),o=po+(s.properties.count+i)*20,f=fo+(s.fields.count+i)*16;binAssert(binU32(grid,o)==s.interfacePointer&&binU32(grid,o+4)===((0x80000000|p.importIndex)>>>0)&&binU32(grid,o+8)===p.sourceField&&binU32(grid,o+12)===s.targetField&&binU32(grid,o+16)===17,'Неверная привязка точки '+id);let text='',start=s.stringsBase+binU32(grid,f);while(start<grid.length&&grid[start])text+=String.fromCharCode(grid[start++]);binAssert(text==='Int32 '+p.spawnID,'Неверная константа '+id)});
 }
}
function binOptions(raw){const ops=raw.ops||{},challenge=ops.challenge??'vanilla',mode=ops.reward?.mode??'vanilla';binAssert(challenge==='vanilla'||BIN_SCHEMA.shared?.challenge.choices[challenge],'Неизвестное испытание');binAssert(['vanilla','silver','bag','gem','moneyOnly','custom'].includes(mode),'Неизвестный режим колеса');let weights={silver:1,bag:1,gem:1,horde:0};if(['silver','bag','gem'].includes(mode))weights={silver:0,bag:0,gem:0,horde:0,[mode]:1};if(mode==='custom'){weights={};for(const key of ['silver','bag','gem','horde']){const v=ops.reward?.weights?.[key];binAssert(Number.isInteger(v)&&v>=0&&v<=1000,'Неверный вес '+key);weights[key]=v}binAssert(Object.values(weights).some(v=>v>0),'Все веса нулевые')}return {challenge,reward:{mode,weights}}}
function binShared(sources,options){
 const selector=sources.CoOps_ChallengeSelector.slice(),reward=sources.CoOps_SlotMachine_RewardSpin.slice(),schema=BIN_SCHEMA.shared;let redirected=0;const distributions=[];
 if(options.challenge!=='vanilla'){const choice=schema.challenge.choices[options.challenge];for(const route of schema.challenge.routes){binAssert(binU32(selector,route.targetOffset)===route.originalTarget&&binU32(selector,route.eventOffset)===route.originalEvent,'Изменился исходный запрос ChallengeSelector');binPut(selector,route.targetOffset,choice.target);binPut(selector,route.eventOffset,choice.event);redirected++}for(const route of schema.challenge.routes)binAssert(binU32(selector,route.targetOffset)===choice.target&&binU32(selector,route.eventOffset)===choice.event,'Запрос испытания не записан')}
 if(options.reward.mode!=='vanilla')for(const row of schema.reward.selectors){const counts={};for(const key of row.outcomes)counts[key]=(counts[key]||0)+1;const target=row.outcomes.map(key=>options.reward.weights[key]/counts[key]);const total=target.reduce((a,b)=>a+b,0);binAssert(total>0,'Для ветки колеса WG'+(row.object-4)+' нет положительных доступных результатов: horde есть только в WG02.');const weights=target.map(v=>100*v/total);reward[row.uniform.offset]=0;for(let i=0;i<weights.length;i++)binPut(reward,row.weights.offset+i*4,weights[i],true);let sum=0;for(let i=0;i<weights.length;i++){const v=binView(reward).getFloat32(row.weights.offset+i*4,true);binAssert(Math.abs(v-weights[i])<0.0001,'Не записан вес колеса');sum+=v}binAssert(Math.abs(sum-100)<0.001,'Неверная сумма весов');distributions.push({branch:'WG'+(row.object-4),outcomes:row.outcomes,weights,aggregate:Object.fromEntries(Object.keys(counts).map(key=>[key,weights.reduce((sum,v,i)=>sum+(row.outcomes[i]===key?v:0),0)]))})}
 return {outputs:{CoOps_ChallengeSelector:selector,CoOps_SlotMachine_RewardSpin:reward},report:{challenge:options.challenge,redirectedRequests:redirected,rewardMode:options.reward.mode,distributions,lifecyclePreserved:true}};
}
function binResourcePath(name){if(name==='AISpawnGrid')return 'Levels/Level_Coop_TimePark/AISpawnGrid';if(name.startsWith('CoOps_'))return 'Levels_Sandbox/Level_Shawbs_Sandbox/CoOps/'+name;return 'Levels_Sandbox/Level_Shawbs_Sandbox/'+(name.startsWith('GraveyardOps')?'GraveyardOps':'GardenOps')+'/'+name}
async function binGenerate(raw,sources){
 const compiled=binPlan(raw),options=binOptions(raw),inputs={};for(const name of BIN_FILES){const b=sources[name];binAssert(b instanceof Uint8Array,'Загрузи '+name+'.bin');const expected=BIN_SCHEMA.files[name];binAssert(b.length===expected.size,'Неверный размер '+expected.filename);const sha256=await binHash(b);binAssert(sha256===expected.sha256,'Неизвестный или уже изменённый '+expected.filename+'. Нужен поддерживаемый оригинал.');binStructuralCheck(b);inputs[name]={sha256,bytes:b.length}}
 const shared=binShared(sources,options);const outputs={AISpawnGrid:binGrid(sources.AISpawnGrid,compiled.points),[BIN_TREE]:binTree(sources[BIN_TREE],compiled),[BIN_LOGIC]:binLogic(sources[BIN_LOGIC],compiled),...shared.outputs};binCheckResults(outputs,compiled);
 for(const row of compiled.selected)if(row.delay!==undefined)binAssert(Math.abs(binView(outputs[BIN_TREE]).getFloat32(row.group.delay.offset,true)-row.delay)<0.0001,'Задержка не записана');for(const [guid,entries]of Object.entries(compiled.limits))for(const [index,v]of Object.entries(entries)){const e=BIN_SCHEMA.tree.subgroups[guid].enemies[Number(index)];binAssert(binU32(outputs[BIN_TREE],e.minOffset)===v.min&&binU32(outputs[BIN_TREE],e.maxOffset)===v.max,'Лимиты не записаны')}
 const files={};for(const [name,b]of Object.entries(outputs))files[name+'.bin']={...binStructuralCheck(b),sha256:await binHash(b),resourcePath:binResourcePath(name),changed:!binSame(b,sources[name])};
 const warnings=['Структура BIN проверена; поведение в игре не проверено.','Метод UseSpecificSpawnID экспериментальный: ранее корректный XML не обеспечивал нужные спавны.','Игровые координаты спавнеров не перемещаются; выбираются существующие точки.','ChallengeSelector и RewardSpin общие для обоих режимов и других карт. Не включай несколько конфликтующих модов.','NoKnockouts/NoBaseDamage/NoPlayerDamage — реальные задания, а не полное отключение испытаний.','Связи завершения испытаний и таймеры не обходятся. Внешние специальные события могут остаться.','Параметры колеса управляют ветками денежных символов; точная визуализация и выплата не проверены.','Min/max — лимиты записей, не гарантированное число врагов; общие подгруппы могут затрагивать другие варианты.','В ZIP всегда пять BIN: оригинальные общие файлы при штатных настройках тоже импортируй для отката прошлых правок.','Одна основная точка на явно назначенную подгруппу; штатные радиусы/alternate positions сохранены.'];
 if(BIN_SCHEMA.mode==='graveyard')warnings.push('Использована общая карта A-точек и AISpawnGrid; применимость фиксированных точек Graveyard Ops ещё не подтверждена в игре.');if(compiled.subgroups.some(s=>s.point==='auto'))warnings.push('Есть подгруппы с «Авто»: их спавны выбирает игра.');
 return {outputs,report:{format:'gw2-timepark-bin-build',version:2,mode:BIN_SCHEMA.mode,title:BIN_SCHEMA.title,status:'STATIC_CHECKED_NOT_GAME_TESTED',createdAt:new Date().toISOString(),placementMap:'user-screenshots-rome-center-corrected-v3',inputs,files,rootGroupsRetained:BIN_SCHEMA.tree.rootGroups.count,logicConnectionsRetained:BIN_SCHEMA.logic.connections.count,registeredPoints:compiled.points,assignments:compiled.subgroups,enemyLimitsApplied:compiled.limits,shared:shared.report,waves:compiled.selected.map(r=>({wave:r.wave,node:r.group.node,groupGuid:r.group.guid,composition:r.compositionGuid,delay:r.delay??r.group.delay.value,subgroups:r.assignments})),warnings},plan:{...JSON.parse(JSON.stringify(raw)),mode:BIN_SCHEMA.mode,ops:options,placementMap:'user-screenshots-rome-center-corrected-v3',readyForFrosty:false,damageChanges:false,photos:PHOTOS.map(z=>({zone:z.id,name:z.name,width:z.width,height:z.height,points:z.points.map(p=>({id:p.id,x:p.x,y:p.y,guid:p.guid,world:p.world,gameSpawnId:null}))}))}};
}
// Small dependency-free ZIP writer (stored entries, UTF-8 names, standard CRC32).
function binCRC32(bytes){let c=0xffffffff;for(const v of bytes){c^=v;for(let j=0;j<8;j++)c=(c>>>1)^(0xedb88320&-(c&1))}return(c^0xffffffff)>>>0}
function binZip(entries){const enc=new TextEncoder(),locals=[],centrals=[];let offset=0;for(const [name,value]of Object.entries(entries)){const filename=enc.encode(name),data=typeof value==='string'?enc.encode(value):value,crc=binCRC32(data),head=new Uint8Array(30+filename.length),dv=binView(head);binPut(head,0,0x04034b50);dv.setUint16(4,20,true);dv.setUint16(6,0x800,true);dv.setUint16(12,0x21,true);binPut(head,14,crc);binPut(head,18,data.length);binPut(head,22,data.length);dv.setUint16(26,filename.length,true);head.set(filename,30);locals.push(head,data);const central=new Uint8Array(46+filename.length),cv=binView(central);binPut(central,0,0x02014b50);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x800,true);cv.setUint16(14,0x21,true);binPut(central,16,crc);binPut(central,20,data.length);binPut(central,24,data.length);cv.setUint16(28,filename.length,true);binPut(central,42,offset);central.set(filename,46);centrals.push(central);offset+=head.length+data.length}const cd=binJoin(...centrals),end=new Uint8Array(22),ev=binView(end);binPut(end,0,0x06054b50);ev.setUint16(8,centrals.length,true);ev.setUint16(10,centrals.length,true);binPut(end,12,cd.length);binPut(end,16,offset);return binJoin(...locals,cd,end)}
function binInstructions(report){return '\ufeff'+`TIME PARK — ${report.title} — ЭКСПЕРИМЕНТАЛЬНАЯ СБОРКА
Статические проверки пройдены; игра НЕ проверена. Не FBMOD.

ПЕРЕД ИМПОРТОМ
Сделай резервную копию. Используй отдельный чистый проект для личного/разрешённого теста.
Пять BIN импортируются вместе. Не включай старые моды с теми же ресурсами.

КУДА ИМПОРТИРОВАТЬ
${Object.entries(report.files).map(([name,f])=>name+' → '+f.resourcePath+(f.changed?' [изменён]':' [оригинал, откат прошлых правок]')).join('\n')}
AISpawnGrid — корневой ресурс, не layer0_aispawns и не слой GraveyardOps.

НАСТРОЙКИ
Испытания: ${report.shared.challenge} / перенаправлено запросов: ${report.shared.redirectedRequests}.
Колесо: ${report.shared.rewardMode}. Распределения: build-report.json.
Замена на «Без потерь» НЕ отключает задания. Оригинал отменяет предыдущие патчи общего ресурса.

ПОСЛЕ ИМПОРТА
Сохрани проект, экспортируй пять ресурсов в XML и сравни с отчётом. Проверь журнал Imported и пути выбранных BIN.
Экспортируй FBMOD во Frosty, замени старую версию в менеджере. Не запускай два конфликтующих пакета Garden/Graveyard одновременно.
Проверь в игре: волны 1–10, переходы/таймер, испытание, точки, два денежных символа на 5/10, визуальный результат и реальную выплату.
XML PASS не доказывает применение движком. Общие файлы влияют и на другие карты/режимы.

ОГРАНИЧЕНИЯ
${report.warnings.map(w=>'— '+w).join('\n')}

НАЗНАЧЕНИЯ
${report.waves.map(w=>'Волна '+w.wave+' · '+w.node+' · задержка '+w.delay+' с\n'+w.subgroups.map(s=>'  '+s.name+' → '+s.point+(s.point==='auto'?'':' / ID '+s.spawnID)).join('\n')).join('\n\n')}

План: plan.json; контрольные суммы, назначения, лимиты и пути: build-report.json.
`}
function binPackage(result){const entries={};for(const [name,b]of Object.entries(result.outputs))entries[name+'.bin']=b;entries['README_IMPORT_RU.txt']=binInstructions(result.report);entries['build-report.json']=JSON.stringify(result.report,null,2);entries['plan.json']=JSON.stringify(result.plan,null,2);return binZip(entries)}
function binUI(){
 const status=$('#binStatus'),list=$('#binFiles');function show(){list.innerHTML=BIN_FILES.map(name=>{const s=BIN_SCHEMA.files[name];return `<li><b>${esc(s.filename)}</b> — ${binSources.has(name)?'✓ оригинал проверен':'не загружен'}<br><code>${s.sha256}</code></li>`}).join('');$('#binBuild').disabled=binLoading||binSources.size!==BIN_FILES.length||!$('#binConsent').checked;$('#binDefaults').disabled=binLoading;$('#binInputs').disabled=binLoading;$('#binClear').disabled=binLoading}
 async function defaults(){
  binLoading=true;binSources.clear();show();status.textContent='Проверяю встроенные оригиналы…';
  try{const verified=new Map();for(const name of BIN_FILES){const text=BIN_BUNDLED[name];binAssert(typeof text==='string','Встроенный оригинал отсутствует: '+name);const bytes=Uint8Array.from(atob(text),c=>c.charCodeAt(0)),expected=BIN_SCHEMA.files[name];binAssert(bytes.length===expected.size,'Неверный размер встроенного '+expected.filename);binAssert(await binHash(bytes)===expected.sha256,'SHA-256 встроенного '+expected.filename+' не совпал');binStructuralCheck(bytes);verified.set(name,bytes)}for(const [name,bytes]of verified)binSources.set(name,bytes);status.textContent='Встроенные оригиналы проверены: '+BIN_FILES.length+'/'+BIN_FILES.length+'. Режим: '+BIN_SCHEMA.title+'. Ручная загрузка не нужна.'}
  catch(err){binSources.clear();status.textContent='Встроенные оригиналы недоступны: '+err.message+'. Можно выбрать свои поддерживаемые BIN.'}finally{binLoading=false;show()}
 }
 $('#binDefaults').onclick=()=>{binReady=defaults()};
 $('#binOpen').onclick=()=>{const panel=$('#binPanel');panel.open=true;panel.scrollIntoView({behavior:'smooth',block:'start'})};$('#binConsent').onchange=show;
 $('#binInputs').onchange=async e=>{const files=[...e.target.files];status.textContent='Проверяю файлы локально…';try{binAssert(files.length>0,'Файлы не выбраны');for(const f of files){const name=BIN_FILES.find(n=>BIN_SCHEMA.files[n].filename.toLowerCase()===f.name.toLowerCase());binAssert(name,'Нужны только пять указанных оригинальных BIN, не '+f.name);binSources.delete(name);binAssert(f.size<=2*1024*1024,'Слишком большой файл');const bytes=new Uint8Array(await f.arrayBuffer()),expected=BIN_SCHEMA.files[name];binAssert(bytes.length===expected.size,'Неверный размер '+f.name+'; нужен оригинальный экспорт.');const actual=await binHash(bytes);binAssert(actual===expected.sha256,'SHA-256 '+f.name+' не совпал. Изменённые Test04–Test07 и другие версии не принимаются.');binStructuralCheck(bytes);binSources.set(name,bytes)}status.textContent='Проверено файлов: '+binSources.size+'/'+BIN_FILES.length+'. Файлы остаются только в памяти этой вкладки.'}catch(err){status.textContent='Не загружено: '+err.message}finally{e.target.value='';show()}};
 $('#binClear').onclick=()=>{binSources.clear();show();status.textContent='Загруженные BIN удалены из памяти вкладки.'};$('#binBuild').onclick=async()=>{const button=$('#binBuild');button.disabled=true;status.textContent='Собираю и проверяю…';try{binAssert($('#binConsent').checked,'Подтверди экспериментальный статус');const snapshot=JSON.parse(JSON.stringify(plan));const result=await binGenerate(snapshot,Object.fromEntries(binSources));const zip=binPackage(result),url=URL.createObjectURL(new Blob([zip],{type:'application/zip'})),a=document.createElement('a');a.href=url;a.download='TimePark_'+BIN_SCHEMA.mode+'_Experimental.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);status.textContent='ZIP готов: 5 BIN + инструкция + отчёт + план. Структура проверена; игра ещё не проверена.'}catch(err){status.textContent='Сборка остановлена: '+err.message}finally{show()}};show();if(BIN_FILES.every(name=>BIN_BUNDLED[name]))binReady=defaults();
}
binUI();
