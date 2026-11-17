// Browser-independent behavior checks. These do not replace visual browser QA.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

class Element {
  constructor(dataset = {}) { this.dataset = dataset; this.events = {}; this.attrs = {}; this.value = ''; this.hidden = false; this.textContent = ''; this.className = ''; this.disabled = false; }
  addEventListener(type, handler) { this.events[type] = handler; }
  setAttribute(key, value) { this.attrs[key] = value; }
  removeAttribute(key) { delete this.attrs[key]; }
  focus() { this.focused = true; }
  querySelector() { return new Element(); }
}
function setup(protocol = 'http:') {
  const ids = ['mobile-menu','sidebar','main','collapse-sidebar','menu-scrim','current-page','backend-status','endpoint','bearer-token','api-response','response-status','copy-response','api-form','send-request','token-row','inspect-node','node-result'];
  const elements = Object.fromEntries(ids.map(id => ['#'+id, new Element()]));
  const names = ['overview','infrastructure','services','api-explorer','database','authentication','object-storage','dns','monitoring','load-balancer','documentation'];
  const pages = names.map(page => new Element({page}));
  const nav = names.map(name => new Element({nav:name}));
  const consoles = ['keycloak','minio','prometheus','grafana','exporter'].map(key => new Element({console:key}));
  consoles.forEach(el => {el.replaceWith = replacement => {el.replacement = replacement;};});
  const classes = new Set();
  const events = {}, requests = [], queue = [];
  let copied = '';
  const document = {
    querySelector: selector => elements[selector],
    querySelectorAll: selector => selector === '[data-page]' ? pages : selector === '[data-nav]' ? nav : selector === '[data-console]' ? consoles : [],
    addEventListener: (name, handler) => {events[name] = handler;},
    createElement: () => new Element(),
    body: {classList:{remove:key => classes.delete(key),contains:key => classes.has(key),toggle:key => {if (classes.has(key)) {classes.delete(key);return false;} classes.add(key);return true;}}}
  };
  const location = {hash:'',protocol,origin:protocol+'//demo.example'};
  const window = {location,matchMedia:() => ({matches:false,addEventListener(){}}),addEventListener:(key,handler) => {events[key] = handler;},scrollTo(){},MMC_CONFIG:{}};
  const response = (body, status=200, type='application/json', extras={}) => ({ok:status>=200&&status<300,status,statusText:status===200?'OK':'Unauthorized',headers:{get:key => key.toLowerCase()==='content-type'?type:extras[key]??null},text:async()=>body});
  const context = {window,document,location,URL,AbortController,setTimeout,clearTimeout,performance,console,navigator:{clipboard:{writeText:async value => {copied=value;}}},fetch:async (url, options) => {requests.push({url,options});return queue.length ? queue.shift()() : response('{"message":"Hello from App Server!"}');}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../web-frontend-server/html/assets/dashboard.js'),'utf8'),context);
  return {elements,pages,nav,consoles,events,requests,queue,response,location,get copied(){return copied;}};
}
const settle = () => new Promise(resolve => setImmediate(resolve));
async function run() {
  const app = setup(); await settle();
  const el = id => app.elements['#'+id];
  assert.match(el('backend-status').textContent,/connected/);
  assert.equal(app.pages.filter(p => !p.hidden).length,1);
  for (const nav of app.nav) {
    app.location.hash = '#'+nav.dataset.nav; app.events.hashchange();
    assert.equal(app.pages.find(p => !p.hidden).dataset.page,nav.dataset.nav);
    assert.equal(nav.attrs['aria-current'],'page');
  }
  assert.equal(app.consoles[0].href,'http://demo.example:8081/admin/');
  assert.equal(app.consoles[4].href,'http://demo.example:9100/metrics');
  const secure = setup('https:'); await settle();
  assert.ok(secure.consoles.every(link => link.replacement), 'HTTPS requires explicit console URLs');
  el('endpoint').value = '/api/secure'; el('endpoint').events.change();
  assert.equal(el('token-row').hidden,false);
  el('bearer-token').value = 'Bearer test-secret';
  let finish;
  app.queue.push(() => new Promise(resolve => {finish=resolve;}));
  const inFlight = el('api-form').events.submit({preventDefault(){}});
  assert.equal(el('send-request').disabled,true);
  assert.equal(el('api-response').attrs['aria-busy'],'true');
  assert.equal(app.requests.at(-1).options.headers.Authorization,'Bearer test-secret');
  finish(app.response('{"token":"test-secret","echo":"test-secret"}'));
  await inFlight;
  assert.ok(!el('api-response').textContent.includes('test-secret'));
  assert.equal(el('bearer-token').value,'');
  assert.equal(el('send-request').disabled,false);
  await el('copy-response').events.click();
  assert.equal(app.copied,el('api-response').textContent);
  app.queue.push(async()=>app.response('{"error":"Missing Bearer token"}',401));
  await el('api-form').events.submit({preventDefault(){}});
  assert.match(el('response-status').textContent,/HTTP 401/);
  assert.equal(app.requests.at(-1).options.headers.Authorization,undefined);
  el('endpoint').value='/student/'; el('endpoint').events.change();
  el('bearer-token').value='must-not-send';
  app.queue.push(async()=>app.response(''));
  await el('api-form').events.submit({preventDefault(){}});
  assert.match(el('api-response').textContent,/Empty response/);
  assert.equal(app.requests.at(-1).options.headers.Authorization,undefined);
  assert.equal(el('copy-response').disabled,true);
  app.queue.push(async()=>{const e = new Error(); e.name='AbortError'; throw e;});
  await el('api-form').events.submit({preventDefault(){}});
  assert.match(el('api-response').textContent,/12 giây/);
  assert.equal(el('send-request').disabled,false);
  app.queue.push(async()=>app.response('<h1>Bad gateway</h1>',502,'text/html'));
  await el('api-form').events.submit({preventDefault(){}});
  assert.match(el('response-status').textContent,/không phải JSON/);
  assert.equal(el('api-response').textContent,'<h1>Bad gateway</h1>');
  app.queue.push(async()=>app.response('',200,'text/html',{'X-Upstream-Addr':'172.19.0.8:80','X-Load-Balancer':'Nginx-Round-Robin'}));
  const inspect = el('inspect-node');
  await inspect.events.click({currentTarget:inspect});
  assert.match(el('node-result').textContent,/172.19.0.8:80/);
  app.queue.push(async()=>app.response('',200,'text/html'));
  await inspect.events.click({currentTarget:inspect});
  assert.match(el('node-result').textContent,/Không có header/);
  el('bearer-token').value='discard'; app.events.pagehide();
  assert.equal(el('bearer-token').value,'');
  console.log('PASS: routes, real-fetch states, token scope/redaction/clearing, copy, empty/401/502/timeout, console host/TLS policy, upstream headers.');
  for (const blocked of [false,true]) {
    const toggle = new Element(), root = new Element();
    let stored = null, ready;
    const system = {matches:true,addEventListener(){}};
    const themeContext = {
      window:{matchMedia:()=>system},
      document:{documentElement:root,querySelectorAll:()=>[toggle],addEventListener:(name,handler)=>{ready=handler;}},
      localStorage:{getItem:()=>{if(blocked)throw new Error('Blocked'); return stored;},setItem:(key,value)=>{if(blocked)throw new Error('Blocked');stored=value;}}
    };
    vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../web-frontend-server/html/assets/theme.js'),'utf8'),themeContext);
    ready();
    assert.equal(root.dataset.theme,'dark');
    assert.equal(toggle.attrs['aria-pressed'],'true');
    toggle.events.click();
    assert.equal(root.dataset.theme,'light');
    assert.equal(toggle.attrs['aria-pressed'],'false');
    assert.equal(stored,blocked?null:'light');
  }
  console.log('PASS: theme system default, toggling, accessibility label and blocked-storage fallback.');
}
run().catch(error => {console.error(error); process.exitCode=1;});
