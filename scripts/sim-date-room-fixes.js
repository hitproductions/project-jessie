#!/usr/bin/env node
// Regression tests for the 29 Sep live-QA fixes (main v182, Book Session v59), offline - no calendar is touched.
//
//   node scripts/sim-date-room-fixes.js <book-session-execution.json>
//
// The execution is a real Book Session run in prepare mode for a conference room (29 Sep: Katha, 30 Sep 2027
// 2-3 PM, exec 16378). Check Conflicts runs on its recorded inputs with only the calendar response replaced, on the
// NEW build and on the OLD one, so each fix is shown failing before and passing after. The date fix (A) lives in
// main's Prepare Booking inputs and is tested in scripts/test-nodes.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = WF(process.env.BOOK || 'book-session-v61.json'), OLD = WF('book-session-v58.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + d)); } };

const MAIL = { Salin: 'c_1887hh5rsv6q4gt8hnu6ered170lg@resource.calendar.google.com', Katha: 'c_1881169pcpn12gsnm6i7sc0gjk7gk@resource.calendar.google.com',
               Likha: 'c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com', Lobby: 'c_188227mpeagjuhi7gqlgns1di14be@resource.calendar.google.com' };
const att = r => [{ email: MAIL[r], displayName: r, resource: true, responseStatus: 'accepted' }];
const D = '2027-09-30', N = '2027-10-01';
const allDay = (id, r, title) => ({ id, status: 'confirmed', summary: title, start: { dateTime: D + 'T00:00:00+08:00' }, end: { dateTime: N + 'T00:00:00+08:00' }, attendees: att(r) });
const timed = (id, r, title, s, e) => ({ id, status: 'confirmed', summary: title, start: { dateTime: D + 'T' + s + ':00+08:00' }, end: { dateTime: D + 'T' + e + ':00+08:00' }, attendees: att(r) });
const page = items => ({ kind: 'calendar#events', items });

const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const cc = (w, items, req = {}) => {
  const REQ = [{ json: { ...REQ0, ...req } }];
  const $ = n => { const it = n === 'When Executed by Another Workflow' ? REQ : rec(n); if (!it) throw new Error('unexecuted ' + n); return { first: () => it[0], all: () => it, last: () => it[it.length - 1] }; };
  const inp = [{ json: page(items) }];
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, { first: () => inp[0], all: () => inp }, () => ({}))[0].json;
};
console.log('Book Session - Check Conflicts (real execution inputs: Katha, 30 Sep 2027 2-3 PM, prepare mode)');
ok(REQ0.rooms === 'Katha' && REQ0.start_iso.startsWith(D), 'the recording is the Katha request', REQ0.rooms + ' ' + REQ0.start_iso);

// B: conference-room alternatives
let r = cc(NEW, [allDay('k', 'Katha', 'KATHA - S&A'), allDay('s', 'Salin', 'SALIN - MUSIC DEPT')]);
ok(r.reason === 'ROOM_OCCUPIED', 'Katha taken -> ROOM_OCCUPIED', r.reason);
ok(JSON.stringify(r.free_alternatives) === '["Likha"]', 'offers only the conference room actually free (Likha), never Salin or the lobby', JSON.stringify(r.free_alternatives));
ok(/Free in that same window: Likha/.test(r.human) && !/usual for this session/.test(r.human), 'says so plainly, without "usual for this session"', r.human);
let o = cc(OLD, [allDay('k', 'Katha', 'KATHA - S&A'), allDay('s', 'Salin', 'SALIN - MUSIC DEPT')]);
ok(!(o.free_alternatives || []).length, '  (old build: nothing offered, so the model guessed)', JSON.stringify(o.free_alternatives));
r = cc(NEW, [allDay('k', 'Katha', 'KATHA - S&A'), allDay('s', 'Salin', 'SALIN - MUSIC DEPT'), timed('l', 'Likha', 'LIKHA - BD', '13:00', '16:00')]);
ok(!(r.free_alternatives || []).length && /No other conference room is free then/.test(r.human), 'every conference room taken -> says so, offers times instead', r.human);
r = cc(NEW, [timed('l', 'Likha', 'LIKHA - BD', '09:00', '10:00'), allDay('k', 'Katha', 'KATHA - S&A')]);
ok(JSON.stringify(r.free_alternatives) === '["Salin","Likha"]' || JSON.stringify(r.free_alternatives) === '["Likha","Salin"]', 'a booking outside the window does not make a room busy', JSON.stringify(r.free_alternatives));
r = cc(NEW, [timed('l', 'Lobby', 'LOBBY - EVENT', '13:00', '16:00')], { rooms: 'Lobby' });
ok(r.reason === 'ROOM_OCCUPIED' && (r.free_alternatives || []).length >= 1, 'the lobby asked for and taken -> alternatives still offered', JSON.stringify(r.free_alternatives));
r = cc(NEW, []);
ok(r.verdict !== 'REJECTED' || r.reason !== 'ROOM_OCCUPIED', 'Katha free -> no ROOM_OCCUPIED', r.reason);

// C: all day
r = cc(NEW, [allDay('k', 'Katha', 'KATHA - S&A')]);
ok(/Katha is taken all day by "KATHA - S&A"/.test(r.human), 'an all-day clash is described as "all day"', r.human);
o = cc(OLD, [allDay('k', 'Katha', 'KATHA - S&A')]);
ok(!/all day/.test(o.human), '  (old build: no "all day", the model wrote 12:00 AM to 12:00 AM)', o.human);
r = cc(NEW, [timed('k', 'Katha', 'KATHA - S&A', '13:30', '15:00')]);
ok(/Katha is taken by "KATHA - S&A"/.test(r.human) && !/all day/.test(r.human), 'a timed clash is not called all day', r.human);

// v61 (live QA 29 Sep): a clash that is the requester's own booking asks to move it
if (/own_booking/.test(code(NEW, 'Check Conflicts'))) {
  const mine = { ...timed('q', 'Katha', 'QATIME / Jem Lim / DR', '14:00', '16:00'), description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U08V3CKDGJF' };
  const theirs = { ...timed('t', 'Katha', 'OTHER / X / TL', '14:00', '16:00'), description: 'Booked by: Tara Lim | ref: U026N6E1R' };
  r = cc(NEW, [mine]);
  ok(r.reason === 'ROOM_OCCUPIED' && r.own_booking === true && /overlaps a booking you already have: "QATIME \/ Jem Lim \/ DR" \(Katha, 2:00 PM – 4:00 PM\)/.test(r.human), 'own booking in the way -> says so and asks to move it', r.human);
  r = cc(NEW, [theirs]);
  ok(r.reason === 'ROOM_OCCUPIED' && !r.own_booking && /is taken/.test(r.human), "someone else's booking -> the usual room-taken answer", r.human);
  r = cc(NEW, [mine, theirs]);
  ok(!r.own_booking, 'own and someone else\'s both in the way -> the usual answer');
  o = cc(OLD, [mine]);
  ok(!o.own_booking, '  (old build: own booking treated as any clash)');
}

console.log('\n' + (fail ? fail + ' failing, ' : '') + pass + ' passing');
process.exit(fail ? 1 : 0);
