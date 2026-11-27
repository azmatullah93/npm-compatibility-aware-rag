/**
 * Evaluate version-pinned, LLM-generated CommonJS solutions.
 * --stage only prepares per-trial files, and NEVER executes generated code.
 * --prepare installs pinned npm packages on the trusted host (ignore-scripts).
 * --run ONLY executes candidate code in a restricted Docker container.
 * IMPORTANT: staging, installation and real execution have distinct statuses.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const specs = JSON.parse(fs.readFileSync(path.join(__dirname, 'execution_specs.json'), 'utf8'));
const args = process.argv.slice(2);
const has = k => args.includes(k);
function opt(k, def = '') {
  const i = args.indexOf(k);
  if (i < 0) return def;
  if (i === args.length - 1 || args[i + 1].startsWith('--')) throw Error(`Missing value for ${k}`);
  return args[i + 1];
}
const input = opt('--generated');
if (!input || !['--stage','--prepare','--run'].some(has)) {
  console.error('Usage: node milestone3/run_generated_code.cjs --generated FILE.jsonl [--stage | --prepare | --run] [--output RESULTS.json]');
  process.exit(2);
}
if ([has('--stage'),has('--prepare'),has('--run')].filter(Boolean).length !== 1) {
  throw Error('Choose exactly one mode: --stage, --prepare, or --run');
}
const mode = has('--stage') ? 'stage' : has('--prepare') ? 'prepare' : 'run';
const outputFile = path.resolve(opt('--output', path.join(__dirname, 'actual_execution_results.json')));
const rows = fs.readFileSync(path.resolve(input), 'utf8').split(/\r?\n/).filter(Boolean).map(JSON.parse);
const output = [];
const attemptedInstalls = new Map();
const safeName = str => String(str).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0,90);
const sha256 = s => crypto.createHash('sha256').update(s).digest('hex');
function evaluateRow(row, index) {
  const spec = specs[row.task_id];
  if (!spec) throw Error(`Unrecognized task id: ${row.task_id}`);
  if (spec.version !== row.target_version || spec.package !== row.package) {
    throw Error(`Package/version mismatch for ${row.task_id}`);
  }
  const meta = {trial: index,task_id: row.task_id,package: spec.package,
    target_version: spec.version,method: row.method,model: row.model};
  if (typeof row.code !== 'string' || !row.code.trim()) return {...meta,status:'NO_GENERATED_CODE'};

  const packageKey = safeName(`${spec.package}-${spec.version}`);
  const pkgdir = path.join(root, 'milestone3', 'npm_workspaces', packageKey);
  const identity = JSON.stringify([row.task_id,row.method,row.model,index]);
  const trialKey = `${safeName(row.task_id+'-'+row.method)}-${sha256(identity).slice(0,12)}`;
  const work = path.join(pkgdir, 'runs', trialKey);
  fs.mkdirSync(work, {recursive:true});
  fs.writeFileSync(path.join(work,'solution.cjs'),row.code);
  fs.writeFileSync(path.join(work,'test.cjs'),spec.test_js+'\n');
  const codeHash=sha256(row.code);
  const metaWithFile={...meta,code_sha256:codeHash};

  if (mode === 'stage') return {...metaWithFile,status:'STAGED_NOT_EXECUTED'};
  fs.mkdirSync(pkgdir, {recursive:true});
  const packageManifest = {name:'api-evaluation',version:'1.0.0',private:true,
    dependencies:{[spec.package]:spec.version}};
  fs.writeFileSync(path.join(pkgdir,'package.json'),JSON.stringify(packageManifest,null,2)+'\n');
  if (mode === 'prepare' && !attemptedInstalls.has(packageKey)) {
    const cmd = process.platform==='win32' ? (process.env.ComSpec||'cmd.exe') : 'npm';
    const npmArgs = process.platform==='win32' ? ['/d','/s','/c','npm install --ignore-scripts --no-audit --no-fund --save-exact']
      : ['install','--ignore-scripts','--no-audit','--no-fund','--save-exact'];
    const proc=cp.spawnSync(cmd,npmArgs,{
      cwd:pkgdir,encoding:'utf8',timeout:180000});
    attemptedInstalls.set(packageKey,proc);
  }
  const installed=path.join(pkgdir,'node_modules',spec.package,'package.json');
  if (mode === 'prepare' && attemptedInstalls.get(packageKey)?.status !== 0) {
    const p=attemptedInstalls.get(packageKey);
    return {...metaWithFile,status:'NPM_INSTALL_FAILED',error:String(p?.stderr || p?.error?.message || 'unknown').slice(-1000)};
  }
  if (!fs.existsSync(installed)) return {...metaWithFile,status:'MISSING_INSTALLED_PACKAGE'};
  const installedVersion=JSON.parse(fs.readFileSync(installed,'utf8')).version;
  if (installedVersion!==spec.version) return {...metaWithFile,status:'WRONG_INSTALLED_VERSION',installed_version:installedVersion};
  if (mode === 'prepare') return {...metaWithFile,status:'PREPARED',installed_version:installedVersion};

  // Generated code can only see the read-only trial files and pinned dependency
  // folder. Do NOT execute this code directly through host Node or a shell.
  const docker=cp.spawnSync('docker',[
    'run','--rm','--network','none','--read-only','--cap-drop','ALL',
    '--security-opt','no-new-privileges','--pids-limit','64',
    '--memory','256m','--cpus','1','--user','65534:65534',
    '--tmpfs','/tmp:rw,nosuid,noexec,size=16m',
    '--mount',`type=bind,source=${pkgdir},target=/deps,readonly`,
    '--mount',`type=bind,source=${work},target=/work,readonly`,
    '--env','NODE_PATH=/deps/node_modules','--workdir','/work',
    'node:22.16.0-bookworm-slim','node','/work/test.cjs'
  ],{encoding:'utf8',timeout:30000});
  const status=docker.error ? (docker.error.code==='ETIMEDOUT'?'DOCKER_TIMEOUT':'DOCKER_NOT_AVAILABLE') :
    [125,126,127].includes(docker.status) ? 'DOCKER_INFRA_ERROR' :
    docker.status===0 ? 'PASS' : 'FAIL';
  return {...metaWithFile,status,installed_version:installedVersion,
    exit_code:docker.status,stdout:(docker.stdout||'').slice(-1500),
    stderr:(docker.stderr||docker.error?.message||'').slice(-1500)};
}
for (let i=0;i<rows.length;i++) output.push(evaluateRow(rows[i],i));
fs.mkdirSync(path.dirname(outputFile),{recursive:true});
fs.writeFileSync(outputFile,JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({mode,results:outputFile,summary:output.reduce((a,r)=>(a[r.status]=(a[r.status]||0)+1,a),{})},null,2));
if (output.some(r=>['NPM_INSTALL_FAILED','WRONG_INSTALLED_VERSION','DOCKER_INFRA_ERROR','DOCKER_TIMEOUT','DOCKER_NOT_AVAILABLE'].includes(r.status)))process.exitCode=1;
