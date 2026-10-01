#!/usr/bin/env node
// Offline tests for Cancel Booking v21 + main v204 (PENDING 69: short cancel + series cards). No calendar is touched.
//
//   node scripts/sim-short-cards.js <main-execution.json>
//
// Same harness as sim-two-cancels (a real main turn, exec 16739). Cards are rendered by Cancel Booking v21 itself:
// no `_check` line -> Guard Probe queues the second card above the confirmation -> the yes -> Prepared Cancel passes
// the card's time and room -> Cancel Booking v21 cancels only the booking still showing them. Old coded cards (sent
// before the import) still work end to end. Then a model-written series summary is cut to the short card.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v204.json'), C = WF(process.env.CANCEL || 'cancel-booking-v21.json'), C20 = WF('cancel-booking-v20.json');
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;

const ME = 'U08V3CKDGJF', OTHER = 'U0OTHER0001', S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const ev = (id, summary, s, e, ref = ME) => ({ id, summary, status: 'confirmed', description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: ' + ref + ' | Dept: Audio Post',
  start: { dateTime: s }, end: { dateTime: e }, attendees: [{ email: S8, displayName: 'KDC Plaza-Top Level-Studio 8 (7)', resource: true }], location: 'KDC Plaza-Top Level-Studio 8 (7)' });
const QM = ev('qm', 'QAMOVE / Jem Lim / DR', '2027-11-17T15:00:00+08:00', '2027-11-17T17:00:00+08:00');
const QT = ev('qt', 'QATIME / Jem Lim / DR', '2027-11-16T14:00:00+08:00', '2027-11-16T16:00:00+08:00');
const QMlater = { ...QM, start: { dateTime: '2027-11-17T16:00:00+08:00' }, end: { dateTime: '2027-11-17T18:00:00+08:00' } };
const base = { requester: ME, event_id: '', authority: '', department: 'Audio Post' };
const coW = (w, req, items) => new Function('$', '$input', code(w, 'Check Ownership'))(() => ({ first: () => ({ json: req }) }), { first: () => ({ json: { items } }) })[0].json;
const co = (req, items) => coW(C, req, items);
const prep = (e, w = C) => coW(w, { ...base, mode: 'prepare', confirmed: false, title: e.summary, booking_date: e.start.dateTime.slice(0, 10) }, [e]);

console.log('Cancel Booking v21 - the card');
const cardM = prep(QM).card_text, cardT = prep(QT).card_text;
ok(!/_check/.test(cardM) && /^\*QAMOVE \/ Jem Lim \/ DR\*\n\*Date:\* .+\n\*Time:\* .+\n\*Room:\* .+\n\nConfirm to cancel\.$/.test(cardM), 'title, date, time, room - no code, no "Booked by" on your own booking', cardM);
const foreign = ev('qf', 'QAFOREIGN / Jem Lim / DR', '2027-11-17T10:00:00+08:00', '2027-11-17T11:00:00+08:00', OTHER);
const fc = coW(C, { ...base, mode: 'prepare', confirmed: false, authority: 'HAIST Dev', title: foreign.summary, booking_date: '2027-11-17' }, [foreign]);
ok(/\*Booked by:\*/.test(fc.card_text || ''), "someone else's booking (dev authority) -> the card says who booked it", fc);
ok(node(C, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'card_time'), 'trigger takes card_time / card_room');

console.log('Guard Probe + Prepared Cancel + Cancel Booking v21 - the yes');
const gp = (output, steps) => new Function('$input', '$', code(M, 'Guard Probe'))(
  wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
const st = (tool, o) => ({ action: { tool }, observation: JSON.stringify([o]) });
const P = c => ({ status: 'PREPARED', card_text: c });
let out = gp('x', [st('Prepare_Cancel', P(cardM))]);
ok(out.startsWith('*QAMOVE') && /Cancel it\? Reply yes or no\.$/.test(out) && !/_check/.test(out), 'one card sent short, one-line confirmation', out);
const two = gp('x', [st('Prepare_Cancel', P(cardM)), st('Prepare_Cancel', P(cardT))]);
ok(/\*Room:\* .+\n_Next: QATIME \/ Jem Lim \/ DR on Tuesday, November 16, 2027 - I'll show it after this one\._\n\nCancel it\? Reply yes or no\.$/.test(two), 'two cards: the second queued above the confirmation', two);
const pcRun = text => new Function('$', '$input', code(M, 'Prepared Cancel'))(
  n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel: true, gate: { saidYes: true } } }]) : n === 'Get Recent Messages'
    ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text, ts: String(Date.now() / 1000 - 60) } }]) : wrap(rec(n) || []),
  wrap([{ json: {} }]))[0].json._cancelDirect;
