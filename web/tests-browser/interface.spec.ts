import {test,expect} from '@playwright/test';
const appointment={title:'Community studio visit',date:'18 September 2026',time:'9:20 AM',timezone:'India Standard Time',location:'Riverside Community Studio',reference:'DF 4821'};

test('missing configuration is explicit and cannot start a mock session',async({page})=>{
  await page.route('**/api/health',route=>route.fulfill({json:{configured:false,missing:['RIME_API_KEY'],speech:{model:'coda',provider:'Rime'},appointment,test_mode:false}}));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:/Let’s confirm/})).toBeVisible();
  await expect(page.getByRole('button',{name:'Start voice session'})).toBeDisabled();
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
