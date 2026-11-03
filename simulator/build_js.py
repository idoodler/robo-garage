# JS part of the v5.0 build (exec'd by build_page.py: uses rep() and s from there)

# ---------------- door table texts
rep("safety:'drops by its own weight – cannot pinch'", "safety:'drops by its own weight · light barrier'")
rep("safety:'stall stop (INA219)'", "safety:'light barrier + stall stop (INA219)'", 3)
rep("Closing pushes, so the INA219 stops it on a stall.'}", "The light barrier in front stops it before it touches anything; the INA219 stall stop is the backup.'}", 3)
rep("going down it simply follows by its own weight (≈5 N), so it can never pinch.'}",
    "going down it simply follows by its own weight (≈5 N), so it can never pinch. The light barrier in front keeps it open while something is in the way.'}")

# ---------------- parts info
rep(" esp:['ESP32 + BTS7960 + buck','In the fixed space above the station: door cover, 3 reeds, LED, rear fan PWM, optional VL53L1X / INA219.'],",
    " esp:['Controller PCB v1.2','Own 100 × 100 mm board (fully assembled by JLCPCB) in a 3D-printed case under the top: ESP32 DevKitC socket, DRV8871 actuator driver + INA219 stall stop, 12 V → 5 V on board, SHT40 temperature/humidity, light-barrier input with self-test, water-leak probe + 12 V valve output, buzzer, fan PWM, LED level shifter, 9 push-button clamps, USB-C socket on the case (flash without opening it). Files and order steps: \"Controller PCB\" below.'],")
rep(" fan:['Rear fan · ARCTIC P12 Slim','On the inside of the back panel, blows into the 4 cm wall gap – invisible from the front. Runs while washing/drying, stops when the drawer is open.'],",
    " fan:['Rear fan · ARCTIC P12 Slim','On the inside of the back panel, blows into the 4 cm wall gap – invisible from the front. Auto vent on the ESP32: above 65 % humidity or 30 °C (SHT40) it runs at 30–100 %, off again 5 %RH / 1 °C below. Stops while the drawer is open.'],")
rep(" led:['Status LED','Dot/Ring in the fascia, Line in the fascia gap, Underglow under the ramp edge · WS2812B · GPIO16 · 330 Ω + 1000 µF.'],",
    " led:['Status LED','Dot/Ring in the fascia, Line in the fascia gap, Underglow under the ramp edge · WS2812B · GPIO16 → level shifter + 330 Ω on the PCB, 470 µF at the LED clamp.'],")
rep(""" obstacle:['Obstacle test','Something in the way while closing. Lift door: it rests on it, "closed" never triggers → HA re-opens. All other doors: INA219 sees the stall → stop + re-open.']""",
    """ obstacle:['Obstacle test','A toy on the floor in front of the door. The light barrier sees it: the door does not close, or stops and re-opens if it is already closing. It closes again 1.5 s after the beam is clear. Backup: INA219 stall stop.'],
 beam:['Light barrier · door safety','12–24 V through-beam pair (NPN, Light-ON) on 2 small brackets at the front corners of the cabinet sides: beam ≈12 cm in front of the door, ≈2 cm above the floor – past the ramp wedge and under the door\\'s swing, so the door never breaks it itself. Before every close the ESP32 switches the sender off for a moment: the receiver must react (self-test), else "Door beam fault" and the door stays open. Try "Toy in front" and "Beam fault".'],
 th:['SHT40 · cabinet air','Temperature + humidity sensor on the controller PCB, on an island with a milled slot, in its own vented corner of the case – it measures cabinet air, not board heat. Drives the auto vent: hot mop drying → humid cabinet → rear fan.']""")
rep('<div class="info" id="info"><b>Tap any part</b>door, ramp, actuator, drawer, wheels, tanks, LED, rear fan, sensors – to see what it is and what to buy.</div>',
    '<div class="info" id="info"><b>Tap any part</b>door, ramp, actuator, drawer, wheels, tanks, LED, rear fan, light barrier, controller, sensors – to see what it is and what to buy.</div>')

# ---------------- state, beam + climate model
rep("mode:'',modeT:-9,ledPrev:0,fanA:0,wait:false,retK:0,retFrom:null,retHd:0,pose:{x:0,z:-19.5,h:2.7,pitch:0,hd:0}};",
    "mode:'',modeT:-9,ledPrev:0,fanA:0,wait:false,retK:0,retFrom:null,retHd:0,\n tc:22,rh:50,fanS:0,vent:false,beamBlk:false,tx:true,test:0,fault:false,faultOn:false,errWhy:'',clrT:0,pose:{x:0,z:-19.5,h:2.7,pitch:0,hd:0}};")
