#!/usr/bin/env node
// Offline tests for main v249 + Book Session v101 + Room Availability v22 (PENDING 102-106, 9 Oct): the live 8 Oct 23:35-23:39
// exchange played through the real nodes - Booked For, Early Room Plan, Room Availability, Early Room Result, Guard Probe - and
// Book Session's Check Conflicts / Return Rejection for the taken-room options and conference-room titles.
//   node scripts/sim-v249.js <main-execution.json>     (PREVIEW=1 prints each reply)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v249.json'), B = WF(process.env.BOOK || 'book-session-v101.json'), RA = WF(process.env.RA || 'room-availability-v22.json');
const OM = WF('project-jessie-v248.json'), ORA = WF('room-availability-v21.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 900))); } };
const show = (t, s) => { if (process.env.PREVIEW) console.log('\n----- ' + t + '\n' + s + '\n'); };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData; const rec = n => run[n] ? run[n][0].data.main[0] : null;
const REF = rec('Room Table')[0].json.referenceData;
const ME = 'U08V3CKDGJF';
Date.now = () => Date.parse('2026-10-08T15:35:00Z');   // 8 Oct 23:35 PHT; Jessie's year is 2027
const E = (room, d, s, e, title, ref) => ({ id: room + d + s, summary: title, location: room, description: 'Booked by: X | ref: ' + ref,
  start: { dateTime: d + 'T' + s + ':00+08:00' }, end: { dateTime: d + 'T' + e + ':00+08:00' } });
// the live calendar: Studio 7 is booked 1-3 PM on Saturday 9 Oct 2027 (and free the next days)
const CAL = [E('Studio 7', '2027-10-09', '13:00', '15:00', 'CATTAIL / Sasa Abella / HL', 'U2')];
const raRun = (W, inp, cal) => new Function('$', '$input', code(W, 'Compute Availability'))(
  n => wrap([{ json: n === 'When Executed by Another Workflow' ? inp : {} }]), wrap([{ json: { items: cal } }]))[0].json;
const STAFF = (rec('All Bookers') || []).map(i => i.json);
const U = (ts, text) => ({ ts: String(ts), text, user: ME }), J = (ts, text) => ({ ts: String(ts), text, bot_id: 'B1' });

// one turn through main: Booked For -> Early Room Plan -> (Room Availability) -> Early Room Result -> Guard Probe
const turn = (W, RAW, hist, { reply = 'What\'s the session type, project and client?', steps = [], dates = '2027-10-09', inMsg = '', cal = CAL } = {}) => {
  const trig = { text: hist[0].text, user: ME, ts: hist[0].ts };
  const O = { 'Gate Context': [{ json: { datesUnderDiscussion: dates, datesInMessage: inMsg, epoch: 0, gate: {} } }],
    'Slack Trigger': [{ json: trig }], 'Get Recent Messages': hist.map(m => ({ json: m })), 'Room Table': [{ json: { referenceData: REF } }],
    'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }], 'All Bookers': STAFF.length ? STAFF.map(j => ({ json: j })) : [{ json: {} }] };
  const $ = n => wrap(O[n] || rec(n) || [{ json: {} }]);
  O['Booked For'] = [{ json: new Function('$', code(W, 'Booked For'))($)[0].json }];
  const plan = new Function('$', '$input', code(W, 'Early Room Plan'))($, wrap([{ json: { prev: 1 } }]))[0].json;
  O['Early Room Plan'] = [{ json: plan }];
  let ra = null;
  if (plan.earlyPlan.run) {
    const P = plan.earlyPlan;
    ra = raRun(RAW, { start_iso: P.start_iso, end_iso: P.end_iso, session_type: '', room: P.room, reference_data: REF, scope: 'all', hours: P.hours || '' }, cal);
    O['Early Room Result'] = [{ json: new Function('$', '$input', code(W, 'Early Room Result'))($, wrap([{ json: ra }]))[0].json }];
  }
  const out = new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output: reply, intermediateSteps: steps } }]),
    n => { if (n === 'Early Room Result' && !O[n]) throw new Error('not executed'); return $(n); })[0].json.output;
  return { bf: O['Booked For'][0].json, plan: plan.earlyPlan, ra, res: O['Early Room Result'] && O['Early Room Result'][0].json, out };
};

