#!/usr/bin/env node
// Offline tests for main v192 (a time range after "Booked.") and Book Session v66 (a proposed time), from live QA 29 Sep
// 20:34-20:36 PHT (ORANGE / Sasa Abella / AEG: "move it to 3-6pm" -> a card for 6-7 PM, twice).
//   node scripts/sim-move-range.js <main-execution.json> <book-session-prepare-execution.json>
// Use 29 Sep main exec 16685 and Book Session exec 16681 (any real runs work: only the nodes' reference inputs are used).
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v192.json'), OM = WF('project-jessie-v191.json');
const B = WF(process.env.BOOK || 'book-session-v66.json'), OB = WF('book-session-v65.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const R = f => { const run = JSON.parse(fs.readFileSync(f)).data.resultData.runData; return n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null; };
const mrec = R(process.argv[2]), brec = R(process.argv[3]);
const ME = 'U08V3CKDGJF', T = 1790690000;
const SUM = '*ORANGE / Sasa Abella / AEG*\n*Date:* Thursday, September 30, 2027\n*Time:* 10:00 AM – 11:00 AM\n*Room:* Studio 7\n\n_check 1c7b1094_\n\nBook it? Reply yes or no.';
const CARD = '*ORANGE / Sasa Abella / AEG*\n*Now:* Thursday, September 30, 2027, 10:00 AM – 11:00 AM, Studio 7\n*Moving to:* Thursday, September 30, 2027, 6:00 PM – 7:00 PM, Studio 7\n\nMove it? Reply yes or no.';
const base = [{ json: { ts: String(T + 40), text: 'Booked.', bot_id: 'B1' } }, { json: { ts: String(T + 30), text: 'yes', user: ME } },
  { json: { ts: String(T + 20), text: SUM, bot_id: 'B1' } }, { json: { ts: String(T + 10), text: 'proj orange, vo recording, studio 7, for sasa. engineer eli', user: ME } }];
const bf = (w, newer) => { const hist = newer.map((x, i) => ({ json: { ts: String(T + 90 - i * 10), ...x } })).concat(base);
  return new Function('$', '$input', code(w, 'Booked For'))(n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: hist[0].json }]) : wrap(mrec(n) || [{ json: {} }]), wrap([{ json: {} }]))[0].json; };
const mv = b => (b.moveStart || '') + '-' + (b.moveEnd || '');
console.log('main v192 - a time range right after "Booked." (10-11 AM)');
for (const [t, want] of [['move it to 3-6pm', '15:00-18:00'], ['move it to 3pm-6pm', '15:00-18:00'], ['move it to 3pm to 6pm', '15:00-18:00'], ['move it to 3 to 6pm', '15:00-18:00'], ['make it 10am-12nn', '10:00-12:00'], ['move it to 3pm', '15:00-16:00'], ['extend it until 12nn', '10:00-12:00']])
  ok(mv(bf(M, [{ text: t, user: ME }])) === want, '"' + t + '" -> ' + want, mv(bf(M, [{ text: t, user: ME }])));
ok(mv(bf(OM, [{ text: 'move it to 3-6pm', user: ME }])) === '18:00-19:00', '  (v191: "3-6pm" -> 18:00-19:00, the card from the live test)');
const two = [{ text: '3-6pm not 6-7', user: ME }, { text: CARD, bot_id: 'B1' }, { text: 'move it to 3-6pm', user: ME }];
ok(mv(bf(M, two)) === '15:00-18:00', '"3-6pm not 6-7" after the wrong card -> 15:00-18:00 (the first range wins)', mv(bf(M, two)));
ok(mv(bf(OM, two)) === '18:00-19:00', '  (v191: the same wrong card again)');

console.log('Book Session v66 - no time typed: the time is proposed, and the summary says so');
const REQ0 = brec('When Executed by Another Workflow')[0].json;
const sum = (w, req) => { const Rq = [{ json: { ...REQ0, ...req } }];
  const $c = n => { const it = n === 'When Executed by Another Workflow' ? Rq : brec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const cc = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(Rq) : n === 'Check Conflicts' ? wrap([{ json: cc }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : wrap(brec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: cc }]))[0].json.summary_text; };
const NT = 'i want to book a sched tomorrow\nproj orange, vo recording, studio 8, client Jem Lim. engineer drey';
let s = sum(B, { requester_text: NT });
ok(/\*Note:\* No time was given, so I proposed 2:00 PM – 4:00 PM \(Studio 8 is free then\)\. What time would you like\? Tell me, or reply yes to book this time\./.test(s) || /No time given, so I picked 2:00 PM – 4:00 PM\. Tell me if you\u2019d like another\./.test(s), 'no time typed -> "No time was given, so I proposed ... What time would you like?"', s);
ok(/_check [0-9a-f]{8}_\n\nReply only with "yes" to book/.test(s) || /\n\nConfirm to book\.$/.test(s), 'the confirmation still comes last (v73: no printed check code)');
ok(!/No time (?:was )?given/.test(sum(OB, { requester_text: NT })), '  (v65: the time shown as if asked for)');
for (const t of ['Book Studio 8 tomorrow from 2pm to 4pm, VO, project X, client Jem Lim', 'book studio 8 tomorrow morning, vo, project x, client Jem Lim', 'book studio 8 tomorrow at 3, vo, project x, client Jem Lim', 'book studio 8 tomorrow 2-4, vo, project x, client Jem Lim', 'book studio 8 tomorrow 14:00, vo, client Jem Lim'])
  ok(!/No time (?:was )?given/.test(sum(B, { requester_text: t })), 'a time was typed ("' + t.replace(/^.*tomorrow /, '').split(',')[0] + '") -> no note');
ok(!/No time (?:was )?given/.test(sum(B, { requester_text: '' })), 'no requester text (a consent placement, an older caller) -> no note');
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
