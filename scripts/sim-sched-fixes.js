#!/usr/bin/env node
// Offline tests for main v217 + Book Session v88 + Room Availability v16 (schedule fixes; live 4 Oct 21:14-21:48 PHT):
// "project wheat sun." read as Sunday (Booked For's project cut to WHEAT), Studio F's clash said only at the card, and
// the room-list layout decided 4 Oct. (Gate Context's day rule is in test-gate.)
//   node scripts/sim-sched-fixes.js <main-execution.json>   (its All Bookers output feeds Book Session too)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v217.json'), OM = WF('project-jessie-v216.json');
const B = WF(process.env.BOOK || 'book-session-v88.json'), OB = WF('book-session-v87.json');
const RA = WF(process.env.RA || 'room-availability-v16.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const runOf = f => JSON.parse(fs.readFileSync(f)).data.resultData.runData;
const recOf = run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const recM = recOf(runOf(process.argv[2]));
const recB = n => n === 'All Bookers' ? recM('All Bookers') : null;
const ME = 'U08V3CKDGJF';

// --- Booked For: the project ------------------------------------------------------------------------------------------
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1790918000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const WHEAT = [{ user: ME, text: 'book vo recording for me tomorrow studio f. client is harold' }, { bot_id: 'B1', text: 'What’s the project? And what time?' }, { user: ME, text: 'project wheat sun. 3-5pm' }];
console.log('Booked For v217 - a day name inside a project');
let o = bf(M, WHEAT);
ok(String(o.project || '').toLowerCase() === 'wheat sun', 'live 21:46: "project wheat sun. 3-5pm" -> WHEAT SUN', o.project);
ok(String(bf(OM, WHEAT).project || '').toLowerCase() === 'wheat', '  (v216: WHEAT)');
o = bf(M, [{ user: ME, text: 'book studio 7, project knorr sat 3pm' }]);
ok(String(o.project || '').toLowerCase() === 'knorr', 'a time after it: "project knorr sat 3pm" -> KNORR (sat is the day)', o.project);
o = bf(M, [{ user: ME, text: 'book studio 7 tomorrow 2-4pm, project thank you' }]);
ok(String(o.project || '').toLowerCase() === 'thank you', 'v211 still: "project thank you"', o.project);
o = bf(M, [{ user: ME, text: 'project red flag tomorrow 3-4pm' }]);
ok(String(o.project || '').toLowerCase() === 'red flag', '"tomorrow" still ends a project', o.project);

// --- Book Session: the room is checked before the questions -----------------------------------------------------------
const REQ0 = { mode: 'prepare', department: '', arranger: '', booked_for: '', all_day: false, reference_data: '' };
const SF = ((code(B, 'Check Conflicts').match(/'Studio F':\s*'([^']+)'/) || [])[1]);
const SMILE = { id: 'smile', summary: 'SMILE / Jem Lim / AEG', start: { dateTime: '2027-10-05T15:00:00+08:00' }, end: { dateTime: '2027-10-05T16:00:00+08:00' }, attendees: [{ email: SF }] };
const cc = (w, req, evs) => { const R = [{ json: { ...REQ0, mode: 'prepare', series: false, bookingType: '', expected_date: '2027-10-05', asked_text: '', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : wrap(recB(n) || [{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: evs } }]), () => ({}))[0].json; };
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const CELEB = { summary: '/ / HL', client: '', engineer: 'Howard Luistro', session_type: 'Celebrity Recording', rooms: 'Studio F',
  start_iso: '2027-10-05T15:00:00+08:00', end_iso: '2027-10-05T16:00:00+08:00', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME,
  requester_text: 'book celeb recording 3-4pm tomorrow studio f' };
console.log('Book Session v88 - a clash in the named room rides on the first question');
let c = cc(B, CELEB, [SMILE]);
ok(/^Heads up: Studio F is booked 3:00 PM – 4:00 PM \("SMILE \/ Jem Lim \/ AEG"\)\. /.test(relay(c.human) || ''), 'live 21:31: the question opens with Studio F\'s booking', [c.reason, relay(c.human)]);
ok(!/Heads up/.test(relay(cc(OB, CELEB, [SMILE]).human) || ''), '  (v87: nothing about the room until the card)');
c = cc(B, CELEB, []);
ok(c.verdict === 'REJECTED' && !/Heads up/.test(c.human), 'a free room -> the question alone', relay(c.human));
c = cc(B, { ...CELEB, start_iso: '2027-10-05T16:00:00+08:00', end_iso: '2027-10-05T17:00:00+08:00', requester_text: 'book celeb recording 4-5pm tomorrow studio f' }, [SMILE]);
ok(!/Heads up/.test(c.human), 'back to back (4-5 PM after 3-4 PM) is not a clash', relay(c.human));
c = cc(B, { ...CELEB, asked_text: 'Heads up: Studio F is booked 3:00 PM – 4:00 PM ("SMILE / Jem Lim / AEG"). Who’s the client? (or "none") What’s the project?' }, [SMILE]);
ok(!/Heads up/.test(c.human), 'said once -> not repeated on the next question', relay(c.human));
c = cc(B, { ...CELEB, requester_text: 'book celeb recording tomorrow studio f' }, [SMILE]);
ok(!/Heads up/.test(c.human), 'no time given -> no heads-up (the window is the model\'s guess)', relay(c.human));
const M6 = (code(B, 'Check Conflicts').match(/'M6':\s*'([^']+)'/) || [])[1];
c = cc(B, { ...CELEB, rooms: 'M6', session_type: '', summary: 'M6 - Howard', requester_text: 'book m6 for me tomorrow 3-4pm' },
  [{ id: 'h', summary: 'M6 - Marketing', recurringEventId: 'r', start: { date: '2027-10-05' }, end: { date: '2027-10-06' }, attendees: [{ email: M6 }] }]);
ok(!/Heads up/.test(String(c.human || '')), 'an M booth\'s standing hold -> left to consent', [c.reason, relay(c.human)]);

// --- Room Availability: layout ----------------------------------------------------------------------------------------
const ROOMS = ['Studio 1', 'Studio 2', 'Studio 5', 'Studio 7', 'Studio 8', 'Studio C', 'Studio F', 'Studio A', 'M2', 'M3'];
const REF = JSON.stringify({ rooms: ROOMS.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: n === 'Studio A', common: false })), types: [] });
Date.now = () => Date.parse('2026-10-04T13:00:00Z');
const ra = (req, evs = []) => new Function('$', '$input', code(RA, 'Compute Availability'))(n => wrap([{ json: { reference_data: REF, scope: 'studios', ...req } }]), wrap([{ json: { items: evs } }]))[0].json;
const RID = n => (code(RA, 'Compute Availability').match(new RegExp("'" + n + "':\\s*'([^']+)'")) || [])[1];
const ev = (room, a, b) => ({ id: room + a, summary: 'X', start: { dateTime: '2027-10-05T' + a + ':00+08:00' }, end: { dateTime: '2027-10-05T' + b + ':00+08:00' }, attendees: [{ email: RID(room) }] });
console.log('Room Availability v16 - layout decided 4 Oct');
let r = ra({ start_iso: '2027-10-05T00:00:00+08:00', end_iso: '2027-10-05T23:59:00+08:00' }, [ev('Studio 5', '12:00', '15:00'), ev('Studio 7', '10:00', '12:00')]);
ok(r.reply_text === '🗓️ October 5 (Tuesday)\n\nFree all day:\nStudios 1, 2, 8, C, and F.\nVocal booth A.\nM2, M3.\n\nStudio 5 (except 12:00 PM – 3:00 PM).\nStudio 7 (except 10:00 AM – 12:00 PM).',
  'a whole day: headline, "Free all day:" with no blank line, "(except ...)"', r.reply_text);
r = ra({ start_iso: '2027-10-05T14:00:00+08:00', end_iso: '2027-10-05T17:00:00+08:00' });
ok(/\nFree studios:\nStudios 1, 2, 5, 7, 8, C, and F\.\nVocal booth A\.\nM2, M3\.$/.test(r.reply_text || ''), 'a set time: "Free studios:" with no blank line', r.reply_text);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
