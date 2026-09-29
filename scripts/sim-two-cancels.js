#!/usr/bin/env node
// Offline tests for main v187 (PENDING 55 two cancels, QA bug 15 start time). No calendar is touched.
//
//   node scripts/sim-two-cancels.js <main-execution.json>
//
// The execution is a real main turn (29 Sep exec 16739: "qamove - november 17 / qatime - nov 16", two Prepare Cancel
// calls). Cards are rendered by Cancel Booking v19 itself, so the whole chain is real code: two cards prepared ->
// Guard Probe shows the first with the second queued -> the yes -> Prepared Cancel reads the queue -> Cancel Direct
// Reply shows the next card -> Prepared Cancel accepts that card at the next yes.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v187.json'), OLD = WF('project-jessie-v186.json'), C = WF('cancel-booking-v19.json');
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;

const ME = 'U08V3CKDGJF', S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const ev = (id, summary, s, e) => ({ id, summary, status: 'confirmed', description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: ' + ME + ' | Dept: Audio Post',
  start: { dateTime: s }, end: { dateTime: e }, attendees: [{ email: S8, displayName: 'KDC Plaza-Top Level-Studio 8 (7)', resource: true }], location: 'KDC Plaza-Top Level-Studio 8 (7)' });
const QM = ev('qm', 'QAMOVE / Jem Lim / DR', '2027-11-17T15:00:00+08:00', '2027-11-17T17:00:00+08:00');
const QT = ev('qt', 'QATIME / Jem Lim / DR', '2027-11-16T14:00:00+08:00', '2027-11-16T16:00:00+08:00');
const QN = ev('qn', 'QANEW / Jem Lim / DR', '2027-11-18T15:00:00+08:00', '2027-11-18T17:00:00+08:00');
const base = { requester: ME, event_id: '', authority: '', department: 'Audio Post' };
const co = (req, items) => new Function('$', '$input', code(C, 'Check Ownership'))(() => ({ first: () => ({ json: req }) }), { first: () => ({ json: { items } }) })[0].json;
const prep = (e) => co({ ...base, mode: 'prepare', confirmed: false, title: e.summary, booking_date: e.start.dateTime.slice(0, 10) }, [e]);
const cardM = prep(QM).card_text, cardT = prep(QT).card_text, cardN = prep(QN).card_text;
ok(/_check [0-9a-f]{8}_/.test(cardM) && /_check [0-9a-f]{8}_/.test(cardT), 'Cancel Booking v19 renders both cards');

// Guard Probe with the recorded inputs; Gate Context / Slack Trigger / Booked For overridable
const gp = (w, output, steps, over = {}) => new Function('$input', '$', code(w, 'Guard Probe'))(
  wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
  n => over[n] ? wrap([{ json: over[n] }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
const st = (tool, o) => ({ action: { tool }, observation: JSON.stringify([o]) });
const P = c => ({ status: 'PREPARED', card_text: c });

console.log('Guard Probe - two cards prepared in one turn');
let out = gp(M, 'x', [st('Find_Booking', []), st('Find_Booking', []), st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardT))]);
ok(out.startsWith('*QAMOVE / Jem Lim / DR*') && /\*Date:\* Wednesday, November 17, 2027/.test(out), 'the first card asked for is shown (QAMOVE)', out);
ok(/_check [0-9a-f]{8}_\n_Next: QATIME \/ Jem Lim \/ DR on Tuesday, November 16, 2027 - I'll show it after this one\._/.test(out), 'the second is queued under the check code', out);
ok(/Cancel it\? Reply yes or no\.$/.test(out) && (out.match(/_check /g) || []).length === 1, 'one check code, one confirmation line', out);
let old = gp(OLD, 'x', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardT))]);
ok(old.startsWith('*QATIME') && !/_Next:/.test(old), '  (v186: only the last card, nothing about the other)', old.slice(0, 60));
out = gp(M, 'x', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardM))]);
ok(!/_Next:/.test(out), 'the same card prepared twice -> one card, nothing queued');
out = gp(M, 'x', [st('Prepare_Cancel', P(cardM))]);
ok(out.startsWith('*QAMOVE') && !/_Next:/.test(out), 'one card -> exactly as before');
out = gp(M, 'Which one did you mean?', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', { status: 'REJECTED', reason: 'AMBIGUOUS_TITLE', human: 'x' })]);
ok(!/_check /.test(out), 'the latest cancel call refused -> no card (as before)', out);
const three = gp(M, 'x', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardT)), st('Prepare_Cancel', P(cardN))]);
ok((three.match(/^_Next: /gm) || []).length === 2, 'three cards -> the first shown, two queued', three);