console.log('102 - 23:35 "book tomorrow 12-2pm studio 7" (Studio 7 booked 1-3 PM)');
const h1 = [U(10, 'book tomorrow 12-2pm studio 7')];
let r = turn(M, RA, h1, { inMsg: '2027-10-09' });
show('23:35 on v249', r.out);
ok(r.plan.run && r.plan.hours === '12:00-14:00' && r.plan.start_iso === '2027-10-09T08:00:00+08:00' && r.plan.end_iso === '2027-10-15T22:00:00+08:00',
  'checked at once: Studio 7, the whole day read 8 AM - 10 PM, the hours asked for passed separately', r.plan);
ok(r.out === '❌ Heads up: *Studio 7 is already booked 1:00 PM – 3:00 PM* on Saturday, October 9 by this session: CATTAIL / Sasa Abella / HL\n\n'
  + '✅ Studio 7 is free on the same day at:\n• 11:00 AM – 1:00 PM\n• 3:00 PM – 5:00 PM\n\n'
  + '✅ Free at that time:\n' + r.out.split('✅ Free at that time:\n')[1].split('\n')[0] + '\n\n'
  + '✅ Studio 7 is free at that time on:\n• Sunday, October 10\n\nWant one of those, or another day or time?',
  'same studio nearest first (11-1 back-to-back, then 3-5), other studios, ONE other day', r.out);
ok(!/Studio 7 ·|· Studio 7\b/.test(r.out.split('✅ Free at that time:\n')[1].split('\n')[0]), '...Studio 7 not among the other studios');
const o1 = turn(OM, ORA, h1, { inMsg: '2027-10-09' });
ok(/is free at that time on:\n• Sunday, October 10\n• Monday, October 11\n• Tuesday, October 12/.test(o1.out) && !/same day/.test(o1.out), '  (v248: no same-day time, three other days)', o1.out);

console.log('103 - 23:38 "book 11-1 instead"');
const heads = r.out;
const h2 = [U(12, 'book 11-1 instead'), J(11, heads), U(10, 'book tomorrow 12-2pm studio 7')];
r = turn(M, RA, h2, { reply: 'Studio 7 is free then. What\'s the session type, project and client?',
  steps: [{ action: { tool: 'Room_Availability' }, observation: JSON.stringify([raRun(RA, { start_iso: '2027-10-09T12:00:00+08:00', end_iso: '2027-10-09T13:00:00+08:00', room: 'Studio 7', reference_data: REF }, CAL)]) }] });
