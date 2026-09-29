#!/usr/bin/env node
// Offline tests for Cancel Booking v20 + main v190 (PENDING 56: a cancel with no date, or the wrong one; the series
// "Engineer: Engineer:" label). No calendar is touched.
//
//   node scripts/sim-cancel-by-title.js <main-execution.json>
//
// The main execution supplies real inputs for Guard Probe (29 Sep exec 16739 works). Cards are rendered by Cancel
// Booking itself and read back by main's Prepared Cancel, so the round trip is real code end to end.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
const C = WF(process.env.CANCEL || 'cancel-booking-v20.json'), OLDC = WF('cancel-booking-v19.json');
const M = WF(process.env.MAIN || 'project-jessie-v190.json'), OLDM = WF('project-jessie-v189.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const ME = 'U08V3CKDGJF', S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const ev = (id, summary, s, e, ref = ME) => ({ id, summary, status: 'confirmed', start: { dateTime: s }, end: { dateTime: e },
  attendees: [{ email: S8, displayName: 'KDC Plaza-Top Level-Studio 8 (7)', resource: true }], location: 'KDC Plaza-Top Level-Studio 8 (7)',
  description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: ' + ref + ' | Dept: Audio Post' });
const QN = ev('qn', 'QANEW / Jem Lim / DR', '2027-11-18T15:00:00+08:00', '2027-11-18T17:00:00+08:00');
const QM1 = ev('qm1', 'QAMOVE / Jem Lim / DR', '2027-10-01T09:00:00+08:00', '2027-10-01T11:00:00+08:00');
const QM2 = ev('qm2', 'QAMOVE / Jem Lim / DR', '2027-11-17T15:00:00+08:00', '2027-11-17T17:00:00+08:00');
const M1 = ev('m1', 'M1 - Rico', '2027-11-21T00:00:00+08:00', '2027-11-22T00:00:00+08:00', 'U026LMLM4');
const base = { requester: ME, event_id: '', authority: '', department: 'Audio Post' };
const co = (w, req, day, wide) => new Function('$', '$input', code(w, 'Check Ownership'))(
  n => n === 'Find By Title' ? wrap([{ json: { items: wide || [] } }]) : wrap([{ json: req }]), wrap([{ json: { items: day } }]))[0].json;

console.log('Cancel Booking v20 - the title is not on the date given');
let r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '2027-11-21' }, [M1], [QN]);
ok(r.verdict === 'PREPARED' && r.event_id === 'qn' && /\*Date:\* Thursday, November 18, 2027/.test(r.card_text), 'exec 16715: "cancel QANEW" looked up on 21 Nov -> the card for 18 Nov', r);
ok(co(OLDC, { ...base, mode: 'prepare', confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '2027-11-21' }, [M1], [QN]).reason === 'NOT_ON_CALENDAR', '  (v19: NOT_ON_CALENDAR)');
r = co(C, { ...base, confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '2027-11-21' }, [M1], [QN]);
ok(r.verdict === 'PREPARED' && r.event_id === 'qn', 'an unconfirmed Cancel Booking call (not only Prepare Cancel) is searched too');
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QAMOVE / Jem Lim / DR', booking_date: '2027-11-18' }, [QN], [QM1, QM2]);
ok(r.reason === 'AMBIGUOUS_TITLE' && /Friday, October 1, 2027 \(9:00 AM\)/.test(r.human) && /Wednesday, November 17, 2027 \(3:00 PM\)/.test(r.human) && /Ask which date/.test(r.human), 'exec 16735: two upcoming QAMOVE -> both dates listed, ask which', r.human);
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QAMOVE / Jem Lim / DR', booking_date: '2027-11-17' }, [QN, QM2], [QM1, QM2]);
ok(r.verdict === 'PREPARED' && r.event_id === 'qm2', 'the title IS on the date given -> that one, the upcoming search is not used');
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QATHEIRS / X / TL', booking_date: '2027-11-21' }, [], [ev('t1', 'QATHEIRS / X / TL', '2027-11-19T10:00:00+08:00', '2027-11-19T11:00:00+08:00', 'U999')]);
ok(r.reason === 'NOT_YOURS', "someone else's booking found this way -> NOT_YOURS, no card", r.reason);

