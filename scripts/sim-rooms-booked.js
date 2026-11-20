#!/usr/bin/env node
// The second 20 Nov round, through the real nodes:
//  PENDING 159 - an event blocks a room only when that room's resource is on it and has not declined (Book Session v132, Room
//    Availability v27, Move v46). No room ("New Event"), a declined room ("Studio F session"), a room only in the location or title
//    -> no block; each room's own free/busy still blocks a room that is really held.
//  PENDING 115 - main v296: a coordinator's typed change that names something finds their department's bookings.
//  PENDING 147 - Room Check v4: a refused "room turned this booking down" DM -> an alert to the ops channel.
//   node scripts/sim-rooms-booked.js
const fs = require('fs');
const L = f => JSON.parse(fs.readFileSync('workflows/' + f + '.json', 'utf8'));
const BS = L('book-session-v132'), BS0 = L('book-session-v131'), RA = L('room-availability-v27'), RA0 = L('room-availability-v26');
const MV = L('move-booking-v46'), MV0 = L('move-booking-v45'), MN = L('project-jessie-v296'), MN0 = L('project-jessie-v295'), RC = L('room-check-v4');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const jsOf = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const RES = { 'Studio 7': 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', 'Studio F': 'c_188em7d58podeju3i8q6juqlufkls@resource.calendar.google.com' };
const Z = s => new Date(Date.parse(s)).toISOString();
const ev = (id, title, room, o) => Object.assign({ id, summary: title, start: { dateTime: '2026-11-24T10:00:00+08:00' }, end: { dateTime: '2026-11-24T12:00:00+08:00' }, status: 'confirmed',
  attendees: room ? [{ email: RES[room], resource: true, responseStatus: (o && o.rs) || 'accepted' }] : [], location: (o && o.loc) || '', description: 'Booked by: X | ref: U9' }, o && o.extra || {});
const NEWEV = ev('ne', 'New Event', null), DECL = ev('dc', 'Studio F session', 'Studio F', { rs: 'declined' }), LOC7 = ev('l7', 'Impromptu', null, { loc: 'KDC Plaza-Top Level-Studio 7 (7)' }),
  TTL7 = ev('t7', 'STUDIO 7 - Party', null), REAL7 = ev('r7', 'ORANGE / HL', 'Studio 7'), PEND7 = ev('p7', 'KIWI / HL', 'Studio 7', { rs: 'needsAction' });
const busyFB = room => ({ calendars: { [RES[room]]: { busy: [{ start: Z('2026-11-24T10:00:00+08:00'), end: Z('2026-11-24T12:00:00+08:00') }] } } });

console.log('Book Session v132 (whole Check Conflicts)');
const refRooms = FX.rooms.map(x => ({ id: x.id, name: x.fields['Room Name'], vocalBooth: !!x.fields['Vocal Booth'], booth: false, common: false }));
const refTypes = FX.sessionTypes.map(s => ({ type: s.fields.Type, priority: [].concat(s.fields.Priority || []).map(id => (FX.rooms.find(x => x.id === id) || { fields: {} }).fields['Room Name']).filter(Boolean), lastResort: [], min: 30, max: 600, requirements: '' }));
const STAFF = [{ Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'] }];
const req = room => ({ mode: '', confirmed: true, summary: 'ORANGE / HL', start_iso: '2026-11-24T10:00:00+08:00', end_iso: '2026-11-24T12:00:00+08:00', rooms: room, all_day: false,
  session_type: 'VO Recording', client: '', engineer: 'Howard Luistro', bookingType: '', department: 'Audio Post', authority: '', expected_date: '2026-11-24',
  requester_text: 'VO Recording in ' + room + ' on 2026-11-24 10:00 am-12:00 pm, project ORANGE, no client, engineer Howard Luistro', staff_data: JSON.stringify(STAFF),
  reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: {} }), description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1', exclude_event_id: '', room_override: true, series: false });
const cc = (w, room, events, fb) => { const outs = { 'When Executed by Another Workflow': [req(room)], 'Get Events In Window': [{ items: events }], 'Room Free Busy': [fb || {}], 'All Bookers': STAFF.map(f => ({ fields: f })), 'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
  return new Function('$', '$input', jsOf(w, 'Check Conflicts'))(n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) }), wrap([{ json: { items: JSON.parse(JSON.stringify(events)) } }]))[0].json; };
const V = r => r.verdict + (r.reason ? ' ' + r.reason : '');
for (const [what, room, evs, fb, want, wantOld] of [
  ['"New Event" (no room), no free/busy read', 'Studio 7', [NEWEV], null, 'CLEAR', 'REJECTED UNVERIFIABLE'],
  ['"Studio F session" - Studio F declined it', 'Studio F', [DECL], null, 'CLEAR', 'REJECTED ROOM_OCCUPIED'],
  ['Studio 7 only in the location text, its calendar free', 'Studio 7', [LOC7], { calendars: { [RES['Studio 7']]: { busy: [] } } }, 'CLEAR', 'REJECTED ROOM_OCCUPIED'],
  ['Studio 7 only in the title ("STUDIO 7 - Party")', 'Studio 7', [TTL7], null, 'CLEAR', 'REJECTED ROOM_OCCUPIED'],
  ['Studio 7 in the location AND busy on its own calendar (Envoy-style)', 'Studio 7', [LOC7], busyFB('Studio 7'), 'REJECTED ROOM_OCCUPIED', 'REJECTED ROOM_OCCUPIED'],
  ['Studio 7 booked (resource accepted)', 'Studio 7', [REAL7], null, 'REJECTED ROOM_OCCUPIED', 'REJECTED ROOM_OCCUPIED'],
  ['Studio 7 booked, the room has not answered yet (needsAction)', 'Studio 7', [PEND7], null, 'REJECTED ROOM_OCCUPIED', 'REJECTED ROOM_OCCUPIED']]) {
  const a = V(cc(BS, room, evs, fb)), b = V(cc(BS0, room, evs, fb));
  ok(a === want && b === wantOld, what + ' -> ' + want + (want !== wantOld ? ' (v131: ' + wantOld + ')' : ''), { v132: a, v131: b });
}

console.log('Room Availability v27');
const REF = JSON.stringify({ rooms: refRooms.map(r => Object.assign({}, r)), types: [] });
const ra = (w, room, events, fb) => new Function('$', '$input', jsOf(w, 'Compute Availability'))(
  n => n === 'Room Free Busy' ? wrap([{ json: fb || {} }]) : wrap([{ json: { start_iso: '2026-11-24T00:00:00+08:00', end_iso: '2026-11-24T23:59:00+08:00', room, session_type: '', scope: '', hours: '', reference_data: REF } }]),
  wrap([{ json: { items: JSON.parse(JSON.stringify(events)) } }]))[0].json;
Date.now = () => Date.parse('2026-11-20T03:00:00Z');
const taken = (r, room) => (r.busy || []).some(b => String(b).replace(/\s*\(.*$/, '') === room);
let r = ra(RA, 'Studio F', [DECL, NEWEV]), r0 = ra(RA0, 'Studio F', [DECL, NEWEV]);
ok(!taken(r, 'Studio F') && taken(r0, 'Studio F'), 'Studio F declined -> free (v26: taken)', { v27: r.busy, v26: r0.busy });
ok(!/no identifiable room|incomplete/.test(r.human || '') && /no identifiable room/.test(r0.human || ''), '"New Event" -> no "treat this as incomplete" note (v26 had it)');
r = ra(RA, 'Studio 7', [LOC7, TTL7]);
ok(!taken(r, 'Studio 7'), 'Studio 7 only in the location / title -> free', r.busy);
r = ra(RA, 'Studio 7', [LOC7], busyFB('Studio 7'));
ok(taken(r, 'Studio 7'), 'Studio 7 busy on its own calendar -> taken (free/busy)', r.busy);
r = ra(RA, 'Studio 7', [REAL7]);
ok(taken(r, 'Studio 7'), 'Studio 7 booked -> taken', r.busy);

console.log('Move v46 (Check New Window)');
const R = { attendees: [{ email: RES['Studio 7'], resource: true }], location: 'KDC Plaza-Top Level-Studio 7 (7)', new_start: '2026-11-24T10:00:00+08:00', new_end: '2026-11-24T12:00:00+08:00', original_id: 'orig' };
const mv = (w, items) => new Function('$', '$input', jsOf(w, 'Check New Window'))(n => wrap([{ json: R }]), wrap([{ json: { items: JSON.parse(JSON.stringify(items)) } }]))[0].json;
const clash = j => j.verdict === 'REJECTED' && j.reason === 'ROOM_OCCUPIED';
ok(!clash(mv(MV, [Object.assign({}, DECL, { attendees: [{ email: RES['Studio 7'], resource: true, responseStatus: 'declined' }] })])), 'moving into Studio 7 where Studio 7 declined an event -> no clash');
ok(!clash(mv(MV, [LOC7])) && clash(mv(MV0, [LOC7])), 'Studio 7 only in the location -> no clash (v45: clash)');
ok(clash(mv(MV, [REAL7])), 'Studio 7 booked -> clash, as before', mv(MV, [REAL7]).verdict);
ok(/const noRoom = false;/.test(jsOf(MV, 'Check New Window')), 'an event with no room no longer blocks the times it offers');

console.log('main v296 (Change Reply) - PENDING 115');
const evB = (id, title, ref, dept) => ({ id, summary: title, start: { dateTime: '2026-11-24T14:00:00+08:00' }, end: { dateTime: '2026-11-24T16:00:00+08:00' }, status: 'confirmed',
  description: 'Booked by: Someone | ref: ' + ref + ' | Dept: ' + dept, attendees: [{ resource: true, email: RES['Studio 7'], displayName: 'KDC Plaza-Top Level-Studio 7 (7)' }] });
const CAL = { items: [evB('m1', 'ORANGE / AB', 'UOTHER1', 'Music'), evB('a1', 'ORANGE / XY', 'UOTHER2', 'Audio Post'), evB('o1', 'MINE / CP', 'UCOORD', 'Music')] };
const reply = async (w, co, booker) => (await new Function('$', '$input', 'return (async function(){' + jsOf(w, 'Change Reply') + '\n})();')(
  n => ({ first: () => n === 'Change Offer' ? { json: { changeOffer: co } } : n === 'Get Booker' ? { json: { fields: booker } } : { json: {} }, all: () => [] }), wrap([{ json: CAL }])))[0].json;
const COORD = { Name: 'Coord Person', Department: ['Music'], Authority: ['Standard', 'Client Booking'], Email: 'coord@example.com' };
const PLAIN = Object.assign({}, COORD, { Authority: ['Standard'] }), DEV = Object.assign({}, COORD, { Authority: ['HAIST Dev'], Department: ['Audio Post'] });
const co = (o) => Object.assign({ kind: 'change', user: 'UCOORD', channel: 'D1', words: ['orange'], fDates: [], fRooms: [], n: { s: '15:00' }, today: '2026-11-20' }, o);
const ids = x => x.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id.slice(3)).join();
(async () => {
  let x = await reply(MN, co(), COORD);
  ok(ids(x) === 'm1', 'a Music coordinator: "move the orange booking" -> the Music department\'s ORANGE (not Audio Post\'s)', ids(x));
  ok(ids(await reply(MN0, co(), COORD)) === '', '  (v295: nothing found)');
  ok(ids(await reply(MN, co(), PLAIN)) === '', 'not a coordinator -> only their own bookings, as before');
  ok(ids(await reply(MN, co({ words: [], n: { s: '15:00' } }), COORD)) === 'o1', 'a coordinator\'s "change my booking" (nothing named) -> only their own');
  ok(ids(await reply(MN, co(), DEV)) === 'a1,m1' || ids(await reply(MN, co(), DEV)) === 'm1,a1', 'HAIST Dev -> every department', ids(await reply(MN, co(), DEV)));
  x = await reply(MN, co({ kind: 'cancel' }), COORD);
  ok(x.count === 0 && /open \*My bookings\*/.test(x.blocks[0].text.text), 'a typed cancel still answers "open My bookings" - no card');

  console.log('Room Check v4 - PENDING 147');
  const df = jsOf(RC, 'DM Failed?');
  const run = res => new Function('$', '$input', df)(n => ({ first: () => ({ json: n === 'Build DM' ? { channel: 'UBOOKER1', text: 'M4 turned down M4 - Ate Weng - nothing is booked.', removed: true } : { title: 'M4 - Ate Weng' } }) }), wrap([{ json: res }]));
  let o = run({ ok: false, error: 'channel_not_found' });
  ok(o.length === 1 && /could not be sent/.test(o[0].json.text) && /channel_not_found/.test(o[0].json.text) && /<@UBOOKER1>/.test(o[0].json.text) && /removed from the calendar/.test(o[0].json.text) && /^U[A-Z0-9]+$/.test(o[0].json.channel),
    'Slack refused the DM -> an alert to the ops channel: who, what, Slack\'s error', o[0] && o[0].json.text);
  ok(run({ ok: true }).length === 0, 'the DM went out -> no alert');
  const C = RC.connections;
  ok(C['Send DM'].main[0].map(t => t.node).sort().join() === 'DM Failed?,Declined Row' && C['DM Failed?'].main[0][0].node === 'Send Alert'
    && RC.nodes.find(n => n.name === 'Send Alert').onError === 'continueRegularOutput', 'wiring: Send DM -> Declined Row and DM Failed? -> Send Alert (continues on error)');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
