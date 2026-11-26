/** Prove Node execution runner works with local stand-ins; NOT genuine npm. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'azmat-api-selftest-'));
let result=[];
const cases=[
 {id:'express-4-old-wildcard',kind:'express',version:4,route:'/*',expect:true},
 {id:'express-5-old-wildcard',kind:'express',version:5,route:'/*',expect:false},
 {id:'express-5-new-wildcard',kind:'express',version:5,route:'/{*splat}',expect:true},
 {id:'express-4-delete-alias',kind:'express',version:4,method:'del',expect:true},
 {id:'express-5-delete-alias',kind:'express',version:5,method:'del',expect:false},
 {id:'express-5-delete-method',kind:'express',version:5,method:'delete',expect:true},
 {id:'mongoose-6-remove',kind:'mongoose',version:6,method:'remove',expect:true},
 {id:'mongoose-7-remove',kind:'mongoose',version:7,method:'remove',expect:false},
 {id:'mongoose-7-deleteMany',kind:'mongoose',version:7,method:'deleteMany',expect:true},
 {id:'mongoose-6-update',kind:'mongoose',version:6,method:'update',expect:true},
 {id:'mongoose-7-update',kind:'mongoose',version:7,method:'update',expect:false},
 {id:'mongoose-7-updateOne',kind:'mongoose',version:7,method:'updateOne',expect:true}
];
try{
 for(const c of cases){
   const src=c.kind==='express'
      ?`const api={}; api.get=function(route){ if(${c.version}===5 && route==='/*') throw Error('unnamed wildcard'); return true }; if(${c.version}===4){api.del=()=>true} api.delete=()=>true; ${c.route?`api.get(${JSON.stringify(c.route)})`:`api[${JSON.stringify(c.method)}]()`}`
      :`const api={}; if(${c.version}===6){api.remove=()=>true; api.update=()=>true} api.deleteMany=()=>true;api.updateOne=()=>true;api[${JSON.stringify(c.method)}]()`;
   const f=path.join(dir,c.id+'.cjs');fs.writeFileSync(f,src);
   const run=cp.spawnSync(process.execPath,[f],{encoding:'utf8',timeout:3000});
   const success=run.status===0;
   result.push({case:c.id,author_defined_expected_success:c.expect,actual_success:success,match:c.expect===success});
   assert.equal(success,c.expect,c.id);
 }
}finally{fs.rmSync(dir,{recursive:true,force:true})}
const output=path.join(__dirname,'fixture_execution_selftest.json');
fs.writeFileSync(output,JSON.stringify({source:'locally emulated API signatures, NOT real npm packages',
  cases:result,pass:result.filter(x=>x.match).length,total:result.length},null,2)+'\n');
console.log('Node fixture execution self-test:',result.filter(x=>x.match).length,'/',result.length,'cases matched');
