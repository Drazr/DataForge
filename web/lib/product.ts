export type Appointment = {title: string; date: string; time: string; timezone: string; location: string; reference: string};
export type Snapshot = { status: string; confirmed: boolean; progress: Record<string,string>; turn: number; current_text: string; failure: string|null; appointment: Appointment };
export type Session = { id: string; capability: string; token: string; url: string; snapshot: Snapshot };
export type Health = { configured: boolean; missing: string[]; speech: Record<string,unknown>; appointment: Appointment; test_mode: boolean };

export async function request<T>(path: string, session?: Session|null, action?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: action === undefined ? 'GET' : 'POST',
    headers: { ...(session ? {Authorization: `Bearer ${session.capability}`} : {}),
      ...(action === undefined ? {} : {'Content-Type': 'application/json'}) },
    ...(action === undefined ? {} : {body: JSON.stringify(action)}),
  });
  if (!response.ok) {
    const error = await response.json().catch(()=>({})) as {detail?:unknown};
    throw new Error(typeof error.detail === 'string' ? error.detail : 'The voice worker could not complete that request.');
  }
  return response.json();
}

export const statusLabels: Record<string,string> = {ready:'Ready when you are',active:'Sharing your appointment',listening:'Listening to you',awaiting_confirmation:'Waiting for your confirmation',confirmed:'Appointment confirmed',ended:'Session ended',recovery:'Let’s reconnect'};
