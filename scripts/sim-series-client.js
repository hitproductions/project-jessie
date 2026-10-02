#!/usr/bin/env node
// Offline tests for main v205 (series client question) - live Slack E2E 1 Oct 14:20-14:22 (exec 20274, 20278).
//
//   node scripts/sim-series-client.js <main-execution.json>
//
// A model-written series summary with no client: Guard Probe asks for the client in place of "Book it?". v204 left it
// long, with the model's "(Mon)" dates; and at "none" the model (whose memory holds its own "Book it?") replied "What
// do you need?". Now the Expand Series dates and the short card apply to it, and Booked For tells the model what the
// answer was.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v205.json'), OLD = WF('project-jessie-v204.json');
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const ME = 'U08V3CKDGJF';

const REQ = 'book qaseries every monday in november 2027 2-4pm vo recording studio 8';
// what the model wrote at 14:20:52 (before Guard Probe), reconstructed from the reply
const SUM = '*QASERIES / HL*\n*Dates:*\n- November 1, 2027 (Mon)\n- November 8, 2027 (Mon)\n- November 15, 2027 (Mon)\n- November 22, 2027 (Mon)\n- November 29, 2027 (Mon)\n'
  + '*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n*Session Type:* VO Recording\n*Engineer:* Howard Luistro\n\nBook it? Reply yes or no.';
const occ = ['01', '08', '15', '22', '29'].map(d => ({ start_iso: '2027-11-' + d + 'T14:00:00+08:00', end_iso: '2027-11-' + d + 'T16:00:00+08:00', all_day: false }));
const ES = [{ action: { tool: 'Expand_Series' }, observation: JSON.stringify([{ status: 'OK', count: 5, occurrences: occ }]) }];
const gp = (w, output, steps, said) => new Function('$input', '$', code(w, 'Guard Probe'))(
  wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { ...(((rec('Booked For') || [{ json: {} }])[0] || {}).json || {}), requesterText: said, bookedFor: '' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;

console.log('Guard Probe - the series summary with no client');
let o = gp(M, SUM, ES, REQ);
ok(/Who’s the client\? \(or "none"\)$/.test(o) && !/Book it\?/.test(o), 'no client given -> asks, no "Book it?" (as before)', o);
ok(/\*Dates \(5\):\*\n- Monday, 1 November 2027\n- Monday, 8 November 2027/.test(o) && !/\(Mon\)/.test(o), 'dates from Expand Series (were the model\'s "(Mon)" list)', o);
ok(/^\*QASERIES \/ HL\*\n\*Dates \(5\):\*/.test(o) && /\*Time:\* 2:00 PM – 4:00 PM\n\*Room:\* Studio 8/.test(o) && !/Session Type:|Engineer:/.test(o), 'the short card: title, dates, time, room', o);
const old = gp(OLD, SUM, ES, REQ);
ok(/Session Type:/.test(old) && /\(Mon\)/.test(old), '  (v204: long, model dates - live 14:20:52)', old.slice(0, 80));
o = gp(M, SUM.replace('*Engineer:* Howard Luistro', '*Engineer:* Howard Luistro\n*Client:* None'), ES, REQ + '\nnone');
ok(/Book it\? Reply yes or no\.$/.test(o) && !/Client:/.test(o) && /\*Dates \(5\):\*/.test(o), 'after "none": the short card ending in "Book it?"', o);
o = gp(M, SUM.replace('*QASERIES / HL*', '*QASERIES / Jem Lim / HL*').replace('*Engineer:* Howard Luistro', '*Engineer:* Howard Luistro\n*Client:* Jem Lim'), ES, REQ + ' for jem lim');
ok(/^\*QASERIES \/ Jem Lim \/ HL\*/.test(o) && /Book it\? Reply yes or no\.$/.test(o) && !/Client:/.test(o), 'with a client: short card, "Book it?"', o);
o = gp(M, '*QASERIES / HL*\n*Dates:*\n- November 1, 2027 (Mon)\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n*Session Type:* VO Recording\n\nBook it? Reply yes or no.', [], REQ + '\nnone');
ok(!/Session Type:/.test(o) && /\*Dates:\*/.test(o), 'no Expand Series this turn: a plain "*Dates:*" summary is cut too', o);

console.log('Booked For - "none" answers the client question');
const bf = (w, convo) => { const h = convo.slice().reverse().map((m, i) => ({ json: { ...m, ts: String(1790835000 + i * 30) } }));
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }])
    : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const Q = '*QASERIES / HL*\n*Dates (5):*\n- Monday, 1 November 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n\nWho’s the client? (or "none")';
let b = bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q }, { user: ME, text: 'none' }]);
ok(/ANSWERING YOUR LAST QUESTION.*"none" means there is no client.*same booking/.test(b.notice || '') && b.clientAnswer === 'none', '"none" -> told: no client, same booking, show it again', b.notice);
ok(/ANSWERING/.test(bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q }, { user: ME, text: 'none *Sent using* <@U0AVDBNH1K4>' }]).notice || ''), '  (the connector\'s "Sent using" suffix is ignored)');
b = bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q }, { user: ME, text: 'Jem Lim' }]);
ok(/"Jem Lim" means the client is Jem Lim/.test(b.notice || ''), 'a name -> told: that is the client', b.notice);
b = bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q.replace("Who’s", "Who's") }, { user: ME, text: 'wala' }]);
ok(/there is no client/.test(b.notice || ''), "straight apostrophe, \"wala\" -> no client");
b = bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: '*QASERIES / HL*\n...\n\nBook it? Reply yes or no.' }, { user: ME, text: 'no' }]);
ok(!/ANSWERING YOUR LAST QUESTION/.test(b.notice || ''), 'a "no" to "Book it?" is not this', b.notice);
b = bf(M, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q }, { user: ME, text: 'actually can you check studio 7 for the whole of november instead please' }]);
ok(!/ANSWERING YOUR LAST QUESTION/.test(b.notice || ''), 'a long new instruction is not read as the client', b.notice);
ok(!/ANSWERING/.test(bf(OLD, [{ user: ME, text: REQ }, { bot_id: 'B1', text: Q }, { user: ME, text: 'none' }]).notice || ''), '  (v204: nothing told - live 14:22:21 "What do you need?")');

if (/v206 \(live 1 Oct 14:31\)/.test(code(M, 'Guard Probe'))) {
  console.log('Guard Probe v206 - no "which day" on a series');
  const gq = (output, steps, said) => new Function('$input', '$', code(M, 'Guard Probe'))(
    wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
    n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { ...(((rec('Gate Context') || [{ json: {} }])[0] || {}).json || {}), datesUnderDiscussion: '' } }])
       : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
  ok(!/which day/i.test(gq("What's the client for this session?", ES, REQ)), 'live 14:31: Expand Series OK -> no "And which day is it for?"');
  ok(!/which day/i.test(gq("What's the client for this session?", [], 'book qa every tuesday until dec 2-4pm studio 8')), '"every tuesday", no tool yet -> none either');
  ok(!/which day/i.test(gq("Who is the client?", [], 'book studio 8 weekly 2-4pm for 4 weeks')), '"weekly" -> none');
  ok(/And which day(?: is it for)?\?$/.test(gq("What's the client for this session?", [], 'Book Studio 7 from 2pm to 5pm')), 'a single booking with no date -> still asked (v164)');
}
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
