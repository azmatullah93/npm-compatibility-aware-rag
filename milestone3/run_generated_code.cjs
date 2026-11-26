/** Execute untrusted LLM code ONLY in Docker; never host Node.
 *
 * The preparation step downloads exact npm package versions into isolated
 * workspaces. The execution step uses Docker with network disabled, read-only
 * mounts, low resource limits, and no credentials in the container.
 */
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
const specs=JSON.parse(fs.readFileSync(path.join(__dirname,'execution_specs.json'),'utf8'));
const args=process.argv.slice(2);
function opt(k,def=''){let i=args.indexOf(k);return i<0?def:args[i+1]}
const file=opt('--generated');
if(!file){console.error('Usage: node milestone3/run_generated_code.cjs --generated FILE.jsonl [--prepare] [--run]');process.exit(2)}
if(!args.includes('--prepare')&&!args.includes('--run')){console.error('Use --prepare to install pinned npm dependencies, --run to evaluate in Docker');process.exit(2)}
const rows=fs.readFileSync(file,'utf8').split(/\r?\n/).filter(Boolean).map(JSON.parse);
const output=[];
const safeName=s=>s.replace(/[^a-zA-Z0-9_-]/g,'_');
for(const row of rows){
  const spec=specs[row.task_id];
  if(!spec)throw Error('Unrecognized task id '+row.task_id);
  if(spec.version!==row.target_version||spec.package!==row.package)throw Error('Version or package mismatch');
  if(!row.code){output.push({task_id:row.task_id,status:'NO_GENERATED_CODE'});continue}
  const work=path.join(root,'milestone3','npm_workspaces',safeName(spec.package+'-'+spec.version),safeName(row.task_id+'-'+row.method));
  fs.mkdirSync(work,{recursive:true});
  const pkgdir=path.join(root,'milestone3','npm_workspaces',safeName(spec.package+'-'+spec.version));
  const pkgManifest={name:'api-evaluation',version:'1.0.0',private:true,dependencies:{[spec.package]:spec.version}};
  fs.mkdirSync(pkgdir,{recursive:true});
  fs.writeFileSync(path.join(pkgdir,'package.json'),JSON.stringify(pkgManifest));
  // install once per package/version and symlink? Docker mount path preserves node_modules
  if(args.includes('--prepare')){
    const cmd=process.platform==='win32'?'npm.cmd':'npm';
    const result=cp.spawnSync(cmd,['install','--ignore-scripts','--no-audit','--no-fund','--save-exact'],{cwd:pkgdir,encoding:'utf8',timeout:180000});
    if(result.status!==0){output.push({task_id:row.task_id,status:'NPM_INSTALL_FAILED',error:(result.stderr||'').slice(-700)});continue}
  }
  if(!fs.existsSync(path.join(pkgdir,'node_modules',spec.package))){output.push({task_id:row.task_id,status:'MISSING_INSTALLED_PACKAGE'});continue}
  fs.writeFileSync(path.join(pkgdir,'solution.cjs'),row.code);
  fs.writeFileSync(path.join(pkgdir,'test.cjs'),spec.test_js+'\n');
  if(!args.includes('--run')){output.push({task_id:row.task_id,status:'PREPARED'});continue}
  const docker=cp.spawnSync('docker',['run','--rm','--network','none','--read-only','--cap-drop','ALL',
    '--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1',
    '--tmpfs','/tmp:rw,nosuid,noexec,size=16m','-v',pkgdir+':/work:ro','-w','/work',
    'node:22-bookworm-slim','node','/work/test.cjs'],{encoding:'utf8',timeout:30000});
  output.push({task_id:row.task_id,method:row.method,model:row.model,
    status:docker.error?'DOCKER_NOT_AVAILABLE':docker.status===0?'PASS':'FAIL',
    exit_code:docker.status,stdout:(docker.stdout||'').slice(-1500),stderr:(docker.stderr||'').slice(-1500)});
}
const out=path.join(__dirname,'actual_execution_results.json');
fs.writeFileSync(out,JSON.stringify(output,null,2)+'\n');
console.log('Execution status written to '+out);console.log(JSON.stringify(output,null,2));
