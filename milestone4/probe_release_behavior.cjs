/**
 * Release-pinned, independent API behavior probes (TRUSTED author code only).
 *
 * This is NOT a model-generation metric. The expected outcomes are specified
 * independently from milestone3/documents.json validity annotations and gold IDs.
 * All observations are against the exact installed npm releases. No MongoDB
 * server is used; Mongoose checks examine public API availability only.
 *
 * Requires milestone3/npm_workspaces/{express-4_21_2,express-5_1_0,
 * mongoose-6_13_8,mongoose-7_8_7} already prepared.
 *
 * node milestone4/probe_release_behavior.cjs
 */
'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs');
const path=require('node:path');
const {once}=require('node:events');
const {createRequire}=require('node:module');
const ROOT=path.resolve(__dirname,'..');
const RELEASES=[
  {name:'express',version:'4.21.2'},
  {name:'express',version:'5.1.0'},
  {name:'mongoose',version:'6.13.8'},
  {name:'mongoose',version:'7.8.7'}
];
const SOURCES={
  express:'https://expressjs.com/en/guide/migrating-5/',
  mongoose:'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'
};

function classifyCheck({case_id,pkg,version,expected,observed,source}) {
  if (typeof expected!=='boolean' || typeof observed!=='boolean') {
    throw Error('Each capability observation must be boolean');
  }
  return {case_id,pkg,version,expected,observed,passed:expected===observed,
          source};
}
function packageDir(pkg,version) {
  const safe=(pkg+'-'+version).replace(/[^a-zA-Z0-9_-]/g,'_');
  return path.join(ROOT,'milestone3','npm_workspaces',safe);
}
function loadPinned({name,version}) {
  const folder=packageDir(name,version);
  const installed=path.join(folder,'node_modules',name,'package.json');
  if (!fs.existsSync(installed)) {
    throw Error('Missing installed npm package '+name+'@'+version+
                '; run milestone4 reference --prepare first; no automatic installs');
  }
  const actual=JSON.parse(fs.readFileSync(installed,'utf8')).version;
  if (actual!==version) throw Error('Wrong installed version: expected '+version+' got '+actual);
  const pkg=createRequire(path.join(folder,'package.json'))(name);
  const lock=path.join(folder,'package-lock.json');
  return {pkg,installed,version,lock_sha256:fs.existsSync(lock)?
    crypto.createHash('sha256').update(fs.readFileSync(lock)).digest('hex'):null};
}
function canRegister(app,route) {
  try { app.get(route,(_req,res)=>res.sendStatus(200)); return true; }
  catch (_error) { return false; }
}
async function requestStatus(app,url) {
  const server=app.listen(0,'127.0.0.1');
  try {
    await once(server,'listening');
    const bound=server.address();
    assert.ok(bound && Number.isInteger(bound.port),'No bound TCP port');
    const response=await fetch('http://127.0.0.1:'+bound.port+url,
       {signal:AbortSignal.timeout(5000)});
    await response.arrayBuffer();
    return response.status;
  } finally {
    await new Promise((resolve,reject)=>
      server.close(error=>error?reject(error):resolve()));
  }
}
async function probe() {
  const observed=[];
  const environment={
    timestamp_utc:new Date().toISOString(),node:process.version,
    os:process.platform,arch:process.arch,experimental_scope:'4 exact pinned releases',
    real_package_imports:true,database_persistence_tested:false,
    generated_code_executed:false,release_locks:[]
  };
  function check(case_id,pkg,version,expected,value) {
    observed.push(classifyCheck({case_id,pkg,version,expected,observed:value,source:SOURCES[pkg]}));
  }
  for (const release of RELEASES) {
    const {name,version}=release;
    const {pkg,lock_sha256}=loadPinned(release);
    environment.release_locks.push({package:name,version,lockfile_sha256:lock_sha256});
    if (name==='express') {
      const old=version.startsWith('4.');
      check('express_app_del',name,version,old,typeof pkg().del==='function');
      const oldWildcard=pkg();
      const acceptsOld=canRegister(oldWildcard,'/*');
      check('express_unnamed_wildcard_registration',name,version,old,acceptsOld);
      if (old && acceptsOld) {
        check('express_old_wildcard_root',name,version,true,
              (await requestStatus(oldWildcard,'/'))===200);
        check('express_old_wildcard_nested',name,version,true,
              (await requestStatus(oldWildcard,'/deep/path'))===200);
      }
      const correct=pkg();
      const pathForVersion=old?'/*':'/{*splat}';
      assert.ok(canRegister(correct,pathForVersion),
          'Supported route unexpectedly rejected by '+name+'@'+version);
      check('express_supported_catchall_root',name,version,true,
            (await requestStatus(correct,'/'))===200);
      check('express_supported_catchall_nested',name,version,true,
            (await requestStatus(correct,'/nested/asset'))===200);
      const health=pkg();
      health.get('/health',(_req,res)=>res.status(200).send('ok'));
      check('express_stable_get_health',name,version,true,
            (await requestStatus(health,'/health'))===200);
    } else if (name==='mongoose') {
      const old=version.startsWith('6.');
      const modelName='ReleaseBehaviorProbe_'+version.replace(/\./g,'_');
      const Model=pkg.model(modelName,new pkg.Schema({name:String}));
      check('mongoose_model_remove',name,version,old,typeof Model.remove==='function');
      check('mongoose_model_update',name,version,old,typeof Model.update==='function');
      check('mongoose_delete_many',name,version,true,typeof Model.deleteMany==='function');
      check('mongoose_update_one',name,version,true,typeof Model.updateOne==='function');
      check('mongoose_stable_find_by_id',name,version,true,typeof Model.findById==='function');
      const query=Model.findById('507f1f77bcf86cd799439011');
      check('mongoose_find_by_id_returns_query',name,version,true,
           query!=null && typeof query.exec==='function');
      try {
        pkg.Types.ObjectId('000000000000000000000000');
        check('mongoose_object_id_without_new',name,version,old,true);
      } catch (_err) {
        check('mongoose_object_id_without_new',name,version,old,false);
      }
    }
  }
  return {environment,observations:observed,summary:{
    passed:observed.filter(x=>x.passed).length,
    failed:observed.filter(x=>!x.passed).length,
    total:observed.length
  }};
}
async function main() {
  const result=await probe();
  const file=path.join(ROOT,'milestone3','npm_workspaces','release_behavior_probes.json');
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const output=JSON.stringify(result,null,2)+'\n';
  if (fs.existsSync(file) && fs.readFileSync(file,'utf8')!==output) {
    // Each invocation is a new timestamped observation; keep previous reports.
    const archive=path.join(path.dirname(file),'release_behavior_probe_history');
    fs.mkdirSync(archive,{recursive:true});
    const suffix=new Date().toISOString().replace(/[:.]/g,'-');
    fs.renameSync(file,path.join(archive,'release_probe_'+suffix+'.json'));
  }
  fs.writeFileSync(file,output);
  console.log(JSON.stringify({path:file,summary:result.summary,
    releases:result.environment.release_locks},null,2));
  if(result.summary.failed) process.exitCode=1;
}
if (require.main===module) main().catch(e=>{console.error(e);process.exitCode=1});
module.exports={classifyCheck,packageDir,probe};
