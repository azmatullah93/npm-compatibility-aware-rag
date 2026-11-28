/** Trusted unit regression: only synthetic, locally authored exports are loaded.
 * NEVER loads or runs an LLM-generated solution.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {acceptNamedSetupExport} = require('./export_contract.cjs');
const specs = JSON.parse(fs.readFileSync(path.join(__dirname,'execution_specs.json'),'utf8'));

for (const [id, spec] of Object.entries(specs)) {
  const adapted = acceptNamedSetupExport(spec.test_js);
  assert.notEqual(adapted, spec.test_js, id + ': source was not adapted');
  new vm.Script(adapted, {filename: id + '/export-compatible-test.cjs'});
}

const tinySource = "module.exports = require('./solution.cjs')('stub');";
const strict = candidate => {
  const sandbox = {module: {exports:null}, require: () => candidate};
  vm.runInNewContext(tinySource,sandbox);
  return sandbox.module.exports;
};
const compatible = candidate => {
  const sandbox = {module: {exports:null}, require: () => candidate};
  vm.runInNewContext(acceptNamedSetupExport(tinySource),sandbox);
  return sandbox.module.exports;
};
const setup = () => 'OK';
assert.equal(strict(setup),'OK');
assert.throws(()=>strict({setup}),TypeError);
assert.equal(compatible(setup),'OK');
assert.equal(compatible({setup}),'OK');
assert.throws(()=>compatible({bad:'wrong'}),/Expected a directly exported function or a named setup function/);
assert.throws(()=>acceptNamedSetupExport('no candidate import'),/Expected exactly one/);
console.log('PASS: strict export contract preserved and named-export sensitivity adapter verified for 4 tasks');
console.log('(Synthetic test only; no generated code executed.)');
