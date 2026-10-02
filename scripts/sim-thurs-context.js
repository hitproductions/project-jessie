#!/usr/bin/env node
// Offline tests for main v215 + Book Session v87 (live 2 Oct 13:20-13:27): "yes so i can book it" was taken as a new
// request (context lost), and "Booked." repeated the heads-up.
//   node scripts/sim-thurs-context.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v215.json'), OM = WF('project-jessie-v214.json'), B = WF(process.env.BOOK || 'book-session-v87.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const ME = 'U08V3CKDGJF';
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1790918000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const CONVO = [{ user: ME, text: 'book studio 7 for cattail isr' }, { bot_id: 'B1', text: 'Studio 7 is busy ... What’s the project?' }, { user: ME, text: 'sure studio 8 is fine' },
  { bot_id: 'B1', text: 'Who’s the client? (or "none") And what time? What’s the project?' }, { user: ME, text: 'michael v client. project is cattail isr' },
  { bot_id: 'B1', text: 'Studio 8 is taken ...' }, { user: ME, text: 'what times are studio 8 free next thursday' }, { bot_id: 'B1', text: 'Studio 8 is free all day ...' },
  { user: ME, text: 'yes so i can book ito. i already said 11am-3pm' }];
console.log('Booked For - an answer that says "book" keeps the booking\'s earlier messages');
let b = bf(M, CONVO), o = bf(OM, CONVO);
ok(/cattail isr/.test(b.requesterText) && /michael v/.test(b.requesterText) && /book studio 7 for cattail isr/.test(b.requesterText), 'live 13:25: the project, client and "isr" still in the requester\'s words', b.requesterText);
ok(!/cattail/.test(o.requesterText), '  (v214: only "yes so i can book ito...")', o.requesterText);
b = bf(M, [{ user: ME, text: 'book studio 7 tomorrow 2pm for project cats' }, { bot_id: 'B1', text: 'Booked.' }, { user: ME, text: 'can you book studio 8 friday 3pm for project dogs' }]);
ok(!/cats/.test(b.requesterText) && /dogs/.test(b.requesterText), 'a real new request still starts a new booking');
for (const t of ['yes book it', 'ok book that', 'i already said book studio 8', 'so book it please']) {
  const r = bf(M, [{ user: ME, text: 'book studio 7 tomorrow 2pm for project cats' }, { bot_id: 'B1', text: 'What kind of session is this?' }, { user: ME, text: t }]);
  ok(/project cats/.test(r.requesterText), JSON.stringify(t) + ' -> not a new request', r.requesterText); }
console.log('Book Session v87 - "Booked." only');
ok(/human: 'Booked\.' \} \}\];/.test(code(B, 'Verify')) && !/'Booked\. ' \+ note/.test(code(B, 'Verify')), 'the Booked reply is "Booked." (no repeated duration note)');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
