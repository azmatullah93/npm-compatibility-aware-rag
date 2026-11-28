/** Synthetic assertion-script unit test; NOT evidence of real npm behavior. */
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const cp=require('node:child_process'),assert=require('node:assert/strict');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'probe-checker-test-'));
const script=path.join(__dirname,'check_real_probes.cjs');
const gold=[
  ['express','4.21.2','unnamed wildcard route accepted',true],
  ['express','5.1.0','unnamed wildcard route accepted',false],
  ['mongoose','6.13.8','Model.remove exists',true],
  ['mongoose','7.8.7','Model.remove exists',false],
  ['mongoose','6.13.8','Model.update exists',true],
  ['mongoose','7.8.7','Model.update exists',false],
  ['mongoose','6.13.8','ObjectId without new works',true],
  ['mongoose','7.8.7','ObjectId without new works',false],
].map(([pkg,version,probe,result])=>({pkg,version,probe,result}));
function check(data){const file=path.join(tmp,'synthetic.json');fs.writeFileSync(file,JSON.stringify(data));return cp.spawnSync(process.execPath,[script,file],{encoding:'utf8',timeout:10000})}
try{
  assert.equal(check(gold).status,0,'Correctly shaped test input should satisfy checker');
  const wrong=gold.map(x=>({...x}));wrong[0].result=!wrong[0].result;
  assert.notEqual(check(wrong).status,0,'Checker must reject wrong-version behaviors');
  assert.notEqual(check([...gold,{pkg:'express',version:'5.1.0',error:'registry unreachable'}]).status,0,'Checker must reject install errors');
  assert.notEqual(check(gold.slice(1)).status,0,'Checker must reject missing observations');
  console.log('PASS 4/4 checker behavior tests (synthetic inputs, no npm installed)');
}finally{fs.rmSync(tmp,{recursive:true,force:true})}
