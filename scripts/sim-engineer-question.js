#!/usr/bin/env node
// Offline tests for main v207 + Book Session v75 (engineer question, PENDING 73). Live 1 Oct 14:36: a series booked
// by an engineer got "Who's the client, and who's engineering?".
//
//   node scripts/sim-engineer-question.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v207.json'), OLD = WF('project-jessie-v206.json'), B = WF(process.env.BOOK || 'book-session-v75.json');
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const ME = 'U08V3CKDGJF';
const REQ = 'book qaseries every monday in november 2027 2-4pm vo recording studio 8';

const gp = (w, output, bfo, said = REQ) => new Function('$input', '$', code(w, 'Guard Probe'))(
  wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: [] } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '', ...bfo } }])
     : n === 'Gate Context' ? wrap([{ json: { ...(((rec('Gate Context') || [{ json: {} }])[0] || {}).json || {}), datesUnderDiscussion: '2027-11-01' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
const KNOWN = { engineer: 'Howard Luistro', engineerResolved: true, engineerDefault: true };

console.log('Guard Probe - an engineer booking is never asked');
let o = gp(M, "Who's the client, and who's engineering?", KNOWN);
ok(o === "Who's the client?", 'live 14:36: "Who\'s the client, and who\'s engineering?" -> "Who\'s the client?"', o);
ok(/engineering/.test(gp(OLD, "Who's the client, and who's engineering?", KNOWN)), '  (v206: sent as written)');
o = gp(M, 'What session type is this, who is the client, and who is engineering?', KNOWN);
ok(o === 'What session type is this and who is the client?', 'three questions -> the other two', o);
o = gp(M, 'Got it. Who will be engineering the session?', { ...KNOWN, client: 'Jem Lim' });
ok(o === 'Got it.' , 'a sentence before it is kept, the question goes', o);
o = gp(M, 'Who is the assigned engineer?', KNOWN);
ok(o === 'Who’s the client? (or "none")', 'only the engineer was asked, no client yet -> the client question', o);
o = gp(M, 'Who is the assigned engineer?', { ...KNOWN, client: 'Jem Lim' });
ok(!/engineer/i.test(o) && o.length > 0, 'only the engineer was asked, client known -> no engineer question, never empty', o);
o = gp(M, 'Who’s the client? (or "none")\nAnd who’s engineering?', KNOWN);
ok(o === 'Who’s the client? (or "none")', '"And who’s engineering?" line goes', o);
o = gp(M, 'Do you have an engineer in mind?', { ...KNOWN, client: 'X' });
ok(!/engineer in mind/.test(o), '"an engineer in mind" goes');
o = gp(M, 'Is Daryl Reyes the engineer, or Daryl Cruz?', KNOWN);
ok(o === 'Is Daryl Reyes the engineer, or Daryl Cruz?', 'a question naming people is left alone', o);
const CARD = '*QASERIES / HL*\n*Dates (5):*\n- Monday, 1 November 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.';
ok(gp(M, CARD, KNOWN) === gp(OLD, CARD, KNOWN), 'a card is not touched');

console.log('Guard Probe - when it is asked, it reads "Who’s the engineer?"');
o = gp(M, "Who's the client, and who's engineering?", {});
ok(o === "Who's the client and who’s the engineer?", '"who\'s engineering" -> "who’s the engineer"', o);
ok(gp(M, 'Who’s engineering?', {}) === 'Who’s the engineer?', 'Book Session v74\'s question -> "Who’s the engineer?"');
ok(gp(M, 'Who is the assigned engineer?', {}) === 'Who’s the engineer?', '"the assigned engineer" -> "Who’s the engineer?"');
ok(gp(M, 'Who’s the engineer?', {}) === 'Who’s the engineer?', 'already right -> unchanged');
o = gp(M, 'What session type is this, who is the client, and who is engineering?', {});
ok(o === 'What session type is this, who is the client, and who’s the engineer?', 'in a list of three', o);

console.log('Booked For - the default, and bare answers after the curly ’ (since Book Session v73)');
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1790835000 + (convo.length - i) * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }])
    : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
let b = bf(M, [{ user: ME, text: REQ }]);
ok(b.engineerResolved === true && b.engineer === 'Howard Luistro' && /do not ask who the engineer is/i.test(b.notice || ''), 'an engineer requester -> the engineer is them (so Guard Probe drops the question)', [b.engineer, b.notice]);
b = bf(M, [{ user: ME, text: 'book studio 8 tomorrow 2-4pm vo recording for jem lim, no engineer yet' }]);
ok(!b.engineerResolved, '"no engineer" -> not defaulted (the question can still be asked)', b.engineer);
const ARR = { bot_id: 'B1', text: 'Who’s the arranger?' };
b = bf(M, [{ user: ME, text: REQ }, ARR, { user: ME, text: 'bp' }]);
const bOld = bf(OLD, [{ user: ME, text: REQ }, ARR, { user: ME, text: 'bp' }]);
ok(b.arrangerResolved === true && !bOld.arrangerResolved, 'a bare "bp" after "Who’s the arranger?" is the arranger (v206 missed it: curly ’)', [b.arranger, bOld.arranger]);

console.log('Book Session v75 - its question');
const cc = code(B, 'Check Conflicts');
ok(/"Who\\u2019s the engineer\?"/.test(cc) && !/Who\\u2019s engineering/.test(cc), 'scripted "Who’s the engineer?"');
const sm = M.nodes.find(x => x.name === 'Jessie AI Agent').parameters.options.systemMessage;
ok(/Ask "Who's the engineer\?"/.test(sm) && !/who's engineering/i.test(sm), 'prompt: "Who\'s the engineer?"');

console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
