const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const elements = new Map(), events = new Map(), stored = new Map();
let focused = '', capture = false;
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    value: '', textContent: '', disabled: false, handlers: {},
    addEventListener(name, fn) { this.handlers[name] = fn; },
    focus() { focused = id; }, removeAttribute(name) { delete this[name]; },
    click() { this.onclick?.(); },
  });
  return elements.get(id);
}
const items = [1,2,3].map(n => ({ number:n,id:'image-'+n,width:64,height:32,alias_count:1,
  aliases:[{object:'Object'+n,resource:'resource'+n}],original_image:'original'+n,
  chinese_image:'revised'+n,previous_image:'previous'+n,previous_feedback:'old, "note"\n'+n,
  action:n===3?'unchanged':'revise-source-style' }));
element('review-data').textContent = JSON.stringify(items);
const context = {
  document: { body:{dataset:{revision:'unit-test'}},getElementById:element,
    addEventListener(name,fn,options) { events.set(name,fn);capture=options.capture; },
    createElement() { return {click(){}}; } },
  localStorage: {getItem:k=>stored.get(k),setItem:(k,v)=>stored.set(k,v)},
  URL:{createObjectURL(){return 'blob:test';},revokeObjectURL(){}},Blob,setTimeout,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../tools/review_page/review.js'),'utf8'),context);
assert.equal(focused,'comment');assert.equal(capture,true);
let prevented=false,stopped=false;
function key(key,target='comment') {
  prevented=stopped=false;
  events.get('keydown')({key,target:element(target),preventDefault(){prevented=true;},stopImmediatePropagation(){stopped=true;}});
}
element('comment').value='保留引号 "和,逗号"\n第二行';element('comment').handlers.input();
for (const target of ['comment','filter','jump','prev']) {
  key('ArrowRight',target);assert.equal(prevented,true);assert.equal(stopped,true);assert.equal(focused,'comment');
  key('ArrowLeft',target);assert.match(element('meta').textContent,/image-1/);
}
key('ArrowLeft');assert.match(element('meta').textContent,/image-3/);key('ArrowRight');
assert.equal(element('comment').value,'保留引号 "和,逗号"\n第二行');
assert.equal(stored.get('image-review-v2-unit-test-image-1'),element('comment').value);
key('ArrowUp');assert.equal(prevented,false);assert.equal(stopped,false);
events.get('keydown')({key:'Process',code:'ArrowRight',isComposing:true,target:element('comment'),preventDefault(){},stopImmediatePropagation(){}});
assert.match(element('meta').textContent,/image-2/);assert.equal(focused,'comment');key('ArrowLeft');
element('filter').value='no-match';element('filter').handlers.input();
assert.equal(element('comment').disabled,true);key('ArrowRight');
element('filter').value='';element('filter').handlers.input();
assert.match(element('meta').textContent,/image-1/);assert.equal(element('comment').disabled,false);
element('revised').onclick();key('ArrowLeft');assert.match(element('meta').textContent,/image-2/);
key('ArrowRight');assert.match(element('meta').textContent,/image-1/);
element('all').onclick();element('jump').value='3';element('go').onclick();
assert.match(element('meta').textContent,/image-3/);assert.equal(focused,'comment');
console.log('PASS: arrows capture every input, prevent caret motion, wrap/filter/jump refocus, feedback persists');