console.log('The yes - Prepared Cancel reads the queue, Cancel Direct Reply shows the next card');
const sent = gp(M, 'x', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardT))]);
const pcRun = text => new Function('$', '$input', code(M, 'Prepared Cancel'))(
  n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel: true, gate: { saidYes: true } } }]) : n === 'Get Recent Messages'
    ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text, ts: String(Date.now() / 1000 - 60) } }]) : wrap(rec(n) || []),
  wrap([{ json: {} }]))[0].json._cancelDirect;
let d = pcRun(sent);
ok(d.use === true && d.title === 'QAMOVE / Jem Lim / DR' && d.booking_date === '2027-11-17', 'the yes cancels the card shown (QAMOVE)', d);
ok(JSON.stringify(d.next) === JSON.stringify([{ title: 'QATIME / Jem Lim / DR', date_text: 'Tuesday, November 16, 2027', booking_date: '2027-11-16' }]), 'the queue is read back: QATIME, 2027-11-16', d.next);
ok(co({ ...base, confirmed: true, title: d.title, booking_date: d.booking_date, check_code: d.check_code }, [QM]).verdict === 'CLEAR', "Cancel Booking still accepts the first card's code (the queue line does not break it)");
ok(JSON.stringify(pcRun(gp(M, 'x', [st('Prepare_Cancel', P(cardM))])).next) === '[]', 'no queue -> next is empty');

const reply = (cd, nx, q) => new Function('$input', '$', code(M, 'Cancel Direct Reply'))(wrap([{ json: nx || cd }]),
  n => n === 'Cancel Direct' ? wrap([{ json: cd }]) : n === 'Prepared Cancel' ? wrap([{ json: { _cancelDirect: { next: q } } }])
     : n === 'Prepare Next Cancel' ? (nx ? wrap([{ json: nx }]) : (() => { throw new Error('unexecuted'); })()) : wrap([{ json: {} }]))[0].json;