rep("const onPath=()=>{const id=PH[S.ph].id;return id==='closeOut'||id==='cleaning'||(id==='returning'&&S.retK<.4);};",
    """const onPath=()=>{const id=PH[S.ph].id;return id==='closeOut'||id==='cleaning'||(id==='returning'&&S.retK<.4);};
/* light barrier: fixed to the cabinet, 12 cm in front of the door, 2 cm above the floor */
const BX=-12;
function beamBlocked(){
 if(S.block||S.drawer>8)return true;
 if(!onPath()){const x0=S.rx-(S.rx>=1.9?S.drawer:0);if(x0<=BX&&x0+35>=BX)return true;}
 return false;
}
/* cabinet air (SHT40) + auto vent on the ESP32 – same rule as the YAML */
const ROOM=[22,50],SRC={idle:[22.6,50],emptying:[24,50],washing:[27,88],drying:[35,72]},V_H=65,V_T=30;
function climate(dtr){
 if(!(dtr>0))return;
 const id=PH[S.ph].id,open=svc();let src=SRC[id]||[22.4,50];
 if(id==='idle'&&S.bat<99.5)src=[24,50];
 const ex=S.fanS/100/300+(open?1/60:0),a=1/900+ex,f=1-Math.exp(-a*dtr);
 S.tc+=((src[0]/900+ex*ROOM[0])/a-S.tc)*f;S.rh+=((src[1]/900+ex*ROOM[1])/a-S.rh)*f;
 if(S.rh>V_H||S.tc>V_T)S.vent=true;else if(S.rh<V_H-5&&S.tc<V_T-1)S.vent=false;
 let sp=0;if(S.vent&&!open){const x=Math.max((S.rh-V_H+5)/20,(S.tc-V_T+1)/7);sp=10*Math.round((30+70*clamp(x,0,1))/10);}
 if((sp>0)!==(S.fanS>0))log(sp?'Auto vent: '+Math.round(S.rh)+' % · '+S.tc.toFixed(1)+' °C → rear fan '+sp+' %':open?'Drawer open → rear fan off':'Auto vent off · '+Math.round(S.rh)+' % · '+S.tc.toFixed(1)+' °C');
 S.fanS=sp;
}""")
rep(" S.ph=IDX[id];S.pt=0;\n", " S.ph=IDX[id];S.pt=0;S.tx=true;S.test=(id==='closeOut'||id==='closing')?.7:0;\n")

# ---------------- step(): self-test, beam stop/reverse, retry, climate
rep(""" const p=PH[S.ph],d=dt*S.speed,bf=BF[S.doorType];
 if(S.err){S.rod=Math.min(1,S.rod+d*.4);S.door=S.block?Math.max(S.rod,bf):S.rod;computePose();return;}""",
    """ const p=PH[S.ph],d=dt*S.speed;
 S.beamBlk=beamBlocked();
 const closingPh=p.id==='closeOut'||p.id==='closing';
 if(S.err){S.rod=Math.min(1,S.rod+d*.4);S.door=S.rod;
  const ok=(S.errWhy==='beam'&&!S.beamBlk)||(S.errWhy==='fault'&&!S.fault);
  S.clrT=ok?S.clrT+dt:0;
  if(ok&&S.clrT>1.5&&S.rod>.999){const w=S.errWhy;S.err=false;S.errWhy='';S.clrT=0;log(w==='beam'?'Beam clear for 1.5 s → close again':'Beam fault fixed → close again');go(p.id);}
  computePose();return;}""")
rep(""" if(S.wait){S.wait=false;log('Drawer closed – docking continues');}
 S.pt+=d;S.clock+=d*p.rate;""",
    """ if(S.wait){S.wait=false;log('Drawer closed – docking continues');}
 if(closingPh&&S.test>0){                                   // light-barrier self-test before every close
  S.test=Math.max(0,S.test-dt);S.tx=!(S.test>.2&&S.test<.5);
  if(S.test===0){S.tx=true;
   if(S.fault){S.err=true;S.errWhy='fault';S.faultOn=true;log('Beam self-test failed → "Door beam fault", door stays open + notify',true);}
   else if(S.beamBlk){S.err=true;S.errWhy='beam';log('Light barrier blocked → door stays open',true);}
   else{S.faultOn=false;log('Beam self-test OK · beam clear → closing');}}
  S.door=S.rod;computePose();return;}
 S.pt+=d;S.clock+=d*p.rate;climate(d*p.rate);""")
