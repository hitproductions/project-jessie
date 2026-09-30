#!/usr/bin/env node
// Offline tests for Book Session v68 (ISR shorthand). Check Conflicts runs on a real prepare run's inputs with only the
// booking fields replaced - live QA 30 Sep 12:44 PHT: "book isr for studio 8 with rico tomorrow at 9am" -> ISR / ISR / EG.
//   node scripts/sim-session-shorthand.js <book-session-prepare-execution.json>   (29 Sep exec 16681)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v68.json'), OB = WF('imported/book-session-v67-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const cc = (w, req) => { const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
const ISR = { summary: 'ISR / ISR / EG', client: 'ISR', requester_text: 'book isr for studio 8 with rico tomorrow at 9am\next', asked_text: '' };

let r = cc(B, ISR);
ok(r.reason === 'SESSION_SHORTHAND' && r.shorthand === 'ISR' && r.session_type === 'VO Recording', 'the live case: ISR as project and client -> nothing prepared, SESSION_SHORTHAND', r);
ok(/"Just to check - by ISR, do you mean an In-Studio Recording \(a VO Recording session\)\? What's the project name, and who is the client\?"/.test(r.human), 'asks: "by ISR, do you mean an In-Studio Recording (a VO Recording session)? ..."', r.human);
ok(cc(OB, ISR).reason !== 'SESSION_SHORTHAND', '  (v67: prepared ISR / ISR / EG)');
r = cc(B, { ...ISR, asked_text: 'Just to check - by ISR, do you mean an In-Studio Recording (a VO Recording session)? What\'s the project name, and who is the client?' });
ok(r.reason === 'SESSION_SHORTHAND' && /"What's the project name, and who is the client\?"/.test(r.human) && !/do you mean/.test(r.human), 'asked already and still in the slot -> only the project and client, never the same question twice', r.human);
r = cc(B, { summary: 'ISR / Jem Lim / EG', client: 'Jem Lim', requester_text: 'book studio 8 tomorrow 9am, vo recording, project ISR, client Jem Lim, engineer rico' });
ok(r.reason !== 'SESSION_SHORTHAND', '"project ISR" typed as the project -> taken as typed', r.reason);
r = cc(B, { summary: 'ORANGE / ISR / EG', client: 'ISR', requester_text: 'book studio 8 tomorrow 9am vo, project orange, client isr' });
ok(r.reason !== 'SESSION_SHORTHAND', '"client ISR" typed as the client -> taken as typed', r.reason);
r = cc(B, { summary: 'ORANGE / ISR / EG', client: 'ISR', requester_text: 'isr session for project orange tomorrow 9am studio 8' });
ok(r.reason === 'SESSION_SHORTHAND' && r.slot === 'client', 'ISR only in the client slot (project named) -> asked about the client slot', r);
r = cc(B, { summary: 'In-Studio Recording / Jem Lim / EG', client: 'Jem Lim', requester_text: 'book an in-studio recording tomorrow 9am, client Jem Lim' });
ok(r.reason === 'SESSION_SHORTHAND', '"In-Studio Recording" spelled out as the project -> asked too', r.reason);
r = cc(B, { summary: 'QANEW / Jem Lim / DR' });
ok(r.reason !== 'SESSION_SHORTHAND', 'an ordinary booking -> unchanged', r.reason);
r = cc(B, { ...ISR, mode: '' });
ok(r.reason !== 'SESSION_SHORTHAND', 'not prepare mode (the yes, a series, a consent placement) -> never asked');
{ const R = JSON.parse(REQ0.reference_data); R.types.find(t => t.type === 'Music Mixing').aka = ['MMX'];
  r = cc(B, { summary: 'MMX / Jem Lim / DR', client: 'Jem Lim', requester_text: 'book an mmx tomorrow at 2pm', reference_data: JSON.stringify(R) });
  ok(r.reason === 'SESSION_SHORTHAND' && r.session_type === 'Music Mixing', 'a nickname from Session Types ("aka" in the reference data) is recognised too', r); }
console.log('The general case - the client is only the project again');
const rs = (w, req) => { const R = [{ json: { ...REQ0, ...req } }];
  const $c = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : wrap(rec(n) || [{ json: {} }]);
  return { c, s: new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json.summary_text }; };
let x = rs(B, { summary: 'ORANGE / ORANGE / DR', client: 'ORANGE', requester_text: 'book orange studio 8 tomorrow 2-4pm vo, engineer drey' });
ok(/\*Client:\* None/.test(x.s) && /^\*ORANGE \/ DR\*/.test(x.s), '"book orange ..." as ORANGE / ORANGE / DR -> "Client: None", title ORANGE / DR (Jessie then asks who the client is)', x.s.split('\n').slice(0, 3));
ok(/\*Client:\* ORANGE/.test(rs(OB, { summary: 'ORANGE / ORANGE / DR', client: 'ORANGE', requester_text: 'book orange studio 8 tomorrow 2-4pm vo, engineer drey' }).s), '  (v67: Client: ORANGE)');
x = rs(B, { summary: 'ORANGE / ORANGE / DR', client: 'ORANGE', requester_text: 'book orange for orange, studio 8 tomorrow 2-4pm vo' });
ok(/\*Client:\* ORANGE/.test(x.s), '"for orange" typed -> the client stands', x.s.split('\n')[1]);
x = rs(B, { summary: 'ORANGE / ORANGE / DR', client: 'ORANGE', requester_text: 'project orange, client orange, studio 8 tomorrow 2-4pm' });
ok(/\*Client:\* ORANGE/.test(x.s), '"client orange" typed -> the client stands');
x = rs(B, { summary: 'ORANGE / ORANGE / DR', client: 'ORANGE', requester_text: 'book orange for studio 8 tomorrow 2-4pm vo, engineer drey' });
ok(/\*Client:\* None/.test(x.s), '"for studio 8" is not naming the client -> still Client: None', x.s.split('\n')[1]);
x = rs(B, { summary: 'ORANGE / Jem Lim / DR', client: 'Jem Lim', requester_text: 'book orange studio 8 tomorrow 2-4pm, client Jem Lim' });
ok(/\*Client:\* Jem Lim/.test(x.s), 'a real client -> unchanged');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
