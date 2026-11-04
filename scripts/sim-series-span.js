#!/usr/bin/env node
// PENDING 150 (4 Nov): Room Availability v26 answers a whole series in one call - one read of KDC Bookings and the rooms'
// free/busy for the span, then each date its own answer. Checks: every date's answer equals v25's answer for that date alone
// (same events, same free/busy), pages (nextPageToken) are followed and an unfinished read fails closed, day_busy for the
// watched rooms, and one window (no dates) is exactly v25.
// Usage: node scripts/sim-series-span.js [room-availability v26] [room-availability v25]
const fs = require('fs');
const load = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const RA = load(process.argv[2], 'workflows/room-availability-v26.json'), RA0 = load(process.argv[3], 'workflows/imported/room-availability-v25-imported.json');
if (!/v26 \(PENDING 150/.test(JSON.stringify(RA.nodes))) { console.log('0 ok, 0 failed (an older build: v26 not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const RES = { 'Studio 7': 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', 'Studio 8': 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com',
  'Studio 1': 'hitproductions.net_3737303833303637363538@resource.calendar.google.com', 'Studio A': 'c_18843dclutqm6hl9nbeg002phapfu@resource.calendar.google.com',
  M4: 'c_18869nhmsj2uki8mljoi48v1cj7l4@resource.calendar.google.com' };
const Z = s => new Date(Date.parse(s)).toISOString();
const NAMES = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 4', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio A', 'Studio B', 'Studio C', 'Studio D', 'Studio E', 'Studio F', 'Studio M',
  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'Salin', 'Katha', 'Likha', 'Lobby'];
const REF = JSON.stringify({ rooms: NAMES.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: /^Studio [ABDE]$/.test(n), booth: /^Studio [ABDE]$/.test(n), common: /Salin|Katha|Likha|Lobby/.test(n) })),
  types: [{ type: 'Localization Dubbing', priority: ['r0', 'r1', 'r5'], last: ['r6'] }] });
const ev = (id, title, s, e, rooms, att) => ({ id, summary: title, location: rooms.join(', '), start: s.length === 10 ? { date: s } : { dateTime: s }, end: e.length === 10 ? { date: e } : { dateTime: e },
  attendees: (att || []).map(r => ({ email: RES[r], resource: true, responseStatus: 'accepted' })), description: 'Booked by: X | ref: U9' });
const CAL = [
  ev('a', 'NRT-BONJOUR6 | JT', '2026-11-05T11:00:00+08:00', '2026-11-05T17:00:00+08:00', ['Studio A', 'Studio 1'], ['Studio A', 'Studio 1']),
  ev('b', 'NET-ISLA6', '2026-11-05T13:00:00+08:00', '2026-11-05T23:00:00+08:00', ['Studio 2']),
  ev('c', 'ORANGE / HL', '2026-11-06T09:00:00+08:00', '2026-11-06T13:00:00+08:00', ['Studio 1'], ['Studio 1']),
  ev('d', 'M4 - Japs', '2026-11-07', '2026-11-08', ['M4'], ['M4']),
  ev('e', 'LATE / DR', '2026-11-07T15:00:00+08:00', '2026-11-07T18:00:00+08:00', ['Studio 7'], ['Studio 7'])];
const FB = { calendars: {
  [RES['Studio 8']]: { busy: [{ start: Z('2026-11-06T14:00:00+08:00'), end: Z('2026-11-06T16:00:00+08:00') }] },   // outside KDC (own calendar)
  [RES['Studio 1']]: { busy: [{ start: Z('2026-11-05T11:00:00+08:00'), end: Z('2026-11-05T17:00:00+08:00') }, { start: Z('2026-11-06T09:00:00+08:00'), end: Z('2026-11-06T13:00:00+08:00') }] } } };
Date.now = () => Date.parse('2026-11-04T06:00:00Z');
const run = (w, trig, pages, fb) => new Function('$', '$input', node(w, 'Compute Availability').parameters.jsCode)(
  n => n === 'Room Free Busy' ? wrap([{ json: fb || {} }]) : wrap([{ json: trig }]), wrap(pages.map(p => ({ json: JSON.parse(JSON.stringify(p)) }))));
const base = { session_type: 'Localization Dubbing', room: '', scope: '', hours: '', reference_data: REF };
const DATES = ['2026-11-05', '2026-11-06', '2026-11-07'];

