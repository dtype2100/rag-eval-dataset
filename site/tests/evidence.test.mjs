import assert from 'node:assert/strict';
import { sufficientEvidence } from '../dist/evidence.mjs';

const cases = [
  [[], false],
  [['X_A'], false],
  [['X_B'], false],
  [['Y'], false],
  [['X_A', 'X_B'], false],
  [['X_A', 'Y'], true],
  [['X_B', 'Y'], true],
  [['X_A', 'X_B', 'Y'], true],
];
for (const [selected, expected] of cases) {
  assert.equal(sufficientEvidence(selected), expected, JSON.stringify(selected));
}
console.log('AND/OR demonstration: all 8 combinations passed');
