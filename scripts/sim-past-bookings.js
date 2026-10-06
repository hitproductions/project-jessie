#!/usr/bin/env node
// Offline tests for main v220 + Book Session v91 + Room Availability v17 (past bookings allowed; decided 6 Oct): a session
// in the past can be booked, a date with a year is taken as written ("oct 1 2026" during the QA year shift), and
// yesterday / last <weekday> / N days ago resolve to dates.
//   node scripts/sim-past-bookings.js <main-execution.json>   (its All Bookers output feeds Book Session)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v220.json'), OM = WF('project-jessie-v219.json');
const B = WF(process.env.BOOK || 'book-session-v91.json'), OB = WF('book-session-v90.json');
const RA = WF(process.env.RA || 'room-availability-v17.json'), ORA = WF('room-availability-v16.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const ME = 'U08V3CKDGJF';
Date.now = () => Date.parse('2026-10-06T05:30:00Z');   // Tue 6 Oct 2026, 13:30 Manila (Jessie: Wed 6 Oct 2027)

console.log('Gate Context v220 - past dates');
const gate = (w, text) => { const store = {};
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: ME, ts: '1791264600.1', channel: 'D1' } : n === 'Get Booker' ? { fields: { Name: 'Howard Luistro', Department: ['Audio Post'] } } : {} }), all: () => [] });
  return new Function('$', '$getWorkflowStaticData', code(w, 'Gate Context'))($, () => store)[0].json; };
let g = gate(M, 'book studio 8 oct 1 2026 3-5pm');
ok(g.datesUnderDiscussion === '2026-10-01', '"oct 1 2026" -> 2026-10-01 (the year as written, not 2027)', g.datesUnderDiscussion);
ok(/ALREADY PASSED: oct 1 2026\. That is allowed/.test(g.pastDateNotice) && !/do not attempt to book/i.test(g.pastDateNotice), 'the notice says it is allowed', g.pastDateNotice);
ok(/do not attempt to book it/.test(gate(OM, 'book studio 8 oct 1 2026 3-5pm').pastDateNotice), '  (v219: "do not attempt to book it")');
ok(gate(M, 'book studio 8 2026-09-15 2-4pm').datesUnderDiscussion === '2026-09-15', '"2026-09-15" -> as written');
ok(gate(M, 'book studio 8 yesterday 2-4pm').datesUnderDiscussion === '2027-10-05', '"yesterday" -> Tue 5 Oct 2027', gate(M, 'book studio 8 yesterday 2-4pm').datesUnderDiscussion);
ok(!gate(OM, 'book studio 8 yesterday 2-4pm').datesUnderDiscussion, '  (v219: unresolved)');
ok(gate(M, 'book studio 8 the day before yesterday 2-4pm').datesUnderDiscussion === '2027-10-04', '"the day before yesterday" -> 4 Oct', gate(M, 'book studio 8 the day before yesterday 2-4pm').datesUnderDiscussion);
ok(gate(M, 'book studio 8 last monday 2-4pm').datesUnderDiscussion === '2027-10-04', '"last monday" (today Wednesday) -> Mon 4 Oct', gate(M, 'book studio 8 last monday 2-4pm').datesUnderDiscussion);
ok(gate(M, 'book studio 8 last wednesday 2-4pm').datesUnderDiscussion === '2027-09-29', '"last wednesday" on a Wednesday -> a week ago', gate(M, 'book studio 8 last wednesday 2-4pm').datesUnderDiscussion);
ok(gate(M, 'book studio 8 last fri 2-4pm').datesUnderDiscussion === '2027-10-01', '"last fri" -> Fri 1 Oct', gate(M, 'book studio 8 last fri 2-4pm').datesUnderDiscussion);
ok(gate(M, 'book studio 8 3 days ago 2-4pm').datesUnderDiscussion === '2027-10-03', '"3 days ago" -> 3 Oct', gate(M, 'book studio 8 3 days ago 2-4pm').datesUnderDiscussion);
ok(gate(M, 'book studio 8 on the last friday of october').datesUnderDiscussion !== '2027-10-01', '"the last friday of october" is not last Friday', gate(M, 'book studio 8 on the last friday of october').datesUnderDiscussion);
ok(gate(M, 'book studio 8 tomorrow 2-4pm').datesUnderDiscussion === '2027-10-07', '"tomorrow" unchanged');
ok(gate(M, 'book studio 8 next thu 3-5pm').datesUnderDiscussion === '2027-10-14', '"next thu" unchanged');
ok(gate(M, 'book studio 8 dec 1 2027 3-5pm').pastDateNotice === '', 'a future date -> no notice');

