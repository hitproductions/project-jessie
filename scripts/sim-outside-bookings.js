#!/usr/bin/env node
// PENDING 148 (3 Nov): a room booked outside KDC Bookings (from someone's own calendar, the room invited) is taken - Room
// Availability v25 and Book Session v125 read every room's free/busy ("Room Free Busy") and count busy time no KDC booking for
// that room covers as "Booked outside KDC Bookings". Covered time is never counted twice, a change's own booking (exclude_event_id)
// never blocks itself, and a failed free/busy read gives exactly the v24 / v124 answer. Runs the real Compute Availability and
// the whole Check Conflicts.
// Usage: node scripts/sim-outside-bookings.js [room-availability v25] [book-session v125] [ra v24] [book-session v124]
const fs = require('fs');
const load = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const RA = load(process.argv[2], 'workflows/room-availability-v25.json'), BS = load(process.argv[3], 'workflows/book-session-v125.json');
const RA0 = load(process.argv[4], 'workflows/imported/room-availability-v24-imported.json'), BS0 = load(process.argv[5], 'workflows/imported/book-session-v124-imported.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const RES = { 'Studio 7': 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', 'Studio 8': 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com',
  'Studio B': 'c_1881vgb66tkpujjelnn3rniugd9pk@resource.calendar.google.com', M3: 'c_188d7dkqgnfs6hu4iunlu5ogftct0@resource.calendar.google.com',
  M4: 'c_18869nhmsj2uki8mljoi48v1cj7l4@resource.calendar.google.com' };
const Z = s => new Date(Date.parse(s)).toISOString();   // free/busy answers in UTC

console.log('Wiring');
for (const [w, into] of [[RA, ['When Executed by Another Workflow']], [BS, ['Cached?', 'Client Unmatched?', 'All Client Names']]]) {
  const fb = node(w, 'Room Free Busy');
  ok(fb && fb.parameters.method === 'POST' && /freeBusy$/.test(fb.parameters.url) && fb.onError === 'continueRegularOutput' && fb.executeOnce && fb.parameters.options.timeout === 10000,
    w.name + ': Room Free Busy - POST freeBusy, carries on after an error, 10 s timeout');
  const ins = Object.keys(w.connections).filter(k => k !== 'Room Free Busy' && JSON.stringify(w.connections[k]).includes('"Room Free Busy"')).sort();
  ok(JSON.stringify(ins) === JSON.stringify(into.slice().sort()) && JSON.stringify(w.connections['Room Free Busy']) === JSON.stringify({ main: [[{ node: 'Get Events In Window', type: 'main', index: 0 }]] }),
    w.name + ': in front of Get Events In Window (' + ins.join(', ') + ')');
  const body = JSON.parse(new Function('$', 'return (' + fb.parameters.jsonBody.slice(3, -2) + ');')(n => ({ first: () => ({ json: { start_iso: '2026-11-10T14:00:00+08:00', end_iso: '2026-11-10T16:00:00+08:00' } }) })));
  ok(body.timeMin === '2026-11-10T14:00:00+08:00' && body.timeMax === '2026-11-10T16:00:00+08:00' && body.items.length === 27, w.name + ': the same window as the events query, all 27 rooms');
}

console.log('Room Availability');
const NAMES = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 4', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio A', 'Studio B', 'Studio C', 'Studio D', 'Studio E', 'Studio F', 'Studio M',
  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'Salin', 'Katha', 'Likha', 'Lobby'];
const REF = JSON.stringify({ rooms: NAMES.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: false, common: /Salin|Katha|Likha|Lobby/.test(n) })), types: [] });
const ev = (id, title, s, e, rooms, att) => ({ id, summary: title, location: rooms.join(', '), start: s.length === 10 ? { date: s } : { dateTime: s }, end: e.length === 10 ? { date: e } : { dateTime: e },
  attendees: (att || []).map(r => ({ email: RES[r], resource: true, responseStatus: 'accepted' })), description: 'Booked by: X | ref: U9' });
const CAL = [ev('trish', 'M3 - Trish', '2026-10-30', '2026-10-31', ['M3'], ['M3']), ev('bonj', 'NET-BONJOUR6', '2026-10-30T09:00:00+08:00', '2026-10-30T21:00:00+08:00', ['Studio B', 'Studio 2']),
  ev('s8a', 'ORANGE / HL', '2026-10-30T10:00:00+08:00', '2026-10-30T12:00:00+08:00', ['Studio 8'], ['Studio 8'])];
