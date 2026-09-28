#!/usr/bin/env node
// Regression tests for the 29 Sep booking review (Book Session v56, Room Availability v11, Find Booking v6,
// Cancel Booking v17, Move Booking v24), offline - no calendar is touched.
//
//   node scripts/sim-booking-review.js <book-session-execution.json>
//
// Every case runs on the NEW build and, where the old build had the bug, on the OLD build too, so each fix is
// shown failing before and passing after. Book Session's Check Conflicts runs on a real execution's inputs
// (a CLEAR Studio 7 booking) with only the calendar response replaced.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = { book: WF('book-session-v56.json'), ra: WF('room-availability-v11.json'), find: WF('find-booking-v6.json'), cancel: WF('cancel-booking-v17.json'), move: WF('move-booking-v24.json') };
const OLD = { book: WF('book-session-v55.json'), ra: WF('room-availability-v10.json'), find: WF('find-booking-v5.json'), cancel: WF('cancel-booking-v16.json'), move: WF('move-booking-v23.json') };
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + d)); } };
const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const room = (flag = true) => [{ email: S7, displayName: 'KDC Plaza-Top Level-Studio 7 (7)', resource: flag, responseStatus: 'accepted' }];
const timed = (id, s, e, extra = {}) => ({ id, status: 'confirmed', summary: 'OTHER / X / TL', start: { dateTime: s }, end: { dateTime: e }, attendees: room(), ...extra });
const allDay = (id, d, dEnd, extra = {}) => ({ id, status: 'confirmed', summary: 'Studio 7 hold', start: { date: d }, end: { date: dEnd }, attendees: room(), ...extra });
const page = (items, extra = {}) => ({ kind: 'calendar#events', items, ...extra });

// ---------------------------------------------------------------- Book Session: Check Conflicts
{
  console.log('Book Session - Check Conflicts (real execution inputs, Studio 7)');
  const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
  const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
  const REQ0 = rec('When Executed by Another Workflow')[0].json;
  const D = REQ0.start_iso.slice(0, 10), next = new Date(Date.parse(D + 'T00:00:00Z') + 864e5).toISOString().slice(0, 10), prev = new Date(Date.parse(D + 'T00:00:00Z') - 864e5).toISOString().slice(0, 10);
  const cc = (w, pages, req = {}) => {
    const REQ = [{ json: { ...REQ0, ...req } }];
    const $ = n => { const it = n === 'When Executed by Another Workflow' ? REQ : rec(n); if (!it) throw new Error('unexecuted ' + n); return { first: () => it[0], all: () => it, last: () => it[it.length - 1] }; };
    const inp = pages.map(j => ({ json: j }));
    const r = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, { first: () => inp[0], all: () => inp }, () => ({}))[0].json;
    return r.verdict === 'REJECTED' ? r.reason : (r.verdict || 'CLEAR');
  };
  const six = { start_iso: D + 'T06:00:00+08:00', end_iso: D + 'T07:00:00+08:00' };
  ok(cc(NEW.book, [page([])]) === 'CLEAR', 'empty calendar -> CLEAR (the recorded booking)');
  ok(cc(NEW.book, [page([], { nextPageToken: 'p2' })]) === 'UNVERIFIABLE', 'a read with a second page is never CLEAR');
  ok(cc(OLD.book, [page([], { nextPageToken: 'p2' })]) === 'CLEAR', '  (old build: that read was CLEAR)');
  ok(cc(NEW.book, [page([]), { error: { message: 'page 2 failed' } }]) === 'UNVERIFIABLE', 'a failed later page is never CLEAR');
  ok(cc(NEW.book, [page([timed('t1', REQ0.start_iso, REQ0.end_iso)])]) === 'ROOM_OCCUPIED', 'overlapping timed booking -> ROOM_OCCUPIED');
  ok(cc(NEW.book, [page([timed('t2', D + 'T08:00:00+08:00', REQ0.start_iso)])]) === 'CLEAR', 'a booking ending exactly at the start is adjacent, not a clash');
  ok(cc(NEW.book, [page([timed('t3', REQ0.end_iso, D + 'T15:00:00+08:00')])]) === 'CLEAR', 'a booking starting exactly at the end is adjacent, not a clash');
  ok(cc(NEW.book, [page([allDay('a1', D, next)])], six) === 'ROOM_OCCUPIED', 'all-day Studio 7 hold blocks a 6-7 AM Manila booking that day');
  ok(cc(OLD.book, [page([allDay('a1', D, next)])], six) !== 'ROOM_OCCUPIED', '  (old build: it did not - the hold "started" at 08:00 Manila)');
  ok(cc(NEW.book, [page([allDay('a0', prev, D)])], six) === 'CLEAR', "the previous day's all-day hold (end date exclusive) does not block");
  ok(cc(NEW.book, [page([timed('t4', D + 'T05:30:00+08:00', D + 'T06:30:00+08:00')])], six) === 'ROOM_OCCUPIED', 'offset-aware dateTime values still compared exactly');
  ok(cc(NEW.book, [page([timed('t5', REQ0.start_iso, REQ0.end_iso, { summary: 'DUP / X / TL' }), timed('t6', REQ0.start_iso, REQ0.end_iso, { summary: 'DUP / X / TL' })])]) === 'ROOM_OCCUPIED', 'duplicate-titled clashes are still clashes');
}

