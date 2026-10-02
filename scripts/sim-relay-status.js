#!/usr/bin/env node
// Offline tests for main v216 (relay Book Session questions) - fixes v203. Live 2 Oct 13:41 (exec 21813): Book Session
// asked "Is this internal, or personal?" and the model sent all four types; the relay tested `verdict`, but Return
// Rejection hands the agent `status`. Observations here are in Return Rejection's shape, as exec 21813 shows them.
//   node scripts/sim-relay-status.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v216.json'), OM = WF('project-jessie-v215.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run2 = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec2 = n => run2[n] ? (((run2[n][0].data || {}).main || [[]])[0] || []) : null;
const said = 'can you book studio 8 thurs 11am-3pm for VO recording, project CATTAIL, client vic icasas';
const rej = (reason, q) => JSON.stringify([{ status: 'REJECTED', reason, conflicts: null, unverifiable: null,
  human: 'Nothing was prepared. Ask exactly this, in one message: "' + q + '" Then prepare it again with their answer.' }], null, 2);
const gp = (W, output, steps) => new Function('$input', '$', code(W, 'Guard Probe'))(
  wrap([{ json: { ...((rec2('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { ...(((rec2('Gate Context') || [{ json: {} }])[0] || {}).json || {}), datesUnderDiscussion: '2027-10-07' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec2(n) || [{ json: {} }]))[0].json.output;
const step = (obs, tool = 'Prepare_Booking') => ({ action: { tool, toolInput: {} }, observation: obs });
const FOUR = 'Is this advertising, entertainment, internal, or personal?';
console.log('Guard Probe v216 - Book Session\'s question goes out as written (status, not verdict)');
let o = gp(M, FOUR, [step(rej('NEED_BOOKING_TYPE', 'Is this internal, or personal?'))]);
ok(o === 'Is this internal, or personal?', 'live 13:41 (exec 21813): the four types -> "Is this internal, or personal?"', o);
ok(gp(OM, FOUR, [step(rej('NEED_BOOKING_TYPE', 'Is this internal, or personal?'))]) === FOUR, '  (v215: the model\'s four types went out)');
o = gp(M, 'What session type is this, and what time works?', [step(rej('NEED_SESSION_TYPE', 'What kind of session is this? And what time?'))]);
ok(o === 'What kind of session is this? And what time?', 'session type + time, as Book Session wrote it', o);
o = gp(M, 'Who is the client for this one?', [step(rej('NEED_CLIENT', 'Who’s the client? (or \\"none\\")'))]);
ok(o === 'Who’s the client? (or "none")', 'the client question, quotes unescaped', o);
o = gp(M, 'Could you tell me the project name?', [step(rej('NEED_SESSION_TYPE', 'What kind of session is this?')), step(rej('MISSING_DATE', 'What’s the project? And which day and time?'))]);
ok(o === 'What’s the project? And which day and time?', 'two calls -> the latest one\'s question', o);
const OCC = JSON.stringify([{ status: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [], unverifiable: null, human: 'Studio 8 is taken from 11:00 AM to 3:00 PM.' }], null, 2);
const occ = 'Studio 8 is taken from 11:00 AM to 3:00 PM by "CATTAIL ISR / Michael V / HL".\n\nStudio 7 and Studio F are free then. Want one of those, or a different time?';
ok(gp(M, occ, [step(OCC)]) === gp(OM, occ, [step(OCC)]), 'a refusal with no question (ROOM_OCCUPIED) is left to the model, as before');
const PREP = JSON.stringify([{ status: 'PREPARED', summary_text: '*CATTAIL / Vic Icasas / HL*\n*Date:* Thursday, October 7, 2027\n*Time:* 3:00 PM – 6:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.' }]);
o = gp(M, 'Here you go', [step(rej('NEED_BOOKING_TYPE', 'Is this internal, or personal?')), step(PREP)]);
ok(/^\*CATTAIL \/ Vic Icasas \/ HL\*/.test(o) && !/internal, or personal/.test(o), 'a later PREPARED card wins over an earlier question', o);
o = gp(M, FOUR, [step(JSON.stringify([{ verdict: 'REJECTED', reason: 'NEED_BOOKING_TYPE', human: 'Ask exactly this: "Is this internal, or personal?"' }]))]);
ok(o === 'Is this internal, or personal?', '`verdict` still read (Check Conflicts shape)', o);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
