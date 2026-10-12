#!/usr/bin/env node
// sim-move-alternatives (Move Booking v28 + main v261, PENDING 102): a move into a taken time offers the room's nearest free times.
//   node scripts/sim-move-alternatives.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f))), code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const MV = WF(process.env.MOVE || 'move-booking-v28.json'), M = WF(process.env.MAIN || 'project-jessie-v261.json');
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData, rec = n => run[n] ? run[n][0].data.main[0] : null;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const E = (id, s, e, t) => ({ id, summary: t, status: 'confirmed', start: { dateTime: s }, end: { dateTime: e }, attendees: [{ email: S7, resource: true }], location: 'KDC Plaza-Top Level-Studio 7 (7)' });
const R = { original_id: 'orig', attendees: [{ email: S7 }], location: 'KDC Plaza-Top Level-Studio 7 (7)', new_start: '2027-10-13T12:00:00+08:00', new_end: '2027-10-13T14:00:00+08:00' };
const cnw = items => new Function('$', '$input', code(MV, 'Check New Window'))(n => wrap([{ json: R }]), wrap([{ json: { items } }]))[0].json;
let r = cnw([E('orig', '2027-10-13T09:00:00+08:00', '2027-10-13T10:00:00+08:00', 'MINE'), E('x', '2027-10-13T13:00:00+08:00', '2027-10-13T15:00:00+08:00', 'CATTAIL / HL')]);
ok(r.reason === 'ROOM_OCCUPIED' && JSON.stringify(r.same_day_slots) === JSON.stringify([{ start: '2027-10-13T11:00:00+08:00', end: '2027-10-13T13:00:00+08:00' }, { start: '2027-10-13T15:00:00+08:00', end: '2027-10-13T17:00:00+08:00' }]),
  'moving to 12-2 PM, taken 1-3 PM -> 11 AM-1 PM, then 3-5 PM (its own 9-10 AM slot not counted)', r.same_day_slots);
r = cnw([E('x', '2027-10-13T17:00:00+08:00', '2027-10-13T18:00:00+08:00', 'LATER')]);
ok(r.verdict === 'CLEAR', 'a booking outside the new window does not block the move', r.verdict);
const rr = new Function('$', '$input', code(MV, 'Return Rejection'))(() => wrap([{ json: {} }]), wrap([{ json: { reason: 'ROOM_OCCUPIED', human: 'x', same_day_slots: [{ start: 'a', end: 'b' }] } }]))[0].json;
ok(Array.isArray(rr.same_day_slots), 'Return Rejection passes the times on');
const url = MV.nodes.find(x => x.name === 'Get New Window').parameters.url;
ok(/T08:00:00\+08:00/.test(url) && /T22:00:00\+08:00/.test(url), 'Get New Window reads the day 8 AM - 10 PM');
const obs = { status: 'REJECTED', reason: 'ROOM_OCCUPIED', same_day_slots: [{ start: '2027-10-13T11:00:00+08:00', end: '2027-10-13T13:00:00+08:00' }, { start: '2027-10-13T15:00:00+08:00', end: '2027-10-13T17:00:00+08:00' }],
  human: 'Nothing was moved - that room is taken in the new window by "CATTAIL / HL". The original booking is untouched. Tell the requester and offer another time.' };
const out = new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output: 'That time is taken.', intermediateSteps: [{ action: { tool: 'Move_Booking', toolInput: {} }, observation: JSON.stringify([obs]) }] } }]),
  n => { if (n === 'Early Room Result') throw new Error('x'); return wrap(rec(n) || [{ json: {} }]); })[0].json.output;
ok(out === '❌ Heads up: *That time is already booked* by this session: CATTAIL / HL\n\n✅ Free the same day at:\n• 11:00 AM – 1:00 PM\n• 3:00 PM – 5:00 PM\n\nThe booking stays where it is. Want one of those, or another time or room?', 'the heads-up lists them', out);
console.log('Move Booking v29 - the new time checked before the card (live 12 Oct 13:27)');
if (/v29 \(live 12 Oct 13:27\)/.test(code(MV, 'Resolve Booking'))) {
  const ME = 'U08V3CKDGJF', mine = { id: 'orig', summary: 'QATEST3 / HL', status: 'confirmed', start: { dateTime: '2027-10-13T10:00:00+08:00' }, end: { dateTime: '2027-10-13T12:00:00+08:00' },
    attendees: [{ email: S7, resource: true }], location: 'KDC Plaza-Top Level-Studio 7 (7)', description: 'Booked by: Howard Luistro | ref: ' + ME };
  const req = { title: 'QATEST3 / HL', booking_date: '2027-10-13', new_start_iso: '2027-10-13T15:00:00+08:00', new_end_iso: '2027-10-13T17:00:00+08:00', requester: ME, confirmed: false, authority: '', department: 'Audio Post', event_id: '' };
  const R1 = new Function('$', '$input', code(MV, 'Resolve Booking'))(n => wrap([{ json: req }]), wrap([{ json: { items: [mine] } }]))[0].json;
  ok(R1.verdict === 'CLEAR' && /\*Moving to:\* Wednesday, October 13, 2027, 3:00 PM – 5:00 PM/.test(R1.preview_card || ''), 'before the yes: no card yet - it goes on to the window check', [R1.verdict, R1.reason]);
  const cnw2 = items => new Function('$', '$input', code(MV, 'Check New Window'))(n => wrap([{ json: R1 }]), wrap([{ json: { items } }]))[0].json;
  let r2 = cnw2([mine, E('w', '2027-10-13T15:00:00+08:00', '2027-10-13T18:00:00+08:00', 'WTR / Jem Lim / AEG')]);
  ok(r2.reason === 'ROOM_OCCUPIED' && Array.isArray(r2.same_day_slots) && r2.same_day_slots.length, 'taken 3-6 PM (live 13:27): the heads-up with free times, no card', [r2.reason, r2.same_day_slots]);
  r2 = cnw2([mine]);
  ok(r2.reason === 'NOT_CONFIRMED' && /Moving to/.test(r2.card_text || '') && r2.verdict !== 'CLEAR', 'free: the move card - and never CLEAR, so nothing is moved before the yes', [r2.verdict, r2.reason]);
  const R2 = new Function('$', '$input', code(MV, 'Resolve Booking'))(n => wrap([{ json: { ...req, confirmed: true } }]), wrap([{ json: { items: [mine] } }]))[0].json;
  ok(R2.verdict === 'CLEAR' && !R2.preview_card, 'at the yes: CLEAR with no preview card (the move goes ahead when free)', [R2.verdict, R2.preview_card]);
}
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
