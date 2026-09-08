import { test,expect,type Page } from '@playwright/test';
import { readFileSync,mkdirSync,writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Session,Snapshot } from '../lib/product';

// Acceptance procedures are version-controlled before measurements. Synthetic
// caller audio reaches the real browser microphone track, VAD and cloud STT.
async function installCaller(page:Page){
  await page.addInitScript(()=>{
    const w=window as any;
    let context:AudioContext;
    let destination:MediaStreamAudioDestinationNode;
    const ensure=()=>{context??=new AudioContext();destination??=context.createMediaStreamDestination();};
    const samples:{at:number;rms:number}[]=[];
    const recordings:Blob[]=[];
    const recorders:MediaRecorder[]=[];
    w.__caller={
      samples,
      async say(base64:string){
        ensure();await context.resume();
        const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
        const buffer=await context.decodeAudioData(bytes.buffer);
        const source=context.createBufferSource();source.buffer=buffer;source.connect(destination);
        const start=performance.now();source.start();
        await new Promise<void>(done=>{source.onended=()=>done();});
        return {start,end:performance.now()};
      },
      async finish(){
        await Promise.all(recorders.map(recorder=>new Promise<void>(done=>{if(recorder.state==='inactive')return done();recorder.addEventListener('stop',()=>done(),{once:true});recorder.stop();})));
        const blob=new Blob(recordings,{type:'audio/webm'});
        const bytes=new Uint8Array(await blob.arrayBuffer());
        let raw='';for(const byte of bytes)raw+=String.fromCharCode(byte);
        return {samples,audio:btoa(raw)};
      }
    };
    navigator.mediaDevices.getUserMedia=async()=>{ensure();await context.resume();return destination.stream.clone();};
    const descriptor=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'srcObject')!;
    const seen=new WeakSet<MediaStream>();
    Object.defineProperty(HTMLMediaElement.prototype,'srcObject',{
      ...descriptor,set(stream:MediaStream){
        descriptor.set!.call(this,stream);
        if(stream?.getAudioTracks().length&&!seen.has(stream)){
          seen.add(stream);ensure();
          const source=context.createMediaStreamSource(stream),analyser=context.createAnalyser();
          source.connect(analyser);analyser.fftSize=1024;
          const values=new Float32Array(analyser.fftSize);
          setInterval(()=>{analyser.getFloatTimeDomainData(values);samples.push({at:performance.now(),rms:Math.sqrt(values.reduce((sum,v)=>sum+v*v,0)/values.length)});},20);
          const recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>recordings.push(e.data);recorder.start(250);recorders.push(recorder);
        }
      }
    });
  });
}

async function begin(page:Page,mode='normal'){
  await installCaller(page);
  let session:Session|undefined;
  await page.route('**/api/sessions',async route=>{
    const response=await route.fetch({postData:JSON.stringify({cache_mode:mode})});
    if(response.ok())session=await response.json();
    await route.fulfill({response});
  });
  await page.goto('/');
  const health=await page.request.get('/api/health').then(r=>r.json());
  expect(health.configured,'Configure the worker .env before live verification.').toBe(true);
  expect(health.test_mode,'Start the backend with DATAFORGE_TEST_MODE=1 for live verification.').toBe(true);
  await page.getByRole('button',{name:'Start voice session'}).click();
  await expect.poll(()=>session,{timeout:75_000}).toBeTruthy();
  return session!;
}
async function state(page:Page,s:Session):Promise<Snapshot>{
  const response=await page.request.get(`/api/sessions/${s.id}`,{headers:{Authorization:`Bearer ${s.capability}`}});
  expect(response.ok()).toBe(true);return response.json();
}
async function action(page:Page,s:Session,name:string){
  const response=await page.request.post(`/api/sessions/${s.id}/action`,{headers:{Authorization:`Bearer ${s.capability}`},data:{action:name}});
  expect(response.ok()).toBe(true);
}
async function say(page:Page,name:string){
  const bytes=readFileSync(resolve('../evidence/caller-fixtures',name+'.wav')).toString('base64');
  return page.evaluate(async bytes=>await (window as any).__caller.say(bytes),bytes);
}
async function save(page:Page,s:Session,name:string){
  const report=await page.request.get(`/api/sessions/${s.id}/evidence`,{headers:{Authorization:`Bearer ${s.capability}`}}).then(r=>r.json());
  const browser=await page.evaluate(async()=>await (window as any).__caller.finish());
  const directory=resolve('../evidence/live',name);mkdirSync(directory,{recursive:true});
  writeFileSync(resolve(directory,'received.webm'),Buffer.from(browser.audio,'base64'));
  writeFileSync(resolve(directory,'events.json'),JSON.stringify({...report,browser_samples:browser.samples},null,2));
  return {report,browser};
}

