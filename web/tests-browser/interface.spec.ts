import {test,expect} from '@playwright/test';
const appointment={title:'Community studio visit',date:'18 September 2026',time:'9:20 AM',timezone:'India Standard Time',location:'Riverside Community Studio',reference:'DF 4821'};

test('missing configuration is explicit and cannot start a mock session',async({page})=>{
  await page.route('**/api/health',route=>route.fulfill({json:{configured:false,missing:['RIME_API_KEY'],speech:{model:'coda',provider:'Rime'},appointment,test_mode:false}}));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:/Let’s confirm/})).toBeVisible();
  await expect(page.getByRole('button',{name:'Start voice session'})).toBeDisabled();
  await expect(page.getByText(/Configure these in the worker/)).toBeAttached();
  await page.getByText('Connection details & session evidence').click();
  await expect(page.getByText(/Configure these in the worker/)).toContainText('RIME_API_KEY');
  await expect(page.getByText('Awaiting your voice confirmation')).toBeVisible();
});

test('provider setup failure is visible without reporting confirmation',async({page})=>{
  await page.route('**/api/health',route=>route.fulfill({json:{configured:true,missing:[],speech:{model:'coda'},appointment,test_mode:false}}));
  await page.route('**/api/sessions',route=>route.fulfill({status:503,json:{detail:'Voice setup failed. Run the product preflight.'}}));
  await page.goto('/');
  await page.getByRole('button',{name:'Start voice session'}).click();
  await expect(page.getByRole('alert')).toContainText('Voice setup failed');
  await expect(page.getByText('Awaiting your voice confirmation')).toBeVisible();
  await expect(page.getByRole('button',{name:'Start voice session'})).toBeEnabled();
});

test('mobile screen keeps the primary task visible and fits the viewport',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.route('**/api/health',route=>route.fulfill({json:{configured:false,missing:['RIME_API_KEY'],speech:{},appointment,test_mode:false}}));
  await page.goto('/');
  await expect(page.getByRole('button',{name:'Start voice session'})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});

test('optional WebMCP end tool validates input and shares the visible action',async({page})=>{
  await page.addInitScript(()=>{
    Object.defineProperty(document,'modelContext',{value:{registerTool:(tool:unknown)=>{(window as any).__registered=tool;}}});
  });
  await page.route('**/api/health',route=>route.fulfill({json:{configured:false,missing:[],speech:{},appointment,test_mode:false}}));
  await page.goto('/');
  await page.waitForFunction(()=>Boolean((window as any).__registered));
  expect(await page.evaluate(()=>(window as any).__registered.name)).toBe('end_voice_session');
  const rejected=await page.evaluate(async()=>{try{await (window as any).__registered.execute({confirm:true});return false;}catch{return true;}});
  expect(rejected).toBe(true);
  expect(await page.evaluate(async()=>await (window as any).__registered.execute({}))).toEqual({ended:true});
});

test('expired session does not prevent starting a replacement',async({page})=>{
  let creates=0;
  await page.route('**/api/health',route=>route.fulfill({json:{configured:true,missing:[],speech:{},appointment,test_mode:false}}));
  await page.route('**/api/sessions',route=>{
    creates++;
    return route.fulfill({json:{id:`expired-${creates}`,capability:'test-only',token:'invalid-token',url:'not-a-url',snapshot:{status:'ready',confirmed:false,progress:{},turn:0,current_text:'',failure:null,appointment}}});
  });
  await page.route('**/api/sessions/*',route=>route.fulfill({status:404,json:{detail:'Session not found or expired.'}}));
  await page.route('**/api/sessions/*/action',route=>route.fulfill({status:404,json:{detail:'Session not found or expired.'}}));
  await page.goto('/');
  await page.getByRole('button',{name:'Start voice session'}).click();
  await expect(page.getByRole('button',{name:'Start a new session'})).toBeEnabled();
  await page.getByRole('button',{name:'Start a new session'}).click();
  await expect.poll(()=>creates).toBe(2);
  await expect(page.getByText('Awaiting your voice confirmation')).toBeVisible();
});

test('ending during connection setup releases the UI before remote cleanup finishes',async({page})=>{
  let creates=0;
  let finishEnd!:()=>void;
  const pendingEnd=new Promise<void>(resolve=>{finishEnd=resolve;});
  const snapshot={status:'ready',confirmed:false,progress:{},turn:0,current_text:'',failure:null,appointment};
  // Keep the signaling handshake pending without contacting a real provider.
  await page.routeWebSocket('ws://localhost:39999/**',()=>{});
  await page.route('**/api/health',route=>route.fulfill({json:{configured:true,missing:[],speech:{},appointment,test_mode:false}}));
  await page.route('**/api/sessions',route=>{
    creates++;
    return route.fulfill({json:{id:`connecting-${creates}`,capability:'test-only',token:'invalid-token',url:'ws://localhost:39999',snapshot}});
  });
  await page.route('**/api/sessions/*',route=>route.fulfill({json:snapshot}));
  await page.route('**/api/sessions/*/action',async route=>{
    if(route.request().postDataJSON().action==='end')await pendingEnd;
    await route.fulfill({json:{...snapshot,status:'ended'}});
  });
  try{
    await page.goto('/');
    await page.getByRole('button',{name:'Start voice session'}).click();
    await page.getByRole('button',{name:'End session'}).click();
    await expect(page.getByRole('button',{name:'Start a new session'})).toBeEnabled();
    await page.getByRole('button',{name:'Start a new session'}).click();
    await expect.poll(()=>creates).toBe(2);
    finishEnd();
    await expect(page.getByRole('button',{name:'End session'})).toBeVisible();
    await expect(page.getByText('Awaiting your voice confirmation')).toBeVisible();
  }finally{finishEnd();}
});

test('ending before session creation completes closes the late worker without starting audio',async({page})=>{
  let finishCreate!:()=>void;
  const pendingCreate=new Promise<void>(resolve=>{finishCreate=resolve;});
  let ends=0;
  await page.route('**/api/health',route=>route.fulfill({json:{configured:true,missing:[],speech:{},appointment,test_mode:false}}));
  await page.route('**/api/sessions',async route=>{
    await pendingCreate;
    await route.fulfill({json:{id:'late-worker',capability:'test-only',token:'invalid-token',url:'not-a-url',snapshot:{status:'ready',confirmed:false,progress:{},turn:0,current_text:'',failure:null,appointment}}});
  });
  await page.route('**/api/sessions/late-worker/action',route=>{
    expect(route.request().postDataJSON().action).toBe('end');ends++;
    return route.fulfill({json:{status:'ended',confirmed:false,progress:{},turn:0,current_text:'',failure:null,appointment}});
  });
  try{
    await page.goto('/');
    await page.getByRole('button',{name:'Start voice session'}).click();
    await page.getByRole('button',{name:'End session'}).click();
    await expect(page.getByRole('button',{name:'Start voice session'})).toBeEnabled();
    finishCreate();
    await expect.poll(()=>ends).toBe(1);
    await expect(page.getByRole('button',{name:'End session'})).toHaveCount(0);
    await expect(page.getByText('Awaiting your voice confirmation')).toBeVisible();
  }finally{finishCreate();}
});
