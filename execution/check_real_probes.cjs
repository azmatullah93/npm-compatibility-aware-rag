/** Check pinned-library observations against documented breaking changes.
 * This is an assertion script for actual npm installations, not an emulator.
 * It refuses incomplete data and errors rather than count them as passing.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const input = process.argv[2] || path.join(__dirname, '..', 'outputs', 'npm_version_probe_results.json');
const rows = JSON.parse(fs.readFileSync(input, 'utf8'));
assert.ok(Array.isArray(rows), 'Expected a JSON array of probe observations');
assert.ok(rows.length >= 4, 'Missing npm observations');
const errors = rows.filter(row => row.error);
assert.equal(errors.length, 0, `Installation/probe errors: ${JSON.stringify(errors)}`);

function observed(pkg, version, probe) {
  const entries = rows.filter(row => row.pkg === pkg && row.version === version && row.probe === probe);
  assert.equal(entries.length, 1, `Expected one observation for ${pkg}@${version} / ${probe}`);
  assert.equal(typeof entries[0].result, 'boolean', `Missing boolean result for ${pkg}@${version} / ${probe}`);
  return entries[0].result;
}

// Expected changes from the official Express 5 migration guide and
// Mongoose 6->7 migration guide. These assertions intentionally cover
// only directly documented, version-discriminating cases.
const expectations = [
  ['express', '4.21.2', 'unnamed wildcard route accepted', true],
  ['express', '5.1.0', 'unnamed wildcard route accepted', false],
  ['mongoose', '6.13.8', 'Model.remove exists', true],
  ['mongoose', '7.8.7', 'Model.remove exists', false],
  ['mongoose', '6.13.8', 'Model.update exists', true],
  ['mongoose', '7.8.7', 'Model.update exists', false],
  ['mongoose', '6.13.8', 'ObjectId without new works', true],
  ['mongoose', '7.8.7', 'ObjectId without new works', false],
];
let passed = 0;
for (const [pkg, version, probe, expected] of expectations) {
  const actual = observed(pkg, version, probe);
  assert.equal(actual, expected, `${pkg}@${version} ${probe}: expected ${expected}, observed ${actual}`);
  passed++;
  process.stdout.write(`PASS ${pkg}@${version}: ${probe} = ${actual}\n`);
}
console.log(`REAL PACKAGE EXPECTATIONS: ${passed}/${expectations.length} passed`);
