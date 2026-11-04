import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const files = new URL('../shop/static/assets/js/', import.meta.url);
const locationContext = vm.createContext({window: {}, URL});
vm.runInContext(fs.readFileSync(new URL('analytics-location.js', files), 'utf8'), locationContext);
const safeLocation = locationContext.window.DecoPaintAnalyticsLocation;
assert.equal(safeLocation('https://decopaint.fi/catalog/?gclid=TEST-click_123&utm_source=google&utm_medium=cpc&email=a%40b.invalid&q=private&checkout-hmac=secret#fragment'), 'https://decopaint.fi/catalog/?gclid=TEST-click_123&utm_source=google&utm_medium=cpc');
assert.equal(safeLocation('https://decopaint.fi/?gclid=bad%40identifier&utm_campaign=person%40example.invalid'), 'https://decopaint.fi/');
assert.equal(safeLocation('javascript:alert(1)'), '');

const calls = [];
const listeners = {};
const elements = {
    'ga4-config': {textContent: JSON.stringify({measurement_id: 'G-TESTONLY', user: {user_id: 'dp_synthetic', login_status: 'authenticated'}})},
    'ga4-page-event': {textContent: JSON.stringify({name: 'purchase', params: {transaction_id: 'DP-SYNTHETIC', value: 12.34}})},
};
const document = {
    cookie: 'cookie_settings=' + encodeURIComponent(JSON.stringify({analytics_storage: 'granted'})),
    getElementById: id => elements[id],
    addEventListener: (name, fn) => {listeners[name] = fn;},
};
const window = {gtag: (...args) => calls.push(args)};
const context = vm.createContext({window, document});
vm.runInContext(fs.readFileSync(new URL('analytics.js', files), 'utf8'), context);
listeners.DOMContentLoaded();
assert.equal(calls.filter(x => x[0] === 'event' && x[1] === 'purchase').length, 0);
assert.equal(window.DecoPaintAnalytics.track('purchase', {transaction_id: 'DP-SYNTHETIC'}), false);
assert.equal(calls.find(x => x[0] === 'config')[2].send_page_view, false);
window.DecoPaintAnalytics.track('add_to_cart', {value: 12.34, email: 'person@example.invalid', items: [{item_id: 'SYNTHETIC'}]});
assert.equal(calls.at(-1)[1], 'add_to_cart');
assert.equal(calls.at(-1)[2].email, undefined);
document.cookie = 'cookie_settings=' + encodeURIComponent(JSON.stringify({analytics_storage: 'denied'}));
const before = calls.length;
window.DecoPaintAnalytics.track('begin_checkout', {value: 12.34});
assert.equal(calls.length, before);
document.cookie = 'cookie_settings=' + encodeURIComponent(JSON.stringify({analytics_storage: 'granted'}));
listeners['decopaint:consent-updated']();
assert.equal(calls.filter(x => x[0] === 'event' && x[1] === 'begin_checkout').length, 1);
assert.equal(calls.filter(x => x[0] === 'event' && x[1] === 'purchase').length, 0);
console.log('Analytics consent, attribution, single purchase owner and page-view checks passed; no network calls.');
