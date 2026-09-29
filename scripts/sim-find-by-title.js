#!/usr/bin/env node
// Offline tests for Find Booking v7 + main v191: a booking found by its name when the date is missing or wrong.
//   node scripts/sim-find-by-title.js
// Case from the live Slack test 29 Sep 17:45 PHT (exec 17079): "cancel QANODATE", looked up on today (2027-09-29 in
// QA dates) - QANODATE was on 7 Oct.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
const F = WF(process.env.FIND || 'find-booking-v7.json'), OLDF = WF('find-booking-v6.json');
const M = WF(process.env.MAIN || 'project-jessie-v191.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const ev = (id, summary, s, e) => ({ id, summary, status: 'confirmed', start: { dateTime: s }, end: { dateTime: e }, attendees: [{ email: S8, resource: true }],
  description: 'Engineer: Daryl Reyes (Post Engineer) | Booked by: Howard Luistro | ref: U08V3CKDGJF | Dept: Audio Post' });
const QN = ev('qn', 'QANODATE / Jem Lim / DR', '2027-10-07T14:00:00+08:00', '2027-10-07T16:00:00+08:00');
const QM1 = ev('m1', 'QAMOVE / Jem Lim / DR', '2027-10-01T09:00:00+08:00', '2027-10-01T11:00:00+08:00');
const QM2 = ev('m2', 'QAMOVE / Jem Lim / DR', '2027-11-17T15:00:00+08:00', '2027-11-17T17:00:00+08:00');
const OTHER = ev('o1', 'SALIN - MUSIC DEPT', '2027-09-29T00:00:00+08:00', '2027-09-30T00:00:00+08:00');
const sr = (w, req, day, wide) => new Function('$', '$input', code(w, 'Shape Results'))(
  n => n === 'Find By Title' ? wrap([{ json: { items: wide || [] } }]) : wrap([{ json: req }]), wrap([{ json: { items: day } }]))[0].json;

console.log('Find Booking v7');
let r = sr(F, { booking_date: '2027-09-29', title: 'QANODATE' }, [OTHER], [QN]);
ok(r.status === 'OK' && r.upcoming.length === 1 && r.upcoming[0].booking_date === '2027-10-07' && r.upcoming[0].title === 'QANODATE / Jem Lim / DR', 'exec 17079: "QANODATE" looked up on today -> found on 7 Oct, with its full title', r.upcoming);
ok(/Nothing on 2027-09-29 is titled "QANODATE"\. Upcoming bookings named "QANODATE":\n- QANODATE \/ Jem Lim \/ DR on Thursday, October 7, 2027, 2:00 PM - 4:00 PM, Studio 8 \(booked by Howard Luistro\)/.test(r.human), 'and says so, with date, time, room and booker', r.human);
ok(sr(OLDF, { booking_date: '2027-09-29', title: 'QANODATE' }, [OTHER], [QN]).upcoming === undefined, '  (v6: the day only - "not found")');
r = sr(F, { booking_date: '', title: 'QANODATE' }, [OTHER], [QN]);
ok(r.status === 'OK' && r.upcoming.length === 1 && r.bookings.length === 0, 'no date at all, a name -> the upcoming match (was MISSING_DATE)', r);
r = sr(F, { booking_date: '', title: 'qamove' }, [], [QM1, QM2]);
ok(r.upcoming.length === 2 && /If several could be, ask which date/.test(r.human), 'two upcoming QAMOVE (any case) -> both listed, ask which', r.human);
r = sr(F, { booking_date: '2027-10-07', title: 'QANODATE' }, [QN], [QN]);
ok(r.status === 'OK' && r.bookings.length === 1 && !(r.upcoming || []).length, 'the name IS on the date given -> the day, as before');
r = sr(F, { booking_date: '', title: 'NOPE' }, [], [QN]);
ok(r.status === 'OK' && !r.upcoming.length && /No upcoming booking is named "NOPE"/.test(r.human), 'nothing by that name -> says so, asks for the date', r.human);
r = sr(F, { booking_date: '2027-09-29', title: '' }, [OTHER], [QN]);
ok(r.status === 'OK' && r.bookings.length === 1 && r.upcoming === undefined, 'a date and no name -> exactly as before');
ok(sr(F, { booking_date: '', title: '' }, [], []).status === 'MISSING_DATE', 'neither -> MISSING_DATE as before');
r = sr(F, { booking_date: '2027-09-29', title: 'QANODATE' }, [OTHER], [{ ...QN, status: 'cancelled' }]);
ok(r.upcoming.length === 0 && /Nothing on 2027-09-29 is titled "QANODATE", and no upcoming booking is named "QANODATE"/.test(r.human), 'a cancelled event is never listed; a date + name with no match says both', r.human);

console.log('wiring and inputs');
const to = (w, n) => ((((w.connections[n] || {}).main || [])[0]) || []).map(t => t.node);
ok(JSON.stringify(to(F, 'When Executed by Another Workflow')) === '["Find By Title"]' && JSON.stringify(to(F, 'Find By Title')) === '["List Day Events"]' && JSON.stringify(to(F, 'List Day Events')) === '["Shape Results"]', 'trigger -> Find By Title -> List Day Events -> Shape Results');
const fb = node(F, 'Find By Title');
ok(/days: 450/.test(fb.parameters.url) && /minutes: 1/.test(fb.parameters.url) && fb.onError === 'continueRegularOutput', 'searches only when a name is given; a failed search cannot fail the lookup');
ok(node(F, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'title'), 'the trigger takes title');
ok(!/\$json/.test(node(F, 'List Day Events').parameters.url), 'the day read takes its date from the trigger (today when none)');
const mt = node(M, 'Find Booking').parameters;
ok(/\$fromAI\('title', /.test(mt.workflowInputs.value.title) && mt.workflowInputs.schema.some(s => s.id === 'title'), 'main: Find Booking passes the title');
ok(/never guess a date\.', 'string', ''\)/.test(mt.workflowInputs.value.booking_date) && /Never guess a date\./.test(mt.description), 'main: the date is optional, never guessed');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
