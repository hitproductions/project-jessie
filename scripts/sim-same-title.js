#!/usr/bin/env node
// sim-same-title (PENDING 72; Cancel Booking v26, Move Booking v27, main v260): two bookings with the same title on one day.
//   node scripts/sim-same-title.js <main-execution.json>      (CANCEL / MOVE / MAIN env pick other builds)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const C = WF(process.env.CANCEL || 'cancel-booking-v26.json'), MV = WF(process.env.MOVE || 'move-booking-v27.json'), M = WF(process.env.MAIN || 'project-jessie-v260.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const ME = 'U08V3CKDGJF', S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const ev = (id, s, e) => ({ id, summary: 'QASER / Jem Lim / HL', status: 'confirmed', start: { dateTime: s }, end: { dateTime: e },
  attendees: [{ email: S7, resource: true }], location: 'KDC Plaza-Top Level-Studio 7 (7)', description: 'Booked by: Howard Luistro | ref: ' + ME });
const A = ev('a', '2027-11-02T10:00:00+08:00', '2027-11-02T12:00:00+08:00'), B = ev('b', '2027-11-02T15:00:00+08:00', '2027-11-02T17:00:00+08:00');
const base = { requester: ME, event_id: '', authority: '', department: 'Audio Post', title: 'QASER / Jem Lim / HL', booking_date: '2027-11-02' };
const co = req => new Function('$', '$input', code(C, 'Check Ownership'))(n => n === 'Find By Title' ? wrap([{ json: { items: [A, B] } }]) : wrap([{ json: req }]), wrap([{ json: { items: [A, B] } }]))[0].json;
const rb = req => new Function('$', '$input', code(MV, 'Resolve Booking'))(n => wrap([{ json: req }]), wrap([{ json: { items: [A, B] } }]))[0].json;

console.log('Cancel Booking v26');
let r = co({ ...base, mode: 'prepare', confirmed: false });
ok(r.reason === 'AMBIGUOUS_TITLE' && /Ask exactly this, in one message: "There are two bookings named \\"QASER \/ Jem Lim \/ HL\\" on Tuesday, November 2:\n- 10:00 AM – 12:00 PM\n- 3:00 PM – 5:00 PM\nWhich one should I cancel\?"/.test(r.human), 'two on the day -> one code question, the times listed', r.human);
r = co({ ...base, mode: 'prepare', confirmed: false, booking_time: '15:00' });
ok(r.verdict === 'PREPARED' && r.event_id === 'b', 'booking_time 15:00 -> the 3-5 PM one', [r.verdict, r.reason, r.event_id]);
r = co({ ...base, mode: 'prepare', confirmed: false, booking_time: '13:00' });
ok(r.reason === 'AMBIGUOUS_TITLE', 'a time that matches neither -> asked again', r.reason);
console.log('Move Booking v27');
const mv = { ...base, new_start_iso: '2027-11-03T10:00:00+08:00', new_end_iso: '2027-11-03T12:00:00+08:00', confirmed: false };
r = rb(mv);
ok(r.reason === 'AMBIGUOUS_TITLE' && /Which one should I move\?"/.test(r.human), 'two on the day -> one code question', r.human);
r = rb({ ...mv, booking_time: '10:00' });
ok(r.reason !== 'AMBIGUOUS_TITLE', 'booking_time 10:00 (the card\'s Now:) -> resolved', [r.verdict || r.status, r.reason]);

console.log('main v260 - the answer read by Booked For');
const STAFF = [{ Name: 'Howard Luistro', Initials: 'HL', Info: 'Post Engineer, Goes by Howard, HL.' }];
const Q = 'There are two bookings named "QASER / Jem Lim / HL" on Tuesday, November 2:\n- 10:00 AM – 12:00 PM\n- 3:00 PM – 5:00 PM\nWhich one should I cancel?';
const bf = (ans, q = Q) => { const hist = [{ ts: '12', text: ans, user: ME }, { ts: '11', text: q, bot_id: 'B1' }, { ts: '10', text: 'cancel QASER on nov 2', user: ME }];
  const $ = n => n === 'Slack Trigger' ? wrap([{ json: hist[0] }]) : n === 'Get Recent Messages' ? wrap(hist.map(h => ({ json: h }))) : n === 'All Bookers' ? wrap(STAFF.map(f => ({ json: { fields: f } })))
    : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '' } }]) : wrap([{ json: {} }]);
  return new Function('$', code(M, 'Booked For'))($)[0].json.whichTime; };
for (const [a, w] of [['the 3pm one', '15:00'], ['3-5', '15:00'], ['the first one', '10:00'], ['the later one', '15:00'], ['10am', '10:00'], ['the 10 one', '10:00'], ['3', '15:00'], ['ok', '']])
  ok(bf(a) === w, '"' + a + '" -> ' + (w || 'nothing'), bf(a));
ok(bf('3pm', 'What time works?') === '', 'not after a which-one question -> nothing');
const pc = M.nodes.find(x => x.name === 'Prepare Cancel').parameters.workflowInputs.value.booking_time, md = M.nodes.find(x => x.name === 'Move Direct').parameters.workflowInputs.value.booking_time;
ok(/whichTime/.test(pc) && /now_start/.test(md), 'Prepare Cancel passes whichTime; Move Direct the card\'s Now: start');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
