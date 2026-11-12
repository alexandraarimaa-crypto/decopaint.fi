import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const documentListeners = {};
const formListeners = {};
const buttons = [{disabled: false}, {disabled: false}];
const priceLabels = [{textContent: '49,32 €'}];
const form = {addEventListener(name, callback) { formListeners[name] = callback; }};
const document = {
    addEventListener(name, callback) { documentListeners[name] = callback; },
    getElementById(id) { return id === 'cart_form' ? form : null; },
    querySelectorAll(selector) {
        return selector === '[data-mobile-price]' ? priceLabels : buttons;
    },
};

const source = fs.readFileSync('shop/static/assets/js/sales-product.js', 'utf8');
assert.doesNotMatch(source, /calculator|laskuri|menekki/i);
vm.runInNewContext(source, {document});
documentListeners.DOMContentLoaded();

let prevented = false;
formListeners.submit({preventDefault() { prevented = true; }});
assert.equal(prevented, true);

documentListeners['decopaint:price-ready']({detail: {price: 49.32, size: '5 kg'}});
assert.deepEqual(buttons.map(button => button.disabled), [false, false]);
prevented = false;
formListeners.submit({preventDefault() { prevented = true; }});
assert.equal(prevented, false);

documentListeners['decopaint:price-loading']();
assert.deepEqual(buttons.map(button => button.disabled), [true, true]);
assert.equal(priceLabels[0].textContent, 'Ladataan hintaa…');
console.log('Sales selection readiness checks passed without calculator code.');