// ---------------------------------------------------------------- Room Availability: Compute Availability
{
  console.log('Room Availability - Compute Availability');
  const rooms = ['Studio 7', 'Studio 1'].map((n, i) => ({ id: 'r' + i, name: n }));
  const ra = (w, pages, s, e) => {
    const REQ = { start_iso: s, end_iso: e, reference_data: JSON.stringify({ rooms, types: [] }), room: '', session_type: '' };
    const inp = pages.map(j => ({ json: j }));
    return new Function('$', '$input', code(w, 'Compute Availability'))(() => ({ first: () => ({ json: REQ }), all: () => [{ json: REQ }] }), { all: () => inp, first: () => inp[0] })[0].json;
  };
  const D = '2027-11-09', s6 = D + 'T06:00:00+08:00', e7 = D + 'T07:00:00+08:00';
  const free = r => (r.free_rooms || []).includes('Studio 7');
  ok(free(ra(NEW.ra, [page([])], s6, e7)), 'empty calendar -> Studio 7 free');
  ok(!free(ra(NEW.ra, [page([allDay('a1', D, '2027-11-10')])], s6, e7)), 'all-day hold -> Studio 7 not free at 6-7 AM');
  ok(free(ra(OLD.ra, [page([allDay('a1', D, '2027-11-10')])], s6, e7)), '  (old build: offered it as free)');
  ok(free(ra(NEW.ra, [page([allDay('a0', '2027-11-08', D)])], s6, e7)), "previous day's all-day hold -> free (end exclusive)");
  ok(free(ra(NEW.ra, [page([timed('t1', D + 'T05:00:00+08:00', s6)])], s6, e7)), 'adjacent booking -> free');
  ok(!free(ra(NEW.ra, [page([timed('t2', D + 'T06:30:00+08:00', D + 'T08:00:00+08:00')])], s6, e7)), 'overlapping booking -> not free');
  ok(ra(NEW.ra, [page([], { nextPageToken: 'p2' })], s6, e7).status === 'CALENDAR_ERROR', 'a read with a second page -> CALENDAR_ERROR, not "all free"');
  ok(free(ra(OLD.ra, [page([], { nextPageToken: 'p2' })], s6, e7)), '  (old build: "all free")');
  ok(ra(NEW.ra, [page([]), { error: { message: 'page 2' } }], s6, e7).status === 'CALENDAR_ERROR', 'a failed later page -> CALENDAR_ERROR');
}

