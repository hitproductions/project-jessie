#!/usr/bin/env node
// PENDING 151 (Howard, 4 Nov: "go ahead with the colors, peacock and grape are fine"): every booking Jessie creates gets a calendar
// colour - Book Session v127 (Check Conflicts' final_color -> Create Event's colour) and Move Booking v43 (the replacement event
// on a change keeps a hand-set colour, otherwise the rule for the booking as changed). Runs the real Check Conflicts and Resolve Booking.
//   node scripts/sim-colours.js [book-session v127] [move-booking v43]
const fs = require('fs');
const load = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const BS = load(process.argv[2], 'workflows/book-session-v127.json'), MV = load(process.argv[3], 'workflows/move-booking-v43.json');
if (!/PENDING 151/.test(JSON.stringify(BS.nodes))) { console.log('0 ok, 0 failed (an older build: v127 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const NAME = { 1: 'Lavender', 2: 'Sage', 3: 'Grape', 4: 'Flamingo', 5: 'Banana', 6: 'Tangerine', 7: 'Peacock', 8: 'Graphite', 9: 'Blueberry', 10: 'Basil', 11: 'Tomato' };

console.log('The rule');
const CC = node(BS, 'Check Conflicts').parameters.jsCode;
const jc = new Function(CC.slice(0, CC.indexOf('\n}\n', CC.indexOf('function __jColour')) + 3) + '\nreturn __jColour;')();
for (const [t, d, r, want, why] of [
  ['Localization Dubbing', 'Localization', 'Studio 1, Studio A', 7, 'Localization'], ['QC', 'Localization', 'Studio 5', 7, 'Localization QC'],
  ['VO Recording', 'Audio Post', 'Studio 7', 9, 'Audio Post'], ['Music Recording', 'Music', 'Studio F', 3, 'Music'], ['Music Mixing', 'Music', 'Studio C', 3, 'Music'],
  ['', '', 'M4', 10, 'an M booth (no type)'], ['__booth', 'Marketing', 'M6', 10, 'an M booth'], ['Celebrity Recording', 'Audio Post', 'Studio F', 11, 'a celebrity booking'],
  ['Meeting', 'Marketing', 'Likha', 5, 'a meeting'], ['Event', 'IT', 'Lobby', 6, 'an event'], ['Van Recording', 'Audio Post', 'Studio M', 4, 'Van Recording'],
  ['Post Processing', 'Video Post', 'Studio E', 1, 'Post Processing'], ['Atmos Mixing', 'Localization, Music', 'Studio C', 2, 'several departments'],
  ['VO Recording', '', 'Studio 7', 8, 'no department'], ['VO Recording', 'Advertising', 'Studio 7', 8, 'another department'], ['Band Recording', 'Post Production', 'Studio F', 9, '"Post Production" = Audio Post']])
  ok(jc(t, d, r.split(',')) === String(want), why + ' -> ' + NAME[want], jc(t, d, r.split(',')));

console.log('Book Session v127 - the colour on the event');
const STAFF = FX.bookers.map(b => b.fields);
const refRooms = FX.rooms.map(r => ({ id: r.id, name: r.fields['Room Name'], vocalBooth: r.fields['Vocal Booth'] === true, booth: r.fields['Vocal Booth'] === true || [].concat(r.fields['Room Type'] || []).indexOf('Recording Booth') !== -1,
  common: /Salin|Katha|Likha|Lobby/.test(r.fields['Room Name']) }));
const refTypes = FX.sessionTypes.map(t => ({ type: t.fields.Type, priority: [].concat(t.fields.Priority || []), last: [].concat(t.fields['Last Resort'] || []) }));
const cc = REQ => { const outs = { 'When Executed by Another Workflow': [Object.assign({ staff_data: JSON.stringify(STAFF) }, REQ)], 'Get Events In Window': [{ items: [] }], 'All Bookers': STAFF.map(f => ({ fields: f })),
    'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
  const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
  return new Function('$', '$input', CC)($, { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json; };
const REQ = (st, rooms, dept, summary) => ({ confirmed: true, mode: 'book', session_type: st, rooms, summary: summary || 'NET-KUBA / HL', start_iso: '2026-11-12T13:00:00+08:00', end_iso: '2026-11-12T15:00:00+08:00',
  booker_name: 'Howard Luistro', booker_id: 'U1', engineer: 'Howard Luistro', department: dept, room_override: true, reference_data: JSON.stringify({ rooms: refRooms, types: refTypes }) });
let c = cc(REQ('Localization Dubbing', 'Studio 1, Studio A', 'Localization'));
ok(c.verdict === 'CLEAR' && c.final_color === '7', 'Localization Dubbing in Studio 1 + A -> CLEAR, final_color 7 (Peacock)', { v: c.verdict, r: c.reason, h: c.human, col: c.final_color });
c = cc(REQ('VO Recording', 'Studio 7', 'Audio Post', 'ORANGE / HL'));
ok(c.verdict === 'CLEAR' && c.final_color === '9', 'VO Recording, Audio Post -> 9 (Blueberry)', { v: c.verdict, r: c.reason, col: c.final_color });
const CE = node(BS, 'Create Event').parameters.additionalFields;
ok(CE.color === "={{ $('Check Conflicts').first().json.final_color || '8' }}", 'Create Event sets colour (n8n sends it to Google as colorId)');

console.log('Move Booking v43 - the replacement event');
const run = (wf, name, input, outs) => new Function('$', '$input', node(wf, name).parameters.jsCode)(n => ({ first: () => ({ json: (outs[n] || [{}])[0].json }), all: () => outs[n] || [] }),
  { first: () => input[0], all: () => input });
const DESC = 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | Dept: Localization\nSType: Localization Dubbing';
const ev = (desc, colorId) => Object.assign({ id: 'e1', summary: 'NET-KUBA / HL', location: 'KDC Plaza-Top Level-Studio 1 (5)', start: { dateTime: '2026-11-12T13:00:00+08:00' }, end: { dateTime: '2026-11-12T15:00:00+08:00' },
  description: desc, attendees: [] }, colorId ? { colorId } : {});
const resolve = (e, nd) => run(MV, 'Resolve Booking', [{ json: { items: [e] } }], { 'When Executed by Another Workflow': [{ json: { event_id: 'e1', booking_date: '2026-11-12', title: 'NET-KUBA / HL',
  new_start_iso: '2026-11-12T16:00:00+08:00', new_end_iso: '2026-11-12T18:00:00+08:00', confirmed: true, requester: 'U1', authority: 'Standard', department: 'Localization',
  new_summary: 'NET-KUBA / HL', new_details: nd ? JSON.stringify(nd) : '' } }] })[0].json;
let rb = resolve(ev(DESC));
ok(rb.verdict === 'CLEAR' && rb.color_id === '7', 'a Jessie booking with no colour yet (made before v127) -> Peacock on its change', { v: rb.verdict, c: rb.color_id, h: rb.human });
rb = resolve(ev(DESC, '7'), { SType: 'Meeting' });
ok(rb.color_id === '5', 'Jessie\'s colour + the type changed to Meeting -> Banana', rb.color_id);
rb = resolve(ev(DESC, '4'));
ok(rb.color_id === '4', 'a colour set by hand (Flamingo on a Localization booking) -> kept', rb.color_id);
rb = resolve(ev('Booked by: Howard Luistro | ref: U1', '11'));   // made by hand (no Dept / SType), the requester's own
ok(rb.verdict === 'CLEAR' && rb.color_id === '11', 'a hand-made booking with its own colour -> kept', { v: rb.verdict, c: rb.color_id, h: rb.human });
rb = resolve(ev('Booked by: Howard Luistro | ref: U1'));
ok(rb.verdict === 'CLEAR' && rb.color_id === '', 'a hand-made booking with no colour -> still none after its change (not recoloured)', { v: rb.verdict, c: rb.color_id });
const body = node(MV, 'Create Replacement').parameters.jsonBody;
const sent = JSON.parse(new Function('$', '$json', 'return (' + body.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => ({ first: () => ({ json: { color_id: '5' } }) }),
  { title: 'T', description: 'D', location: 'L', attendees: [], new_start: 'S', new_end: 'E' }));
ok(sent.colorId === '5' && sent.summary === 'T', 'Create Replacement sends the colour as colorId', sent);
const sent0 = JSON.parse(new Function('$', '$json', 'return (' + body.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => ({ first: () => ({ json: {} }) }),
  { title: 'T', description: 'D', location: 'L', attendees: [], new_start: 'S', new_end: 'E' }));
ok(!('colorId' in sent0), 'no colour worked out -> none sent (Google keeps its default)', sent0);
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
