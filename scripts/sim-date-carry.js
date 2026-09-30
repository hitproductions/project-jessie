#!/usr/bin/env node
// Offline tests for main v195 (date carry fix): Gate Context re-reads the date from the requester's earlier messages
// when static data has not caught up (a reply typed seconds after the previous turn, which is still writing its
// Turn Log row). No Slack or n8n is touched.
//
//   node scripts/sim-date-carry.js
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const gate = w => w.nodes.find(x => x.name === 'Gate Context').parameters.jsCode;
const NEW = gate(WF(process.env.MAIN || 'project-jessie-v195.json')), OLD = gate(WF('imported/project-jessie-v194-imported.json'));
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };

// 30 Sep 2026 13:18 PHT (Jessie's QA year: Thu 30 Sep 2027, so "tomorrow" = Fri 1 Oct 2027)
const T0 = 1790745485;                     // "book qaorange ..." 13:18:05
Date.now = () => (T0 + 13) * 1000;
const ME = 'U08V3CKDGJF';
const U = (dt, text) => ({ text, user: ME, ts: String(T0 + dt) + '.1' });
const B = (dt, text) => ({ text, bot_id: 'B0BTVF2HTPC', ts: String(T0 + dt) + '.1' });
const run = (src, text, dt, older, store = {}) => {
  const trig = U(dt, text), hist = [trig, ...older];
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { ...trig, channel: 'D0BTP8VQ6UB' }
    : n === 'Get Booker' ? { fields: { Name: 'Howard Luistro', Department: ['Audio Post'] } } : {} }),
    all: () => (n === 'Get Recent Messages' ? hist : []).map(j => ({ json: j })) });
  const r = new Function('$', '$getWorkflowStaticData', src)($, () => store)[0].json;
  return { dates: r.datesUnderDiscussion, notice: r.dateNotice || '', store };
};
const REQ = 'book qaorange studio 8 tomorrow 2pm to 4pm, vo recording, engineer drey';
const Q = B(10, 'Who is the client (or is there none), and is this booking External (Hit Productions work) or Personal (their own project)?');
const RESET = [B(-13, 'All cleared. What do you need?'), U(-19, 'reset')];
const EPOCH = { ['epoch_' + ME]: String(T0 - 19) + '.1' };

console.log('The 30 Sep race: "no client" 3 s after the question, before the previous turn saved the date');
let r = run(NEW, 'no client', 13, [Q, U(0, REQ), ...RESET], { ...EPOCH });
ok(r.dates === '2027-10-01' && /THE DATE UNDER DISCUSSION IS Friday, 1 October 2027/.test(r.notice), '"tomorrow" read from the request -> Fri 1 Oct 2027', r);
ok(r.store['lastdate_' + ME] && r.store['lastdate_' + ME].date === '2027-10-01', 'and written back to the store for the next turn');
ok(run(OLD, 'no client', 13, [Q, U(0, REQ), ...RESET], { ...EPOCH }).dates === '', '  (v194: nothing -> MISSING_DATE, "What is the date for this booking?")');

console.log('Unchanged when the store did save');
{ const st = { ...EPOCH }; run(NEW, REQ, 0, RESET, st);
  r = run(NEW, 'no client', 13, [Q, U(0, REQ), ...RESET], st);
  ok(r.dates === '2027-10-01', 'carried from the store as before'); }
r = run(NEW, 'make it next friday instead', 13, [Q, U(0, REQ)], { ...EPOCH });
ok(r.dates === '2027-10-08', 'a date in this message still wins (next Friday = 8 Oct)', r.dates);

console.log('The newest dated message wins, and only the requester\'s');
r = run(NEW, 'external', 40, [B(35, 'Summary for Monday ...'), U(30, 'actually make it monday'), Q, U(0, REQ)], { ...EPOCH });
ok(r.dates === '2027-10-04', '"actually make it monday" (newer) over "tomorrow" (older) -> Mon 4 Oct', r.dates);
r = run(NEW, 'no client', 13, [B(10, 'Tomorrow is fully booked. Which day?'), U(0, 'book qaorange studio 8, vo recording')], { ...EPOCH });
ok(r.dates === '', 'a date only Jessie wrote does not count');
r = run(NEW, 'no client', 13, [Q, U(0, 'book qaorange on oct 5 2pm to 4pm')], { ...EPOCH });
ok(r.dates === '2027-10-05', 'a written date ("oct 5") -> 5 Oct', r.dates);

console.log('Where the search stops');
r = run(NEW, 'no client', 13, [Q, U(-5, 'reset'), U(-30, REQ)], {});
ok(r.dates === '', 'a reset in between -> nothing carried across it');
r = run(NEW, 'no client', 13, [Q, U(-3 * 3600 * 24, REQ)], {});
ok(r.dates === '', '"tomorrow" typed on an earlier day -> not reused');
r = run(NEW, 'no client', 13, [Q, U(-60, REQ)], { ['epoch_' + ME]: String(T0 - 30) + '.1' });
ok(r.dates === '', 'a message from before the epoch -> not reused');
r = run(NEW, 'studio 8 then', 13, [Q, U(5, 'what is free this week'), U(0, REQ)], { ...EPOCH });
ok(r.dates === '', 'a range ("this week") newer than the date -> stops, as it retires a carried date', r.dates);
r = run(NEW, 'no client', 13, [Q, U(5, 'make it the 30th'), U(0, REQ)], { ...EPOCH });
ok(r.dates === '', 'an unresolved date ("the 30th") newer than the date -> stops', r.dates);
r = run(NEW, 'no client', 13, [Q, U(0, 'book qaorange friday next week 2pm')], { ...EPOCH });
ok(r.dates === '2027-10-08', '"friday next week" is a day, not a range -> 8 Oct', r.dates);
r = run(NEW, 'reset', 13, [Q, U(0, REQ)], { ...EPOCH });
ok(r.dates === '', 'a reset itself carries nothing');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