rep(""" S.door=S.block?Math.max(S.rod,bf):S.rod;
 const closingPh=p.id==='closeOut'||p.id==='closing';
 if(S.block&&S.doorType!=='lift'&&closingPh&&S.rod<bf-.02){S.err=true;log('Stall (INA219): door hit something → stop, re-open + notify',true);computePose();return;}
 if(k>=1){
  if(closingPh&&S.door>.03){S.err=true;log(""",
    """ S.door=S.rod;
 if(closingPh&&S.beamBlk&&S.rod<.999){S.err=true;S.errWhy='beam';log('Beam broken while closing → stop + re-open',true);computePose();return;}
 if(k>=1){
  if(closingPh&&S.door>.03){S.err=true;S.errWhy='timeout';log(""")

# ---------------- render
rep("cap:E('cap3d'),spk:E('wheelSpk'),", "cap:E('cap3d'),spk:E('wheelSpk'),bDot:E('beamDot'),bGlow:E('beamGlow'),")
rep(" el.obst.setAttribute('transform',t==='lift'?'':'translate(-11,1.2)');\n", "")
rep(""" const fanOn=(id==='washing'||id==='drying')&&!svc()&&!S.err;
 if(fanOn&&!RM)S.fanA=(S.fanA+(id==='washing'?28:16))%360;
 el.fan.setAttribute('transform','rotate('+S.fanA+',49.5,-72)');E('btnRingS').setAttribute('opacity',btnRing().toFixed(2));
 el.air.setAttribute('opacity',fanOn?(.55+.35*Math.sin(S.t*4)).toFixed(2):0);""",
    """ const fanOn=S.fanS>0;
 if(fanOn&&!RM)S.fanA=(S.fanA+S.fanS*.28)%360;
 el.fan.setAttribute('transform','rotate('+S.fanA+',49.5,-72)');E('btnRingS').setAttribute('opacity',btnRing().toFixed(2));
 el.air.setAttribute('opacity',fanOn?(.3+.45*S.fanS/100+.2*Math.sin(S.t*4)).toFixed(2):0);
 E('fanTxt').textContent='rear fan'+(fanOn?' '+S.fanS+' %':'');
 E('thTxt').textContent=S.tc.toFixed(1)+' °C · '+Math.round(S.rh)+' %';
 {const c=S.tx?(S.beamBlk?'#ff3b30':'#3ddc84'):'#5b6370';el.bDot.setAttribute('fill',c);el.bGlow.setAttribute('fill',c);el.bGlow.setAttribute('opacity',S.tx?.65:0);}""")
rep(" E('sPhase').textContent=S.err?'Error – door blocked':S.wait?'Waiting – drawer open':p.name;",
    """ const errTxt=S.errWhy==='beam'?'Waiting – beam blocked':S.errWhy==='fault'?'Error – beam fault':'Error – door blocked';
 E('sPhase').textContent=S.err?errTxt:S.wait?'Waiting – drawer open':S.test>0&&(id==='closeOut'||id==='closing')?'Beam self-test':p.name;
 E('sAir').textContent=S.tc.toFixed(1)+' °C · '+Math.round(S.rh)+' % · fan '+(S.fanS?S.fanS+' %':'off');""")
rep("E('badge3d').textContent=(svc()?'Service drawer':S.err?'Error – door blocked':", "E('badge3d').textContent=(svc()?'Service drawer':S.err?errTxt:")
rep(" E('bBlock').disabled=!S.block&&S.door<BF[S.doorType];\n", "")

# ---------------- HA entities, automations, cover state
rep("'binary_sensor.robo_garage_door_closed','binary_sensor.robo_garage_drawer','fan.robo_garage_rear_fan',",
    "'binary_sensor.robo_garage_door_closed','binary_sensor.robo_garage_door_beam','binary_sensor.robo_garage_door_beam_fault','binary_sensor.robo_garage_drawer','fan.robo_garage_rear_fan','sensor.robo_garage_cabinet_temperature','sensor.robo_garage_cabinet_humidity',")
rep(" set('fan.robo_garage_rear_fan',svc()?'off (drawer open)':id==='washing'?'on · 100 %':id==='drying'?'on · 60 %':'off');",
    """ set('fan.robo_garage_rear_fan',svc()?'off (drawer open)':S.fanS?'on · '+S.fanS+' % (auto vent)':'off');
 set('sensor.robo_garage_cabinet_temperature',S.tc.toFixed(1)+' °C');
 set('sensor.robo_garage_cabinet_humidity',Math.round(S.rh)+' %');
 set('binary_sensor.robo_garage_door_beam',S.beamBlk?'on (detected)':'off (clear)');
 set('binary_sensor.robo_garage_door_beam_fault',S.faultOn?'on (problem)':'off');""")
