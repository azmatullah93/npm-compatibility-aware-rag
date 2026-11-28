/** Optional diagnostic adapter for alternate CommonJS export shapes.
 * This affects the evaluation harness only. It never alters model-generated code.
 * Strict mode (the original benchmark contract) remains the default.
 */
'use strict';

const REQUIRE_CALL = "require('./solution.cjs')(";
// The test fixtures deliberately use exactly one call to the generated export.
// Fail closed if their layout changes rather than weakening another expression.
function acceptNamedSetupExport(testSource) {
  if (typeof testSource !== 'string') throw new TypeError('Expected test source');
  const occurrences = testSource.split(REQUIRE_CALL).length - 1;
  if (occurrences !== 1) {
    throw Error('Expected exactly one directly invoked CommonJS solution import; found ' + occurrences);
  }
  const adaptedCall = [
    '((candidate) => {',
    "const setup = typeof candidate === 'function' ? candidate :",
    "  candidate && typeof candidate.setup === 'function' ? candidate.setup : null;",
    "if (!setup) throw new TypeError('Expected a directly exported function or a named setup function');",
    'return setup;',
    "})(require('./solution.cjs'))("
  ].join(' ');
  return testSource.replace(REQUIRE_CALL, adaptedCall);
}
module.exports = { acceptNamedSetupExport };