const FB = { calendars: {
  [RES.M4]: { busy: [{ start: Z('2026-10-30T00:00:00+08:00'), end: Z('2026-10-31T00:00:00+08:00') }] },   // Tel's own-calendar hold
  [RES.M3]: { busy: [{ start: Z('2026-10-30T00:00:00+08:00'), end: Z('2026-10-31T00:00:00+08:00') }] },   // = the KDC booking
  [RES['Studio B']]: { busy: [{ start: Z('2026-10-30T09:00:00+08:00'), end: Z('2026-10-30T21:00:00+08:00') }] },   // = KDC (by location)
  [RES['Studio 8']]: { busy: [{ start: Z('2026-10-30T10:00:00+08:00'), end: Z('2026-10-30T14:00:00+08:00') }] },   // KDC 10-12 + outside 12-14, merged
  [RES['Studio 7']]: { busy: [{ start: Z('2026-10-30T14:00:00+08:00'), end: Z('2026-10-30T16:00:00+08:00') }] } } };
Date.now = () => Date.parse('2026-10-29T10:00:00Z');
const ra = (w, room, fb, win) => new Function('$', '$input', node(w, 'Compute Availability').parameters.jsCode)(
  n => n === 'Room Free Busy' ? wrap([{ json: fb || {} }]) : wrap([{ json: { start_iso: (win || [])[0] || '2026-10-30T00:00:00+08:00', end_iso: (win || [])[1] || '2026-10-30T23:59:00+08:00', room, session_type: '', scope: '', hours: '', reference_data: REF } }]),
  wrap([{ json: { items: JSON.parse(JSON.stringify(CAL)) } }]))[0].json;
let r = ra(RA, 'M4', FB);
const det = k => ((r.busy_detail || []).find(d => d.room === k) || { events: [] }).events;
ok((r.busy || []).includes('M4 (Booked outside KDC Bookings)'), 'M4 booked from a personal calendar -> taken ("Booked outside KDC Bookings")', r.busy);
ok(/M4/.test(r.reply_text || r.human || '') && !/M4 is free/.test(r.reply_text || r.human || ''), 'and the answer about M4 does not say it is free', r.reply_text || r.human);
ok(det('M4').length === 1 && !det('M4')[0].ref && !det('M4')[0].bookedBy, 'no owner on it, so the form never offers it for a request', det('M4'));
ok(det('M3').length === 1 && det('M3')[0].title === 'M3 - Trish', 'M3: the KDC booking only - not counted twice', det('M3'));
ok(det('Studio B').length === 1, 'Studio B (a KDC booking matched by location) - not counted twice', det('Studio B'));
ok(det('Studio 8').map(e => e.title + ' ' + e.start.slice(11, 16) + '-' + e.end.slice(11, 16)).join() === 'ORANGE / HL 10:00-12:00,Booked outside KDC Bookings 12:00-14:00',
  'Studio 8: free/busy merged 10-2; only the uncovered 12-2 is added', det('Studio 8'));
ok(det('Studio 7').length === 1 && det('Studio 7')[0].start === '2026-10-30T14:00:00+08:00', 'Studio 7: 2-4 PM outside -> taken then', det('Studio 7'));
r = ra(RA, 'Studio 7', FB, ['2026-10-30T09:00:00+08:00', '2026-10-30T11:00:00+08:00']);
ok(!(r.busy || []).some(b => /^Studio 7/.test(b)), 'Studio 7 in the morning (outside the 2-4 PM) -> still free', r.busy);
// a failed read = the v24 answer exactly
const strip = o => JSON.stringify(o);
for (const fb of [{}, { error: { message: 'Forbidden' } }, { calendars: { [RES.M4]: { errors: [{ reason: 'notFound' }] } } }]) {
  ok(strip(ra(RA, 'M4', fb)) === strip(ra(RA0, 'M4', fb)), 'free/busy ' + JSON.stringify(fb).slice(0, 60) + ' -> exactly v24\'s answer');
}
ok(strip(ra(RA, 'Studio C', { calendars: { [RES.M3]: FB.calendars[RES.M3] } })) === strip(ra(RA0, 'Studio C', {})), 'busy time only where KDC already has it -> exactly v24\'s answer');

