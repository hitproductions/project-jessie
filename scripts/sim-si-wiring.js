#!/usr/bin/env node
// Slack Interactions wiring (v20): every Execute Workflow call that passes on its input item must get it from a Code node
// that builds it (through IF / Switch only) - never from a Slack HTTP call. v19 fed Prepare from Show Source (chat.update), so
// every single booking from the form reached Book Session empty (MISSING_DETAILS, 15 Oct 17:09). The node sims never saw it:
// they run each node's code, not the wiring.
// Usage: node scripts/sim-si-wiring.js [slack-interactions file]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v20.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const by = {}; for (const n of si.nodes) by[n.name] = n;
const pred = {}; for (const [a, v] of Object.entries(si.connections)) for (const o of v.main || []) for (const c of o) (pred[c.node] = pred[c.node] || []).push(a);
const feeders = (n, seen = new Set()) => [].concat(...(pred[n] || []).filter(p => !seen.has(p) && seen.add(p)).map(p =>
  /\.(if|switch)$/.test(by[p].type) ? feeders(p, seen) : [p]));
const calls = si.nodes.filter(n => /executeWorkflow$/.test(n.type) && !n.parameters.workflowInputs);
ok(calls.length >= 8, 'found the sub-workflow calls (' + calls.length + ')');
for (const n of calls) {
  const f = feeders(n.name);
  ok(f.length && f.every(p => /\.code$/.test(by[p].type)), n.name + ' is fed only by Code nodes - ' + f.map(p => p + ' [' + by[p].type.split('.').pop() + ']').join(', '));
}
// Prepare gets exactly To Prepare's output
if (by['Prepare Input']) {
  const toPrep = { summary: 'M2 - Howard', rooms: 'M2', start_iso: '2027-10-19T13:00:00+08:00', end_iso: '2027-10-19T15:00:00+08:00', mode: 'prepare' };
  const $ = n => ({ first: () => { if (n !== 'To Prepare') throw new Error('reads ' + n); return { json: toPrep }; } });
  const out = new Function('$', '$input', by['Prepare Input'].parameters.jsCode)($, { first: () => ({ json: { ok: true, channel: 'D1', ts: '1' } }) });
  ok(JSON.stringify(out[0].json) === JSON.stringify(toPrep), 'Prepare gets the booking (title, times, room), not Slack\'s answer');
}
// v21: every toggle / button the form draws reaches a handler - v19 drew "Use another room" (room_toggle) and the router sent it
// to "other", so ticking it did nothing
{
  const ids = new Set(); for (const n of si.nodes) { const c = n.parameters.jsCode || ''; let m; const re = /action_id:\s*'([a-z_]+)'/g; while ((m = re.exec(c))) ids.add(m[1]); }
  const live = [...ids].filter(x => /_toggle$|^add_|^bk_|^my_|^open_|^hello_open$/.test(x));
  const cs = by['Check Signature'].parameters.jsCode;
  const route = a => new Function('$', '$input', cs)(n => ({ first: () => ({ json: n === 'Read Request' ? { sig: 'v0=x', ts: String(Math.floor(Date.now() / 1000)), payload: { type: 'block_actions', actions: [{ action_id: a }] } } : {} }) }),
    { first: () => ({ json: { computed: 'x' } }) })[0].json.route;
  const lost = live.filter(a => route(a) === 3);
  ok(live.length >= 8 && !lost.length, 'every toggle / button has a route (' + live.length + ' checked)' + (lost.length ? ' - not routed: ' + lost.join(', ') : ''));
}
console.log(pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
