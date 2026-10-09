#!/usr/bin/env node
// Offline tests for main v235 + Book Session v97 + Book Series v7 (taken-room layout, asked 7 Oct): every "room taken" message in the
// ❌ / ✅ heads-up layout. Book Session's ROOM_OCCUPIED goes through its real Check Conflicts and Return Rejection into Guard Probe.
//   node scripts/sim-taken-layout.js <main-execution.json>     (PREVIEW=1 prints each message)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v235.json'), OM = WF('project-jessie-v234.json');
const B = WF(process.env.BOOK || 'book-session-v97.json'), OB = WF('book-session-v96.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 900))); } };
const show = (t, s) => { if (process.env.PREVIEW) console.log('\n----- ' + t + '\n' + s + '\n'); };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const REF = recM('Room Table')[0].json.referenceData;
const ME = 'U08V3CKDGJF';
Date.now = () => Date.parse('2026-10-07T09:40:00Z');
const E = (room, d, s, e, title, ref) => ({ id: room + d + s, summary: title, location: room, description: 'Booked by: X | ref: ' + ref,
  start: { dateTime: d + 'T' + s + ':00+08:00' }, end: { dateTime: d + 'T' + e + ':00+08:00' } });
const TXT = 'book studio 7 on oct 8 2027 3-5pm, vo recording, project orange, client jem lim, engineer howard';
const cc = (w, cal, req = {}) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    rooms: 'Studio 7', engineer: 'Howard Luistro', session_type: 'VO Recording', client: 'Jem Lim', expected_date: '2027-10-08', start_iso: '2027-10-08T15:00:00+08:00', end_iso: '2027-10-08T17:00:00+08:00',
    summary: 'ORANGE / Jem Lim / HL', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: TXT, requester_text: TXT, ...req } }];
  const O = { 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim' } } }], 'Client Aliases': [{ json: {} }], 'All Client Names': [{ json: { fields: { Name: 'Jem Lim' } } }] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: cal } }]), () => ({}))[0].json; };
const rr = (w, v) => new Function('$', '$input', code(w, 'Return Rejection'))(() => wrap([{ json: {} }]), wrap([{ json: v }]))[0].json;
const gp = (W, out, tool, obs) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output: out, intermediateSteps: [{ action: { tool, toolInput: {} }, observation: JSON.stringify([obs]) }] } }]),
  n => { if (n === 'Early Room Result') throw new Error('not executed'); return wrap(n === 'Booked For' ? [{ json: { requesterText: TXT } }] : recM(n) || [{ json: {} }]); })[0].json.output;
const MODEL = 'Studio 7 is taken by "WHEAT SUN / Jem Lim / AEG". Want Studio 8 instead?';

console.log('Book Session ROOM_OCCUPIED -> written by code (main v235 + Book Session v97)');
const CAL = [E('Studio 7', '2027-10-08', '15:00', '17:00', 'WHEAT SUN / Jem Lim / AEG', 'U2')];
let c = cc(B, CAL);
ok(c.verdict === 'REJECTED' && c.reason === 'ROOM_OCCUPIED' && Array.isArray(c.free_alternatives) && c.free_alternatives.length, 'Check Conflicts: ROOM_OCCUPIED with free alternatives', [c.verdict, c.reason, c.free_alternatives, c.human]);
let o = rr(B, c);
ok(Array.isArray(o.free_alternatives) && o.own_booking === false && o.conflicts.length === 1, 'Return Rejection now passes free_alternatives and own_booking', o);
ok(!('free_alternatives' in rr(OB, c)) || rr(OB, c).free_alternatives == null, '  (v96: the agent never saw the alternatives)');
let t = gp(M, MODEL, 'Prepare_Booking', o); show('taken (someone else\'s)', t);
const V101 = Array.isArray(o.same_day_slots);
ok(t === '❌ Heads up: *Studio 7 is already booked 3:00 PM – 5:00 PM* on Friday, October 8 by this session: WHEAT SUN / Jem Lim / AEG\n\n'
  + (V101 ? '✅ Studio 7 is free on the same day at:\n• 1:00 PM – 3:00 PM\n• 5:00 PM – 7:00 PM\n\n' : '') + '✅ Free at that time:\n'
  + o.free_alternatives.join(' · ') + '\n\nWant one of those, or another day or time?', 'the reply is the ❌ / ✅ layout', t);