const DONE = { status: 'CANCELLED', human: 'Cancelled "QAMOVE / Jem Lim / DR".' };
// Prepare Next Cancel runs Cancel Booking in prepare mode with next[0]:
const nx = prep(QT);
let r = reply(DONE, nx, d.next);
ok(r.output.startsWith('Cancelled "QAMOVE / Jem Lim / DR".\n\nNext:\n\n*QATIME / Jem Lim / DR*'), 'reply: cancelled, then the next card', r.output);
ok(/Cancel it\? Reply yes or no\.$/.test(r.output) && !/Reply only with/.test(r.output) && r.directCancel.nextShown === 'QATIME / Jem Lim / DR', 'the next card ends in the one-line confirmation', r.output);
const d2 = pcRun(r.output);
ok(d2.use === true && d2.title === 'QATIME / Jem Lim / DR' && d2.booking_date === '2027-11-16' && JSON.stringify(d2.next) === '[]', 'the next yes cancels QATIME, nothing left queued', d2);
ok(co({ ...base, confirmed: true, title: d2.title, booking_date: d2.booking_date, check_code: d2.check_code }, [QT]).verdict === 'CLEAR', "Cancel Booking accepts the second card's code");
// three: after the first yes, the next card carries the third as its queue
const d3 = pcRun(three);
r = reply(DONE, prep(QT), d3.next);
ok((r.output.match(/^_Next: QANEW \/ Jem Lim \/ DR on Thursday, November 18, 2027/gm) || []).length === 1, 'three: the second card carries the third in its queue', r.output);
const d4 = pcRun(r.output);
ok(d4.title === 'QATIME / Jem Lim / DR' && d4.next.length === 1 && d4.next[0].booking_date === '2027-11-18', 'three: the second yes cancels QATIME and queues QANEW', d4);
r = reply(DONE, { status: 'REJECTED', reason: 'NOT_ON_CALENDAR', human: 'Nothing was cancelled - call Cancel Booking again' }, d.next);
ok(/I couldn't get "QATIME \/ Jem Lim \/ DR" \(Tuesday, November 16, 2027\) ready to cancel, so it is untouched\. Ask me again for it\./.test(r.output) && !/call Cancel/.test(r.output), 'the next one cannot be prepared -> says so plainly, no tool instructions', r.output);
r = reply({ status: 'REJECTED', reason: 'CHANGED' }, nx, d.next);
ok(/changed since I showed it/.test(r.output) && /Next:\n\n\*QATIME/.test(r.output), 'the first fails -> its reason, then the next card still');
r = reply(DONE, null, []);
ok(r.output === 'Cancelled "QAMOVE / Jem Lim / DR".', 'no queue -> the reply exactly as before', r.output);

console.log('Wiring');
const to = (n, b = 0) => ((((M.connections[n] || {}).main || [])[b]) || []).map(t => t.node);
ok(JSON.stringify(to('Cancel Direct')) === '["Next Cancel?"]' && JSON.stringify(to('Next Cancel?', 0)) === '["Prepare Next Cancel"]'
   && JSON.stringify(to('Next Cancel?', 1)) === '["Cancel Direct Reply"]' && JSON.stringify(to('Prepare Next Cancel')) === '["Cancel Direct Reply"]'
   && JSON.stringify(to('Cancel Direct Reply')) === '["Send Reply"]', 'Cancel Direct -> Next Cancel? -> (Prepare Next Cancel) -> Cancel Direct Reply -> Send Reply');
const pn = node(M, 'Prepare Next Cancel'), pv = pn.parameters.workflowInputs.value;
ok(pn.parameters.workflowId.value === 'bAyDw7udhmY0NL38' && pv.mode === 'prepare' && pv.confirmed === '={{ false }}' && pv.event_id === '' && pn.onError === 'continueRegularOutput',
   'Prepare Next Cancel: Cancel Booking, prepare mode, never confirmed, no event id, cannot fail the turn');
const cond = node(M, 'Next Cancel?').parameters.conditions.conditions[0].leftValue;
ok(new Function('$', 'return ' + cond.replace(/^=\{\{|\}\}$/g, ''))(() => wrap([{ json: { _cancelDirect: { next: [{}] } } }])) === 'yes'
   && new Function('$', 'return ' + cond.replace(/^=\{\{|\}\}$/g, ''))(() => wrap([{ json: { _cancelDirect: { use: true } } }])) === 'no', 'Next Cancel? is yes only when something is queued');

console.log('Guard Probe - QA bug 15, a start time and no end');
const G = { startOnlyNotice: 'THEY GAVE A START TIME AND NO END TIME.', dateNotice: '', pastDateNotice: '' };
const ask = t => ({ 'Gate Context': G, 'Slack Trigger': { text: t, user: ME }, 'Booked For': { requesterText: t } });
const RA = [st('Room_Availability', { status: 'OK', asked: { room: 'Studio 7', status: 'FREE' } })];
out = gp(M, 'Studio 7 is free next Thursday, October 7 from 2:00 PM to 4:00 PM.', RA, ask('is studio 7 free next thursday at 2pm?'));
ok(out === 'Studio 7 is free next Thursday, October 7 at 2:00 PM (checked until 4:00 PM).\n\nHow long do you need it?', 'exec 15881: "from 2:00 PM to 4:00 PM" -> "at 2:00 PM (checked until 4:00 PM)", asks how long', out);
old = gp(OLD, 'Studio 7 is free next Thursday, October 7 from 2:00 PM to 4:00 PM.', RA, ask('is studio 7 free next thursday at 2pm?'));
ok(/from 2:00 PM to 4:00 PM/.test(old), '  (v186: the invented end went out)');
out = gp(M, 'Yes, Studio 7 is free from 2:00 PM – 4:00 PM. How long will you need it?', RA, ask('is studio 7 free at 2pm next wednesday'));
ok(/free at 2:00 PM \(checked until 4:00 PM\)\. How long will you need it\?$/.test(out) && (out.match(/\?/g) || []).length === 1, 'en dash form; a question already asked is not asked twice', out);
out = gp(M, 'Studio 7 is free from 2:00 PM to 4:00 PM.', RA, { ...ask('is studio 7 free next thursday 2pm to 4pm?') });
ok(out === 'Studio 7 is free from 2:00 PM to 4:00 PM.', 'both times typed -> untouched', out);
out = gp(M, 'Studio 7 is free from 2:00 PM to 4:00 PM.', RA, { 'Gate Context': { ...G, startOnlyNotice: '' }, 'Slack Trigger': { text: 'is studio 7 free at 2pm?' } });
ok(out === 'Studio 7 is free from 2:00 PM to 4:00 PM.', 'no start-only notice -> untouched');
out = gp(M, 'Studio 7 is taken from 1:00 PM to 3:00 PM by NET-KUBA. Studio 8 is free at 2:00 PM.', RA, ask('is studio 7 free at 2pm?'));
ok(/taken from 1:00 PM to 3:00 PM/.test(out), "someone else's booking keeps its real times", out);
out = gp(M, 'Studio 7 is free from 12:00 PM to 2:00 PM.', RA, ask('is studio 7 free at 12nn tomorrow?'));
ok(/free at 12:00 PM \(checked until 2:00 PM\)/.test(out), '"12nn" counts as the start typed', out);
out = gp(M, 'Studio 7 is free from 3:00 PM to 5:00 PM.', RA, ask('is studio 7 free at 2pm?'));
ok(out === 'Studio 7 is free from 3:00 PM to 5:00 PM.', 'a window that does not start at their time (an alternative) is left alone', out);

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
