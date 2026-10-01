#!/usr/bin/env node
// Offline tests for Book Session v71 (self-engineer default) and v72 (v71 fixed: the note when the model put the requester in): no engineer named + the requester is an engineer -> the
// requester engineers, and the summary says so. Decided 30 Sep 14:16 PHT (QAANJ). Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-self-engineer.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const FULL = require('./lib-full-summary.js');   // v73: the stored fields as the old summary lines
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v72.json'), OB = WF('imported/book-session-v70-imported.json'), O71 = WF('imported/book-session-v71-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const go = (w, req, over = {}) => { const R = [{ json: { ...REQ0, ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], ...over };
  const $c = n => { if (n === 'When Executed by Another Workflow') return wrap(R); if (O[n]) return wrap(O[n]); const it = rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  if (c.verdict === 'REJECTED') return { c, s: '' };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(rec(n) || [{ json: {} }]);
  return { c, s: FULL(new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json, c) }; };
const NOTE = "No engineer was named, so you're down as the engineer. If someone else is engineering, tell me who.";
const BASE = { summary: 'QASELF / HL', client: '', engineer: '', bookingType: 'External', session_type: 'VO Recording', rooms: 'Studio 7', mode: 'prepare',
  description: 'Booked by: Howard Luistro | ref: U08V3CKDGJF', requester_text: 'book qaself studio 7 tomorrow 2pm to 4pm, vo recording, no client, external', asked_text: '' };

let r = go(B, BASE);
ok(/\*Engineer:\* Howard Luistro \(Post Engineer\)/.test(r.s) && /^\*QASELF \/ HL\*/.test(r.s) && r.s.indexOf(NOTE) !== -1 && /Engineer: Howard Luistro/.test(r.c.final_description || ''),
   'no engineer named, requester is a Post Engineer -> Engineer: Howard Luistro (Post Engineer), QASELF / HL, and the note', r.s || r.c);
ok(!/\*Engineer:\*/.test(go(OB, BASE).s), '  (v70: no Engineer line - it was up to the model)');
r = go(B, { ...BASE, engineer: 'Drey', description: 'Engineer: Drey | Booked by: Howard Luistro | ref: U08V3CKDGJF', summary: 'QASELF / DR' });
ok(/\*Engineer:\* Daryl Reyes/.test(r.s) && r.s.indexOf(NOTE) === -1, 'an engineer named -> that engineer, no note', r.s.split('\n').filter(l => /Engineer|Note/.test(l)));
r = go(B, { ...BASE, description: 'Engineer: | Booked by: Howard Luistro | ref: U08V3CKDGJF' });
ok(/\*Engineer:\* Howard Luistro/.test(r.s) && (r.c.final_description.match(/Engineer:/g) || []).length === 1, 'an empty "Engineer:" segment -> filled in, not doubled', r.c.final_description);
r = go(B, { ...BASE, requester_text: 'book qaself studio 7 tomorrow 2pm to 4pm, vo recording, no client, external, no engineer' });
ok(!/\*Engineer:\* Howard/.test(r.s) && r.s.indexOf(NOTE) === -1, '"no engineer" typed -> left empty');
r = go(B, { ...BASE, description: 'Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF' });
ok(!/\*Engineer:\* Howard/.test(r.s), 'booked for a colleague -> not assumed (v70 asks who the engineer is)', r.c.reason || r.s.split('\n').filter(l => /Engineer/.test(l)));
r = go(B, { ...BASE, description: 'Booked by: Cristel Cube | ref: U0XXXX' });
ok(!/\*Engineer:\* Cristel/.test(r.s) && r.s.indexOf(NOTE) === -1, 'a requester who is not an engineer (Documentation Officer) -> left as before', r.s.split('\n').filter(l => /Engineer|Note/.test(l)));
r = go(B, { ...BASE, summary: 'QAANJ / Angela Dela Calzada', client: 'Angela Dela Calzada', requester_text: 'book qaanj studio 7 tomorrow 2pm to 4pm, vo recording, client angela dela calzada, external' });
ok(/^\*QAANJ \/ Angela Dela Calzada \/ HL\*/.test(r.s), '"PROJECT / Client" with no initials yet -> initials added, client kept', r.s.split('\n')[0]);
r = go(B, { ...BASE, mode: '' });
ok(!(r.c.final_description || '').includes('Engineer: Howard'), 'not prepare mode (the yes books the approved summary) -> untouched', r.c.final_description);

console.log('v72 - the model already put the requester in (live QA 30 Sep 15:29, QASELF)');
const ME = { ...BASE, engineer: 'Howard Luistro', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U08V3CKDGJF' };
r = go(B, ME);
ok(/\*Engineer:\* Howard Luistro \(Post Engineer\)/.test(r.s) && r.s.indexOf(NOTE) !== -1, 'the live case: Engineer: Howard Luistro from the model, nobody named -> the note', r.s || r.c);
ok(go(O71, ME).s.indexOf(NOTE) === -1, '  (v71: no note)');
ok(go(B, { ...ME, engineer: 'Howard', description: 'Engineer: Howard | Booked by: Howard Luistro | ref: U08V3CKDGJF' }).s.indexOf(NOTE) !== -1, '"Howard" (first name) from the model -> the note');
for (const t of ['book qaself studio 7 tomorrow 2pm to 4pm, vo recording, engineer howard', "book qaself studio 7 tomorrow 2pm to 4pm, vo recording, i'll engineer", 'book qaself studio 7 tomorrow 2pm to 4pm, vo recording, engineer me', 'book qaself studio 7 tomorrow 2pm to 4pm, vo recording, with howie'])
  ok(go(B, { ...ME, requester_text: t + ', no client, external' }).s.indexOf(NOTE) === -1, 'named themselves ("' + t.split(', ').pop() + '") -> no note');
r = go(B, { ...BASE, engineer: 'Drey', summary: 'QASELF / DR', description: 'Engineer: Drey | Booked by: Howard Luistro | ref: U08V3CKDGJF' });
ok(r.s.indexOf(NOTE) === -1, 'someone else from the model -> no note (not the requester)');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
