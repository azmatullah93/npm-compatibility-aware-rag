/** Offline synthetic checks; imports no npm release package, no model calls. */
'use strict';
const assert=require('node:assert/strict');
const path=require('node:path');
const {classifyCheck,packageDir}=require('./probe_release_behavior.cjs');
const x=classifyCheck({
  case_id:'old_api_removed',pkg:'express',version:'5.1.0',
  expected:false,observed:false,source:'https://expressjs.com/en/guide/migrating-5/'
});
assert.equal(x.passed,true,'Expected absent API is a passing negative control');
assert.equal(x.observed,false);
assert.equal(classifyCheck({
  case_id:'unexpected_old_api',pkg:'express',version:'5.1.0',
  expected:false,observed:true,source:x.source
}).passed,false,'Unexpected retained API must fail negative control');
assert.equal(classifyCheck({
  case_id:'stable_api',pkg:'mongoose',version:'7.8.7',
  expected:true,observed:true,source:'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'
}).passed,true);
assert.throws(()=>classifyCheck({
  case_id:'invalid',pkg:'mongoose',version:'7.8.7',
  expected:true,observed:'true',source:''
}),/boolean/);
assert.ok(packageDir('express','4.21.2').endsWith(
  path.join('milestone3','npm_workspaces','express-4_21_2')));
assert.ok(packageDir('mongoose','7.8.7').endsWith(
  path.join('milestone3','npm_workspaces','mongoose-7_8_7')));
console.log('PASS: 6 offline pinned-release behavior-probe checks (synthetic only)');
