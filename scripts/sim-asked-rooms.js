#!/usr/bin/env node
// main v287 (Howard, 28 Oct 1:40 PM): "is studio f and c free tomorrow?" was answered for Studio C only - the AI passed one
// room to Room Availability. Booked For now reads the rooms named in the message (two or more) and the tool's room input
// uses them; Room Availability (unchanged) answers each one. Checks: what is read from a message, that nothing else Booked
// For returns changes (v286 vs v287 on the same messages), the tool input, the answer Room Availability writes, and that
// only those two nodes changed.
//   node scripts/sim-asked-rooms.js [main v287] [main v286] [room-availability]
const fs = require('fs'), path = require('path');
const W = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const NEW = W(process.argv[2] || 'workflows/project-jessie-v287.json');
const OLD = W(process.argv[3] || 'workflows/imported/project-jessie-v286-imported.json');
const RA = W(process.argv[4] || 'workflows/imported/room-availability-v24-imported.json');
const node = (w, n) => w.nodes.find(x => x.name === n);
if (!/askedRooms/.test(JSON.stringify(node(NEW, 'Booked For') || {}))) { console.log('0 ok, 0 failed (an older build: v287 not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });

// Rooms & Studios as in Airtable (read 28 Oct)
const ROOMS = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 4', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio A', 'Studio B', 'Studio C',
  'Studio D', 'Studio E', 'Studio F', 'Studio M', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'Salin', 'Likha', 'Katha', 'Lobby'];
const BOOTH = ['Studio A', 'Studio B', 'Studio D'], COMMON = ['Salin', 'Likha', 'Katha', 'Lobby'];
const bookers = [{ Name: 'Howard Luistro', 'Slack User ID': 'U1', Info: 'Post Engineer', Initials: 'HL' }, { Name: 'Daryl Reyes', 'Slack User ID': 'U2', Info: 'Post Engineer. Goes by Drey', Initials: 'DR' }];
const outs = text => {
  const trig = { text, user: 'U1', ts: '1793000000.1' };
  return { 'Slack Trigger': [{ json: trig }], 'Get Recent Messages': [{ json: trig }], 'Gate Context': [{ json: { epoch: 0, gate: {}, datesInMessage: '2027-10-29' } }],
    'Get Booker': [{ json: { fields: bookers[0] } }], 'All Bookers': bookers.map(f => ({ json: { fields: f } })),
    'All Session Types': ['VO Recording', 'Localization Dubbing', 'Atmos Mixing'].map(t => ({ json: { fields: { Type: t } } })),
    'All Rooms': ROOMS.map(n => ({ json: { fields: { 'Room Name': n } } })) };
};
const bookedFor = (w, text) => { const O = outs(text); return new Function('$', '$input', node(w, 'Booked For').parameters.jsCode)(n => wrap(O[n] || []), wrap([{ json: {} }]))[0].json; };

console.log('Rooms read from the message (two or more, in the order typed)');
const CASES = [
  ['is studio f and c free tomorrow?', 'Studio F, Studio C'],
  ['are studios 7, 8 and c free on friday', 'Studio 7, Studio 8, Studio C'],
  ['is studio 7 or studio 8 open tomorrow', 'Studio 7, Studio 8'],
  ['studio 7 & 8 tomorrow 2-4pm?', 'Studio 7, Studio 8'],
  ['is m3 or m4 free tomorrow', 'M3, M4'],
  ['are m3 and 5 free tomorrow?', 'M3, M5'],
  ['is booth b and d free tomorrow', 'Studio B, Studio D'],
  ['is likha or katha free tomorrow at 3?', 'Likha, Katha'],
  ['is studio 7 free tomorrow, if not studio 8', 'Studio 7, Studio 8'],
  ['Studio F and Studio A tomorrow?', 'Studio F, Studio A'],
  ['studio 7 and A free tomorrow?', 'Studio 7, Studio A'],
];
for (const [q, want] of CASES) { const r = bookedFor(NEW, q); ok(r.askedRooms === want, JSON.stringify(q) + ' -> ' + want, r.askedRooms); }
console.log('One room or none -> empty (the AI\'s room, as before)');
const NONE = ['is studio 7 free tomorrow', 'is studio c free tomorrow?', 'what rooms are free tomorrow?', 'thanks!', 'book studio 8 friday 2-4pm',
  'is studio 7 and a vocal booth free tomorrow?',   // "a" is a word here
  'is studio 7 free from 3 and 4pm?', 'is studio 8 free at 2 or 3pm', 'is studio 5 free 3 or 4 hours tomorrow',   // numbers that are times
  "i'm 3 minutes away, is studio 7 free?", 'is m6 free tomorrow', 'is the studio free and do you have a mac?', 'studio 7 at 3 and 5pm'];
for (const q of NONE) { const r = bookedFor(NEW, q); ok(r.askedRooms === '', JSON.stringify(q) + ' -> none', r.askedRooms); }

console.log('Nothing else Booked For returns changes (v286 vs v287, same messages)');
const MSGS = CASES.map(c => c[0]).concat(NONE, ['book studio 7 for Drey tomorrow 2-4pm for Netflix', 'VO recording in studio 3 friday 1-3pm for Spotify, engineer HL',
  'are studios free tomorrow', 'is any room free tomorrow afternoon?']);
for (const q of MSGS) {
  const a = bookedFor(OLD, q), b = Object.assign({}, bookedFor(NEW, q)); delete b.askedRooms;
  ok(JSON.stringify(a) === JSON.stringify(b), 'unchanged: ' + JSON.stringify(q), { v286: a, v287: b });
}
{ const O = outs('is studio f and c free'); delete O['All Rooms'];
  const r = new Function('$', '$input', node(NEW, 'Booked For').parameters.jsCode)(n => { if (!O[n]) throw new Error(n + ' not executed'); return wrap(O[n]); }, wrap([{ json: {} }]))[0].json;
  ok(r.askedRooms === '' && r.roomScope === 'studios', 'All Rooms unreadable -> no rooms, the rest still answered', r); }

console.log('The tool input');
const T = node(NEW, 'Room Availability').parameters.workflowInputs.value, T0 = node(OLD, 'Room Availability').parameters.workflowInputs.value;
const roomOf = (expr, asked, ai) => new Function('$', '$fromAI', 'return (' + expr.replace(/^=\{\{/, '').replace(/\}\}$/, '') + ');')(
  n => wrap([{ json: n === 'Booked For' ? { askedRooms: asked } : {} }]), () => ai);
ok(roomOf(T.room, 'Studio F, Studio C', 'Studio C') === 'Studio F, Studio C', 'rooms typed -> those rooms, whatever the AI passes');
ok(roomOf(T.room, '', 'Studio C') === 'Studio C' && roomOf(T.room, '', '') === '', 'no rooms typed -> the AI\'s room, as before');
ok(roomOf(T.room, undefined, 'Studio 7') === 'Studio 7', 'an older Booked For answer (no field) -> the AI\'s room');
ok(/\$fromAI\('window_room', 'The room the requester named, when they named one - e\.g\. "Studio 3"\. Empty when they are asking what is free generally\.', 'string', ''\)/.test(T.room),
  'the AI\'s own input is unchanged (same schema)');
ok(Object.keys(T).every(k => k === 'room' || T[k] === T0[k]) && Object.keys(T).length === Object.keys(T0).length, 'every other input unchanged');

console.log('Room Availability (unchanged) answers both rooms - the 1:40 PM question on the 29 Oct calendar');
const REF = JSON.stringify({ rooms: ROOMS.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: BOOTH.includes(n), common: COMMON.includes(n) })), types: [] });
const ev = (title, s, e, rooms) => ({ id: title, summary: title, location: rooms.join(', '), start: s.length === 10 ? { date: s } : { dateTime: s }, end: e.length === 10 ? { date: e } : { dateTime: e } });
const CAL = [ev('NET-TSTING / JT', '2027-10-29T14:00:00+08:00', '2027-10-29T18:00:00+08:00', ['Studio A', 'Studio 3']),
  ev('M1 - Rico', '2027-10-29T00:00:00+08:00', '2027-10-30T00:00:00+08:00', ['M1']), ev('M2 - Dilan', '2027-10-29T00:00:00+08:00', '2027-10-30T00:00:00+08:00', ['M2']),
  ev('M6 - Marketing', '2027-10-29T00:00:00+08:00', '2027-10-30T00:00:00+08:00', ['M6'])];
