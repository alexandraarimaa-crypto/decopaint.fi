import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const elements = Object.fromEntries(['variant-price-per-m2', 'variant-coverage'].map(id => [id, {hidden: true, textContent: ''}]));
const window = {};
runInNewContext(readFileSync('shop/static/assets/js/variant-material-info.js', 'utf8'), {
    window, document: {getElementById: id => elements[id]}
});
const update = window.updateVariantMaterialInfo;
update({price_per_m2: '4.85', coverage_m2: '85–135'});
assert.equal(elements['variant-price-per-m2'].textContent, 'alk. 4,85 €/m²');
assert.equal(elements['variant-coverage'].textContent, 'Riittoisuus 85–135 m²');
assert.equal(elements['variant-price-per-m2'].hidden, false);
assert.equal(elements['variant-coverage'].hidden, false);
update({price_per_m2: '1.01', coverage_m2: '100', quantity: 8, discount_percent: 30});
assert.equal(elements['variant-price-per-m2'].textContent, 'alk. 1,01 €/m²');
assert.equal(elements['variant-coverage'].textContent, 'Riittoisuus 100 m²');
update({price_per_m2: null, coverage_m2: '85–135'});
assert.equal(elements['variant-price-per-m2'].hidden, true);
assert.equal(elements['variant-coverage'].hidden, false);
update({price_per_m2: '0.00', coverage_m2: '   '});
assert.equal(elements['variant-price-per-m2'].textContent, 'alk. 0,00 €/m²');
assert.equal(elements['variant-coverage'].hidden, true);
update({coverage_m2: '<img src=x onerror=alert(1)>'});
assert.equal(elements['variant-coverage'].textContent, 'Riittoisuus <img src=x onerror=alert(1)> m²');
update();
for (const element of Object.values(elements)) {
    assert.equal(element.hidden, true);
    assert.equal(element.textContent, '');
}
window.prepareVariantMaterialInfo('5 L');
update({price_per_m2: '3.95', coverage_m2: '40–60'});
// Colour/quantity requests retain the information for the current package.
window.prepareVariantMaterialInfo('5 L');
assert.equal(elements['variant-price-per-m2'].textContent, 'alk. 3,95 €/m²');
assert.equal(elements['variant-coverage'].textContent, 'Riittoisuus 40–60 m²');
// A package change immediately clears the previous package while loading.
window.prepareVariantMaterialInfo('10 L');
assert.equal(elements['variant-price-per-m2'].hidden, true);
assert.equal(elements['variant-coverage'].hidden, true);
update({price_per_m2: '3.45', coverage_m2: '80–120'});
window.prepareVariantMaterialInfo('10 L');
assert.equal(elements['variant-price-per-m2'].textContent, 'alk. 3,45 €/m²');
assert.equal(elements['variant-coverage'].textContent, 'Riittoisuus 80–120 m²');
window.prepareVariantMaterialInfo('5 kg');
update({price_per_m2: null, coverage_m2: null});
assert.equal(elements['variant-price-per-m2'].hidden, true);
assert.equal(elements['variant-coverage'].hidden, true);
console.log('Manual package info: formatting, colour/quantity retention, package changes, blank fields and text-only rendering passed.');
