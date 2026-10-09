#!/usr/bin/env node
// Offline tests for main v230 + Room Availability v18 (early room check; QA B4, 7 Oct, PENDING 95): when a booking names a
// room and a date, the room is checked at once - free, carry on; taken, say so and offer other rooms or days.
//   node scripts/sim-early-room-check.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v235.json'), OM = WF('project-jessie-v229.json');
const RA = WF(process.env.RA || 'room-availability-v18.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 900))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData; const rec = n => run[n] ? run[n][0].data.main[0] : null;
const REF = rec('Room Table')[0].json.referenceData;
const JESS = 'U0B4S0EKSAY', TRISH = 'U098UFMKQHZ';

// the calendar: Studio F 14 Oct 1-4 PM (Jess's), Studio 1 the same time (someone else's), Studio F 15 Oct 12-5 PM
const E = (room, d, s, e, title, ref) => ({ id: room + d + s, summary: title, location: room, description: 'Booked by: X | ref: ' + ref,
  start: { dateTime: d + 'T' + s + ':00+08:00' }, end: { dateTime: d + 'T' + e + ':00+08:00' } });
const CAL0 = [E('Studio F', '2027-10-14', '13:00', '16:00', 'SESH / Netflix / JD', JESS), E('Studio 1', '2027-10-14', '13:00', '16:00', 'ORBIT / TL', 'U1'),
  E('Studio F', '2027-10-15', '12:00', '17:00', 'OTHER / HL', 'U2')];

const raRun = (inp, cal) => new Function('$', '$input', code(RA, 'Compute Availability'))(
  n => wrap([{ json: n === 'When Executed by Another Workflow' ? inp : {} }]), wrap([{ json: { items: cal } }]))[0].json;

const turn = ({ text, user = JESS, timeStart = '', timeEnd = '', dates = '2027-10-14', inMsg = dates, history = [], gate = {}, reqText, cal = CAL0, reply = 'What kind of session is this?', steps = [] }) => {
  const trig = { text, user, ts: '1791900000.1' };
  const O = { 'Gate Context': [{ json: { datesUnderDiscussion: dates, datesInMessage: inMsg, epoch: 0, gate: {}, ...gate } }],
    'Booked For': [{ json: { timeStart, timeEnd, requesterText: reqText || [text].concat(history.filter(m => !m.bot_id).map(m => m.text)).join('\n') } }],
    'Slack Trigger': [{ json: trig }], 'Get Recent Messages': [{ json: trig }].concat(history.map(m => ({ json: m }))),
    'Room Table': [{ json: { referenceData: REF } }] };
  const $ = n => wrap(O[n] || rec(n) || [{ json: {} }]);
  const plan = new Function('$', '$input', code(M, 'Early Room Plan'))($, wrap([{ json: { prev: 1 } }]))[0].json;
  O['Early Room Plan'] = [{ json: plan }];
  let res = plan, ra = null;
  if (plan.earlyPlan.run) {
    const P = plan.earlyPlan;
    ra = raRun({ start_iso: P.start_iso, end_iso: P.end_iso, session_type: '', room: P.room, reference_data: REF, scope: 'all', hours: P.hours || '' }, cal);   // v249: hours
    res = new Function('$', '$input', code(M, 'Early Room Result'))($, wrap([{ json: ra }]))[0].json;
    O['Early Room Result'] = [{ json: res }];
  }
  const G = (W, skipEarly) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output: reply, intermediateSteps: steps } }]),
    n => { if (n === 'Early Room Result' && (skipEarly || !O[n])) throw new Error('not executed'); return wrap(O[n] || rec(n) || [{ json: {} }]); })[0].json.output;
  // asIs: what Guard Probe sends with no early check (its other rewrites still apply to the model's reply)
  return { plan: plan.earlyPlan, res, ra, out: G(M), asIs: G(M, true) };
};