// ---------------------------------------------------------------- Find Booking: Shape Results
{
  console.log('Find Booking - Shape Results');
  const fb = (w, raw) => new Function('$', '$input', code(w, 'Shape Results'))(() => ({ first: () => ({ json: { booking_date: '2027-11-09', requester: 'U026N6E1R' } }), all: () => [{ json: {} }] }), { first: () => ({ json: raw }), all: () => [{ json: raw }] })[0].json;
  ok(fb(NEW.find, page([timed('t1', '2027-11-09T10:00:00+08:00', '2027-11-09T12:00:00+08:00')])).status !== 'LOOKUP_FAILED', 'a complete day is listed');
  ok(fb(NEW.find, page([], { nextPageToken: 'p2' })).status === 'LOOKUP_FAILED', 'a day with a second page -> LOOKUP_FAILED, not "nothing booked"');
}

// ---------------------------------------------------------------- Cancel Check Ownership / Move Resolve Booking
const ME = 'U026N6E1R';
const ev = (id, summary, ref, t, extra = {}) => ({ id, summary, status: 'confirmed', description: ref ? ('Booked by: Someone | ref: ' + ref) : 'no marker',
  start: { dateTime: '2027-09-09T' + t + ':00:00+08:00' }, end: { dateTime: '2027-09-09T18:00:00+08:00' }, ...extra });
const DAY = [ev('a1', 'ALPHA / X / TL', ME, '14'), ev('u1', '', ME, '09'), ev('u2', '   ', ME, '10'),
             ev('q1', 'QATEST38 / Jem Lim / TL', ME, '11'), ev('d1', 'DUP / Q / TL', ME, '12'), ev('d2', 'DUP / Q / TL', ME, '13'),
             ev('e1', 'NET-KUBA EP01 / FP', ME, '15'), ev('e2', 'NET-KUBA EP02 / FP', ME, '16')];
for (const [label, key, node, extra] of [['Cancel Booking - Check Ownership', 'cancel', 'Check Ownership', {}],
                                         ['Move Booking - Resolve Booking', 'move', 'Resolve Booking', { new_start_iso: '2027-09-09T19:00:00+08:00', new_end_iso: '2027-09-09T20:00:00+08:00' }]]) {
  console.log(label);
  const go = (w, req, items = DAY, pg = {}) => new Function('$', '$input', code(w, node))(() => ({ first: () => ({ json: req }) }), { first: () => ({ json: page(items, pg) }) })[0].json;
  const base = { requester: ME, confirmed: true, booking_date: '2027-09-09', event_id: '', ...extra };
  const idOf = r => r.verdict === 'CLEAR' ? (r.original_id || r.event_id || (r.event && r.event.id) || 'CLEAR') : r.reason;
  let r = go(NEW[key], { ...base, title: 'ALPHA / X / TL' });
  ok(r.verdict === 'CLEAR', 'one exact title -> acted on');
  r = go(NEW[key], { ...base, title: 'GAMMA / X / TL' });
  ok(r.reason === 'NOT_ON_CALENDAR', 'an unmatched title never lands on an untitled event', r.reason);
  const ONE_UNTITLED = [ev('a1', 'ALPHA / X / TL', ME, '14'), ev('u1', '', ME, '09')];
  const o = go(OLD[key], { ...base, title: 'GAMMA / X / TL' }, ONE_UNTITLED);
  ok(go(NEW[key], { ...base, title: 'GAMMA / X / TL' }, ONE_UNTITLED).reason === 'NOT_ON_CALENDAR', 'same day with ONE untitled event -> still NOT_ON_CALENDAR');
  ok(o.verdict === 'CLEAR', '  (old build: it matched an untitled event and cleared it)', o.reason);
  r = go(NEW[key], { ...base, title: 'DUP / Q / TL' });
  ok(r.reason === 'AMBIGUOUS_TITLE', 'duplicate exact titles -> ask which');
  r = go(NEW[key], { ...base, title: 'QATEST38' });
  ok(r.reason === 'AMBIGUOUS_TITLE' && /QATEST38 \/ Jem Lim \/ TL/.test(r.human), 'a partial title -> offered back as a candidate, not acted on');
  const TITLED = DAY.filter(e => e.summary.trim());
  ok(go(NEW[key], { ...base, title: 'QATEST38' }, TITLED).reason === 'AMBIGUOUS_TITLE', 'partial title on a day with no untitled events -> still a candidate only');
  ok(go(OLD[key], { ...base, title: 'QATEST38' }, TITLED).verdict === 'CLEAR', '  (old build: acted on the partial title)');
  r = go(NEW[key], { ...base, title: 'NET-KUBA EP03 / FP' });
  ok(r.verdict !== 'CLEAR', 'a near title (EP03 when only EP01/EP02 exist) is never acted on', r.reason);
  r = go(NEW[key], { ...base, title: 'wrong title', event_id: 'a1' });
  ok(r.verdict === 'CLEAR', 'a verified event id is acted on');
  r = go(NEW[key], { ...base, title: 'ALPHA / X / TL' }, DAY, { nextPageToken: 'p2' });
  ok(r.reason === 'LOOKUP_FAILED', 'a day with a second page -> LOOKUP_FAILED');
}