console.log('Book Session v91 - a past session is prepared and booked');
const REF = JSON.stringify({ rooms: [{ id: 'r8', name: 'Studio 8', common: false }], types: [{ type: 'Post Mixing', typical: 120, ranked: ['Studio 8'], priority: ['Studio 8'] }] });
const cc = (w, req) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    rooms: 'Studio 8', engineer: 'Howard Luistro', session_type: 'Post Mixing', client: '', summary: 'RUNWAY / HL',
    description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: '', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  if (c.verdict !== 'CLEAR') return { c, s: '' };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(recM(n) || [{ json: {} }]);
  let s = ''; try { s = new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json.summary_text || ''; } catch (e) { s = 'ERR ' + e.message; }
  return { c, s }; };
const P26 = { expected_date: '2026-10-01', start_iso: '2026-10-01T15:00:00+08:00', end_iso: '2026-10-01T17:00:00+08:00', requester_text: 'book studio 8 oct 1 2026 3-5pm post mixing project runway, no client' };
let r = cc(B, P26);
ok(r.c.verdict === 'CLEAR', '1 Oct 2026 (past) -> prepared', [r.c.reason, r.c.human]);
ok(/Heads up: this date has already passed\./.test(r.s), 'the card says the date has passed', r.s);
ok(cc(OB, P26).c.reason === 'PAST_DATE', '  (v90: PAST_DATE)');
r = cc(B, { ...P26, mode: '', prepared_ok: true, confirmed: true });
ok(r.c.verdict === 'CLEAR', 'at the yes -> booked, not refused', [r.c.reason]);
r = cc(B, { expected_date: '2026-10-06', start_iso: '2026-10-06T09:00:00+08:00', end_iso: '2026-10-06T11:00:00+08:00', requester_text: 'book studio 8 today 9-11am post mixing project runway, no client' });
ok(r.c.verdict === 'CLEAR' && !/already passed/.test(r.s), 'earlier today -> no heads-up', [r.c.reason, r.s]);
r = cc(B, { expected_date: '2027-10-14', start_iso: '2027-10-14T15:00:00+08:00', end_iso: '2027-10-14T17:00:00+08:00', requester_text: 'book studio 8 next thu 3-5pm post mixing project runway, no client' });
ok(r.c.verdict === 'CLEAR' && !/already passed/.test(r.s), 'a future date -> no heads-up', [r.c.reason, r.s]);
r = cc(B, { expected_date: '', start_iso: '2026-09-28T15:00:00+08:00', end_iso: '2026-09-28T17:00:00+08:00', requester_text: 'book studio 8 last week 3-5pm post mixing project runway, no client' });
ok(r.c.reason === 'MISSING_DATE', '"last week" (no day) -> "Which day?", not PAST_DATE', r.c.reason);

console.log('Room Availability v17 - a past window is checked');
const RREF = JSON.stringify({ rooms: [{ id: 'r8', name: 'Studio 8', common: false }, { id: 'r7', name: 'Studio 7', common: false }], types: [] });
const ra = (w, req) => new Function('$', '$input', code(w, 'Compute Availability'))(n => wrap([{ json: { reference_data: RREF, scope: 'studios', ...req } }]), wrap([{ json: { items: [] } }]))[0].json;
const W26 = { start_iso: '2026-10-01T15:00:00+08:00', end_iso: '2026-10-01T17:00:00+08:00' };
ok(ra(RA, W26).status !== 'PAST_DATE' && /Studio 8/.test(JSON.stringify(ra(RA, W26))), '1 Oct 2026 3-5pm -> the free rooms', ra(RA, W26).status);
ok(ra(ORA, W26).status === 'PAST_DATE', '  (v16: PAST_DATE)');

console.log('main v220 prompt');
const sm = M.nodes.find(x => x.name === 'Jessie AI Agent').parameters.options.systemMessage;
ok(/Past dates are fine/.test(sm) && !/never in the past/.test(sm) && !/If it has passed, say so/.test(sm), 'no "refuse a past date" left in the prompt');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
