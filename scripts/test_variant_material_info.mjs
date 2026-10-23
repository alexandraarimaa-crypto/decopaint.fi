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
console.log('Variant material info: formatting, switching, independent optional fields, clearing, zero, and text-only rendering passed.');