let d = pcRun(two);
ok(d.use === true && d.title === 'QAMOVE / Jem Lim / DR' && d.booking_date === '2027-11-17' && !d.check_code && d.card_time && d.card_room, 'the yes: title, date, the card\'s time and room', d);
ok(JSON.stringify(d.next) === JSON.stringify([{ title: 'QATIME / Jem Lim / DR', date_text: 'Tuesday, November 16, 2027', booking_date: '2027-11-16' }]), 'the queue is read back', d.next);
const yes = (dd, items, w = C) => coW(w, { ...base, confirmed: true, title: dd.title, booking_date: dd.booking_date, check_code: dd.check_code, card_time: dd.card_time, card_room: dd.card_room }, items);
ok(yes(d, [QM]).verdict === 'CLEAR', 'Cancel Booking v21 cancels the booking still showing that time and room');
ok(yes(d, [QMlater]).verdict !== 'CLEAR', 'moved since the card was shown -> refused', yes(d, [QMlater]).verdict);
const QMroom = { ...QM, attendees: [], location: '' };
ok(yes(d, [QMroom]).verdict !== 'CLEAR', 'room changed since the card -> refused', yes(d, [QMroom]).verdict);
const twin = { ...QMlater, id: 'qm2' };
const r2 = yes(d, [twin, QM]);
ok(r2.verdict === 'CLEAR' && (r2.event_id || (r2.event || {}).id || JSON.stringify(r2).includes('"qm"')), 'two of that title that day -> the one on the card', r2);
const notMine = { ...QM, description: QM.description.replace(ME, OTHER) };
ok(yes(d, [notMine]).verdict !== 'CLEAR', 'ownership still checked (NOT_YOURS)', yes(d, [notMine]).verdict);

console.log('Cancel Direct Reply - the next card');
const reply = (cd, nx, q) => new Function('$input', '$', code(M, 'Cancel Direct Reply'))(wrap([{ json: nx || cd }]),
  n => n === 'Cancel Direct' ? wrap([{ json: cd }]) : n === 'Prepared Cancel' ? wrap([{ json: { _cancelDirect: { next: q } } }])
     : n === 'Prepare Next Cancel' ? (nx ? wrap([{ json: nx }]) : (() => { throw new Error('unexecuted'); })()) : wrap([{ json: {} }]))[0].json;
const r = reply({ status: 'CANCELLED', human: 'Cancelled "QAMOVE / Jem Lim / DR".' }, prep(QT), d.next);
ok(r.output.startsWith('Cancelled "QAMOVE / Jem Lim / DR".\n\nNext:\n\n*QATIME') && /Cancel it\? Reply yes or no\.$/.test(r.output) && !/_check/.test(r.output), 'cancelled, then the next short card', r.output);
const d2 = pcRun(r.output);
ok(d2.use === true && d2.title === 'QATIME / Jem Lim / DR' && yes(d2, [QT]).verdict === 'CLEAR', 'the next yes cancels QATIME', d2);
const rq = reply({ status: 'CANCELLED', human: 'Cancelled "QAMOVE / Jem Lim / DR".' }, prep(QT), [d.next[0], { title: 'QANEW / Jem Lim / DR', date_text: 'Thursday, November 18, 2027', booking_date: '2027-11-18' }]);
ok(/\*Room:\* .+\n_Next: QANEW .+\n\nCancel it\? Reply yes or no\.$/.test(rq.output), 'three: the third queued under the next card', rq.output);