console.log('QA B4 - "book studio f on oct 14, 1-4pm plz" when Studio F is taken then');
let r = turn({ text: 'book studio f on oct 14, 1-4pm plz', timeStart: '13:00', timeEnd: '16:00' });
const V249 = /v249 \(PENDING 102\)/.test(code(M, 'Early Room Plan'));
ok(r.plan.run && r.plan.room === 'Studio F' && (V249 ? r.plan.start_iso === '2027-10-14T08:00:00+08:00' && r.plan.end_iso === '2027-10-20T22:00:00+08:00' && r.plan.hours === '13:00-16:00'
    : r.plan.start_iso === '2027-10-14T13:00:00+08:00' && r.plan.end_iso === '2027-10-20T16:00:00+08:00'),
  'checked at once: Studio F, 14-20 Oct, 1-4 PM', r.plan);
ok(/^❌ Heads up: \*You already have Studio F booked 1:00 PM – 4:00 PM\* on Thursday, October 14 with this session: SESH \/ Netflix \/ JD\n\n/.test(r.out), 'Jess\'s own booking -> "You already have Studio F booked ..."', r.out);
ok(/\n✅ Free at that time:\nStudio 2 · Studio 7 · Studio 8 · /.test(r.out) && !/Studio 1 ·|Studio 1$|Studio F ·/.test(r.out.split('✅ Free at that time:\n')[1].split('\n')[0]),
  'other rooms free then, same kind, Studio 1 (taken) left out', r.out);
ok(V249 ? /\n\n✅ Studio F is free on the same day at:\n• 10:00 AM – 1:00 PM\n• 4:00 PM – 7:00 PM\n\n✅ Free at that time:\n/.test(r.out) && /\n✅ Studio F is free at that time on:\n• Saturday, October 16\n\nWant one of those, or another day or time\?$/.test(r.out)
    : /\n✅ Studio F is free at that time on:\n• Saturday, October 16\n• Sunday, October 17\n• Monday, October 18\n\nWant one of those, or another day or time\?$/.test(r.out),
  V249 ? 'v249: the same day first (a tie: the earlier), then other rooms, then ONE other day (15 Oct is taken)' : 'and the next days Studio F is free then (15 Oct is taken)', r.out);
ok(!/What kind of session/.test(r.out), 'the model\'s questions are not sent');
ok(/^ROOM CHECK/.test(r.res.earlyRoomNotice) && r.res.earlyRoomNotice.includes(r.out), 'the prompt is told the same reply', r.res.earlyRoomNotice);
r = turn({ text: 'book studio f on oct 14, 1-4pm plz', user: TRISH, timeStart: '13:00', timeEnd: '16:00' });
ok(/^❌ Heads up: \*Studio F is already booked 1:00 PM – 4:00 PM\* on Thursday, October 14 by this session: SESH \/ Netflix \/ JD\n/.test(r.out), 'someone else\'s -> "❌ Heads up: *Studio F is already booked ...*"', r.out);
r = turn({ text: 'book studio f on oct 14, 3-6pm', timeStart: '15:00', timeEnd: '18:00' });
ok(/booked 1:00 PM – 4:00 PM\* on Thursday, October 14 /.test(r.out), 'an overlap shows the booking\'s own times', r.out);

console.log('free');
r = turn({ text: 'book studio 7 on oct 14, 1-4pm', timeStart: '13:00', timeEnd: '16:00' });
ok(r.res.earlyRoom && r.res.earlyRoom.mode === 'free' && r.out === r.asIs, 'Studio 7 free -> the reply goes out as written', [r.res.earlyRoom, r.out]);
ok(/Studio 7 is free on Thursday, October 14, 1:00 PM – 4:00 PM/.test(r.res.earlyRoomNotice), 'and the prompt is told it is free', r.res.earlyRoomNotice);
r = turn({ text: 'book studio f on oct 14, 5-7pm', timeStart: '17:00', timeEnd: '19:00' });
ok(r.res.earlyRoom && r.res.earlyRoom.mode === 'free' && r.out === r.asIs, 'Studio F after 4 PM -> free', r.out);

