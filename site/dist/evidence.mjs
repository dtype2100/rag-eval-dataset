export function sufficientEvidence(selected) {
  return selected.includes('Y') && (selected.includes('X_A') || selected.includes('X_B'));
}