console.log('Book Session - the whole Check Conflicts');
const FX = require('./sim-fixture-rooms.js');
const STAFF = [{ Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.', Department: ['Audio Post'] }];
const refRooms = FX.rooms.map(x => ({ id: x.id, name: x.fields['Room Name'], vocalBooth: !!x.fields['Vocal Booth'], booth: false, common: /conference|lobby/i.test(String(x.fields['Room Type'] || '')) }));
const refTypes = FX.sessionTypes.map(s => ({ type: s.fields.Type, priority: [].concat(s.fields.Priority || []).map(id => (FX.rooms.find(x => x.id === id) || { fields: {} }).fields['Room Name']).filter(Boolean), lastResort: [], min: 60, max: 480, requirements: s.fields['Room Requirements'] || '' }));
const base = { mode: '', confirmed: true, summary: 'ORANGE / HL', start_iso: '2026-11-10T14:00:00+08:00', end_iso: '2026-11-10T16:00:00+08:00', rooms: 'Studio 7', all_day: false,
  session_type: 'VO Recording', client: '', engineer: 'Howard Luistro', bookingType: '', department: 'Audio Post', authority: '', expected_date: '2026-11-10',
  requester_text: 'VO Recording in Studio 7 on 2026-11-10 2:00 pm-4:00 pm, project ORANGE, no client, engineer Howard Luistro', staff_data: JSON.stringify(STAFF),
  reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: {} }), description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1', exclude_event_id: '', room_override: false, series: false };
const cc = (w, req, events, fb) => { const outs = { 'When Executed by Another Workflow': [req], 'Get Events In Window': [{ items: events }], 'Room Free Busy': [fb || {}], 'All Bookers': STAFF.map(f => ({ fields: f })),
    'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
  const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
  return new Function('$', '$input', node(w, 'Check Conflicts').parameters.jsCode)($, wrap([{ json: { items: JSON.parse(JSON.stringify(events)) } }]))[0].json; };
const fb7 = { calendars: { [RES['Studio 7']]: { busy: [{ start: Z('2026-11-10T14:00:00+08:00'), end: Z('2026-11-10T16:00:00+08:00') }] } } };
let b = cc(BS, base, [], fb7);
ok(b.verdict === 'REJECTED' && b.reason === 'ROOM_OCCUPIED' && (b.conflicts || []).some(c => /outside KDC/.test(c.summary || '')), 'Studio 7 booked from a personal calendar -> refused (ROOM_OCCUPIED), nothing booked', b);
b = cc(BS, base, [], {});
ok(b.verdict === 'CLEAR' && strip(b) === strip(cc(BS0, base, [], {})), 'free/busy empty -> CLEAR, exactly v124\'s answer', b.verdict);
b = cc(BS, base, [], { error: { message: 'timeout' } });
ok(b.verdict === 'CLEAR', 'free/busy failed -> as before (CLEAR on an empty calendar)', b.verdict);
const own = ev('own1', 'ORANGE / HL', '2026-11-10T14:00:00+08:00', '2026-11-10T16:00:00+08:00', ['Studio 7'], ['Studio 7']);
b = cc(BS, Object.assign({}, base, { exclude_event_id: 'own1' }), [own], fb7);
ok(b.verdict === 'CLEAR', 'a change of my own booking: its busy time is that KDC booking, excluded - not blocked by itself', b);
const other = ev('oth1', 'BLUE / RG', '2026-11-10T14:00:00+08:00', '2026-11-10T16:00:00+08:00', ['Studio 7'], ['Studio 7']);
b = cc(BS, base, [other], fb7);
ok(b.verdict === 'REJECTED' && b.reason === 'ROOM_OCCUPIED' && (b.conflicts || []).length === 1 && b.conflicts[0].summary === 'BLUE / RG', 'someone else\'s KDC booking -> one conflict (the free/busy copy not added)', b.conflicts);
b = cc(BS, Object.assign({}, base, { start_iso: '2026-11-10T16:00:00+08:00', end_iso: '2026-11-10T18:00:00+08:00', expected_date: '2026-11-10', requester_text: base.requester_text.replace('2:00 pm-4:00 pm', '4:00 pm-6:00 pm') }), [], fb7);
ok(b.verdict === 'CLEAR', 'right after the outside booking (4-6 PM) -> free', b);

console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