console.log('Gate Context - a short card counts as a cancel card');
const gsrc = code(M, 'Gate Context'), gl = gsrc.split('\n').find(l => l.trim().startsWith('const _cancelCard')).trim();
const cc = lastBotText => new Function('lastBotText', gl + '\nreturn _cancelCard;')(lastBotText);
ok(cc(out) === true, 'short card -> cancel card');
ok(cc(prep(QM, C20).card_text.replace(/\n*Reply only[^\n]*\nConfirm to cancel\.$/, '\n\nCancel it? Reply yes or no.')) === true, 'old coded card -> still a cancel card');
ok(cc('*QAMOVE*\n*Date:* x\n*Time:* y\n*Room:* z\n\nBook it? Reply yes or no.') === false, 'a booking card is not');

console.log('Old coded cards (sent before the import) still work');
const oldCard = gp('x', [st('Prepare_Cancel', P(prep(QM, C20).card_text))]);
ok(/_check [0-9a-f]{8}_/.test(oldCard), 'v20 card keeps its code through Guard Probe');
const dO = pcRun(oldCard);
ok(dO.use === true && /^[0-9a-f]{8}$/.test(dO.check_code) && !dO.card_time, 'the yes passes the code (not time/room)', dO);
ok(yes(dO, [QM]).verdict === 'CLEAR' && yes(dO, [QMlater]).verdict !== 'CLEAR', 'v21 verifies the code as v20 did');
ok(yes(d, [QM], C20).verdict === 'CLEAR', '(v20 with a short-card yes: falls back to title + date - safe while the two imports land)', yes(d, [QM], C20).verdict);
ok(pcRun('*QAMOVE / Jem Lim / DR*\n*Date:* Wednesday, November 17, 2027\n\nCancel it? Reply yes or no.').use !== true, 'a card with no code and no time/room lines -> not used directly');

ok(pcRun(cardM.replace('*Room:*', '*Engineer:* Daryl Reyes\n*Room:*')).use !== true, 'a card with lines Cancel Booking never writes (the model wrote it) -> the model handles it, as before');
console.log('Guard Probe - series summary cut to the short card');
const ser = ['Here is the recurring booking for QAMD:', '', '*QAMD / Jem Lim / DR*', '*Client:* Jem Lim', '*Project:* QAMD', '*Session Type:* VO Recording',
  '*Engineer:* Daryl Reyes', '*Department:* Audio Post', '*Booking Type:* Advertising', '*Booked by:* Howard Luistro',
  '*Dates (3):*', '• Monday, November 8, 2027', '• Monday, November 15, 2027', '• Monday, November 22, 2027', '*Time:* 2:00 PM – 4:00 PM', '*Room:* Studio 8', '', 'Confirm to book.'].join('\n');
const so = gp(ser, [st('Expand_Series', { status: 'OK', dates: ['2027-11-08', '2027-11-15', '2027-11-22'] })]);
ok(so.startsWith('*QAMD / Jem Lim / DR*\n*Dates (3):*'), 'starts at the title, details dropped', so);
ok(/• Monday, November 22, 2027\n\*Time:\* 2:00 PM – 4:00 PM\n\*Room:\* Studio 8/.test(so) && !/Client:|Engineer:|Session Type:|Department:|Booking Type:|Booked by:/.test(so), 'dates, time and room kept', so);
ok(/(Book it\? Reply yes or no\.|Confirm to book\.)$/.test(so), 'confirmation kept', so);
const serFor = gp(ser.replace('*Booked by:* Howard Luistro', '*Booked by:* Howard Luistro (for Tara Lim)'), [st('Expand_Series', { status: 'OK' })]);
ok(/\*Booked by:\* Howard Luistro \(for Tara Lim\)/.test(serFor), 'booked for someone else -> "Booked by ... (for X)" kept', serFor);
const single = '*QAMD / Jem Lim / DR*\n*Date:* Monday, November 8, 2027\n*Client:* Jem Lim\n\nConfirm to book.';
ok(/Client:/.test(gp(single, [])), 'a single-date summary is not cut by the series rule');

console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
