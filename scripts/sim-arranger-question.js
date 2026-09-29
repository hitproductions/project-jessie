#!/usr/bin/env node
// Offline test for Book Session v65: the arranger question names the engineer already taken in.
//   node scripts/sim-arranger-question.js <book-session-prepare-execution.json>
// The execution is the real QAPERSONAL prepare run (29 Sep 16:05 PHT, main exec 16937) that asked for the arranger.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = WF(process.env.BOOK || 'book-session-v65.json'), OLD = WF('book-session-v64.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const cc = (w, req = {}) => { const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
let r = cc(NEW);
ok(r.reason === 'NEED_ARRANGER' && /"Daryl Reyes is down as the engineer\. Music Vocal Recording sessions usually have an arranger too - who is it, or is there none\?"/.test(r.human), 'names the engineer: "Daryl Reyes is down as the engineer. ..."', r.human);
ok(!/as well as the engineer/.test(r.human), 'no "as well as the engineer"');
ok(/as well as the engineer/.test(cc(OLD).human), '  (v64: "as well as the engineer", no name)');
r = cc(NEW, { engineer: 'Daryl Reyes (Music Engineer)' });
ok(/"Daryl Reyes is down as the engineer\./.test(r.human), 'a role in brackets is left off', r.human);
r = cc(NEW, { engineer: '', description: 'Engineer: Tara Lim | Booked by: Howard Luistro' });
ok(/"Tara Lim is down as the engineer\./.test(r.human), 'no engineer input -> read from the description', r.human);
r = cc(NEW, { engineer: '', description: '' });
ok(r.reason === 'NEED_ARRANGER' && /Ask exactly this, in one message: "Music Vocal Recording sessions usually have an arranger too/.test(r.human), 'no engineer at all -> just the arranger question', r.human);
r = cc(NEW, { description: 'Engineer: Daryl Reyes | Arranger: BP Valenzuela' });
ok(r.reason !== 'NEED_ARRANGER', 'an arranger given -> not asked');
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