rep(" ['Rear fan','washing / drying → fan on · off +10 min · off if drawer open',()=>['washing','drying'].includes(pid())&&!svc()],",
    " ['Auto vent (on the ESP32)','humidity > 65 % or temp > 30 °C → rear fan 30–100 % · off 5 %RH / 1 °C below · off while the drawer is open',()=>S.fanS>0],")
rep(" ['Door safety','closed reed not reached / stall → cover.open + notify',()=>S.err],",
    """ ['Light barrier (on the ESP32)','before every close: sender off → receiver must react · beam blocked → stay open · broken while closing → stop + re-open',()=>S.test>0||(S.err&&(S.errWhy==='beam'||S.errWhy==='fault'))],
 ['Door safety','beam fault / closed reed not reached / stall → cover.open + notify phone',()=>S.err&&S.errWhy!=='beam'],""")
rep(" if(S.err)return'opening (retry)';", " if(S.err)return S.errWhy==='beam'?'open (beam blocked)':S.errWhy==='fault'?'open (beam fault)':'opening (retry)';")

# ---------------- test buttons
old = s[s.index("E('bBlock').onclick=()=>{"):s.index("E('bTank').onclick=")]
rep(old, """E('bBlock').onclick=()=>{
 S.block=!S.block;setP(E('bBlock'),S.block);
 log(S.block?'Test: toy on the floor in front of the door':'Toy removed');
};
E('bFault').onclick=()=>{
 S.fault=!S.fault;setP(E('bFault'),S.fault);
 log(S.fault?'Test: beam receiver stuck on "clear" (shorted output)':'Beam receiver fixed');
 if(!S.fault)S.faultOn=false;
};
""")
rep("if(S.block){S.block=false;setP(E('bBlock'),false);}if(S.err){S.err=false;}", "if(S.block){S.block=false;setP(E('bBlock'),false);}if(S.err){S.err=false;S.errWhy='';}")

# ---------------- 3D
rep("""add(B(.5,2.8,5.5),M.pcb,-27.7,75.4,-12,carcass,'esp');
add(B(1.8,5,5),M.pcbRed,-27.1,70,-10.5,carcass,'esp');
add(B(.5,1.7,2.2),M.pcbBlue,-27.7,71.2,-17,carcass,'esp');""",
    """/* controller: the printed case (case/robo-garage-case.scad -> files/case-model-v<V>.json = base64 GLB, cm, y up) hangs under the top at the
   left, lid down, USB-C socket towards the front. A plain box stands in until the model has loaded. */
const caseG=new THREE.Group();caseG.position.set(-26.1,80,-14);carcass.add(caseG);
const caseBox=add(B(11.15,2.71,10.5),M.plug,4.675,-1.355,5,caseG,'esp');
M.caseLid=std(0x9fb8d6,.35,0,{transparent:true,opacity:.5,depthWrite:false});
fetch('files/case-model-v1.2.json').then(r=>r.ok?r.json():Promise.reject(r.status)).then(j=>{const s=atob(j.glb),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);
 new GLTFLoader().parse(a.buffer,'',g=>{const mats={base:M.plug,lid:M.caseLid,pcb:M.pcb};
 g.scene.traverse(o=>{if(o.isMesh){if(!o.geometry.attributes.normal)o.geometry.computeVertexNormals();o.material=mats[o.name]||M.plug;o.castShadow=o.name!=='lid';o.receiveShadow=true;o.userData.part='esp';pick.push(o);}});
 caseG.remove(caseBox);caseG.add(g.scene);},()=>{});}).catch(()=>{});""")
rep("import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';",
    "import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';\nimport {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';")