// ---------------------------------------------------------------- Move: room attendees + Check New Window
{
  console.log('Move Booking - room attendees and the new window');
  const go = (w, items) => new Function('$', '$input', code(w, 'Resolve Booking'))(() => ({ first: () => ({ json: { requester: ME, confirmed: true, booking_date: '2027-09-09', event_id: '', title: 'ALPHA / X / TL', new_start_iso: '2027-09-09T19:00:00+08:00', new_end_iso: '2027-09-09T20:00:00+08:00' } }) }), { first: () => ({ json: page(items) }) })[0].json;
  const withAtt = att => [ev('a1', 'ALPHA / X / TL', ME, '14', { attendees: att })];
  const person = { email: 'tara@hitproductions.net', responseStatus: 'accepted' };
  let r = go(NEW.move, withAtt([person, ...room(true)]));
  ok(JSON.stringify(r.attendees) === JSON.stringify([{ email: S7 }]), 'a flagged room is kept, people are not copied');
  r = go(NEW.move, withAtt([person, { email: S7 }]));
  ok(JSON.stringify(r.attendees) === JSON.stringify([{ email: S7 }]), 'a known room email WITHOUT the resource flag is kept');
  ok(JSON.stringify(go(OLD.move, withAtt([person, { email: S7 }])).attendees) === '[]', '  (old build: dropped it - the replacement had no room)');
  r = go(NEW.move, withAtt([{ email: 'c_unknown123@resource.calendar.google.com' }]));
  ok(r.attendees.length === 1, 'an unlisted @resource.calendar.google.com room is kept');
  r = go(NEW.move, withAtt([]));
  ok(r.verdict === 'CLEAR' && r.attendees.length === 0, 'a booking that never had a room attendee (M booth hold) still moves as it is');

  const cnw = (w, raw) => new Function('$', '$input', code(w, 'Check New Window'))(() => ({ first: () => ({ json: { attendees: [{ email: S7 }], location: 'Studio 7', new_start: '2027-11-09T06:00:00+08:00', new_end: '2027-11-09T07:00:00+08:00', original_id: 'o1' } }) }), { first: () => ({ json: raw }), all: () => [{ json: raw }] })[0].json;
  ok(cnw(NEW.move, page([])).verdict !== 'REJECTED', 'empty new window -> not refused');
  ok(cnw(NEW.move, page([allDay('a1', '2027-11-09', '2027-11-10')])).verdict === 'REJECTED', 'all-day hold on the new day blocks a 6-7 AM move');
  ok(cnw(OLD.move, page([allDay('a1', '2027-11-09', '2027-11-10')])).verdict !== 'REJECTED', '  (old build: it did not)');
  ok(cnw(NEW.move, page([timed('t1', '2027-11-09T05:00:00+08:00', '2027-11-09T06:00:00+08:00')])).verdict !== 'REJECTED', 'adjacent booking -> not refused');
  ok(cnw(NEW.move, page([], { nextPageToken: 'p2' })).reason === 'LOOKUP_FAILED', 'new window with a second page -> LOOKUP_FAILED');
}

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
