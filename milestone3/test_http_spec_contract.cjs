/**
 * Regression guard for Express test-harness server startup.
 * This checks trusted test source and native HTTP lifecycle, not LLM correctness.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const vm = require('node:vm');
const { once } = require('node:events');

const specs = JSON.parse(fs.readFileSync(path.join(__dirname, 'execution_specs.json'), 'utf8'));
const ids = ['express-wildcard-task-new', 'express-del-task-new'];
for (const id of ids) {
  const source = specs[id].test_js;
  // Catch JavaScript syntax errors without executing any candidate code.
  new vm.Script(source, { filename: id + '/test.cjs' });
  const listen = source.indexOf("await once(server, 'listening')");
  const address = source.indexOf('server.address()');
  assert.ok(listen >= 0 && address > listen, id + ': must await listening before address()');
  assert.ok(source.includes('AbortSignal.timeout(5000)'), id + ': HTTP call must be bounded');
}

(async () => {
  const server = http.createServer((req, res) => { res.end('OK'); });
  server.listen(0, '127.0.0.1');
  try {
    await once(server, 'listening');
    const port = server.address()?.port;
    assert.ok(Number.isInteger(port) && port > 0, 'Server port must be assigned');
    const response = await fetch('http://127.0.0.1:' + port, { signal: AbortSignal.timeout(5000) });
    assert.equal(response.status, 200);
    assert.equal(await response.text(), 'OK');
    console.log('PASS: 2 Express harness sources checked and native HTTP readiness verified');
    console.log('(Trusted harness regression only; does not execute generated code.)');
  } finally {
    server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