ok(gp(OM, MODEL, 'Prepare_Booking', o) !== t, '  (v234: the model\'s own wording)');
c = cc(B, [E('Studio 7', '2027-10-08', '15:00', '17:00', 'ORANGE / Jem Lim / HL', ME)]); o = rr(B, c);
t = gp(M, 'That overlaps a booking you already have.', 'Prepare_Booking', o); show('taken (your own)', t);
ok(o.own_booking === true && t === '❌ Heads up: *You already have Studio 7 booked 3:00 PM – 5:00 PM* on Friday, October 8 with this session: ORANGE / Jem Lim / HL\n\nWant to move that booking to this time instead?',
  'your own booking -> "You already have ..." and the move question', t);
c = cc(B, [E('Studio 7', '2027-10-08', '14:00', '15:30', 'A / HL', 'U2'), E('Studio 7', '2027-10-08', '16:30', '18:00', 'B / HL', 'U3')]); o = rr(B, c);
t = gp(M, MODEL, 'Prepare_Booking', o); show('taken by two sessions', t);
ok(/^❌ Heads up: \*Studio 7 is already booked 2:00 PM – 3:30 PM and 4:30 PM – 6:00 PM\* on Friday, October 8 by these sessions: A \/ HL · B \/ HL\n\n/.test(t), 'two sessions -> both times, "these sessions"', t);
const allDay = { id: 'x', summary: 'HOLD', location: 'Studio 7', description: 'ref: U2', start: { date: '2027-10-08' }, end: { date: '2027-10-09' } };
o = rr(B, cc(B, [allDay])); t = gp(M, MODEL, 'Prepare_Booking', o);
ok(/^❌ Heads up: \*Studio 7 is already booked all day\* on Friday, October 8 by this session: HOLD\n/.test(t), 'an all-day hold -> "all day", the right date', t);
o = Object.assign(rr(B, cc(B, CAL)), { free_alternatives: [] }); t = gp(M, MODEL, 'Prepare_Booking', o);
ok(V101 ? /\n\n✅ Studio 7 is free on the same day at:\n• 1:00 PM – 3:00 PM\n• 5:00 PM – 7:00 PM\n\nWant one of those, or another day or time\?$/.test(t)
    : /\n\nNothing like it is free then\. What other day or time works\?$/.test(t), V101 ? 'no other room free -> the same-day times still offered (v101)' : 'nothing else free -> asks for another day or time', t);
t = gp(M, MODEL, 'Prepare_Booking', Object.assign({}, o, { same_day_slots: [] }));
ok(/\n\nNothing like it is free then\. What other day or time works\?$/.test(t), 'nothing at all free -> asks for another day or time', t);
ok(gp(M, MODEL, 'Prepare_Booking', { status: 'REJECTED', reason: 'MISSING_DETAILS', human: 'x' }) === gp(OM, MODEL, 'Prepare_Booking', { status: 'REJECTED', reason: 'MISSING_DETAILS', human: 'x' }), 'any other refusal -> as before');

console.log('Move Booking ROOM_OCCUPIED');
const mv = { status: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'Nothing was moved - that room is taken in the new window by "WHEAT SUN / Jem Lim / AEG". The original booking is untouched. Tell the requester and offer another time.' };
t = gp(M, 'That time is taken.', 'Move_Booking', mv); show('move into a taken time (before the yes)', t);
ok(t === '❌ Heads up: *That time is already booked* by this session: WHEAT SUN / Jem Lim / AEG\n\nThe booking stays where it is. Want a different time or room?', 'before the yes -> the layout, with the session', t);
const mdr = new Function('$', '$input', code(M, 'Move Direct Reply'))(n => ({ first: () => ({ json: n === 'Booked For' ? { approvedMove: { title: 'X' } } : {} }) }), wrap([{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED' } }]))[0].json.output;
show('move into a taken time (at the yes)', mdr);
ok(mdr === '❌ Heads up: *That time is already booked now*\n\nThe booking stays where it is. Want a different time or room?', 'at the yes (Move Direct) -> the layout', mdr);

console.log('Book Session v97 - the priority card note');
const rs = code(B, 'Render Summary');
ok(rs.includes("'❌ *' + o.room + ' is already booked then* by this session: ' + (o.incumbentTitle || 'another session') + '\\nYour session outranks it"), 'priority: "❌ *Studio 7 is already booked then* by this session: X" + the outrank line');
ok(rs.includes("It is a standing hold - if you confirm, I will ask"), 'M booth hold: same first line, then the hold line');
show('priority card note', '❌ *Studio 7 is already booked then* by this session: WHEAT SUN / Jem Lim / AEG\nYour session outranks it, so if you confirm I will ask them to move, and book it once they do.');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
