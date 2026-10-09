// Offline check of the date guard: Gate Context's datesUnderDiscussion (main v159)
// and Book Session's DATE_MISMATCH refusal (book v47), replaying Camille's
// QA round-2 conversation of 2026-09-24.
//   node scripts/sim-date-guard.js
const fs = require('fs');
const node = (f, n) => JSON.parse(fs.readFileSync(f, 'utf8')).nodes.find(x => x.name === n).parameters.jsCode;
const GATE = node(process.env.MAIN || 'workflows/project-jessie-v160.json', 'Gate Context');
const CHECK = node(process.env.BOOK || 'workflows/book-session-v48.json', 'Check Conflicts');
let fails = 0;
const ok = (c, m) => { console.log((c ? '  ok    ' : '  FAIL  ') + m); if (!c) fails++; };

// ---- Gate Context -----------------------------------------------------------
Date.now = () => Date.UTC(2026, 8, 24, 6, 31, 53);   // Thu 24 Sep 2026 14:31 Manila (Jessie: 2027)
const ME = 'U08JL17A50A', store = {};
const gate = (text, history) => {
  const $ = name => ({
    first: () => ({ json:
      name === 'Slack Trigger' ? { text, user: ME, ts: '1790228000.1', channel: 'D0BUVN5FERE' } :
      name === 'Get Booker'    ? { fields: { Name: 'Camille Caridad', Department: ['Sales & Accounts'] } } : {} }),
    all: () => history.map(h => ({ json: h }))
  });
  return new Function('$', '$getWorkflowStaticData', GATE)($, () => store)[0].json;
};
console.log('Gate Context - what date does the conversation hold?');
const t1 = gate('Book Studio F for Japs next Thursday from 1pm to 4pm', []);
const V255 = /__nextOf/.test(GATE), NT = V255 ? '2027-10-07' : '2027-09-30';   // v255: from Friday on, "next Thursday" is the one after the coming one
ok(t1.datesUnderDiscussion === NT, 'turn 1 "next Thursday" -> ' + t1.datesUnderDiscussion);
const t2 = gate('Daryl', []);
ok(t2.datesUnderDiscussion === NT, 'turn "Daryl" (no date) carries -> ' + t2.datesUnderDiscussion);
const t3 = gate('actually make it Friday Oct 1', []);
ok(t3.datesUnderDiscussion.split(',')[0] === '2027-10-01', '"Friday Oct 1": the written date wins -> ' + t3.datesUnderDiscussion);
const t3b = gate('yes', []);
ok(t3b.datesUnderDiscussion === '2027-10-01', '...and the yes turn carries Oct 1 -> ' + t3b.datesUnderDiscussion);
const t3c = gate('sorry, make that oct 7', []);
ok(t3c.datesUnderDiscussion === '2027-10-07', '"oct 7" with no year is now resolved -> ' + t3c.datesUnderDiscussion);
const t3d = gate('oct 5 4-7pm. studio 1', []);
ok(t3d.datesUnderDiscussion === '2027-10-05', 'Howard\'s "oct 5 4-7pm. studio 1" -> ' + t3d.datesUnderDiscussion);
const t3e = gate('7th October at 2', []);
ok(t3e.datesUnderDiscussion === '2027-10-07', '"7th October" -> ' + t3e.datesUnderDiscussion);
const t3f = gate('can we do the 30th instead', []);
ok(t3f.datesUnderDiscussion === '', 'an unreadable date ("the 30th") stops tracking -> "' + t3f.datesUnderDiscussion + '"');
const t3g = gate('yes', []);
ok(t3g.datesUnderDiscussion === '', '...and the next turn does not revive the old date -> "' + t3g.datesUnderDiscussion + '"');
const t3h = gate('book studio 5 for the may session', []);
ok(t3h.datesUnderDiscussion === '', '"may" as a word with no day is not a date -> "' + t3h.datesUnderDiscussion + '"');
console.log('Gate Context - week and month phrases');
const saveNow = Date.now;
Date.now = () => Date.UTC(2026, 8, 26, 8, 30, 0);  // Sat 26 Sep 2026 16:30 Manila = Jessie's Sunday 26 Sep 2027
const w1 = gate('show my bookings next week', []);
ok(/Monday, 27 September 2027.*to Sunday, 3 October 2027/.test(w1.dateNotice), '"next week" on Sunday 26 Sep = 27 Sep - 3 Oct');
ok(w1.datesUnderDiscussion.split(',').length === 7 && w1.datesUnderDiscussion.startsWith('2027-09-27'), '...all seven days count for the guard');
const w2 = gate('anything free this week', []);
ok(/Monday, 20 September 2027.*to Sunday, 26 September 2027/.test(w2.dateNotice), '"this week" = 20 - 26 Sep');
const w3 = gate('book the lobby next weekend', []);
ok(/Saturday, 2 October 2027.*to Sunday, 3 October 2027/.test(w3.dateNotice), '"next weekend" = 2 - 3 Oct');
const w4 = gate('what do i have next month', []);
ok(/Friday, 1 October 2027.*to Sunday, 31 October 2027/.test(w4.dateNotice), '"next month" = 1 - 31 Oct');
gate('book studio 3 next thursday 10am', []);
const w5 = gate('show me next week', []);
const w6 = gate('yes', []);
ok(w6.datesUnderDiscussion === '', 'a range is never carried: the turn after "next week" tracks nothing');
Date.now = saveNow;
const t4 = gate('reset', []);
const t5 = gate('hi', []);
ok(t5.datesUnderDiscussion === '', 'after reset nothing is tracked -> "' + t5.datesUnderDiscussion + '"');