console.log('a date and no time yet');
r = turn({ text: 'book studio f on oct 14' });
ok(r.plan.run && r.plan.start_iso === '2027-10-14T08:00:00+08:00' && r.plan.end_iso === '2027-10-20T22:00:00+08:00', 'checked 8 AM - 10 PM', r.plan);
ok(/^❌ Heads up: \*You already have Studio F booked 1:00 PM – 4:00 PM\* on Thursday, October 14 with this session: SESH \/ Netflix \/ JD\n\n✅ Studio F is free on the same day at:\n• 8:00 AM – 1:00 PM\n• 4:00 PM – 10:00 PM\n\n✅ Free all day:\nStudio 2 · Studio 7 · Studio 8 · /.test(r.out)
  && (/v255 \(PENDING 109/.test(code(M, 'Guard Probe')) ? r.out.endsWith('\n\nWhat time works?') : r.out.endsWith('\n\n' + r.asIs) && /^What kind of session/.test(r.asIs)) && !/Free all day:\n[^\n]*Studio 1\b/.test(r.out),   // v255: no time yet -> "What time works?" under the heads-up (v252)
  'booked for part of the day -> the heads-up, when the room is still free, the rooms free all day (Studio 1 is not), then the questions', r.out);
// v231 (live 7 Oct 17:17): "book studio 7 tomorrow for me" - Studio 7 taken 3-5 PM by someone else
r = turn({ text: 'book studio 7 tomorrow for me', dates: '2027-10-08', inMsg: '2027-10-08', user: 'U08V3CKDGJF', cal: [E('Studio 7', '2027-10-08', '15:00', '17:00', 'WHEAT SUN / Jem Lim / AEG', 'U2')] });
ok(r.out.startsWith('❌ Heads up: *Studio 7 is already booked 3:00 PM – 5:00 PM* on Friday, October 8 by this session: WHEAT SUN / Jem Lim / AEG\n\n✅ Studio 7 is free on the same day at:\n• 8:00 AM – 3:00 PM\n• 5:00 PM – 10:00 PM\n\n✅ Free all day:\nStudio 1 · Studio 2 · Studio 8 · ')
  && r.out.endsWith('\n\n' + r.asIs), 'live 17:17: the options come with the heads-up, in the first reply', r.out);
ok(/do not repeat them or list rooms yourself/.test(r.res.earlyRoomNotice) && !/\n/.test(r.res.earlyRoomNotice.split('ROOM CHECK')[1].split('Those lines')[0]), 'the prompt is told, on one line', r.res.earlyRoomNotice);
r = turn({ text: 'book studio 7 tomorrow', dates: '2027-10-08', inMsg: '2027-10-08', user: TRISH, cal: [E('Studio 7', '2027-10-08', '08:00', '12:00', 'A', 'U2'), E('Studio 7', '2027-10-08', '12:15', '21:45', 'B', 'U2')] });
ok(/^❌ Heads up: \*Studio 7 is already booked 8:00 AM – 12:00 PM and 12:15 PM – 9:45 PM\* on Friday, October 8 by these sessions: A · B\n\n✅ Free all day:\n/.test(r.out), 'v234: several bookings -> the times together in bold, the sessions in the same order', r.out);
ok(!/[*❌✅•\n]/.test(r.res.earlyRoomNotice.split('Those lines')[0]), 'the prompt gets it as plain text, on one line', r.res.earlyRoomNotice);
ok(!/free on the same day at/.test(r.out) && /\n✅ Free all day:\n/.test(r.out) && !/• 12:00 PM|• 9:45 PM/.test(r.out), 'gaps under 30 minutes are not offered (12:00-12:15, 9:45-10:00)', r.out);
r = turn({ text: 'book studio f on oct 14', user: TRISH, cal: [{ id: 'x', summary: 'HOLD', location: 'Studio F', description: 'ref: U2', start: { date: '2027-10-14' }, end: { date: '2027-10-15' } }] });
ok(/^❌ Heads up: \*Studio F is already booked all day\* on Thursday, October 14 by this session: HOLD\n\n✅ Free all day:\nStudio 1 · Studio 2 · /.test(r.out) && /\n✅ Studio F is free all day on:\n• Friday, October 15\n/.test(r.out),
  'booked all day -> taken, the rooms free that day, and the next days', r.out);
r = turn({ text: 'book studio 7 on oct 14' });
ok(r.res.earlyRoom && r.res.earlyRoom.mode === 'free' && /free on Thursday, October 14 \(8 AM – 10 PM\)/.test(r.res.earlyRoomNotice), 'free all day -> carry on', r.res.earlyRoomNotice);

console.log('the room from earlier in the booking');
const H = (text, bot) => bot ? { text, bot_id: 'B1', ts: '1791899999.' + text.length } : { text, user: JESS, ts: '1791899998.' + text.length };
r = turn({ text: '1-4pm', inMsg: '', timeStart: '13:00', timeEnd: '16:00', history: [H('What time?', true), H('book studio f on oct 14')] });
ok(r.plan.run && r.plan.room === 'Studio F' && /^❌ Heads up: \*You already have Studio F/.test(r.out), 'the time given later -> Studio F checked then', [r.plan, r.out]);
r = turn({ text: 'oct 14 then', timeStart: '13:00', timeEnd: '16:00', history: [H('Studio F is already booked ...\n\nFree at that time: Studio 7 · Studio 8', true), H('book studio f on oct 13, 1-4pm')] });
ok(!r.plan.run, 'Jessie has offered other rooms since -> not guessed', r.plan);
r = turn({ text: 'studio 7 then', inMsg: '', timeStart: '13:00', timeEnd: '16:00', history: [H('You already have Studio F ...', true), H('book studio f on oct 14, 1-4pm plz')] });
ok(r.plan.run && r.plan.room === 'Studio 7' && r.res.earlyRoom.mode === 'free' && r.out === r.asIs, '"studio 7 then" -> Studio 7 checked, free, carry on', [r.plan, r.out]);
r = turn({ text: 'vo recording', inMsg: '', timeStart: '13:00', timeEnd: '16:00', history: [H('What kind of session is this?', true), H('book studio f on oct 14, 1-4pm plz')] });
ok(!r.plan.run, 'an answer with no room, date or time -> not checked again', r.plan);
r = turn({ text: '2pm', inMsg: '', timeStart: '13:00', timeEnd: '16:00', history: [H('Booked. Studio F ...', true), H('book studio f on oct 14, 1-4pm')] });
ok(!r.plan.run, 'a finished booking is not carried', r.plan);

console.log('said once - the consent engine still gets its turn');
r = turn({ text: 'i still need studio f', inMsg: '', timeStart: '13:00', timeEnd: '16:00', user: TRISH,
  history: [H('Studio F is already booked on Thursday, October 14, 1:00 PM – 4:00 PM (“SESH / Netflix / JD”).\n\nFree at that time: Studio 2', true), H('book studio f on oct 14, 1-4pm')] });
ok(!r.plan.run && r.out === r.asIs, 'told once, still wants Studio F -> the normal flow (Book Session: priority request or ROOM_OCCUPIED)', r.plan);
r = turn({ text: 'ok how about oct 15', dates: '2027-10-15', inMsg: '2027-10-15', timeStart: '13:00', timeEnd: '16:00', user: TRISH,
  history: [H('Studio F is already booked on Thursday, October 14, 1:00 PM – 4:00 PM (“SESH / Netflix / JD”).', true), H('book studio f on oct 14, 1-4pm')] });
ok(r.plan.run && r.plan.room === 'Studio F' && /^❌ Heads up: \*Studio F is already booked 12:00 PM – 5:00 PM\* on Friday, October 15 /.test(r.out), '"how about oct 15" after being told about Studio F -> Studio F on the 15th, checked (taken too)', r.out);
r = turn({ text: 'studio f on oct 15 then', dates: '2027-10-15', timeStart: '13:00', timeEnd: '16:00', user: TRISH,
  history: [H('Studio F is already booked on Thursday, October 14, 1:00 PM – 4:00 PM (“SESH / Netflix / JD”).', true), H('book studio f on oct 14, 1-4pm')] });
ok(r.plan.run && /^❌ Heads up: \*Studio F is already booked 12:00 PM – 5:00 PM\* on Friday, October 15 /.test(r.out), 'Studio F on another date -> checked again (taken 15 Oct too)', r.out);
r = turn({ text: 'i still need studio f', inMsg: '', timeStart: '13:00', timeEnd: '16:00', user: TRISH,
  history: [H('❌ Heads up: *Studio F is already booked 1:00 PM – 4:00 PM* on Thursday, October 14 by this session: SESH / Netflix / JD\n\n✅ Free at that time:\nStudio 2\n\nWant one of those, or another day or time?', true), H('book studio f on oct 14, 1-4pm')] });
ok(!r.plan.run, 'v235: told in the ❌ layout, still wants Studio F -> the normal flow', r.plan);
r = turn({ text: '1-4pm', inMsg: '', timeStart: '13:00', timeEnd: '16:00', user: TRISH,
  history: [H('❌ Heads up: *Studio F is already booked 1:00 PM – 4:00 PM* on Thursday, October 14 by this session: SESH / Netflix / JD\n\n✅ Studio F is free on the same day at:\n• 8:00 AM – 1:00 PM\n\nWhat time?', true), H('book studio f on oct 14')] });
ok(r.plan.run && /^❌ Heads up: \*Studio F is already booked/.test(r.out), 'v235: a heads-up on a question is not "told" -> the time given later is checked', [r.plan, r.out]);
const MB = [E('M3', '2027-10-14', '09:00', '18:00', 'M3 - HOLD', 'U2')];
r = turn({ text: 'book m3 on oct 14, 1-4pm', timeStart: '13:00', timeEnd: '16:00', user: TRISH, cal: MB });
ok(r.plan.room === 'M3' && /^❌ Heads up: \*M3 is already booked 9:00 AM – 6:00 PM\* on Thursday, October 14 by this session: M3 - HOLD\n\n✅ Free at that time:\nM1 · M2 · M4 · M5 · M6\n\n/.test(r.out) && r.out.endsWith('\n\n' + r.asIs),
  'an M booth taken -> a heads-up with the M booths free then, and the questions go on (a standing hold is shared through the consent engine)', r.out);
r = turn({ text: "book studio 7 on oct 14 i'm 2 mins away", timeStart: '13:00', timeEnd: '16:00' });
ok(r.plan.room === 'Studio 7', '"i\'m 2" is not M2', r.plan);

console.log('not checked');
for (const [t, g, why] of [['yes', { confirmed: true }, 'a yes'], ['cancel studio f on oct 14', {}, 'a cancel'], ['move it to studio f oct 14 2pm', {}, 'a move'],
  ['is studio f free on oct 14 1-4pm?', {}, 'an availability question'], ['book studio f every thursday 1-4pm', {}, 'a series'],
  ['book studio 1 with booth a on oct 14 1-4pm', {}, 'two rooms'], ['studio f', { presentedMove: true }, 'answering a move card']]) {
  r = turn({ text: t, timeStart: '13:00', timeEnd: '16:00', gate: { ...g, gate: g } });
  ok(!r.plan.run && r.out === r.asIs, why + ' -> no check', r.plan);
}
r = turn({ text: 'book studio f 1-4pm', dates: '', inMsg: '', timeStart: '13:00', timeEnd: '16:00' });
ok(!r.plan.run, 'no date yet -> no check', r.plan);
r = turn({ text: 'book studio f on oct 14 and oct 21', dates: '2027-10-14,2027-10-21' });
ok(!r.plan.run, 'two dates -> no check', r.plan);

console.log('a booking card is never touched');
const card = '*SESH / Netflix / JD*\n*Date:* Thursday, October 14, 2027\n*Time:* 1:00 PM – 4:00 PM\n*Room:* Studio F\n\nBook it? Reply yes or no.';
r = turn({ text: 'book studio f on oct 14, 1-4pm, vo recording, project sesh, client netflix, engineer drey', timeStart: '13:00', timeEnd: '16:00', reply: card });
ok(r.out === card, 'a card in the reply -> sent as it is', r.out);

console.log('alternatives in the session type\'s ranking');
const R = JSON.parse(REF), nm = {}; R.rooms.forEach(x => nm[x.id] = x.name);
const vo = R.types.find(t => t.type === 'VO Recording'); const rank = [].concat(vo.priority || [], vo.last || []).map(i => nm[i]);
if (rank.includes('Studio F')) {
  r = turn({ text: 'book studio f on oct 14, 1-4pm, vo recording', timeStart: '13:00', timeEnd: '16:00' });
  const want = rank.filter(n => !['Studio F', 'Studio 1'].includes(n)).slice(0, 5).join(' · ');
  ok(r.out.includes('✅ Free at that time:\n' + want + '\n'), 'VO Recording named -> its ranking: ' + want, r.out);
} else ok(true, '(VO Recording does not rank Studio F in this fixture - skipped)');

console.log('wiring and prompt');
const to = (n, i = 0) => (((M.connections[n] || {}).main || [])[i] || []).map(x => x.node);
ok(JSON.stringify(to('Already Done?', 1)) === '["Early Room Plan"]' && JSON.stringify(to('Early Room Plan')) === '["Early Room Check?"]'
  && JSON.stringify(to('Early Room Check?', 0)) === '["Early Room Check"]' && JSON.stringify(to('Early Room Check?', 1)) === '["Jessie AI Agent"]'
  && JSON.stringify(to('Early Room Check')) === '["Early Room Result"]' && JSON.stringify(to('Early Room Result')) === '["Jessie AI Agent"]',
  'Already Done? -> Early Room Plan -> Early Room Check? -> (Early Room Check -> Early Room Result ->) AI Agent');
const call = M.nodes.find(x => x.name === 'Early Room Check');
ok(call.parameters.workflowId.value === 'e7tBQB458nstrqei' && call.onError === 'continueRegularOutput', 'Early Room Check calls Room Availability (e7tBQB458nstrqei), carries on after an error');
ok(M.nodes.find(x => x.name === 'Jessie AI Agent').parameters.options.systemMessage.includes("{{ $json.earlyRoomNotice || '' }}"), 'the prompt reads the notice from its input');
ok(!OM.nodes.some(x => x.name === 'Early Room Plan'), '  (v229: no early check)');
// Room Availability v18: the old outputs are unchanged
const old = WF('room-availability-v17.json');
const o17 = new Function('$', '$input', code(old, 'Compute Availability'))(n => wrap([{ json: n === 'When Executed by Another Workflow' ? { start_iso: '2027-10-14T13:00:00+08:00', end_iso: '2027-10-14T16:00:00+08:00', room: 'Studio F', reference_data: REF } : {} }]), wrap([{ json: { items: CAL0 } }]))[0].json;
const o18 = raRun({ start_iso: '2027-10-14T13:00:00+08:00', end_iso: '2027-10-14T16:00:00+08:00', room: 'Studio F', reference_data: REF }, CAL0);
ok(JSON.stringify(o17) === JSON.stringify(o18), 'Room Availability v18: a one-day answer is exactly v17\'s');
const m18 = raRun({ start_iso: '2027-10-14T13:00:00+08:00', end_iso: '2027-10-20T16:00:00+08:00', room: 'Studio F', reference_data: REF }, CAL0);
ok(m18.human === new Function('$', '$input', code(old, 'Compute Availability'))(n => wrap([{ json: n === 'When Executed by Another Workflow' ? { start_iso: '2027-10-14T13:00:00+08:00', end_iso: '2027-10-20T16:00:00+08:00', room: 'Studio F', reference_data: REF } : {} }]), wrap([{ json: { items: CAL0 } }]))[0].json.human,
  'Room Availability v18: the day-by-day text the model reads is unchanged');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
