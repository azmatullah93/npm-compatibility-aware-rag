/** Offline infrastructure test. NEVER executes generated JavaScript. */
'use strict';
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const cp=require('node:child_process');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'npm-runner-test-'));
const pkgdir=path.join(__dirname,'npm_workspaces','express-5_1_0');
const marker=`sandbox-runner-isolation-${process.pid}`;
const trialRows=[
  {task_id:'express-wildcard-task-new',package:'express',target_version:'5.1.0',method:`${marker}-baseline`,model:'test',code:'module.exports = () => 1;'},
  {task_id:'express-wildcard-task-new',package:'express',target_version:'5.1.0',method:`${marker}-compatible`,model:'test',code:'module.exports = () => 2;'},
];
try{
  const input=path.join(tmp,'input.jsonl'),output=path.join(tmp,'output.json');
  fs.writeFileSync(input,trialRows.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const r=cp.spawnSync(process.execPath,[path.join(__dirname,'run_generated_code.cjs'),'--generated',input,'--stage','--output',output],{encoding:'utf8',timeout:15000});
  assert.equal(r.status,0,`staging failed: ${r.stderr}\n${r.stdout}`);
  const results=JSON.parse(fs.readFileSync(output,'utf8'));
  assert.equal(results.length,2);
  assert.deepEqual(results.map(x=>x.status),['STAGED_NOT_EXECUTED','STAGED_NOT_EXECUTED']);
  assert.notEqual(results[0].code_sha256,results[1].code_sha256);
  const runs=path.join(pkgdir,'runs');
  const dirs=fs.readdirSync(runs).filter(x=>x.includes(marker));
  assert.equal(dirs.length,2,'Separate retrieval conditions must get separate directories');
  const code=dirs.map(x=>fs.readFileSync(path.join(runs,x,'solution.cjs'),'utf8')).sort();
  assert.deepEqual(code,trialRows.map(r=>r.code).sort());
  console.log('PASS 2/2 independent trial staging; NO generated code executed');
  for(const d of dirs)fs.rmSync(path.join(runs,d),{recursive:true,force:true});
} finally {fs.rmSync(tmp,{recursive:true,force:true});}