for(const mode of ['bypass','normal'])test(`normal confirmation with ${mode} cache`,async({page})=>{
  const s=await begin(page,mode);
  try{
    await expect.poll(async()=>(await state(page,s)).status,{timeout:100_000}).toBe('awaiting_confirmation');
    expect((await state(page,s)).confirmed).toBe(false);
    await say(page,'yes');
    await expect.poll(async()=>(await state(page,s)).confirmed,{timeout:20_000}).toBe(true);
    await expect.poll(async()=>(await state(page,s)).current_text,{timeout:20_000}).toBe('');
    const {report,browser}=await save(page,s,`normal-${mode}`);
    expect(report.events.filter((e:any)=>e.event==='confirmed')).toHaveLength(1);
    expect(browser.samples.some((s:any)=>s.rms>.003)).toBe(true);
    const audio=report.events.filter((e:any)=>e.event==='audio_ready');
    expect(audio.length).toBeGreaterThan(3);
    expect(audio.every((e:any)=>e.cached===(mode==='normal'))).toBe(true);
  }finally{await action(page,s,'end');}
});

test('spoken interruption cancels output and repeats the requested detail',async({page})=>{
  const s=await begin(page);
  try{
    await page.waitForFunction(()=> (window as any).__caller.samples.some((s:any)=>s.rms>.01),{},{timeout:60_000});
    const input=await say(page,'repeat');
    const stopped=await page.evaluate((start:number)=>{
      const samples=(window as any).__caller.samples.filter((s:any)=>s.at>=start);
      // Require at least 100 ms of consecutive quiet, not one zero crossing.
      for(let i=0;i<samples.length-5;i++)if(samples.slice(i,i+6).every((s:any)=>s.rms<.003))return samples[i].at-start;
      return null;
    },input.start);
    expect(stopped,'Received speech should stop within the frozen 1500 ms engineering bound.').not.toBeNull();
    expect(stopped!).toBeLessThanOrEqual(1500);
    await expect.poll(async()=>(await state(page,s)).status,{timeout:100_000}).toBe('awaiting_confirmation');
    expect((await state(page,s)).confirmed).toBe(false);
    const {report}=await save(page,s,'interruption');
    expect(report.events.some((e:any)=>e.event==='intent'&&e.intent==='repeat'&&e.detail==='time')).toBe(true);
  }finally{await action(page,s,'end');}
});

test('provider failure is disclosed and recovery asks for a fresh confirmation',async({page})=>{
  const s=await begin(page);
  try{
    await expect.poll(async()=>(await state(page,s)).status,{timeout:100_000}).toBe('awaiting_confirmation');
    await action(page,s,'fail_next_synthesis');
    await say(page,'repeat');
    await expect.poll(async()=>(await state(page,s)).status,{timeout:20_000}).toBe('recovery');
    expect((await state(page,s)).confirmed).toBe(false);
    await page.waitForTimeout(6000); // allow disclosed recovery prompt to finish
    await action(page,s,'recover');
    await expect.poll(async()=>(await state(page,s)).status,{timeout:60_000}).toBe('awaiting_confirmation');
    const {report}=await save(page,s,'provider-failure');
    expect(report.events.some((e:any)=>e.event==='failure'&&e.category==='speech_provider')).toBe(true);
    expect(report.events.some((e:any)=>e.event==='fallback'&&e.cached_rime===true)).toBe(true);
  }finally{await action(page,s,'end');}
});

test('connection loss clears confirmation eligibility',async({page})=>{
  const s=await begin(page);
  try{
    await expect.poll(async()=>(await state(page,s)).status,{timeout:100_000}).toBe('awaiting_confirmation');
    await page.context().setOffline(true);await page.waitForTimeout(2500);await page.context().setOffline(false);
    // Explicit browser control records transport loss even before SDK timeout.
    await action(page,s,'connection_lost');
    expect((await state(page,s)).status).toBe('recovery');
    expect((await state(page,s)).confirmed).toBe(false);
    await save(page,s,'connection-loss');
  }finally{await page.context().setOffline(false);await action(page,s,'end');}
});