console.log('No date at all');
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '' }, [], [QN]);
ok(r.verdict === 'PREPARED' && /November 18, 2027/.test(r.card_text), 'a title alone -> the card with its date (was MISSING_DATE)', r);
ok(co(OLDC, { ...base, mode: 'prepare', confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '' }, [], [QN]).reason === 'MISSING_DATE', '  (v19: MISSING_DATE)');
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'NOPE / X / DR', booking_date: '' }, [], [QN]);
ok(r.reason === 'NOT_ON_CALENDAR' && /no upcoming booking is titled exactly "NOPE \/ X \/ DR"/.test(r.human), 'nothing by that title -> says so, asks for the date', r.human);
r = co(C, { ...base, confirmed: true, title: 'QANEW / Jem Lim / DR', booking_date: '', check_code: 'abcd1234' }, [], [QN]);
ok(r.reason === 'MISSING_DATE', 'a confirmed cancel (the yes) still needs its date - never searched', r.reason);
r = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QA', booking_date: '' }, [], [QN, QM1]);
ok(r.verdict !== 'PREPARED', 'a partial title never matches an upcoming booking (exact titles only)', r.reason);

console.log('The round trip - card from the upcoming search, yes cancels exactly it');
const card = co(C, { ...base, mode: 'prepare', confirmed: false, title: 'QANEW / Jem Lim / DR', booking_date: '2027-11-21' }, [M1], [QN]).card_text;
const sent = card.replace(/\n\nReply only with[^\n]*\nConfirm to cancel\.$/, '\n\nCancel it? Reply yes or no.');
const d = new Function('$', '$input', code(M, 'Prepared Cancel'))(n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel: true, gate: { saidYes: true } } }])
  : n === 'Get Recent Messages' ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text: sent, ts: String(Date.now() / 1000 - 30) } }]) : wrap([{ json: {} }]),
  wrap([{ json: {} }]))[0].json._cancelDirect;
ok(d.use === true && d.booking_date === '2027-11-18', 'main reads 18 Nov off the card', d);
r = co(C, { ...base, confirmed: true, title: d.title, booking_date: d.booking_date, check_code: d.check_code }, [QN], []);
ok(r.verdict === 'CLEAR' && r.event_id === 'qn' && r.matched_on === 'card', 'the yes cancels exactly that booking', r);

console.log('Find By Title - when it searches');
const fb = node(C, 'Find By Title'), url = fb.parameters.url;
ok(/[?&]q=\{\{ encodeURIComponent\(String\(\(\$\('When Executed by Another Workflow'\)\.first\(\)\.json\)\.title/.test(url) && /days: 450/.test(url) && /minutes: 1/.test(url), 'searches by title about 15 months ahead; a 1-minute window when it is not needed');
ok(/mode \|\| ''\)\.toLowerCase\(\) === 'prepare' \|\| String\(\(\$\('When Executed by Another Workflow'\)\.first\(\)\.json\)\.confirmed\)\.toLowerCase\(\) !== 'true'/.test(url), 'only when preparing a card (prepare mode or unconfirmed)');
ok(fb.onError === 'continueRegularOutput' && fb.alwaysOutputData === true, 'a failed search cannot fail the cancel');
const to = (w, n) => ((((w.connections[n] || {}).main || [])[0]) || []).map(t => t.node);
ok(JSON.stringify(to(C, 'When Executed by Another Workflow')) === '["Find By Title"]' && JSON.stringify(to(C, 'Find By Title')) === '["List Day Events"]' && JSON.stringify(to(C, 'List Day Events')) === '["Check Ownership"]', 'wiring: trigger -> Find By Title -> List Day Events -> Check Ownership (its input is still the day)');
ok(!/\$json/.test(node(C, 'List Day Events').parameters.url) && /toISODate\(\)/.test(node(C, 'List Day Events').parameters.url), 'the day query reads the date from the trigger, today when none');

console.log('main v190');
const pcd = node(M, 'Prepare Cancel').parameters.workflowInputs.value.booking_date;
ok(/Never guess a date\.', 'string', ''\)/.test(pcd), "Prepare Cancel's date is optional: leave it empty rather than guess");
{ const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
  const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
  const gp = (w, output) => new Function('$input', '$', code(w, 'Guard Probe'))(wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: [] } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
  const S = 'Here is the series:\n*Engineer:* Engineer: Daryl Reyes\n*Arranger:* Arranger: Brian Cua\n*Client:* Jem Lim';
  const o = gp(M, S);
  ok(/\*Engineer:\* Daryl Reyes\n\*Arranger:\* Brian Cua\n\*Client:\* Jem Lim/.test(o) && !/Engineer:\*? Engineer:/.test(o), 'series: "*Engineer:* Engineer: Daryl Reyes" -> "*Engineer:* Daryl Reyes"', o);
  ok(/Engineer:\*? Engineer:/.test(gp(OLDM, S)), '  (v189: the label twice)');
  ok(/\*Engineer:\* Daryl Reyes \(Post Engineer\)/.test(gp(M, '*Engineer:* Daryl Reyes (Post Engineer)')), 'a normal line is left alone'); }

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
