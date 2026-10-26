import { sufficientEvidence } from './evidence.mjs';

const choices = [...document.querySelectorAll('[name="evidence"]')];
const result = document.querySelector('#evidence-result');
function update() {
  const selected = choices.filter(input => input.checked).map(input => input.value);
  const sufficient = sufficientEvidence(selected);
  result.dataset.sufficient = String(sufficient);
  result.textContent = sufficient
    ? '충분한 근거를 확보했습니다. X의 출처는 A 또는 B 중 하나면 됩니다.'
    : '아직 근거가 부족합니다. X의 출처 하나와 Y가 함께 필요합니다.';
}
choices.forEach(input => input.addEventListener('change', update));
update();
