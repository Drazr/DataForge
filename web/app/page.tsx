'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Headphones, ArrowUpRight, CalendarDays, ShieldCheck, Mic, MicOff, PhoneOff, Download } from 'lucide-react';
import { Room, RoomEvent } from 'livekit-client';
import { RoomContext, RoomAudioRenderer, StartAudio } from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { ApiError, request, statusLabels, type Session, type Snapshot, type Health } from '@/lib/product';

type Connection = {room:Room|null;session:Session|null};
async function release({room,session}:Connection):Promise<Snapshot|undefined> {
  const results=await Promise.allSettled([
    room?.disconnect(),
    session?request<Snapshot>(`/api/sessions/${session.id}/action`,session,{action:'end'},true):undefined,
  ]);
  const response=results[1];
  if(response.status==='fulfilled')return response.value;
  if(!(response.reason instanceof ApiError&&response.reason.status===404))throw response.reason;
}

export default function Home() {
  const [health, setHealth] = useState<Health|null>(null);
  const [session, setSession] = useState<Session|null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot|null>(null);
  const [room, setRoom] = useState<Room|null>(null);
  const [busy, setBusy] = useState(false);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState('');
  const current = useRef<Connection>({room:null,session:null});
  const generation = useRef(0);
  const busyRef = useRef(false);
  const state = snapshot?.status ?? 'ready';
  const terminal = state === 'confirmed' || state === 'ended';
  const appointment = snapshot?.appointment ?? health?.appointment;

  // Detach immediately: remote teardown must never keep a stale session active.
  const detach = useCallback(()=>{
    const previous=current.current;
    current.current={room:null,session:null};generation.current++;
    busyRef.current=false;setBusy(false);setRoom(null);
    setSnapshot(value=>value?{...value,status:value.confirmed?'confirmed':'ended',current_text:''}:value);
    return previous;
  },[]);

  useEffect(()=>{
    if(terminal&&room)void room.localParticipant.setMicrophoneEnabled(false).then(()=>{if(current.current.room===room)setMuted(true);}).catch(()=>{});
  },[terminal,room]);

  useEffect(()=>{
    request<Health>('/api/health').then(setHealth).catch(()=>setError('The local voice worker is not running. Start it, then reload this page.'));
    return ()=> {
      const previous=current.current;
      generation.current++;current.current={room:null,session:null};busyRef.current=false;
      void release(previous).catch(()=>{});
    };
  },[]);

  useEffect(()=>{
    if (!session) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async()=> {
      if(current.current.session!==session)return;
      try {const next=await request<Snapshot>(`/api/sessions/${session.id}`,session); if(active&&current.current.session===session)setSnapshot(next);}
      catch(e){
        if(active&&current.current.session===session){
          setError((e as Error).message);
          if(e instanceof ApiError&&e.status===404){active=false;void release(detach()).catch(()=>{});}
        }
      }
      if(active)timer=setTimeout(poll,500);
    };
    void poll();
    return ()=>{active=false;clearTimeout(timer);};
  },[session,detach]);

  const action = useCallback(async(name:string)=>{
    const s=current.current.session;
    if(!s)throw new Error('Start a voice session first.');
    const next=await request<Snapshot>(`/api/sessions/${s.id}/action`,s,{action:name});
    if(current.current.session===s)setSnapshot(next);return next;
  },[]);

  const end = useCallback(async()=>{
    const previous=detach(),epoch=generation.current;
    try{
      const next=await release(previous);
      if(next&&generation.current===epoch)setSnapshot(next);
    }catch(e){if(generation.current===epoch)throw e;}
  },[detach]);

  const start = useCallback(async()=>{
    if(busyRef.current)return;
    void release(detach()).catch(()=>{});
    const epoch=generation.current;
    busyRef.current=true;setBusy(true);setError('');
    let next:Session|null=null;
    const connection=new Room({adaptiveStream:true,dynacast:true});
    const isCurrent=()=>generation.current===epoch;
    const checkCurrent=()=>{if(!isCurrent())throw new Error('Session ended.');};
    try {
      next=await request<Session>('/api/sessions',null,{});
      checkCurrent();
      current.current={room:connection,session:next};setSession(next);setSnapshot(next.snapshot);setRoom(connection);
      connection.on(RoomEvent.Reconnecting,()=>{
        if(isCurrent())void action('connection_lost').catch(e=>{if(isCurrent())setError(e.message);});
      });
      connection.on(RoomEvent.Disconnected,()=>{
        if(isCurrent()){setError('Audio disconnected. Your session needs recovery before it can continue.');void action('connection_lost').catch(()=>{});}
      });
      connection.on(RoomEvent.MediaDevicesError,()=>{if(isCurrent())setError('Microphone access failed. Check your browser permissions.');});
      await connection.connect(next.url,next.token);
      checkCurrent();
      await connection.startAudio();
      checkCurrent();
      await connection.localParticipant.setMicrophoneEnabled(true,{echoCancellation:true,noiseSuppression:false,autoGainControl:false});
      checkCurrent();
      setMuted(false);
      await action('start');
    } catch(e) {
      if(isCurrent()){setError((e as Error).message);detach();}
      await release({room:connection,session:next}).catch(()=>{});
    } finally {if(isCurrent()){busyRef.current=false;setBusy(false);}}
  },[action,detach]);

  const mute = async()=>{
    try {if(room){await room.localParticipant.setMicrophoneEnabled(muted);if(current.current.room===room)setMuted(!muted);}}
    catch {setError('The microphone could not be changed.');}
  };
  const recover = async()=>{
    if(busyRef.current)return;
    const epoch=generation.current;
    const checkCurrent=()=>{if(generation.current!==epoch)throw new Error('Session ended.');};
    busyRef.current=true;setBusy(true);setError('');
    try {
      const s=current.current.session,r=current.current.room;
      if(s&&r&&r.state==='disconnected'){
        await r.connect(s.url,s.token);checkCurrent();
        await r.startAudio();checkCurrent();
        await r.localParticipant.setMicrophoneEnabled(true,{echoCancellation:true,noiseSuppression:false,autoGainControl:false});checkCurrent();
        setMuted(false);
      }
      checkCurrent();
      await action('recover');
    }catch(e){if(generation.current===epoch)setError((e as Error).message);}
    finally{if(generation.current===epoch){busyRef.current=false;setBusy(false);}}
  };
  const exportEvidence = async()=>{
    try{
      const s=session;if(!s)return;
      const data=await request(`/api/sessions/${s.id}/evidence`,s);
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download=`dataforge-${s.id}.json`;link.click();URL.revokeObjectURL(url);
    }catch(e){setError((e as Error).message);}
  };

  useEffect(()=>{
    const context=(document as Document & {modelContext?:{registerTool:(tool:unknown,options:unknown)=>void|Promise<void>}}).modelContext;
    if(!context)return;
    const lifecycle=new AbortController();
    const tool={name:'end_voice_session',description:'End the current DataForge voice session. Does not confirm an appointment.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false},execute:async(input:unknown)=>{
      if(!input||typeof input!=='object'||Object.keys(input).length)throw new Error('Expected an empty object.');
      await end();return {ended:true};
    }};
    try{void Promise.resolve(context.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch{/* Optional browser capability. */}
    return ()=>lifecycle.abort();
  },[end]);

  return <main className="shell">
    <header className="topbar"><a className="brand" href="/">dataforge<span>VOICE</span></a><span className="tag">LOCAL DEMO · SYNTHETIC APPOINTMENT</span></header>
    <div className="intro"><p className="eyebrow">ONE CONVERSATION. EVERY DETAIL.</p><h1>Let’s confirm<br/>your appointment.</h1><p>Listen to the details, then confirm or ask again.</p></div>
    <div className="workspace"><section className="conversation" aria-label="Voice conversation">
      <div className="section-label"><span className="status-dot"/>{busy?'Connecting voice…':statusLabels[state]??state}<span>01 / CONVERSATION</span></div>
      <div className={`voice-circle ${snapshot?.current_text?'active':''}`}><Headphones size={52} strokeWidth={1.4}/></div>
      <h2>{snapshot?.confirmed?'You’re all set.':state==='ended'?'Your session has ended.':'A little clarity goes a long way.'}</h2>
      <p>{snapshot?.confirmed?'Your practice appointment is confirmed.':<>Hear the time, location, and reference code.<br/>Wait for the question, then reply or ask for a repeat.</>}</p>
      {(!room||terminal)&&<Button className="primary" disabled={busy||!health?.configured} onClick={start}><Headphones size={18}/>{session?'Start a new session':'Start voice session'}<ArrowUpRight size={18}/></Button>}
      {(room||busy)&&<div className="controls">{room&&!terminal&&<Button variant="outline" className="secondary" onClick={mute} disabled={busy}>{muted?<MicOff size={18}/>:<Mic size={18}/>} {muted?'Unmute':'Mute'}</Button>}<Button variant="outline" className="secondary" onClick={()=>void end().catch(e=>setError(e.message))}><PhoneOff size={18}/> End session</Button></div>}
      {room&&!terminal&&<Button variant="outline" className="secondary" style={{marginTop:10,borderColor:'#e2a52d',color:'#704d08',background:'#fff9ec'}} disabled={busy} onClick={()=>void action('hearing_difficulty').catch(e=>setError(e.message))}><Headphones size={18}/>Hearing another voice?</Button>}
      {state==='recovery'&&<Button className="primary" disabled={busy} onClick={recover}>Retry connection</Button>}
      <p className="fine">{muted?'Microphone muted. Unmute to answer.':'Microphone access is needed to speak.'}</p>
      <output aria-live="polite">{snapshot?.confirmed?'No real booking has been changed.':state==='ended'?'Your appointment was not confirmed.':state==='recovery'?'Service interrupted. Your appointment remains unconfirmed.':state==='awaiting_fact'?`Say the ${snapshot?.pending_fact==='reference'?'reference code':'appointment time'} now.`:snapshot?.speech_risk?.state==='suspected'?'Hearing difficulty reported. Code and time must be checked before confirmation.':!health?.configured?'Voice setup is needed before you can begin. Open connection details below.':'Your appointment is not confirmed yet.'}</output>
      {error&&<p role="alert" className="error">{error}</p>}
      {room&&<RoomContext.Provider value={room}><RoomAudioRenderer/><StartAudio label="Enable speaker audio"/></RoomContext.Provider>}
    </section>
    <aside className="appointment"><div className="section-label"><CalendarDays size={18}/> YOUR APPOINTMENT</div><h2>{appointment?.title??'Community studio visit'}</h2><p className="muted">A practice appointment, made for this demo.</p><dl><div><dt>Date & time</dt><dd>{appointment?.date??'18 September 2026'}<br/>{appointment?.time??'9:20 AM'} · {appointment?.timezone??'India Standard Time'}</dd></div><div><dt>Location</dt><dd>{appointment?.location??'Riverside Community Studio'}</dd></div><div><dt>Reference code</dt><dd className="reference">{appointment?.reference??'DF 4821'}</dd></div></dl><div className={`outcome ${snapshot?.confirmed?'confirmed':''}`}><ShieldCheck size={20}/><span>{snapshot?.confirmed?'Confirmed by you':'Awaiting your voice confirmation'}</span></div></aside></div>
    <details className="diagnostics"><summary>Connection details & session evidence</summary><p className="fine">Rime is the only speech provider. Automatic competing-speech detection is not installed; hearing difficulty is user-reported or visibly injected in test mode. Cached recovery audio is labeled in the exported events.</p>{health?.missing.length? <p className="error">Configure these in the worker’s .env file: {health.missing.join(', ')}. Restart the worker and reload this page.</p>:null}<pre>{JSON.stringify({speech:health?.speech,session:snapshot},null,2)}</pre>{session&&<Button variant="outline" className="secondary" onClick={exportEvidence}><Download size={16}/>Export session evidence</Button>}{health?.test_mode&&room&&!terminal&&<><Button variant="outline" className="secondary" onClick={()=>void action('competing_speech_demo').catch(e=>setError(e.message))}>Inject disclosed speech-risk event</Button><Button variant="outline" className="secondary" onClick={()=>void action('speech_failure').catch(e=>setError(e.message))}>Demonstrate speech failure</Button></>}</details>
    <footer><span>Rime speech · Guided conversation</span><span>You’re in control. End the session at any time.</span></footer>
  </main>;
}
