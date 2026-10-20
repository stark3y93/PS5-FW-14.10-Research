/* Node's built-in VM only: no packages, browser, console or network. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../diagnostics/browser/diagnostic.js'), 'utf8');
let passed = 0;
function check(name, fn) { fn(); passed++; console.log('PASS ' + name); }
function environment(overrides = {}) {
  const nodes = {};
  for (const id of ['run', 'select', 'firmware', 'status', 'summary', 'output']) {
    nodes[id] = {value: id === 'firmware' ? '14.10' : '', textContent: '', disabled: false,
      onclick: null, focus() {}, select() { this.selected = true; }};
  }
  const calls = [];
  const doc = {getElementById(id) {return nodes[id];}, fonts: {check() {throw Error('must not call');}}};
  const win = {document: doc, navigator: {userAgent: 'test-browser'},
    Promise, Map, Set, Symbol, BigInt, WebAssembly: {}, FontFace: function () {throw Error('must not construct');},
    ArrayBuffer, Uint8Array, TextEncoder, CSS: {supports() {return true;}},
    isSecureContext: false};
  Object.assign(win, overrides);
  const context = vm.createContext({window: win, document: doc, Date, JSON,
    fetch() {calls.push('network'); throw Error('network forbidden');}});
  vm.runInContext(source, context, {timeout: 1000});
  return {nodes, calls, win};
}
check('no automatic run', () => {
  const {nodes, calls} = environment();
  assert.equal(nodes.output.value, '');
  assert.equal(calls.length, 0);
});
check('complete bounded passive capture', () => {
  const {nodes, calls} = environment(); nodes.run.onclick();
  const r = JSON.parse(nodes.output.value);
  assert.equal(r.status, 'complete'); assert.equal(r.schema, 'ps5-browser-diagnostic/1');
  assert.equal(r.features.FontFace, true); assert.equal(r.features.fontSet, true);
  assert.equal(r.features.BigInt, true); assert.equal(r.features.cssGrid, true);
  assert.equal(calls.length, 0); assert.ok(nodes.summary.textContent.includes('FontFace: true'));
});
check('missing APIs are false', () => {
  const {nodes} = environment({FontFace: undefined, CSS: undefined, BigInt: undefined});
  nodes.run.onclick(); const r = JSON.parse(nodes.output.value);
  assert.equal(r.features.FontFace, false); assert.equal(r.features.cssGrid, false);
  assert.equal(r.features.BigInt, false); assert.equal(r.status, 'complete');
});
check('CSS font-family syntax is not mislabeled as font loading', () => {
  const {nodes} = environment(); nodes.run.onclick(); const r = JSON.parse(nodes.output.value);
  assert.equal(r.features.cssFontFamily, true);
  assert.equal(r.features.cssFontLoading, undefined);
  assert.equal(r.features.TransformStream, false);
});
check('restricted getter is error without losing other checks', () => {
  const e = environment(); Object.defineProperty(e.win, 'FontFace', {get() {throw Error('restricted');}});
  e.nodes.run.onclick(); const r = JSON.parse(e.nodes.output.value);
  assert.equal(r.features.FontFace, 'error'); assert.equal(r.features.Promise, true);
});
check('hostile user agent stays in text', () => {
  const {nodes} = environment({navigator: {userAgent: '<img src=x onerror=alert(1)>'}});
  nodes.run.onclick();
  assert.ok(nodes.summary.textContent.includes('<img src=x'));
  assert.equal(nodes.summary.innerHTML, undefined);
});
check('transcription and rerun refresh results', () => {
  const {nodes, win} = environment(); nodes.run.onclick(); nodes.select.onclick();
  assert.equal(nodes.output.selected, true);
  win.FontFace = undefined; nodes.run.onclick();
  assert.equal(JSON.parse(nodes.output.value).features.FontFace, false);
});
check('invalid firmware label requires correction', () => {
  const {nodes} = environment(); nodes.firmware.value = '14'; nodes.run.onclick();
  assert.equal(nodes.output.value, ''); assert.ok(nodes.status.textContent.includes('firmware'));
});
console.log(passed + ' JavaScript tests passed');