show('23:38 on v249', r.out);
ok(r.bf.timeStart === '11:00' && r.bf.timeEnd === '13:00' && r.bf.timeForced === true, '"11-1" is 11 AM - 1 PM, and it is the time', [r.bf.timeStart, r.bf.timeEnd, r.bf.timeForced]);
ok(r.plan.run && r.plan.room === 'Studio 7' && r.plan.hours === '11:00-13:00', 'no studio named: the heads-up\'s Studio 7, checked again at the new time', r.plan);
ok(r.res && r.res.earlyRoom && r.res.earlyRoom.mode === 'free', '11 AM - 1 PM is free (back-to-back with the 1 PM booking)', r.res && r.res.earlyRoom);
ok(r.out === (/v255 \(PENDING 109/.test(code(M, 'Guard Probe')) ? '🗓️ Studio 7 · Saturday, October 9 · 11:00 AM – 1:00 PM\n\n' : '✅ Studio 7 is free · Saturday, October 9 · 11:00 AM – 1:00 PM\n') + 'What\'s the session type, project and client? (or "none" for no client)',
  'the booking said back (free, checked by code this turn), then the details question - no availability layout', r.out);
const o2 = turn(OM, ORA, h2, { reply: 'Studio 7 is free then. What\'s the session type, project and client?',
  steps: [{ action: { tool: 'Room_Availability' }, observation: JSON.stringify([raRun(ORA, { start_iso: '2027-10-09T12:00:00+08:00', end_iso: '2027-10-09T13:00:00+08:00', room: 'Studio 7', reference_data: REF }, CAL)]) }] });
ok(/✅ Studio 7 is free 12:00 PM – 1:00 PM\./.test(o2.out) && !o2.bf.timeStart.startsWith('11'), '  (v248: the 23:38 reply - 12-1 PM, as availability)', [o2.bf.timeStart, o2.out]);

console.log('v251 - the history as Slack returns it (":x:" codes, live 9 Oct 11:49)');
if (/v251 \(live 9 Oct 11:49\)/.test(code(M, 'Early Room Plan'))) {
  const codes = heads.replace(/❌/g, ':x:').replace(/✅/g, ':white_check_mark:');
  r = turn(M, RA, [U(12, 'book 11-1 instead'), J(11, codes), U(10, 'book tomorrow 12-2pm studio 7')], { reply: 'Studio 7 is free then. What\'s the session type, project, client and engineer?' });
  ok(r.plan.run && r.plan.room === 'Studio 7' && r.plan.knownRoom === 'Studio 7', 'Studio 7 kept, checked again at 11-1', r.plan);
  ok(r.out === (/v255 \(PENDING 109/.test(code(M, 'Guard Probe')) ? '🗓️ Studio 7 · Saturday, October 9 · 11:00 AM – 1:00 PM\n\n' : '✅ Studio 7 is free · Saturday, October 9 · 11:00 AM – 1:00 PM\n') + 'What\'s the session type, project and client? (or "none" for no client)', 'the restated line with the room, no engineer asked (the requester is one)', r.out);
  r = turn(M, RA, [U(12, 'studio 7 12-2pm please'), J(11, codes), U(10, 'book tomorrow 12-2pm studio 7')]);
  ok(!r.plan.run && r.plan.why === 'already told this booking', 'the same time again: "already told" now works on Slack\'s text too', r.plan);
}
console.log('103 - the same taken time again goes on to the normal flow (a priority request can still be made)');
r = turn(M, RA, [U(12, 'studio 7 12-2pm please'), J(11, heads), U(10, 'book tomorrow 12-2pm studio 7')]);
ok(!r.plan.run && r.plan.why === 'already told this booking', 'told once: not checked again', r.plan);
r = turn(M, RA, [U(12, 'still studio 7'), J(11, heads), U(10, 'book tomorrow 12-2pm studio 7')]);
ok(!r.plan.run, '"still studio 7": not checked again', r.plan);
console.log('103 - a new time that is also taken: told again');
r = turn(M, RA, [U(12, 'how about 2-4 instead'), J(11, heads), U(10, 'book tomorrow 12-2pm studio 7')]);
show('2-4 instead', r.out);
ok(r.plan.run && r.plan.hours === '14:00-16:00' && /^❌ Heads up: \*Studio 7 is already booked 1:00 PM – 3:00 PM\*/.test(r.out) && /• 3:00 PM – 5:00 PM\n• 11:00 AM – 1:00 PM/.test(r.out),
  '2-4 PM is taken too: the heads-up again, 3-5 PM (nearer) before 11-1', r.out);
console.log('103 - a studio Jessie offered is taken when named');
r = turn(M, RA, [U(12, 'studio 8 then'), J(11, heads), U(10, 'book tomorrow 12-2pm studio 7')]);
ok(r.plan.run && r.plan.room === 'Studio 8' && r.res.earlyRoom.mode === 'free', '"studio 8 then": Studio 8, at 12-2 PM, free', [r.plan, r.res && r.res.earlyRoom]);

console.log('102 - no same-day time');
const FULL = [E('Studio 7', '2027-10-09', '08:00', '13:00', 'A / HL', 'U2'), E('Studio 7', '2027-10-09', '13:00', '22:00', 'B / HL', 'U3')];
r = turn(M, RA, h1, { inMsg: '2027-10-09', cal: FULL });
show('no same-day time', r.out);
ok(!/same day/.test(r.out) && /is free at that time on:\n• Sunday, October 10\n• Monday, October 11\n\nWant one/.test(r.out), 'nothing that day -> two other days', r.out);
console.log('102 - suggestions stay within 8 AM - 10 PM');
r = turn(M, RA, [U(10, 'book studio 7 tomorrow 8-10pm')], { inMsg: '2027-10-09', cal: [E('Studio 7', '2027-10-09', '19:00', '21:00', 'LATE / HL', 'U2')] });
show('8-10 PM', r.out);
ok(r.bf.timeStart === '20:00' && /• 5:00 PM – 7:00 PM\n/.test(r.out) && !/• 9:00 PM/.test(r.out), '8-10 PM taken: 5-7 PM offered, nothing past 10 PM', r.out);

console.log('104 - day by day: a blank line more between days');
let a = raRun(RA, { start_iso: '2027-10-09T00:00:00+08:00', end_iso: '2027-10-10T23:59:00+08:00', reference_data: REF, scope: 'studios' }, CAL);
show('two days', a.reply_text);
ok(/\n\n\n🗓️ /.test(a.reply_text) && !/\n\n\n\n/.test(a.reply_text), 'two blank lines before the next day (none elsewhere)', a.reply_text);
a = raRun(RA, { start_iso: '2027-10-09T00:00:00+08:00', end_iso: '2027-10-10T23:59:00+08:00', room: 'Studio 7', reference_data: REF }, CAL);
ok(/free the rest of the day\.\n\n\n🗓️ October 10/.test(a.reply_text), 'the same with a room asked about', a.reply_text);
const gpO = new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output: 'Here you go.', intermediateSteps: [{ action: { tool: 'Room_Availability' }, observation: JSON.stringify([raRun(RA, { start_iso: '2027-10-09T00:00:00+08:00', end_iso: '2027-10-10T23:59:00+08:00', reference_data: REF, scope: 'studios' }, CAL)]) }] } }]),
  n => { if (n === 'Early Room Result') throw new Error('not executed'); return wrap(n === 'Slack Trigger' ? [{ json: { text: 'what studios are free tomorrow and sunday' } }] : rec(n) || [{ json: {} }]); })[0].json.output;
