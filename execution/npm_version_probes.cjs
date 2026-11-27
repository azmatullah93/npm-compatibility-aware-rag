/**
 * Actual-library version probes (not mocked). Requires network access for
 * initial npm install. This script is PROVIDED BUT HAS NOT BEEN RUN in the
 * offline authoring environment. Do not report its expected cases as results.
 *
 * Usage: node execution/npm_version_probes.cjs
 */
const fs = require('node:fs');
const crypto = require('node:crypto');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const { createRequire } = require('node:module');
const libraryVersions = [
  ['express','4.21.2'], ['express','5.1.0'],
  ['mongoose','6.13.8'], ['mongoose','7.8.7']
];
const results = [];
const environment = {node: process.version, platform:process.platform, arch:process.arch,
  recorded_at: new Date().toISOString(), resolved_versions:[]};
const outputDir=path.join(__dirname,'..','outputs');
const lockDir=path.join(outputDir,'npm_probe_locks');
fs.mkdirSync(lockDir,{recursive:true});
for (const [pkg, version] of libraryVersions) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'npm-api-evolution-'));
  fs.writeFileSync(path.join(dir,'package.json'), JSON.stringify({private:true, name:'api-probe',version:'1.0.0'}));
  try {
    const installCommand = process.platform === 'win32' ? (process.env.ComSpec || 'cmd.exe') : 'npm';
    const installArgs = process.platform === 'win32'
      ? ['/d', '/s', '/c', `npm install --no-audit --no-fund --ignore-scripts ${pkg}@${version}`]
      : ['install', '--no-audit', '--no-fund', '--ignore-scripts', `${pkg}@${version}`];
    cp.execFileSync(installCommand, installArgs, {
      cwd:dir, stdio:'pipe', timeout:120000, env:{...process.env, npm_config_update_notifier:'false'}
    });
    const resolvedPackage=JSON.parse(fs.readFileSync(path.join(dir,'node_modules',pkg,'package.json'),'utf8'));
    if (resolvedPackage.version !== version) throw Error(`Expected ${pkg}@${version}, installed ${resolvedPackage.version}`);
    const lock=fs.readFileSync(path.join(dir,'package-lock.json'));
    const lockHash=crypto.createHash('sha256').update(lock).digest('hex');
    fs.copyFileSync(path.join(dir,'package-lock.json'),path.join(lockDir,`${pkg}-${version}.json`));
    environment.resolved_versions.push({pkg,version,lockfile_sha256:lockHash});
    const lib = createRequire(path.join(dir,'package.json'))(pkg);
    if (pkg==='express') {
      const app = lib();
      results.push({pkg, version, probe:'app.del exists', result: typeof app.del==='function'});
      let acceptsWildcard;
      try { app.get('/*',()=>{}); acceptsWildcard=true; }
      catch (e) { acceptsWildcard=false; }
      results.push({pkg, version, probe:'unnamed wildcard route accepted', result:acceptsWildcard});
    } else {
      const M=lib.model('Probe',new lib.Schema({value:String}));
      results.push({pkg,version,probe:'Model.remove exists',result:typeof M.remove==='function'});
      results.push({pkg,version,probe:'Model.update exists',result:typeof M.update==='function'});
      let works;
      try { lib.Types.ObjectId('0'.repeat(24));works=true;}catch (e) {works=false;}
      results.push({pkg,version,probe:'ObjectId without new works',result:works});
    }
  } catch (e) {
    results.push({pkg,version,error:String(e.message)});
  } finally {
    fs.rmSync(dir,{recursive:true,force:true});
  }
}
const out=path.join(outputDir,'npm_version_probe_results.json');
fs.writeFileSync(path.join(outputDir,'npm_version_probe_environment.json'),JSON.stringify(environment,null,2)+'\n');
fs.writeFileSync(out,JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify(results,null,2));
if(results.some(r=>r.error)) process.exitCode=1;
