#!/usr/bin/env node
// Slack Interactions v44 + main v283 + Reminders v6 + Move v38 + Cancel v32 (26 Oct, Howard): the booking's note in Slack - "*Notes:*"
// at the end of a card (Booked, series, Changed, reminders, the cancel / move notices; the engineer / arranger notice carries the
// Booked card), "📝" and the note's first line in a list (My bookings, typed "what do I have").
// Usage: node scripts/sim-notes-in-slack.js [si v44] [main v283] [reminders v6] [move v38] [cancel v32]
const fs = require('fs');
const L = (i, d) => JSON.parse(fs.readFileSync(process.argv[i] || d, 'utf8'));
const si = L(2, 'workflows/slack-interactions-v44.json'), main = L(3, 'workflows/project-jessie-v283.json'), RM = L(4, 'workflows/reminders-v6.json'),
  mv = L(5, 'workflows/move-booking-v38.json'), cx = L(6, 'workflows/cancel-booking-v32.json');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (JSON.stringify(si.nodes).indexOf('function evNote(') === -1) { console.log('0 ok, 0 failed (an older build: the note not in it)'); process.exit(0); }
const run = async (wf, name, input, outs) => { const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  return new Function('$', '$input', 'return (async function(){' + wf.nodes.find(x => x.name === name).parameters.jsCode + '\n})();')($, { first: () => input[0], all: () => input }); };
const B = (id, name, slack, info) => ({ id, fields: { Name: name, Initials: 'HL', 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: [B('b1', 'Howard Luistro', 'U1', 'Post Engineer')] }) } }];
const NOTE = 'this is a testing for notes\n\ntesting spaces';
const NEW = 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1 | Type: Advertising | Dept: Audio Post\nSType: VO Recording\n\nNotes:\n' + NOTE;
const OLD = 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | Notes: bring cans | Type: Advertising | Dept: Audio Post\nSType: VO Recording';
const EV = (id, desc) => ({ id, summary: 'TESTING-NOTES ONE / Jem Lim / HL', start: { dateTime: '2027-10-27T18:00:00+08:00' }, end: { dateTime: '2027-10-27T21:00:00+08:00' },
  attendees: [{ resource: true, email: 'f@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio F (12)' }], description: desc });
