#!/usr/bin/env node
// Offline tests for main v222 + Book Session v92 (live 6 Oct 14:35-14:37 PHT on main v221 / v91): "project dinos 10-12pm"
// put the time in the project, and "that will be all" to the client question became the client.
//   node scripts/sim-time-and-filler.js <main-execution.json>   (its All Bookers output feeds both)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v222.json'), OM = WF('project-jessie-v221.json');
const B = WF(process.env.BOOK || 'book-session-v92.json'), OB = WF('book-session-v91.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const ME = 'U08V3CKDGJF';
Date.now = () => Date.parse('2026-10-06T06:37:00Z');
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1791268000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const B1 = t => ({ bot_id: 'B1', text: t }), U = t => ({ user: ME, text: t });
const LIVE = [U('book studio 7 for oct 8'), B1('What kind of session is this, what’s the project, and what time? Who’s the client? (or "none")'), U('mixing session. project dinos 10-12pm'),
  B1('Which one - Post Mixing, Localization Mixing, Localization Atmos Mixing or Music Mixing?'), U('post mix'), B1('Who’s the client? (or "none")'), U('that will be all')];

console.log('Booked For v222 - the project stops at a time');
let o = bf(M, LIVE);
ok(String(o.project).toLowerCase() === 'dinos', 'live 14:36: "project dinos 10-12pm" -> DINOS', o.project);
ok(/10-12pm/i.test(String(bf(OM, LIVE).project)), '  (v221: "dinos 10-12pm")', bf(OM, LIVE).project);
for (const [txt, want] of [['project dinos 10-12pm', 'dinos'], ['project dinos 2pm', 'dinos'], ['project dinos at 2pm', 'dinos'], ['project dinos 10:30-12', 'dinos'],
    ['project dinos 10 - 12pm', 'dinos'], ['project dinos 10 to 12pm', 'dinos'], ['project dinos 3 pm', 'dinos'], ['project DINOS 10-12PM', 'DINOS'], ['project dinos noon', 'dinos'],
    ['project dinos 10/8 2-4pm', 'dinos'], ['project SEASON 2', 'SEASON 2'], ['project top 10', 'top 10'], ['project top 10, 2-4pm', 'top 10'], ['project thank you', 'thank you'], ['project wheat sun. 3-5pm', 'wheat sun']])
  ok(String(bf(M, [U('book studio 7 tomorrow vo recording, ' + txt)]).project) === want, JSON.stringify(txt) + ' -> ' + want, bf(M, [U('book studio 7 tomorrow vo recording, ' + txt)]).project);

console.log('Booked For v222 - filler is not a client');
ok(!o.client, 'live 14:37: "that will be all" -> no client', o.client);
ok(!!bf(OM, LIVE).client, '  (v221: read as a client - "that"; the model then passed "That Will Be All")', bf(OM, LIVE).client);
const ans = a => bf(M, [U('book studio 7 tomorrow 2-4pm post mixing project dinos'), B1('Who’s the client? (or "none")'), U(a)]).client;
for (const a of ['ok thanks', 'nothing else', 'idk', "that's all", 'not sure', 'wala pa', 'sige', 'ok na yun', 'later'])
  ok(!ans(a), JSON.stringify(a) + ' -> no client', ans(a));
for (const [a, want] of [['john ableton', 'john ableton'], ['Jem Lim', 'Jem Lim'], ['sir vic', 'sir vic'], ['Spotify', 'Spotify']])
  ok(String(ans(a)) === want, JSON.stringify(a) + ' -> ' + want, ans(a));

console.log('Book Session v92 - the backstop');
const REF = JSON.stringify({ rooms: [{ id: 'r7', name: 'Studio 7', common: false }], types: [{ type: 'Post Mixing', typical: 120, ranked: ['Studio 7'], priority: ['Studio 7'] }] });
const cc = (w, req) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    rooms: 'Studio 7', engineer: 'Howard Luistro', session_type: 'Post Mixing', client: '', expected_date: '2027-10-08', start_iso: '2027-10-08T10:00:00+08:00', end_iso: '2027-10-08T12:00:00+08:00',
    description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: '', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const RT = LIVE.filter(m => m.user).map(m => m.text).reverse().join('\n');
const ASK = LIVE.filter(m => m.bot_id).map(m => m.text).reverse().join('\n');
let c = cc(B, { summary: 'DINOS 10-12PM / That Will Be All / HL', client: 'That Will Be All', requester_text: RT, asked_text: ASK });
ok(c.reason === 'NEED_CLIENT' && relay(c.human) === 'Who’s the client? (or "none")', 'live 14:37 inputs -> the client asked again, no card', [c.reason, relay(c.human)]);
const c91 = cc(OB, { summary: 'DINOS 10-12PM / That Will Be All / HL', client: 'That Will Be All', requester_text: RT, asked_text: ASK });
ok(c91.verdict === 'CLEAR' && /That Will Be All/.test(c91.final_summary), '  (v91: the card "DINOS 10-12PM / That Will Be All / HL")', [c91.verdict, c91.final_summary]);
c = cc(B, { summary: 'DINOS 10-12PM / HL', client: '', requester_text: RT + '\nnone', asked_text: ASK });
ok(c.verdict === 'CLEAR' && c.final_summary === 'DINOS / HL', 'a time on the end of the project -> taken off ("DINOS / HL")', [c.verdict, c.final_summary]);
c = cc(B, { summary: 'DINOS 2PM / John Ableton / HL', client: 'John Ableton', requester_text: 'book studio 7 oct 8 post mixing project dinos 2pm, client john ableton', asked_text: '' });
ok(c.verdict === 'CLEAR' && c.final_summary === 'DINOS / John Ableton / HL', '"DINOS 2PM / John Ableton / HL" -> "DINOS / John Ableton / HL"', [c.verdict, c.reason, c.final_summary, c.human]);
c = cc(B, { summary: 'SEASON 2 / John Ableton / HL', client: 'John Ableton', requester_text: 'book studio 7 oct 8 10-12pm post mixing project season 2, client john ableton', asked_text: '' });
ok(c.verdict === 'CLEAR' && c.final_summary === 'SEASON 2 / John Ableton / HL', '"SEASON 2" keeps its number', [c.verdict, c.final_summary]);
c = cc(B, { summary: 'DINOS / John Ableton / HL', client: 'John Ableton', requester_text: RT + '\njohn ableton', asked_text: ASK });
ok(c.verdict === 'CLEAR' && c.final_summary === 'DINOS / John Ableton / HL', 'a real client stays', [c.verdict, c.final_summary]);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