ok(/\n\n\n🗓️ /.test(gpO), 'Guard Probe sends the extra line as it is', gpO);
a = raRun(RA, { start_iso: '2027-10-09T12:00:00+08:00', end_iso: '2027-10-09T14:00:00+08:00', room: 'Studio 7', reference_data: REF }, CAL);
const a0 = raRun(ORA, { start_iso: '2027-10-09T12:00:00+08:00', end_iso: '2027-10-09T14:00:00+08:00', room: 'Studio 7', reference_data: REF }, CAL);
ok(JSON.stringify(a) === JSON.stringify(a0), 'a one-day answer is exactly v21\'s');

console.log('102 - Book Session ROOM_OCCUPIED (prepare)');
const TXT = 'book studio 7 tomorrow 12-2pm, vo recording, project orange, client jem lim, engineer howard';
const cc = (w, cal, req = {}) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    rooms: 'Studio 7', engineer: 'Howard Luistro', session_type: 'VO Recording', client: 'Jem Lim', expected_date: '2027-10-09', start_iso: '2027-10-09T12:00:00+08:00', end_iso: '2027-10-09T14:00:00+08:00',
    summary: 'ORANGE / Jem Lim / HL', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: TXT, requester_text: TXT, ...req } }];
  const O = { 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim' } } }], 'Client Aliases': [{ json: {} }], 'All Client Names': [{ json: { fields: { Name: 'Jem Lim' } } }] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(rec('All Bookers') || [{ json: {} }]) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: cal } }]), () => ({}))[0].json; };
const rr = v => new Function('$', '$input', code(B, 'Return Rejection'))(() => wrap([{ json: {} }]), wrap([{ json: v }]))[0].json;
let c = cc(B, CAL), o = rr(c);
ok(c.reason === 'ROOM_OCCUPIED' && JSON.stringify(o.same_day_slots) === JSON.stringify([{ start: '2027-10-09T11:00:00+08:00', end: '2027-10-09T13:00:00+08:00' }, { start: '2027-10-09T15:00:00+08:00', end: '2027-10-09T17:00:00+08:00' }]),
  'same day: 11 AM - 1 PM, then 3 - 5 PM, passed to the agent', o.same_day_slots);
const gpB = (out, obs) => new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output: out, intermediateSteps: [{ action: { tool: 'Prepare_Booking', toolInput: {} }, observation: JSON.stringify([obs]) }] } }]),
  n => { if (n === 'Early Room Result') throw new Error('not executed'); return wrap(n === 'Booked For' ? [{ json: { requesterText: TXT } }] : rec(n) || [{ json: {} }]); })[0].json.output;
