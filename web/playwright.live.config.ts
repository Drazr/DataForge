import { defineConfig } from '@playwright/test';
const python=process.platform==='win32'?'../.venv/Scripts/python.exe':'../.venv/bin/python';
export default defineConfig({
  testDir:'./tests-live',timeout:180_000,workers:1,retries:0,
  outputDir:'../evidence/browser-artifacts',
  reporter:[['list'],['json',{outputFile:'../evidence/live-tests.json'}]],
  use:{baseURL:'http://localhost:3000',headless:true,permissions:['microphone'],launchOptions:{args:['--autoplay-policy=no-user-gesture-required']}},
  webServer:[
    {command:`${python} -m uvicorn product.server:app --app-dir .. --host 127.0.0.1 --port 8000`,url:'http://127.0.0.1:8000/api/health',reuseExistingServer:true,env:{DATAFORGE_TEST_MODE:'1'},timeout:90_000},
    {command:'pnpm dev',url:'http://localhost:3000',reuseExistingServer:true,timeout:120_000},
  ],
});
