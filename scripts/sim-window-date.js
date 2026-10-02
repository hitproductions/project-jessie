#!/usr/bin/env node
// Offline tests for main v213 (live 2 Oct 12:44: "free tomorrow" -> the model asked for 2027-10-04; Gate had said
// "tomorrow" = 2027-10-03). Room Availability's window is pinned to the one date named in the message.
//   node scripts/sim-window-date.js
const fs = require('fs'), path = require('path');
const M = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', process.env.MAIN || 'project-jessie-v213.json')));
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d))); } };
const v = M.nodes.find(x => x.name === 'Room Availability').parameters.workflowInputs.value;
const ev = (expr, start, end, gate) => new Function('$', '$fromAI', 'return ' + expr.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''))(
  n => ({ first: () => ({ json: gate }) }), k => k === 'window_start' ? start : end);
const win = (s, e, g) => [ev(v.start_iso, s, e, g), ev(v.end_iso, s, e, g)];
let r = win('2027-10-04T00:00:00+08:00', '2027-10-04T23:59:59+08:00', { datesInMessage: '2027-10-03' });
ok(r[0] === '2027-10-03T00:00:00+08:00' && r[1] === '2027-10-03T23:59:59+08:00', 'live 12:44: model 4 Oct, "tomorrow" = 3 Oct -> 3 Oct', r);
r = win('2027-10-04T14:00:00+08:00', '2027-10-04T16:00:00+08:00', { datesInMessage: '2027-10-03' });
ok(r[0] === '2027-10-03T14:00:00+08:00' && r[1] === '2027-10-03T16:00:00+08:00', 'a set time keeps its hours', r);
r = win('2027-10-04T00:00:00+08:00', '2027-10-05T00:00:00+08:00', { datesInMessage: '2027-10-03' });
ok(r[0] === '2027-10-03T00:00:00+08:00' && r[1] === '2027-10-04T00:00:00+08:00', 'a day ending at midnight -> the next midnight', r);
r = win('2027-10-03T00:00:00+08:00', '2027-10-03T23:59:59+08:00', { datesInMessage: '2027-10-03' });
ok(r[0] === '2027-10-03T00:00:00+08:00', 'the right date -> unchanged');
r = win('2027-10-04T00:00:00+08:00', '2027-10-10T23:59:59+08:00', { datesInMessage: '2027-10-03' });
ok(r[0] === '2027-10-04T00:00:00+08:00' && r[1] === '2027-10-10T23:59:59+08:00', 'a range (this week) -> unchanged', r);
r = win('2027-10-04T00:00:00+08:00', '2027-10-04T23:59:59+08:00', { datesInMessage: '', datesUnderDiscussion: '2027-10-03' });
ok(r[0] === '2027-10-04T00:00:00+08:00', 'a date only carried from earlier (none named now) -> unchanged');
r = win('2027-10-04T00:00:00+08:00', '2027-10-04T23:59:59+08:00', { datesInMessage: '2027-10-03,2027-10-05' });
ok(r[0] === '2027-10-04T00:00:00+08:00', 'two dates named -> unchanged (the model picks)');
// gotcha 5: a $fromAI key used twice must carry the same description everywhere in the node
const keys = {}; let clash = false;
for (const e of Object.values(v)) for (const m of String(e).matchAll(/\$fromAI\('([^']+)',\s*'((?:[^'\\]|\\.)*)'/g)) { if (keys[m[1]] !== undefined && keys[m[1]] !== m[2]) clash = true; keys[m[1]] = m[2]; }
ok(!clash, 'window_start / window_end: same description wherever they appear (gotcha 5)');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