(async () => {
  console.log('My bookings (the list)');
  const W = { user: 'U1', start: '2027-10-26', end: '2027-11-02', ch: 'D1', ts: '5.5' };
  let r = (await run(si, 'Render My Bookings', [{ json: { items: [EV('e1', NEW), EV('e2', OLD), EV('e3', 'Booked by: Howard Luistro | ref: U1\nSType: VO Recording')] } }], { 'My Window': [{ json: W }], 'Read Cache 4': cache }))[0].json;
  const rows = (r.blocks || []).filter(b => /^bk_/.test(b.block_id || '')).map(b => b.text.text);
  ok(/\n📝 this is a testing for notes$/.test(rows[0]), 'a note -> "📝" and its first line', rows[0]);
  ok(/\n📝 bring cans$/.test(rows[1]), 'an older booking\'s inline note too', rows[1]);
  ok(!/📝/.test(rows[2]), 'no note -> no line', rows[2]);
  console.log('Typed "what do I have" (main)');
  const mc = { go: true, user: 'U1', channel: 'D1', start: '2027-10-26', end: '2027-11-02', week: true, room: '' };
  r = (await run(main, 'Mine Reply', [{ json: { items: [EV('e1', NEW)] } }], { 'Mine Check': [{ json: { mineCheck: mc } }] }))[0].json;
  ok(/\n📝 this is a testing for notes/.test(JSON.stringify(r.blocks).replace(/\\n/g, '\n')), 'the same row');
  console.log('Reminders (the card)');
  const out = (await run(RM, 'Build Reminders', [], { 'Window': [{ json: { kind: 'daily', start: '2027-10-27', end: '2027-10-28' } }], 'List Events R': [{ json: { items: [EV('e1', NEW)] } }], 'Read Cache R': cache })).map(i => i.json);
  const card = ((out[0] || {}).blocks || []).find(b => b.block_id === 'bk_e1');
  ok(card && /\*Room:\* Studio F\n\*Notes:\*\nthis is a testing for notes\n\ntesting spaces$/.test(card.text.text), 'the reminder card ends with *Notes:* and the note (line breaks kept)', card && card.text.text);
  console.log('Booked (the form)');
  const R = { viewId: 'V1', channel: 'D1', calTitle: 'TESTING-NOTES ONE / Jem Lim / HL', rooms: 'Studio F', s: { date: '2027-10-27', t0: '18:00', t1: '21:00', when: 'Wednesday, Oct 27, 2027 · 6:00 PM–9:00 PM', kind: 'studio', purpose: 'VO Recording' } };
  const A = { F: { Date: 'Wednesday, October 27, 2027', Time: '6:00 PM – 9:00 PM', Room: 'Studio F' }, book: { start_iso: '2027-10-27T18:00:00+08:00', end_iso: '2027-10-27T21:00:00+08:00',
    description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1 | Notes: ' + NOTE } };
  r = (await run(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'e9', title: 'TESTING-NOTES ONE / Jem Lim / HL' } }], { 'Read Step 2': [{ json: R }], 'After Prepare': [{ json: A }] }))[0].json;
  ok(/\*Room:\* Studio F\n\*Notes:\*\nthis is a testing for notes\n\ntesting spaces$/.test(r.text) && /\*Notes:\*/.test(JSON.stringify(r.view)), 'the Booked card (DM and form) ends with the note', r.text);
  const bn = await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: Object.assign({}, R, { engineerId: 'U7', arrangerId: '', s: Object.assign({}, R.s, { requester: 'U1' }) }) }], 'After Book': [{ json: r }], 'Read Cache 3': cache });
  ok(bn.length === 1 && /\*Notes:\*\nthis is a testing for notes/.test(JSON.stringify(bn[0].json).replace(/\\n/g, '\n')), 'the engineer\'s notice carries it (the Booked card)');
  console.log('Changed (the form) - the replacement\'s note');
  const RC = { viewId: 'V1', user: 'U1', meta: { ch: 'D1', ts: '5.5' }, b: { id: 'e1', d: '2027-10-27', s: '18:00', e: '21:00', r: 'Studio F', t: 'TESTING-NOTES ONE / Jem Lim / HL' }, n: { d: '2027-10-28', s: '10:00', e: '12:00', r: 'Studio F' } };
  r = (await run(si, 'After Move', [{ json: { status: 'MOVED', event_id: 'e10', description: NEW } }], { 'Read Change': [{ json: RC }], 'To Move': [{ json: { new_summary: '' } }], 'Read Cache 7': cache }))[0].json;
  ok(r.ok && /\*Notes:\*\nthis is a testing for notes\n\ntesting spaces$/.test(r.card), 'the Changed card ends with the note', r.card);
  const rm = mv.nodes.find(n => n.name === 'Return Moved').parameters.jsCode;
  const mo = new Function('$', rm)(n => ({ first: () => ({ json: n === 'Create Replacement' ? { id: 'e10', description: NEW } : { title: 'T', description: OLD } }) }))[0].json;
  ok(mo.description === NEW, 'Move v38 returns the replacement\'s description');
  console.log('Cancel / Move notices');
  const notice = (wf, co, nm) => new Function('$', wf.nodes.find(n => n.name === 'Build Recipients').parameters.jsCode)(n => ({ first: () => ({ json: n === nm ? co : n === 'When Executed by Another Workflow' ? { requester: 'U9', requester_name: 'Camy Caridad', booking_date: '2027-10-27' } : {} }) })).map(i => i.json);
  let ns = notice(cx, { title: 'T / HL', bookerRef: 'U1', bookerName: 'Howard', team: [], start: '2027-10-27T18:00:00+08:00', end: '2027-10-27T21:00:00+08:00', room: 'Studio F', notes_desc: NEW }, 'Check Ownership');
  ok(/\*Room:\* Studio F\n\*Notes:\*\nthis is a testing for notes\n\ntesting spaces$/.test(ns[0].blocks[0].text.text), 'the cancel notice', ns[0].blocks[0].text.text);
  ns = notice(mv, { title: 'T / HL', bookerRef: 'U1', bookerName: 'Howard', team: [], new_start: '2027-10-28T10:00:00+08:00', new_end: '2027-10-28T12:00:00+08:00', location: 'Studio F', description: OLD }, 'Resolve Booking');
  ok(/\*Notes:\* bring cans$/.test(ns[0].blocks[0].text.text), 'the move notice (an older inline note: one line)', ns[0].blocks[0].text.text);
  ns = notice(mv, { title: 'T / HL', bookerRef: 'U1', bookerName: 'Howard', team: [], new_start: '2027-10-28T10:00:00+08:00', new_end: '2027-10-28T12:00:00+08:00', location: 'Studio F', description: 'ref: U1\nSType: VO Recording' }, 'Resolve Booking');
  ok(!/Notes/.test(ns[0].blocks[0].text.text), 'no note -> no Notes line');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