console.log('One call for three dates = three single calls (v25)');
let r = run(RA, Object.assign({}, base, { dates: DATES.join(','), t0: '14:00', t1: '16:00', start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-07T16:00:00+08:00', watch: 'Studio 1, Studio A' }),
  [{ items: CAL }], FB)[0].json;
ok(r.span === true && r.status === 'OK' && (r.per_date || []).length === 3 && r.per_date.map(x => x.date).join() === DATES.join(), 'span: one answer per date, in order', r);
for (const [i, d] of DATES.entries()) {
  const one = run(RA0, Object.assign({}, base, { start_iso: d + 'T14:00:00+08:00', end_iso: d + 'T16:00:00+08:00' }), [{ items: CAL }], FB)[0].json;
  const a = Object.assign({}, r.per_date[i]); delete a.date; delete a.day_busy; delete one.human; delete one.reply_text;
  ok(JSON.stringify(a) === JSON.stringify(one), d + ': the same answer as v25 asked about that date alone', { span: a, v25: one });
}
ok(r.per_date[0].busy.some(b => /^Studio 1 /.test(b)) && r.per_date[0].busy.some(b => /^Studio A /.test(b)) && !r.per_date[1].busy.some(b => /^Studio 1 /.test(b)), 'Nov 5 2-4 PM: Studio 1 and Studio A taken; Nov 6: Studio 1 free then (its booking ends at 1)');
ok(r.per_date[1].busy.some(b => /^Studio 8 \(Booked outside KDC Bookings\)/.test(b)), 'a room booked from its own calendar is taken on that date (v25)', r.per_date[1].busy);
ok(JSON.stringify(r.per_date[0].day_busy['Studio 1']) === '[[660,1020]]' && JSON.stringify(r.per_date[1].day_busy['Studio 1']) === '[[540,780]]' && JSON.stringify(r.per_date[2].day_busy['Studio 1']) === '[]',
  'day_busy: Studio 1 11:00-17:00 on Nov 5, 9:00-13:00 on Nov 6 (KDC + its own calendar, merged), nothing Nov 7', r.per_date.map(x => x.day_busy));
ok(!('human' in r.per_date[0]) && !('reply_text' in r.per_date[0]), 'no human / reply_text per date (kept small)');

console.log('Pages');
r = run(RA, Object.assign({}, base, { dates: DATES.join(','), t0: '14:00', t1: '16:00', start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-07T16:00:00+08:00' }),
  [{ items: CAL.slice(0, 2), nextPageToken: 'p2' }, { items: CAL.slice(2) }], FB)[0].json;
ok(r.status === 'OK' && r.per_date[2].busy.some(b => /^Studio 7 /.test(b)), 'two pages read as one (the second page\'s bookings count)', r.per_date[2]);
r = run(RA, Object.assign({}, base, { dates: DATES.join(','), t0: '14:00', t1: '16:00', start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-07T16:00:00+08:00' }),
  [{ items: CAL.slice(0, 2), nextPageToken: 'p2' }], FB)[0].json;
ok(r.status === 'CALENDAR_ERROR', 'a read that stopped with a page still to come -> CALENDAR_ERROR, never "free"', r);
r = run(RA, Object.assign({}, base, { dates: DATES.join(','), t0: '14:00', t1: '16:00' }), [{ error: { message: 'x' } }], FB)[0].json;
ok(r.status === 'CALENDAR_ERROR', 'a failed read -> CALENDAR_ERROR', r);
const one2 = run(RA, Object.assign({}, base, { start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-05T16:00:00+08:00' }), [{ items: CAL.slice(0, 1), nextPageToken: 'p2' }, { items: CAL.slice(1) }], FB)[0].json;
ok(one2.status === 'OK' && one2.busy.some(b => /^Studio 2 /.test(b)), 'one window: pages followed too', one2);

console.log('One window - exactly v25');
for (const [s, e, room] of [['2026-11-05T14:00:00+08:00', '2026-11-05T16:00:00+08:00', ''], ['2026-11-05T00:00:00+08:00', '2026-11-05T23:59:00+08:00', 'Studio 1'], ['2026-11-07T09:00:00+08:00', '2026-11-07T12:00:00+08:00', 'M4, Studio 7']]) {
  const T = Object.assign({}, base, { start_iso: s, end_iso: e, room });
  const a = run(RA, T, [{ items: CAL }], FB)[0].json, b = run(RA0, T, [{ items: CAL }], FB)[0].json;
  ok(JSON.stringify(a) === JSON.stringify(b), s.slice(0, 16) + (room ? ' (' + room + ')' : '') + ': identical to v25', { v26: a.reply_text || a.human, v25: b.reply_text || b.human });
}
const GE = node(RA, 'Get Events In Window').parameters;
ok(GE.queryParameters.parameters.find(q => q.name === 'maxResults').value === '2500' && GE.options.pagination.pagination.parameters.parameters[0].name === 'pageToken', 'Get Events In Window: 2500 a page, follows nextPageToken');
ok(['dates', 't0', 't1', 'watch'].every(k => node(RA, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === k)), 'the trigger takes dates, t0, t1, watch');
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
