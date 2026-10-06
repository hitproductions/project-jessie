#!/usr/bin/env node
// Offline tests for Cancel Booking v22 + Find Booking v8 + main v221 (name search includes past; decided 6 Oct): a booking
// named without a date is looked for in the last 60 days as well as ahead, and the same name on a past and an upcoming
// booking is always said - coming up first, past ones marked "(already passed)".
//   node scripts/sim-name-search-past.js <main-execution.json>   (real inputs for Guard Probe)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
const C = WF(process.env.CANCEL || 'cancel-booking-v22.json'), OC = WF('cancel-booking-v21.json');
const F = WF(process.env.FIND || 'find-booking-v8.json'), OF = WF('find-booking-v7.json');
const M = WF(process.env.MAIN || 'project-jessie-v221.json'), OM = WF('project-jessie-v220.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
Date.now = () => Date.parse('2026-10-06T05:30:00Z');   // Tue 6 Oct 2026, 13:30 Manila
const ME = 'U08V3CKDGJF', S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const ev = (id, summary, s, e, ref = ME) => ({ id, summary, status: 'confirmed', start: { dateTime: s }, end: { dateTime: e },
  attendees: [{ email: S8, displayName: 'KDC Plaza-Top Level-Studio 8 (7)', resource: true }], location: 'KDC Plaza-Top Level-Studio 8 (7)',
  description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ref + ' | Dept: Audio Post' });
const T = 'RUNWAY / John Ableton / HL';
const PAST = ev('p1', T, '2026-10-01T15:00:00+08:00', '2026-10-01T17:00:00+08:00');
const PAST2 = ev('p2', T, '2026-09-24T10:00:00+08:00', '2026-09-24T12:00:00+08:00');
const NEXT = ev('n1', T, '2026-10-15T15:00:00+08:00', '2026-10-15T17:00:00+08:00');
const LATER = ev('n2', T, '2026-11-05T09:00:00+08:00', '2026-11-05T11:00:00+08:00');
const base = { requester: ME, event_id: '', authority: '', department: 'Audio Post', mode: 'prepare', confirmed: false, title: T, booking_date: '' };
const co = (w, req, wide, day = []) => new Function('$', '$input', code(w, 'Check Ownership'))(
  n => n === 'Find By Title' ? wrap([{ json: { items: wide } }]) : wrap([{ json: req }]), wrap([{ json: { items: day } }]))[0].json;

console.log('Cancel Booking v22 - the search window');
const curl = node(C, 'Find By Title').parameters.url;
ok(/timeMin=\{\{ encodeURIComponent\(DateTime\.now\(\)\.minus\(\{ days: 60 \}\)\.toISO\(\)\) \}\}/.test(curl), 'from 60 days back');
ok(/days: 450/.test(curl), 'still 450 days ahead');
console.log('Cancel Booking v22 - one match');
let r = co(C, base, [PAST]);
ok(r.verdict === 'PREPARED' && r.event_id === 'p1' && /\*Date:\* Thursday, October 1, 2026/.test(r.card_text), 'last week\'s booking by name -> its card', r);
ok(/Heads up: this booking has already passed\.\n\nConfirm to cancel\.$/.test(r.card_text), 'the card says it has passed', r.card_text);
ok(/timeMin=\{\{ encodeURIComponent\(DateTime\.now\(\)\.toISO\(\)\) \}\}/.test(node(OC, 'Find By Title').parameters.url), '  (v21: searched from now on, so last week was never found)');
r = co(C, base, [NEXT]);
ok(r.verdict === 'PREPARED' && r.event_id === 'n1' && !/already passed/.test(r.card_text), 'an upcoming booking -> its card, no heads-up', r.card_text);
console.log('Cancel Booking v22 - past and upcoming with one name');
r = co(C, base, [PAST, NEXT]);
const Q1 = 'There are two bookings named "RUNWAY / John Ableton / HL" - one coming up and one that has already passed:\n- Thursday, October 15, 2026, 3:00 PM – 5:00 PM, Studio 8\n- Thursday, October 1, 2026, 3:00 PM – 5:00 PM, Studio 8 (already passed)\nWhich one should I cancel?';
ok(r.reason === 'AMBIGUOUS_TITLE' && r.ask === Q1, 'one past + one upcoming -> asked, coming up first, the past one marked', r.ask);
ok(Array.isArray(r.matches) && r.matches.length === 2 && r.matches[0].passed === false && r.matches[1].passed === true, 'matches carry passed', r.matches);
r = co(C, base, [PAST2, LATER, PAST, NEXT]);
ok(/^There are four bookings named .* - two coming up and two that have already passed:\n- Thursday, October 15.*\n- Thursday, November 5.*\n- Thursday, October 1.*\(already passed\)\n- Thursday, September 24.*\(already passed\)\nWhich one should I cancel\?$/.test(r.ask), 'two and two -> soonest first, then most recent', r.ask);
r = co(C, base, [PAST, PAST2]);
ok(/^There are two bookings named .*, all already passed:/.test(r.ask), 'both past -> "all already passed"', r.ask);
r = co(C, base, [NEXT, LATER]);
ok(/^There are two bookings named "[^"]+":\n/.test(r.ask) && !/passed/.test(r.ask), 'both upcoming -> no past wording', r.ask);
const rj = new Function('$input', code(C, 'Return Rejection'))(wrap([{ json: co(C, base, [PAST, NEXT]) }]))[0].json;
ok(rj.status === 'REJECTED' && rj.ask === Q1 && rj.matches.length === 2, 'Return Rejection passes ask and matches to main', rj);
r = co(C, { ...base, booking_date: '2026-10-15' }, [PAST, NEXT], [NEXT]);
ok(r.verdict === 'PREPARED' && r.event_id === 'n1', 'a date given and the booking is on it -> that one, no question');
r = co(C, { ...base, title: 'NOPE / X / HL' }, [PAST, NEXT]);
ok(r.reason === 'NOT_ON_CALENDAR' && /in the last 60 days or coming up/.test(r.human), 'nothing by that name -> says where it looked', r.human);
r = co(C, { ...base, confirmed: true, check_code: 'x' }, [PAST]);
ok(r.verdict !== 'PREPARED', 'the yes (confirmed) is never searched by name', r.reason);

console.log('Find Booking v8');
const fsr = (w, req, wide, day = []) => new Function('$', '$input', code(w, 'Shape Results'))(
  n => n === 'Find By Title' ? wrap([{ json: { items: wide } }]) : wrap([{ json: req }]), wrap([{ json: { items: day } }]))[0].json;
const furl = node(F, 'Find By Title').parameters.url;
ok(/DateTime\.now\(\)\.minus\(\{ days: 60 \}\) : DateTime\.now\(\)/.test(furl), 'a name -> from 60 days back; no name -> from now (unchanged)');
let f = fsr(F, { title: 'RUNWAY', booking_date: '' }, [PAST, NEXT]);
ok(f.matches.length === 2 && f.upcoming.length === 1 && f.upcoming[0].id === 'n1', 'matches holds both; upcoming only the coming one', f);
ok(f.ask === Q1.replace('Which one should I cancel?', 'Which one do you mean?'), 'the same question (not tied to cancelling)', f.ask);
ok(/already passed/.test(f.human) && /Ask exactly this/.test(f.human), 'the model is told both and the question', f.human);
f = fsr(F, { title: 'RUNWAY', booking_date: '' }, [PAST]);
ok(f.matches.length === 1 && !f.ask && /already passed/.test(f.human), 'one past booking -> listed as passed, no question', f.human);
ok(fsr(OF, { title: 'RUNWAY', booking_date: '' }, [NEXT]).upcoming.length === 1, '  (v7 still lists upcoming - same key kept)');
f = fsr(F, { title: 'RUNWAY', booking_date: '' }, [PAST, ev('o1', 'RUNWAY 2 / Spotify / HL', '2026-10-20T10:00:00+08:00', '2026-10-20T12:00:00+08:00')]);
ok(/named "RUNWAY"/.test(f.ask) && /- RUNWAY 2 \/ Spotify \/ HL, Tuesday, October 20/.test(f.ask), 'different titles -> each line carries its title', f.ask);

console.log('main v221 Guard Probe');
const gp = (W, output, steps) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: 'cancel runway', bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: {} }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(recM(n) || [{ json: {} }]))[0].json.output;
const FIND = { action: { tool: 'Find_Booking' }, observation: JSON.stringify([fsr(F, { title: 'RUNWAY', booking_date: '' }, [PAST, NEXT])]) };
let o = gp(M, 'You have a RUNWAY booking on October 15. Do you want to cancel it?', [FIND]);
ok(o === Q1.replace('Which one should I cancel?', 'Which one do you mean?'), 'the model mentions only the upcoming one -> the question with both', o);
ok(/^You have a RUNWAY booking on October 15/.test(gp(OM, 'You have a RUNWAY booking on October 15. Do you want to cancel it?', [FIND])), '  (v220: the past one never mentioned)');
o = gp(M, 'There are two RUNWAY bookings: October 15 (coming up) and October 1 (already passed). Which one?', [FIND]);
ok(/^There are two RUNWAY bookings: October 15/.test(o), 'the model names both -> its reply stands', o);
const card = co(C, { ...base, booking_date: '2026-10-15' }, [], [NEXT]);
const PC = { action: { tool: 'Prepare_Cancel' }, observation: JSON.stringify([{ status: 'PREPARED', event_id: 'n1', title: T, card_text: card.card_text, human: 'x' }]) };
o = gp(M, 'x', [FIND, PC]);
ok(/\*Date:\* Thursday, October 15, 2026/.test(o) && /_Also named "RUNWAY \/ John Ableton \/ HL": Thursday, October 1, 2026, 3:00 PM – 5:00 PM, Studio 8 \(already passed\)\._/.test(o), 'the model chose the upcoming one -> the card says the past one exists', o);
ok(!/_Also named/.test(gp(M, 'x', [PC])), 'a card with no duplicate -> unchanged');
const RJ = { action: { tool: 'Prepare_Cancel' }, observation: JSON.stringify([rj]) };
o = gp(M, 'Nothing was cancelled. Which date?', [RJ]);
ok(o === Q1, 'Prepare Cancel\'s own question goes out word for word', o);
// the card with the extra line still cancels exactly the card's booking at the yes
const withAlso = gp(M, 'x', [FIND, PC]);
const d = new Function('$', '$input', code(M, 'Prepared Cancel'))(n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel: true, gate: { saidYes: true } } }])
  : n === 'Get Recent Messages' ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text: withAlso, ts: String(Date.now() / 1000 - 30) } }]) : wrap([{ json: {} }]),
  wrap([{ json: {} }]))[0].json._cancelDirect || {};
ok(d.use === true && d.booking_date === '2026-10-15', 'the yes to that card cancels 15 Oct, not the past one', d);
const yes = (W, txt) => new Function('$', '$input', code(W, 'Prepared Cancel'))(n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel: true, gate: { saidYes: true } } }])
  : n === 'Get Recent Messages' ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text: txt, ts: String(Date.now() / 1000 - 30) } }]) : wrap([{ json: {} }]),
  wrap([{ json: {} }]))[0].json._cancelDirect || {};
const pastCard = co(C, base, [PAST]).card_text.replace(/Confirm to cancel\.$/, 'Cancel it? Reply yes or no.');
ok(yes(M, pastCard).use === true && yes(M, pastCard).booking_date === '2026-10-01', 'a yes to the past card (with its heads-up) cancels 1 Oct in code', yes(M, pastCard));
ok(yes(OM, pastCard).use === false, '  (v220: the heads-up line would have sent the yes to the model)');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
