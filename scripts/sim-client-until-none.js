#!/usr/bin/env node
// Offline tests for main v219 + Book Session v90 (client until none; decided 6 Oct, on top of v218 / v89):
// the client is asked until the requester names one or declines (v89 stopped after two asks).
//   node scripts/sim-client-until-none.js <main-execution.json>   (its All Bookers output feeds Book Session too)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v219.json'), OM = WF('project-jessie-v218.json');
const B = WF(process.env.BOOK || 'book-session-v90.json'), OB = WF('book-session-v89.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const ME = 'U08V3CKDGJF';
const REF = JSON.stringify({ rooms: [{ id: 'r8', name: 'Studio 8', common: false }, { id: 'rl', name: 'Likha', common: true }],
  types: ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording', 'Localization Mixing', 'Localization Atmos Mixing', 'Music Mixing', 'Localization Dubbing', 'Meeting']
    .map(t => ({ type: t, typical: 120, ranked: ['Studio 8'] })) });
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const cc = (w, req, client = [{ json: {} }]) => {
  const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    expected_date: '2027-10-14', start_iso: '2027-10-14T15:00:00+08:00', end_iso: '2027-10-14T17:00:00+08:00', rooms: 'Studio 8', engineer: 'Howard Luistro',
    description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: '', client: '', ...req } }];
  const O = { 'Get Client': client, 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };


const Q = 'Who’s the client? (or "none")';
const T3 = 'book studio 8 next thu 3-5pm\nmixing. for proj runway\npost mixing';
const A2 = 'Which one - Post Mixing, Localization Mixing, Localization Atmos Mixing or Music Mixing? ' + Q + '\nWhat kind of session is this? What’s the project, and who’s the client? (or "none")';
console.log('Book Session v90 - asked until answered or declined');
let c = cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3, asked_text: A2 });
ok(c.reason === 'NEED_CLIENT' && relay(c.human) === Q, 'passed by twice -> asked again', [c.reason, relay(c.human)]);
ok(cc(OB, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3, asked_text: A2 }).verdict === 'CLEAR', '  (v89: the card, no client)');
c = cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3 + '\nok', asked_text: Q + '\n' + Q + '\n' + A2 });
ok(c.reason === 'NEED_CLIENT', 'passed by four times -> still asked', c.reason);
for (const d of ['none', 'None.', 'no client', 'No client yet', 'nope', 'nah', 'n/a', 'NA', 'wala', 'walang client', 'nobody', 'no one', 'not applicable', 'none for now',
    'there is no client', "there's no client", 'without a client', 'client is tbd', 'client: none', 'no', 'No.'])
  ok(cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3 + '\n' + d, asked_text: Q + '\n' + A2 }).verdict === 'CLEAR', JSON.stringify(d) + ' -> declined, the card');
for (const d of ['no, make it 4-6pm', 'none of those rooms', 'post mixing'])
  ok(cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3 + '\n' + d, asked_text: Q + '\n' + A2 }).reason === 'NEED_CLIENT', JSON.stringify(d) + ' -> not a decline, asked again');
c = cc(B, { summary: 'SESSION / HL', session_type: '', requester_text: 'book studio 8 next thu 3-5pm', asked_text: Q + '\n' + Q });
ok(/who’s the client/.test(relay(c.human) || ''), 'a combined question still carries the client after earlier asks', relay(c.human));

console.log('Booked For v219 - a bare answer to the client question is the client');
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1790918000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const conv = ans => [{ user: ME, text: 'book studio 8 next thu 3-5pm post mixing project runway' }, { bot_id: 'B1', text: Q }, { user: ME, text: ans }];
let o = bf(M, conv('john ableton'));
ok(String(o.client).toLowerCase() === 'john ableton', '"john ableton" after the client question -> the client', o.client);
ok(!bf(OM, conv('john ableton')).client, '  (v218: no client - left to the model)');
ok(String(bf(M, conv('Jem Lim.')).client) === 'Jem Lim', '"Jem Lim." -> Jem Lim', bf(M, conv('Jem Lim.')).client);
for (const a of ['none', 'nope', 'no client', 'n/a', 'post mixing', 'make it 4-6pm', 'studio 7 instead'])
  ok(!bf(M, conv(a)).client, JSON.stringify(a) + ' -> no client read', bf(M, conv(a)).client);
o = bf(M, [{ user: ME, text: 'book studio 8 next thu 3-5pm' }, { bot_id: 'B1', text: 'What kind of session is this? What’s the project, and who’s the client? (or "none")' }, { user: ME, text: 'post mixing' }]);
ok(!o.client, 'an answer to a combined question is not read as the client', o.client);
o = bf(M, [{ user: ME, text: 'book studio 8 next thu 3-5pm post mixing project runway, client is vic' }]);
ok(String(o.client).toLowerCase() === 'vic', '"client is vic" still read as before', o.client);

console.log('Guard Probe v219 - no client question after a decline');
const gp = (W, output, said) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output, intermediateSteps: [] } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { datesUnderDiscussion: '2027-10-14' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(recM(n) || [{ json: {} }]))[0].json.output;
for (const d of ['nope', 'n/a', 'nobody'])
  ok(gp(M, 'What kind of session is this?', 'book studio 8 next thu 3-5pm project runway\n' + d) === 'What kind of session is this?', JSON.stringify(d) + ' -> nothing added');
ok(/who’s the client/.test(gp(M, 'What kind of session is this?', 'book studio 8 next thu 3-5pm')), 'nothing said -> the client is asked');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