let t = gpB('Studio 7 is taken.', o); show('Book Session ROOM_OCCUPIED', t);
ok(/^❌ Heads up: \*Studio 7 is already booked 1:00 PM – 3:00 PM\* on Saturday, October 9 by this session: CATTAIL \/ Sasa Abella \/ HL\n\n✅ Studio 7 is free on the same day at:\n• 11:00 AM – 1:00 PM\n• 3:00 PM – 5:00 PM\n\n✅ Free at that time:\n/.test(t),
  'the reply: heads-up, the same-day times, then other rooms', t);
c = cc(B, [E('Studio 7', '2027-10-09', '13:00', '15:00', 'MINE / HL', ME)]);
ok(c.own_booking === true && !('same_day_slots' in c), 'your own booking: the move question, no options (as before)', c);
c = cc(B, CAL, { mode: 'book', confirmed: true, prepared_ok: true });
ok(c.reason === 'ROOM_OCCUPIED' && Array.isArray(c.same_day_slots) && c.same_day_slots.length === 0, 'book mode (window only read): no same-day times offered', c.same_day_slots);
const qB = n => code(B, 'Get Events In Window') ;
const qs = JSON.stringify(B.nodes.find(x => x.name === 'Get Events In Window').parameters);
ok(/if \(String\(j\.mode \|\| ''\)\.trim\(\)\.toLowerCase\(\) === 'prepare'\) \{/.test(qs.replace(/\\'/g, "'")) && (qs.match(/=== 'prepare'\) \{   \/\/ v101/g) || []).length === 2, 'the calendar read: the whole day for every prepare (timeMin and timeMax)');

console.log('106 - a Management meeting in a conference room');
const CONF = { rooms: 'Salin', session_type: '', engineer: '', client: '', bookingType: 'Internal', department: 'Management', start_iso: '2027-10-11T12:00:00+08:00', end_iso: '2027-10-11T13:00:00+08:00', expected_date: '2027-10-11' };
const desc = f => 'Booked by: Camy Caridad' + (f ? ' (for ' + f + ')' : '') + ' | ref: ' + ME;
c = cc(B, [], { ...CONF, summary: 'SALIN - Management', description: desc('Vic Icasas'), requester_text: 'Pls Book salin on monday with sir vic at 12pm-1pm' });
ok(c.final_summary === 'SALIN - Vic Icasas', 'QA B6: "SALIN - Management" -> "SALIN - Vic Icasas"', [c.verdict, c.reason, c.final_summary, c.human]);
c = cc(B, [], { ...CONF, summary: 'SALIN - Budget Review - Mgmt', description: desc('Vic Icasas') });
ok(c.final_summary === 'SALIN - Budget Review', 'a meeting title: the department dropped, the title kept', c.final_summary);
c = cc(B, [], { ...CONF, summary: 'SALIN - Mgmt', description: desc('') });
ok(c.verdict === 'REJECTED' && c.reason === 'NEED_MEETING_TITLE' && /Ask exactly this, in one message: "What’s the meeting title\?"/.test(c.human), 'no title, no one named: asks for the meeting title', [c.reason, c.human]);
c = cc(B, [], { ...CONF, summary: 'KATHA - Mgmt x BD', rooms: 'Katha', description: desc('') });
ok(c.final_summary === 'KATHA - Mgmt x BD', 'a joint meeting keeps its departments', c.final_summary);
c = cc(B, [], { ...CONF, summary: 'KATHA - Marketing', rooms: 'Katha', department: 'Marketing', description: desc('') });
ok(c.final_summary === 'KATHA - Marketing', 'another department: unchanged', c.final_summary);
c = cc(B, CAL, { summary: 'MGMT / Jem Lim / HL' });
ok(c.reason === 'ROOM_OCCUPIED', 'a studio title is never touched by it', c.reason);
const sm = M.nodes.find(x => x.type.endsWith('.agent')).parameters.options.systemMessage;
ok(/A meeting of Management alone has no department segment/.test(sm) && /Management → Mgmt \(only with another department\)/.test(sm), 'the prompt says so');

console.log('Book Session v102 - a person in a conference-room title (live 9 Oct 11:41)');
if (/v102 \(live 9 Oct 11:41\)/.test(code(B, 'Check Conflicts'))) {
  c = cc(B, [], { ...CONF, summary: 'SALIN - Sir Vic', description: desc('') });
  ok(c.final_summary === 'SALIN - Vic Icasas', '"SALIN - Sir Vic" -> "SALIN - Vic Icasas"', c.final_summary);
  c = cc(B, [], { ...CONF, summary: "SALIN - Ma'am Jen", description: desc('') });
  ok(/^SALIN - (?!Ma)/.test(c.final_summary), 'an honorific is dropped even when the name is not one staff member', c.final_summary);
  c = cc(B, [], { ...CONF, summary: 'SALIN - Budget Review', description: desc('') });
  ok(c.final_summary === 'SALIN - Budget Review', 'a meeting title is left alone', c.final_summary);
  c = cc(B, [], { ...CONF, summary: 'SALIN - Sir Vic - Mgmt x BD', description: desc('') });
  ok(c.final_summary === 'SALIN - Vic Icasas - Mgmt x BD', 'with departments: only the person changes', c.final_summary);
}
console.log('Book Session v103 / Cancel Booking v25');
if (/v103 \(PENDING 83/.test(code(B, 'Check Conflicts'))) {
  c = cc(B, [], { rooms: 'M3', summary: '', session_type: '', engineer: '', client: '', all_day: true, start_iso: '2027-10-11', end_iso: '2027-10-12', expected_date: '2027-10-11', description: 'Booked by: Howard Luistro | ref: ' + ME });
  ok(c.reason !== 'MISSING_DETAILS' && /^M3 - Howard$/.test(c.final_summary || ''), 'an M booth with no title: "M3 - Howard", nothing asked (PENDING 83)', [c.verdict, c.reason, c.final_summary]);
}
{ const CB = WF(process.env.CANCEL || 'cancel-booking-v25.json'), C0 = code(CB, 'Check Ownership');
  if (/v25 \(live 9 Oct 12:19\)/.test(C0)) { const cxTime = new Function(C0.slice(C0.indexOf('const cxTime'), C0.indexOf('const cxN')) + '; return cxTime;')();
    ok(cxTime({ start: { dateTime: '2027-10-10T00:00:00+08:00' }, end: { dateTime: '2027-10-11T00:00:00+08:00' } }) === 'All day', 'a 12:00 AM - 12:00 AM hold reads "All day", as its card (live 12:19)');
    ok(cxTime({ start: { dateTime: '2027-10-10T13:00:00+08:00' }, end: { dateTime: '2027-10-10T15:00:00+08:00' } }) === '1:00 PM – 3:00 PM', 'a timed booking is unchanged'); } }
console.log('main v254 - an all-day hold stored with times (live 9 Oct 12:26)');
if (/v254 \(live 9 Oct 12:26\)/.test(code(M, 'Early Room Result'))) {
  const HOLD = [{ id: 'h', summary: 'M6 - Marketing', location: 'M6', description: 'ref: U9', transparency: 'transparent',
    start: { dateTime: '2027-10-12T00:00:00+08:00' }, end: { dateTime: '2027-10-13T00:00:00+08:00' } }];
  r = turn(M, RA, [U(10, 'book m6 on tuesday')], { dates: '2027-10-12', inMsg: '2027-10-12', cal: HOLD });
  ok(r.out.startsWith('❌ Heads up: *M6 is already booked all day* on Tuesday, October 12'), '"booked all day", not "12:00 AM – 12:00 AM"', r.out);
}
console.log('Book Session v104 (PENDING 110 / 111, M booth nickname)');
if (/v104 \(PENDING 110/.test(code(B, 'Check Conflicts'))) {
  c = cc(B, [], { summary: 'QATEST1 / Jem Lim / HL', session_type: 'Post Mixing', requester_text: 'book studio 6 tomorrow 2-4pm. mixing, project QATEST1, client jem lim', start_iso: '2027-10-10T14:00:00+08:00', end_iso: '2027-10-10T16:00:00+08:00', expected_date: '2027-10-10', rooms: 'Studio 6' });
  ok(/^(?:SESSION_TYPE_CHECK|NEED_SESSION_TYPE)$/.test(c.reason) && /Ask exactly this, in one message: "Which (?:kind of mixing|one) - [^"]*Post Mixing[^"]*\?/.test(c.human), '"mixing" alone: asked which kind, from the session types (live 15:09)', [c.reason, c.human]);
  c = cc(B, [], { summary: 'QATEST1 / Jem Lim / HL', session_type: 'Post Mixing', requester_text: 'book studio 6 tomorrow 2-4pm. post mixing, project QATEST1, client jem lim', start_iso: '2027-10-10T14:00:00+08:00', end_iso: '2027-10-10T16:00:00+08:00', expected_date: '2027-10-10', rooms: 'Studio 6' });
  ok(!/^(?:SESSION_TYPE_CHECK|NEED_SESSION_TYPE)$/.test(c.reason), '"post mixing" typed: not asked', c.reason);
  c = cc(B, [], { summary: 'PROJECT BLUE BIRD / Jem Lim / HL', requester_text: 'book studio 7 tomorrow 3-5pm, vo recording, project blue bird, client is jem lim, engineer howard' });
  ok(/^BLUE BIRD \/ Jem Lim \/ HL$/.test(c.final_summary || ''), '"PROJECT BLUE BIRD" -> "BLUE BIRD" (live 15:28)', [c.reason, c.final_summary]);
  c = cc(B, [], { rooms: 'M4', summary: 'M4 - Howie', session_type: '', engineer: '', client: '', all_day: true, start_iso: '2027-10-12', end_iso: '2027-10-13', expected_date: '2027-10-12', description: 'Booked by: Howard Luistro | ref: ' + ME });
  ok(/^M4 - (Howard|Howie)$/.test(c.final_summary || ''), 'M booth nickname -> first name when it is one staff member ("M4 - Howie", live 12:57)', c.final_summary);
}
console.log('wiring');
const chk = M.nodes.find(x => x.name === 'Early Room Check').parameters.workflowInputs;
ok(chk.schema.some(x => x.id === 'hours') && chk.value.hours === "={{ $json.earlyPlan.hours || '' }}", 'Early Room Check passes hours');
ok(RA.nodes.find(x => x.name === 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'hours'), 'Room Availability takes hours');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
