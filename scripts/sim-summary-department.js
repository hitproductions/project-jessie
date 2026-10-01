#!/usr/bin/env node
// Offline tests for Book Session v69 (department line fix): the summary's Department line when the model sends none.
// Live QA 30 Sep 13:29 PHT (Turn Log exec 18529): the QAORANGE2 summary had no Department line.
//   node scripts/sim-summary-department.js <book-session-prepare-execution.json>   (29 Sep exec 16681)
const fs = require('fs'), path = require('path');
const FULL = require('./lib-full-summary.js');   // v73: the stored fields as the old summary lines
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v69.json'), OB = WF('imported/book-session-v68-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const rs = (w, req) => { const R = [{ json: { ...REQ0, ...req } }];
  const $c = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : wrap(rec(n) || [{ json: {} }]);
  return { c, s: FULL(new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json, c) }; };
const Q = { summary: 'QAORANGE2 / DR', client: '', session_type: 'VO Recording', bookingType: 'External',
  requester_text: 'book qaorange2 studio 8 tomorrow 2pm to 4pm, vo recording, engineer drey\nno client\nexternal booking. move to 6pm' };

let x = rs(B, { ...Q, department: '' });
ok(/\*Department:\* Audio Post/.test(x.s) && /Dept: Audio Post/.test(x.c.final_description || ''), 'no department from the model -> the summary shows the one worked out (Audio Post)', x.s);
ok(!/\*Department:\*/.test(rs(OB, { ...Q, department: '' }).s), '  (v68: no Department line)');
x = rs(B, { ...Q, department: 'Music' });
ok(/\*Department:\* Music/.test(x.s) && !/\*Department:\* Audio Post/.test(x.s), 'a department the model sent -> shown as before');
x = rs(B, { ...Q, department: '' });
ok((x.s.match(/\*Department:\*/g) || []).length === 1, 'one Department line only');
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
