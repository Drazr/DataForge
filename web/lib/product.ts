export type Appointment = {title: string; date: string; time: string; timezone: string; location: string; reference: string};
export type SpeechRisk = {state:string;source:string;detector_installed:boolean;reported_at?:number};
export type Snapshot = { status: string; confirmed: boolean; turn: number; current_text: string; failure: string|null; appointment: Appointment; pending_fact:string|null;verified_facts:string[];fact_check_required:boolean;speech_risk:SpeechRisk };
export type Session = { id: string; capability: string; token: string; url: string; snapshot: Snapshot };
export type Health = { configured: boolean; missing: string[]; speech: Record<string,unknown>; appointment: Appointment; test_mode: boolean };

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function request<T>(path: string, session?: Session|null, action?: unknown, keepalive = false): Promise<T> {
  const response = await fetch(path, {
    keepalive,
    method: action === undefined ? 'GET' : 'POST',
    headers: { ...(session ? {Authorization: `Bearer ${session.capability}`} : {}),
      ...(action === undefined ? {} : {'Content-Type': 'application/json'}) },
    ...(action === undefined ? {} : {body: JSON.stringify(action)}),
  });
  if (!response.ok) {
    const error = await response.json().catch(()=>({})) as {detail?:unknown};
    throw new ApiError(typeof error.detail === 'string' ? error.detail : 'The voice worker could not complete that request.', response.status);
  }
  return response.json();
}

export const statusLabels: Record<string,string> = {ready:'Ready when you are',active:'Sharing your appointment',awaiting_fact:'Checking a critical detail',awaiting_confirmation:'Waiting for your confirmation',confirmed:'Appointment confirmed',ended:'Session ended',recovery:'Let’s reconnect'};
