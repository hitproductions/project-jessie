#!/usr/bin/env node
// Offline tests for main v232 + Book Session v96 (live 7 Oct 17:22-17:24 PHT on main v231 / Book Session v95): "10-12pm" became
// 10 PM - 12 PM, "for sasa" was not taken as the client, and "Nothing was booked - the end time is not after the start time."
//   node scripts/sim-time-client.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v232.json'), OM = WF('project-jessie-v231.json');
const B = WF(process.env.BOOK || 'book-session-v96.json'), OB = WF('book-session-v95.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const ME = 'U08V3CKDGJF';
Date.now = () => Date.parse('2026-10-07T09:23:00Z');
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1791364000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const B1 = t => ({ bot_id: 'B1', text: t }), U = t => ({ user: ME, text: t });
const HEADS = 'Heads up: Studio 7 is already booked 3:00 PM – 5:00 PM (“WHEAT SUN / Jem Lim / AEG”) on Friday, October 8.\nStudio 7 is free 8:00 AM – 3:00 PM and 5:00 PM – 10:00 PM.\n\nWhat\'s the session type and the project title? Who’s the client? (or "none") And what time?';
const T2 = [U('book studio 7 tomorrow'), B1(HEADS), U('vo recording, project coild jacket. for sasa. 10-12pm')];

console.log('main v232 - "10-12pm" is 10 AM - 12 PM everywhere');
let o = bf(M, T2);
ok(o.timeStart === '10:00' && o.timeEnd === '12:00', 'the range: 10:00 - 12:00', [o.timeStart, o.timeEnd]);
ok(o.timesMentioned.includes('10:00') && !o.timesMentioned.includes('22:00'), 'what they typed: 10:00, not 22:00', o.timesMentioned);
ok(bf(OM, T2).timesMentioned.includes('22:00'), '  (v231: 22:00 counted as typed - the range read as 10 PM, and Jessie\'s "... 10:00 PM" - so the model\'s 10 PM was kept)', bf(OM, T2).timesMentioned);
// Prepare Booking's start_iso, with the model's 10 PM
const expr = (w, k, v, b) => { const e = w.nodes.find(x => x.name === 'Prepare Booking').parameters.workflowInputs.value[k].replace(/^=\{\{ /, '').replace(/ \}\}$/, '');
  return new Function('$fromAI', '$', 'return (' + e + ');')(() => v, n => ({ first: () => ({ json: n === 'Booked For' ? b : n === 'Gate Context' ? { datesUnderDiscussion: '2027-10-08' } : {} }) })); };
ok(expr(M, 'start_iso', '2027-10-08T22:00:00+08:00', o) === '2027-10-08T10:00:00+08:00', 'Prepare Booking: the model\'s 10 PM start -> 10:00 AM', expr(M, 'start_iso', '2027-10-08T22:00:00+08:00', o));
ok(expr(OM, 'start_iso', '2027-10-08T22:00:00+08:00', bf(OM, T2)) === '2027-10-08T22:00:00+08:00', '  (v231: 10 PM kept -> "end time is not after the start time")');
for (const [txt, s, e] of [['11 to 1pm', '11:00', '13:00'], ['10-12pm', '10:00', '12:00'], ['2-4pm', '14:00', '16:00'], ['9-11am', '09:00', '11:00'], ['10am-12pm', '10:00', '12:00'], ['8-10pm', '20:00', '22:00']]) {
  const r = bf(M, [U('book studio 7 tomorrow vo recording project orange ' + txt)]);
  ok(r.timeStart === s && r.timeEnd === e && r.timesMentioned.includes(s) && !r.timesMentioned.some(x => x !== s && x !== e), JSON.stringify(txt) + ' -> ' + s + ' - ' + e + ', and only those typed', [r.timeStart, r.timeEnd, r.timesMentioned]);
}

o = bf(M, [U('book studio 7 tomorrow 2-4pm vo recording project orange'), B1('Studio 7 is taken then. Studio 7 is free 5:00 PM – 7:00 PM.'), U('ok')]);
ok(o.timeStart === '14:00' && o.timesMentioned.includes('17:00'), 'an offer made after their range still counts as typed (they took it)', [o.timeStart, o.timesMentioned]);
o = bf(M, T2);
console.log('main v232 - "for sasa" is the client');
ok(o.forClient === 'Sasa', 'live 17:23: "... jacket. for sasa. 10-12pm" -> client Sasa', [o.forClient, o.forClientPhrase]);
ok(!bf(OM, T2).forClient, '  (v231: not taken - lowercase)');
const T3 = T2.concat([B1('Who’s the client? (or "none")'), U('for sasa')]);
o = bf(M, T3);
ok(o.forClient === 'Sasa' || /^sasa$/i.test(o.client), 'live 17:24: the answer "for sasa" -> Sasa', [o.client, o.forClient]);
const ans = a => bf(M, [U('book studio 7 tomorrow 2-4pm vo recording project orange'), B1('Who’s the client? (or "none")'), U(a)]).client;
for (const [a, want] of [['for sasa', 'sasa'], ["it's for jem lim", 'jem lim'], ['the producer is ABS', 'ABS'], ['producer: spotify', 'spotify'], ['Jem Lim', 'Jem Lim']])
  ok(String(ans(a)).toLowerCase() === want.toLowerCase(), 'the answer ' + JSON.stringify(a) + ' -> ' + want, ans(a));
for (const [txt, why] of [['book studio 7 for tomorrow 2-4pm', 'a date word'], ['book m3 for me tomorrow', 'me'], ['book studio 7 tomorrow. for vo recording.', 'a session type'],
    ['book studio 7 tomorrow 2-4pm. for lunch', 'lunch'], ['book studio 7 tomorrow. for howard', 'staff (booked for)'], ['book studio 7 tomorrow project orange. for orange', 'the project'],
    ['book studio 7 tomorrow for 2 hours', 'a length'], ['book likha tomorrow 2-4pm for a meeting', 'a meeting'], ['book studio 7 tomorrow, for mixing', 'mixing'], ['book studio 7 tomorrow for the client meeting', 'mid-sentence']]) {
  const r = bf(M, [U(txt)]);
  ok(!r.forClient, JSON.stringify(txt) + ' -> no client (' + why + ')', [r.forClient, r.bookedFor]);
}
ok(bf(M, [U('book studio 7 tomorrow 2-4pm vo recording, for jem lim')]).forClient === 'Jem Lim', '"..., for jem lim" (end of message) -> Jem Lim');
ok(bf(M, [U('book studio 7 tomorrow 2-4pm vo recording for Jem Lim')]).forClient === 'Jem Lim', 'capitalised, mid-sentence -> Jem Lim, as before');

console.log('Book Session v96 - a bad time range is a question');
const REF = recM('Room Table')[0].json.referenceData;
const cc = (w, req) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    rooms: 'Studio 7', engineer: 'Howard Luistro', session_type: 'VO Recording', client: '', expected_date: '2027-10-08', start_iso: '2027-10-08T22:00:00+08:00', end_iso: '2027-10-08T12:00:00+08:00',
    summary: 'COILD JACKET / HL', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: 'vo recording, project coild jacket. for sasa. 10-12pm', requester_text: 'book studio 7 tomorrow\nvo recording, project coild jacket. for sasa. 10-12pm\nnone', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
let c = cc(B, {});
ok(c.reason === 'DURATION_INVALID' && /Ask exactly this: "What time does it start and end\?"/.test(c.human) && !/Nothing was booked/.test(c.human), 'DURATION_INVALID carries "What time does it start and end?"', c);
ok(/Nothing was booked/.test(cc(OB, {}).human), '  (v95: "Nothing was booked - the end time is not after the start time.")');
// through Guard Probe, as the agent sees it (Return Rejection: status)
const gp = (W, out, obs) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output: out, intermediateSteps: [{ action: { tool: 'Prepare_Booking', toolInput: {} }, observation: JSON.stringify([obs]) }] } }]),
  n => { if (n === 'Early Room Result') throw new Error('not executed'); return wrap(n === 'Booked For' ? [{ json: { requesterText: 'x' } }] : recM(n) || [{ json: {} }]); })[0].json.output;
const obs = { status: 'REJECTED', reason: 'DURATION_INVALID', human: c.human };
ok(gp(M, 'Nothing was booked - the end time is not after the start time.', obs) === 'What time does it start and end?', 'Guard Probe sends the question, not "Nothing was booked"', gp(M, 'Nothing was booked - the end time is not after the start time.', obs));
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
