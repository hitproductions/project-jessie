#!/usr/bin/env node
// Offline check of the hello-form workflow (workflows/slack-interactions-v1.json): signed Slack requests - a click, a
// form submission, a forged signature, an old timestamp - through Read Request -> (Crypto HMAC, done here) -> Check
// Signature, then Build Form / Read Submission / Report. Usage: node scripts/sim-hello-form.js [workflow file]
const fs = require('fs');
const crypto = require('crypto');
const file = process.argv[2] || 'workflows/slack-interactions-v1.json';
const wf = JSON.parse(fs.readFileSync(file, 'utf8'));
const node = n => wf.nodes.find(x => x.name === n);
const SECRET = 'test-signing-secret';
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };

async function run(name, inputItems, outputs, helpers) {
  const js = node(name).parameters.jsCode;
  const $ = n => ({ first: () => outputs[n][0], all: () => outputs[n] });
  const $input = { first: () => inputItems[0], all: () => inputItems };
  const fn = new Function('$', '$input', 'Buffer', 'URLSearchParams', 'return (async function(){' + js + '\n}).call(this);');
  return fn.call({ helpers }, $, $input, Buffer, URLSearchParams);
}

function request(payload, { secret = SECRET, age = 0, binary = true } = {}) {
  const raw = 'payload=' + encodeURIComponent(JSON.stringify(payload));
  const ts = String(Math.floor(Date.now() / 1000) - age);
  const sig = 'v0=' + crypto.createHmac('sha256', secret).update('v0:' + ts + ':' + raw).digest('hex');
  const item = { json: { headers: { 'x-slack-signature': sig, 'x-slack-request-timestamp': ts }, body: { payload: JSON.stringify(payload) } } };
  if (binary) item.binary = { data: { data: Buffer.from(raw).toString('base64') } };
  return { item, raw };
}

async function pipeline(payload, opts) {
  const { item, raw } = request(payload, opts);
  const helpers = { getBinaryDataBuffer: async () => Buffer.from(raw) };
  const out = {};
  out['Read Request'] = await run('Read Request', [item], out, helpers);
  const r = out['Read Request'][0].json;
  if (node('To Sign')) {            // v2: To Sign -> Jessie — Slack Signature (emulated) returns only { computed }
    out['To Sign'] = await run('To Sign', out['Read Request'], out, helpers);
    const base = out['To Sign'][0].json.base;
    ok(base === 'v0:' + r.ts + ':' + r.raw, 'To Sign builds the signed string');
    out['Signature'] = [{ json: { computed: crypto.createHmac('sha256', SECRET).update(base).digest('hex') } }];
  } else {                          // v1: the Crypto node in this workflow
    const computed = crypto.createHmac('sha256', SECRET).update('v0:' + r.ts + ':' + r.raw).digest('hex');
    out['Signature'] = [{ json: Object.assign({}, r, { computed }) }];
  }
  out['Check Signature'] = await run('Check Signature', out['Signature'], out, helpers);
  return out;
}

(async () => {
  const click = { type: 'block_actions', user: { id: 'U1' }, trigger_id: 'T123', actions: [{ action_id: 'hello_open' }] };
  let o = await pipeline(click);
  let c = o['Check Signature'][0].json;
  ok(c.route === 1 && c.sigOk && c.fresh, 'click routes to 1 with a good signature: ' + JSON.stringify(c));
  ok(c.rawSource === 'binary', 'raw body read from binary');
  o['Build Form'] = await run('Build Form', o['Check Signature'], o, {});
  const f = o['Build Form'][0].json;
  ok(f.trigger_id === 'T123' && f.view.callback_id === 'hello_submit', 'form has the trigger id and callback');
  const y = new Date(Date.now() + 8 * 3600e3).getUTCFullYear() + 1;
  ok(f.view.blocks[1].element.initial_date.startsWith(String(y)), 'date picker opens a year ahead: ' + f.view.blocks[1].element.initial_date);

  const submit = { type: 'view_submission', user: { id: 'U1' }, view: { id: 'V9', callback_id: 'hello_submit', private_metadata: '{"openedAt":1}',
    state: { values: { date: { date_pick: { selected_date: '2027-10-15' } }, note: { note_in: { value: 'hi' } } } } } };
  o = await pipeline(submit);
  c = o['Check Signature'][0].json;
  ok(c.route === 2 && c.viewId === 'V9', 'submission routes to 2');
  o['Read Submission'] = await run('Read Submission', o['Check Signature'], o, {});
  const s = o['Read Submission'][0].json;
  ok(s.date === '2027-10-15' && s.note === 'hi' && s.working.response_action === 'update', 'submission read; working answer is an update');
  o['Update Form'] = [{ json: { ok: true } }];
  o['Report'] = await run('Report', [], o, {});
  const rep = o['Report'][0].json.text;
  ok(/Signature check: OK/.test(rep) && /2027-10-15/.test(rep) && /Update call: OK/.test(rep), 'report: ' + rep.replace(/\n/g, ' | '));

  o = await pipeline(click, { secret: 'wrong' });
  ok(o['Check Signature'][0].json.route === 0, 'a forged signature is refused');
  o = await pipeline(click, { age: 600 });
  ok(o['Check Signature'][0].json.route === 0, 'a 10-minute-old request is refused');
  o = await pipeline({ type: 'block_actions', actions: [{ action_id: 'something_else' }] });
  ok(o['Check Signature'][0].json.route === 3, 'any other click is just acknowledged');
  o = await pipeline(click, { binary: false });
  ok(o['Check Signature'][0].json.route === 0 && o['Read Request'][0].json.payloadSource === 'parsed-body',
     'without Raw Body the payload is still read but the signature cannot be checked - refused, and the report says why');
  o['Refused'] = await run('Report Refused', [], o, {});

  const types = new Set(wf.nodes.map(n => n.type));
  const v2 = !!node('To Sign');
  ok(['n8n-nodes-base.webhook', v2 ? 'n8n-nodes-base.executeWorkflow' : 'n8n-nodes-base.crypto', 'n8n-nodes-base.respondToWebhook'].every(t => types.has(t)), 'node types present');
  if (v2) ok(node('Signature').parameters.workflowId.value === 'R06CBQNhFK0x4ZuO' && JSON.stringify(wf).indexOf('PASTE-THE') === -1,
             'v2 calls Jessie — Slack Signature and carries no secret placeholder');
  ok(node('Slack Interactions').parameters.options.rawBody === true && node('Slack Interactions').parameters.responseMode === 'responseNode',
     'webhook: raw body on, answers through Respond nodes');
  if (!v2) ok(JSON.stringify(wf).indexOf('PASTE-THE-SLACK-SIGNING-SECRET-HERE') !== -1, 'the secret is a placeholder in the file');
  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