Date.now = () => Date.parse('2026-10-28T05:40:00Z');
const ra = (room, cal = CAL, win = ['2027-10-29T00:00:00+08:00', '2027-10-29T23:59:00+08:00']) => new Function('$', '$input', node(RA, 'Compute Availability').parameters.jsCode)(
  n => wrap([{ json: { start_iso: win[0], end_iso: win[1], room, session_type: '', scope: 'studios', hours: '', reference_data: REF } }]), wrap([{ json: { items: cal } }]))[0].json;
let r = ra('Studio F, Studio C');
const t = String(r.reply_text || '');
ok(/^🗓️ October 29 \(Friday\)\n\n✅ Studio F is free all day\.\n✅ Studio C is free all day\.\n\n✅ Free all day:\nStudios 1, 2, 4, 5, 6, 7, 8, E, and M\./.test(t),
  'both rooms on top, neither repeated in the rest', t);
ok(/⚠️ Studio 3: booked 2:00 PM – 6:00 PM, free the rest of the day\.\n⚠️ Studio A: booked 2:00 PM – 6:00 PM, free the rest of the day\.$/.test(t), 'the rest of the day as before', t);
r = ra('Studio F, Studio C', CAL.concat([ev('FULL / HL', '2027-10-29', '2027-10-30', ['Studio F'])]));
ok(/❌ Studio F is booked all day \(FULL \/ HL\)\.\n✅ Studio C is free all day\./.test(r.reply_text || ''), 'the case that mattered: F booked all day is now said, not left out', r.reply_text);
r = ra('Studio C');
ok(/^🗓️ October 29 \(Friday\)\n\n✅ Studio C is free all day\.\n\n✅ Free all day:\nStudios 1, 2, 4, 5, 6, 7, 8, E, F, and M\./.test(r.reply_text || ''), 'one room: exactly the 1:40 PM layout (unchanged)', r.reply_text);
r = ra('Studio 7, Studio 8', CAL, ['2027-10-29T14:00:00+08:00', '2027-10-29T16:00:00+08:00']);
ok(/✅ Studio 7 is free 2:00 PM – 4:00 PM\.\n✅ Studio 8 is free 2:00 PM – 4:00 PM\./.test(r.reply_text || ''), 'at a time: each room\'s line', r.reply_text);

console.log('Only Booked For and the Room Availability tool changed');
const A = Object.fromEntries(OLD.nodes.map(n => [n.name, n])), B = Object.fromEntries(NEW.nodes.map(n => [n.name, n]));
const changed = Object.keys(B).filter(k => !A[k] || JSON.stringify(A[k].parameters) !== JSON.stringify(B[k].parameters));
ok(JSON.stringify(changed.sort()) === JSON.stringify(['Booked For', 'Room Availability']), 'changed nodes: Booked For, Room Availability', changed);
ok(Object.keys(A).every(k => B[k]) && NEW.nodes.length === OLD.nodes.length, 'no node added or removed');
ok(JSON.stringify(NEW.connections) === JSON.stringify(OLD.connections), 'wiring unchanged');
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