// ---- Book Session Check Conflicts ------------------------------------------
Date.now = () => Date.UTC(2026, 8, 24, 6, 40, 0);
const check = req => {
  const $ = name => ({
    first: () => ({ json: name === 'When Executed by Another Workflow' ? req : {} }),
    all: () => []
  });
  const $input = { all: () => [], first: () => ({ json: {} }) };
  return new Function('$', '$input', CHECK)($, $input)[0].json;
};
const base = { summary: 'SUSHI / Pael Laurena / DR', rooms: 'Studio C', confirmed: true,
               session_type: 'Music Vocal Recording',
               reference_data: JSON.stringify({ rooms: [{ name: 'Studio C' }], types: [{ type: 'Music Vocal Recording', min: 60, max: 120 }] }),
               start_iso: '2027-10-07T13:00:00+08:00', end_iso: '2027-10-07T16:00:00+08:00' };
console.log('Book Session - does it refuse the wrong date?');
let r = check(Object.assign({}, base, { expected_date: '2027-09-30' }));
ok(r.reason === 'DATE_MISMATCH', "Camille's case: 7 Oct booked, 30 Sep discussed -> " + r.reason);
ok(/Thursday, October 7, 2027/.test(r.human) && /Thursday, September 30, 2027/.test(r.human), 'refusal names both dates: ' + r.human.slice(0, 110) + '...');
r = check(Object.assign({}, base, { expected_date: '2027-09-24,2027-10-07' }));
ok(r.reason !== 'DATE_MISMATCH', 'booking date is one of several named in the message -> passes');
r = check(Object.assign({}, base, { expected_date: '2027-10-07' }));
ok(r.reason !== 'DATE_MISMATCH', 'matching date is not refused by the guard (' + (r.reason || r.verdict || 'passes') + ')');
r = check(Object.assign({}, base, { expected_date: '' }));
ok(r.reason !== 'DATE_MISMATCH', 'nothing tracked -> guard stays out of the way');
r = check(Object.assign({}, base, { expected_date: '2027-09-30', series: 'true' }));
ok(r.reason !== 'DATE_MISMATCH', 'series occurrence is exempt');
r = check(Object.assign({}, base, { expected_date: '2027-10-07', start_iso: '2027-10-06T17:30:00Z', end_iso: '2027-10-06T19:00:00Z' }));
ok(r.reason !== 'DATE_MISMATCH', 'a UTC timestamp that is 7 Oct in Manila matches 7 Oct');
r = check(Object.assign({}, base, { expected_date: '2027-10-07', start_iso: '2027-10-07', end_iso: '2027-10-08', all_day: true, rooms: 'M4' }));
ok(r.reason !== 'DATE_MISMATCH', 'all-day date-only booking on the right day passes');
r = check(Object.assign({}, base, { expected_date: '2027-09-30', start_iso: '2025-01-01T10:00:00+08:00', end_iso: '2025-01-01T11:00:00+08:00' }));
if (/v91 \(decided 6 Oct\)/.test(String(CHECK))) ok(r.reason === 'DATE_MISMATCH', 'v91: past dates are allowed - a past date that is not the one discussed is still DATE_MISMATCH', r.reason);
else ok(r.reason === 'PAST_DATE', 'a past date is still refused as PAST_DATE first');

console.log(fails ? '\n' + fails + ' FAILED' : '\nall passed');
process.exit(fails ? 1 : 0);
