#!/usr/bin/env node
// Offline tests for main v189 + Move Booking v25: duplicate deliveries (PENDING 57), the code-written move card, and a
// change right after "Moved". No calendar or Slack is touched.
//
//   node scripts/sim-dedupe-move.js <execution-dir>
//
// <execution-dir> holds real main executions from 29 Sep, named <id>.json:
//   16875 (re-sent booking request, on time)  16877 (Slack's late retry of the first copy)
//   16951 (second "yes", on time, booked)       16954 (Slack's late retry of the first "yes")
//   16685 ("make that 3pm instead" right after "Booked.")
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
const M = WF(process.env.MAIN || 'project-jessie-v189.json'), OLDM = WF('project-jessie-v188.json');
const MV = WF(process.env.MOVE || 'move-booking-v25.json'), OLDMV = WF('move-booking-v24.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const load = id => JSON.parse(fs.readFileSync(path.join(process.argv[2], id + '.json'))).data.resultData.runData;
const recOf = run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;

console.log('Duplicate Check - the real 29 Sep deliveries');
const dupRun = (id, over = {}) => { const rec = recOf(load(id));
  const $ = n => over[n] ? wrap(over[n]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(M, 'Duplicate Check'))($, wrap([{ json: { gate: 'kept' } }]))[0].json; };
let r = dupRun('16877');
ok(r._dup === true, '16877: the 15:41:01 request arriving 61 s late, after the re-sent copy was answered -> dropped', r);
r = dupRun('16875');
ok(r._dup !== true && r.gate === 'kept', '16875: the re-sent copy, when it arrived (nothing answered yet) -> handled, input passed through', r);
r = dupRun('16954');
ok(r._dup === true, '16954: the first "yes" arriving 61 s late, after the second was booked -> dropped', r);
r = dupRun('16951');
ok(r._dup !== true, '16951: the second "yes", on time -> handled (it booked)', r);
{ const U = (ts, text) => ({ json: { ts: String(ts), text, user: 'U1' } }), B = (ts, text) => ({ json: { ts: String(ts), text, bot_id: 'B1' } });
  const T = t => [{ json: { user: 'U1', ts: String(t), text: 'yes' } }];
  r = dupRun('16951', { 'Slack Trigger': T(1060), 'Get Recent Messages': [U(1060, 'yes'), B(1050, 'summary B ... Book it? Reply yes or no.'), B(1040, 'Booked.'), U(1030, 'yes'), B(1020, 'summary A ... Book it?')] });
  ok(r._dup !== true, 'two "yes" replies to two different summaries (a Jessie message between) -> both count');
  r = dupRun('16951', { 'Slack Trigger': T(1300), 'Get Recent Messages': [U(1300, 'yes'), B(1200, 'Booked.'), U(1100, 'yes')] });
  ok(r._dup !== true, 'the same text more than 2 minutes apart -> handled');
  r = dupRun('16951', { 'Slack Trigger': [{ json: { user: 'U1', ts: '1030', text: 'Yes ' } }], 'Get Recent Messages': [B(1045, 'Booked.'), U(1035, 'yes'), U(1030, 'Yes ')] });
  ok(r._dup === true, 'case and spacing do not matter');
  r = dupRun('16951', { 'Slack Trigger': [{ json: { user: 'U1', ts: '1030', text: 'yes' } }], 'Get Recent Messages': [B(1045, 'Booked.'), { json: { ts: '1035', text: 'yes', user: 'U2' } }, U(1030, 'yes')] });
  ok(r._dup !== true, "someone else's identical message does not count"); }
const to = (w, n, b = 0) => ((((w.connections[n] || {}).main || [])[b]) || []).map(t => t.node);
ok(JSON.stringify(to(M, 'Gate Context')) === '["Duplicate Check"]' && JSON.stringify(to(M, 'Duplicate Check')) === '["Duplicate?"]'
   && JSON.stringify(to(M, 'Duplicate?', 0)) === '["Clear Ack"]' && JSON.stringify(to(M, 'Duplicate?', 1)) === JSON.stringify(to(OLDM, 'Gate Context')),
   'wiring: Gate Context -> Duplicate Check -> Duplicate? -> (dropped: Clear Ack, nothing sent) / (else: as before)');
ok(/\$json\._dup === true/.test(node(M, 'Duplicate?').parameters.conditions.conditions[0].leftValue), 'Duplicate? tests only the _dup flag');

console.log('Move Booking v25 - the card');
const S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com', ME = 'U08V3CKDGJF';
const EV = { id: 'q1', status: 'confirmed', summary: 'QAMOVE / Jem Lim / DR', start: { dateTime: '2027-11-17T14:00:00+08:00' }, end: { dateTime: '2027-11-17T16:00:00+08:00' },
  location: 'KDC Plaza-Top Level-Studio 8 (7)', attendees: [{ email: S8, resource: true }], description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: ' + ME + ' | Dept: Audio Post' };
const base = { requester: ME, title: 'QAMOVE / Jem Lim / DR', booking_date: '2027-11-17', new_start_iso: '2027-11-17T15:00:00+08:00', new_end_iso: '2027-11-17T17:00:00+08:00', event_id: '', new_rooms: '', authority: '', department: 'Audio Post' };
const rb = (w, req, items = [EV]) => new Function('$', '$input', code(w, 'Resolve Booking'))(
  n => n === 'When Executed by Another Workflow' ? wrap([{ json: req }]) : wrap([{ json: {} }]), wrap([{ json: { items } }]))[0].json;
r = rb(MV, { ...base, confirmed: false });
ok(r.reason === 'NOT_CONFIRMED' && r.card_text === '*QAMOVE / Jem Lim / DR*\n*Now:* Wednesday, November 17, 2027, 2:00 PM – 4:00 PM, Studio 8\n*Moving to:* Wednesday, November 17, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nConfirm to move.',
   'unconfirmed -> a card with where it is now and where it is going', r.card_text);
ok(!/Confirm to move/.test(r.human) && /do not write one/.test(r.human), 'the model is told not to write its own card');
r = rb(MV, { ...base, confirmed: false, new_rooms: 'Studio 7' });
ok(/\*Moving to:\* Wednesday, November 17, 2027, 3:00 PM – 5:00 PM, Studio 7/.test(r.card_text), 'a room change shows the new room', r.card_text);
r = rb(MV, { ...base, confirmed: false, requester: 'U999' });
ok(r.reason === 'NOT_YOURS', "someone else's booking -> refused before any card (was: after the yes)", r.reason);
ok(rb(OLDMV, { ...base, confirmed: false, requester: 'U999' }).reason === 'NOT_CONFIRMED', '  (v24: a card first, the refusal only after the yes)');
r = rb(MV, { ...base, confirmed: false, title: 'NOPE / X / DR' });
ok(r.reason === 'NOT_ON_CALENDAR', 'a booking that is not there -> refused before any card', r.reason);
r = rb(MV, { ...base, confirmed: true });
ok(r.verdict === 'CLEAR' && r.original_id === 'q1' && r.new_start === base.new_start_iso, 'confirmed -> CLEAR as before');
const rej = new Function('$input', code(MV, 'Return Rejection'))(wrap([{ json: rb(MV, { ...base, confirmed: false }) }]))[0].json;
ok(rej.status === 'REJECTED' && rej.reason === 'NOT_CONFIRMED' && /\*Now:\*/.test(rej.card_text), 'Return Rejection carries the card back to main');

console.log('Guard Probe - the move card is the reply');
{ const rec = recOf(load('16685'));
  const gp = (w, steps, output = 'Moving QAMOVE to 3 PM. Confirm to move.') => new Function('$input', '$', code(w, 'Guard Probe'))(
    wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
  const st = o => [{ action: { tool: 'Move_Booking' }, observation: JSON.stringify([o]) }];
  const out = gp(M, st(rej));
  ok(out === '*QAMOVE / Jem Lim / DR*\n*Now:* Wednesday, November 17, 2027, 2:00 PM – 4:00 PM, Studio 8\n*Moving to:* Wednesday, November 17, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.', 'the card is sent, one-line confirmation', out);
  ok(!/\*Now:\*/.test(gp(M, st({ status: 'REJECTED', reason: 'NOT_YOURS', human: 'x' }), "That booking isn't yours.")), 'a refusal -> no card');
  ok(!/\*Now:\*/.test(gp(OLDM, st(rej))), '  (v188: the model\'s own card)'); }

console.log('Booked For - a change right after "Moved"');
{ const rec = recOf(load('16685'));
  const hist = [{ json: { ts: '1790662300.1', text: 'make it 3pm instead', user: ME } },
    { json: { ts: '1790662290.1', text: 'Moved "QAMOVE / Jem Lim / DR" to Friday, October 1, 2027, 9:00 AM – 11:00 AM in Studio 8.', bot_id: 'B1' } },
    { json: { ts: '1790662280.1', text: 'yes', user: ME } }];
  const bf = w => new Function('$', '$input', code(w, 'Booked For'))(n => n === 'Get Recent Messages' ? wrap(hist)
    : n === 'Slack Trigger' ? wrap([{ json: hist[0].json }]) : wrap(rec(n) || [{ json: {} }]), wrap([{ json: {} }]))[0].json;
  const b = bf(M);
  ok(b.changeJustBooked === true && b.justBooked && b.justBooked.title === 'QAMOVE / Jem Lim / DR' && b.justBooked.iso === '2027-10-01', 'the booking is read from the "Moved" message', b.justBooked);
  ok(b.moveStart === '15:00' && b.moveEnd === '17:00', '"make it 3pm" after a 9-11 move -> 3-5 PM (length kept)', [b.moveStart, b.moveEnd]);
  ok(/THEY ARE CHANGING THE BOOKING THEY JUST MOVED/.test(b.notice), 'the model is told it is the booking just moved');
  const o = bf(OLDM);
  ok(!o.changeJustBooked, '  (v188: nothing after "Moved" - the model worked the times out itself)'); }

console.log('Gate Context - a lone time right after "Moved" is a change, not start-only');
ok(/\(\?:booked\|moved\)\\b\/i\.test\(lastBotText\)/.test(code(M, 'Gate Context')), 'the rule covers "Moved"');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