rep("const toy=add(B(9,7.5,7),M.toy,10,5.25,-.6,drawer,'obstacle');toy.visible=false;",
    """const toy=add(B(9,7.5,7),M.toy,10,3.8,11,carcass,'obstacle');toy.visible=false;
/* light barrier: sender + receiver on brackets at the front corners, beam 12 cm in front, 2.2 cm high */
const lbMat=new THREE.MeshBasicMaterial({color:0x3ddc84,transparent:true,opacity:.9,toneMapped:false});
[-1,1].forEach(k=>{add(B(1.6,3.2,2.2),M.black,k*31,2.2,12,carcass,'beam');add(B(.4,1.2,12.4),M.steel,k*30.2,1.2,6.4,carcass,'beam');});
const lbRay=add(CY(.13,.13,60.4,8),lbMat,0,2.2,12,carcass,'beam',{cast:false,recv:false});lbRay.rotation.z=Math.PI/2;""")
rep("legsG.visible=v!=='flap';\n toy.position.set(10,v==='lift'?5.25:4.05,v==='lift'?-.6:11);};", "legsG.visible=v!=='flap';};")
rep(""" const fanOn=(id==='washing'||id==='drying')&&!SIM.svc()&&!S.err;
 if(fanOn&&!RM)blades.rotation.z-=dt*(id==='washing'?28:16);
 updAir(fanOn,S.t);""",
    """ const fanOn=S.fanS>0;
 if(fanOn&&!RM)blades.rotation.z-=dt*S.fanS*.28;
 updAir(fanOn,S.t);
 lbRay.visible=S.tx!==false;lbMat.color.set(S.beamBlk?0xff3b30:0x3ddc84);""")

# ---------------- downloads (claude.ai downloads capability) + copy YAML
rep('<script type="module">', """<script>
(()=>{
 const E=id=>document.getElementById(id),note=E('dlNote'),btns=[...document.querySelectorAll('[data-dl]')];
 const PKG={pcb:'files/pcb-v1.2.json',case:'files/case-v1.2.json'};
 E('cpYaml').onclick=async()=>{try{await navigator.clipboard.writeText(E('yaml').textContent);E('cpNote').textContent='Copied.';}catch(e){E('cpNote').textContent='Copy is blocked here – select the text and copy it.';}};
 let zipLib=null;
 const loadZip=()=>zipLib||(zipLib=new Promise((res,rej)=>{if(window.JSZip)return res(window.JSZip);
  const sc=document.createElement('script');sc.src='https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
  sc.onload=()=>window.JSZip?res(window.JSZip):rej({message:'zip library missing'});sc.onerror=()=>{zipLib=null;rej({message:'zip library did not load'});};document.head.appendChild(sc);}));
 async function addAll(Z,zip,list){for(const f of list){
  if(f.zip){const inner=new Z();await addAll(Z,inner,f.zip);zip.file(f.path,await inner.generateAsync({type:'uint8array',compression:'DEFLATE'}));}
  else if(f.url){const r=await fetch(f.url);if(!r.ok)throw{message:'HTTP '+r.status};zip.file(f.path,await r.arrayBuffer());}
  else if(f.b64)zip.file(f.path,f.b64,{base64:true});
  else zip.file(f.path,f.text);}}
 (async()=>{
  let dl=null;
  try{dl=window.claude&&typeof window.claude.use==='function'?await window.claude.use('downloads'):null;}catch(e){dl=null;}
  if(!dl){note.textContent='Downloads work when the page is opened on claude.ai.';btns.forEach(b=>b.hidden=true);return;}
  note.textContent='';
  btns.forEach(b=>{b.disabled=false;b.onclick=async()=>{
   b.disabled=true;note.textContent='Packing the files …';
   try{const Z=await loadZip(),r=await fetch(PKG[b.dataset.dl]);if(!r.ok)throw{message:'HTTP '+r.status};
    const man=await r.json(),zip=new Z();await addAll(Z,zip,man.files);
    const blob=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:6}});
    await dl.save({filename:man.zip,data:blob});note.textContent='Saved: '+man.zip;}
   catch(e){const c=e&&e.code;note.textContent=c==='declined'?'Download cancelled.':c==='rate_limited'?'Another download prompt is still open – try again.':'Download not possible here ('+(c||(e&&e.message)||'error')+').';}
   finally{b.disabled=false;}};});
 })();
})();
</script>

<script type="module">""")

# ---------------- totals (PCB replaces BTS7960 + buck + loose parts; INA219 now on the PCB)
rep("const BASE=[273.13,326.13],", "const BASE=[422.13,527.13],")   # PCB order 140-180 replaces BTS7960, buck, loose parts, WAGO, headers; + USB-C socket 4-15
rep("DP={lift:[8.09,17.89],flap:[12.79,18.79],upover:[14.09,29.89],parallel:[10.15,26.05]}", "DP={lift:[8.09,17.89],flap:[11.79,15.79],upover:[13.09,26.89],parallel:[9.15,23.05]}")
# ---------------- phase messages (fan now runs from the SHT40, not from the phase)
rep("msg:'Hot mop wash (1150 W) → rear fan on'}", "msg:'Hot mop wash (1150 W) → humidity rises'}")
rep("msg:'Mop drying → rear fan 60 %'}", "msg:'Mop drying with hot air → auto vent as needed'}")
print('js replacements ok')
