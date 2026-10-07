#!/usr/bin/env node
// Offline tests for Book Session v95 (colleague engineers; QA round 3 B2, 7 Oct): booking FOR a colleague who is an engineer
// makes them the engineer (not asked), and the colleague's name is never taken as the project.
//   node scripts/sim-colleague-engineer.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v95.json'), OB = WF('book-session-v94.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData; const rec = n => run[n] ? run[n][0].data.main[0] : null;
Date.now = () => Date.parse('2026-10-07T06:00:00Z');
const REF = rec('Room Table')[0].json.referenceData;
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const cc = (w, req) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF, rooms: 'Studio F', expected_date: '2027-10-12', start_iso: '2027-10-12T13:00:00+08:00', end_iso: '2027-10-12T16:00:00+08:00', client: '', asked_text: '', engineer: '', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(rec('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
const TR = forWho => 'Booked by: Tricia Rumbaoa' + (forWho ? ' (for ' + forWho + ')' : '') + ' | ref: U098UFMKQHZ';
const T1 = 'Book Studio F for elijah next Tuesday from 1pm to 4pm';
console.log('QA B2 as Trish: "for elijah" (Alec Elijah Gan, Post Engineer)');
let c = cc(B, { summary: 'ELIJAH / X', session_type: '', description: TR('Alec Elijah Gan'), requester_text: T1 });
ok(relay(c.human) === 'What kind of session is this? What’s the project, and who’s the client? (or "none")', 'first question: no engineer question, and the project IS asked (ELIJAH is not a project)', relay(c.human));
const c94 = cc(OB, { summary: 'ELIJAH / X', session_type: '', description: TR('Alec Elijah Gan'), requester_text: T1 });
ok(/engineer/i.test(relay(c94.human) || '') && !/project/i.test(relay(c94.human) || ''), '  (v94: asked the engineer, not the project - the QA run)', relay(c94.human));
c = cc(B, { summary: 'VIOLET / Sasa Abella / X', client: 'Sasa Abella', session_type: 'VO Recording', description: TR('Alec Elijah Gan'), requester_text: T1 + '\nvo recording, project violet, client sasa abella', asked_text: 'x' });
ok(c.verdict === 'CLEAR' && /\/ AEG$/.test(c.final_summary) && /Engineer: Alec Elijah Gan/.test(c.final_description), 'second round -> the card: VIOLET / Sasa Abella / AEG, Engineer: Alec Elijah Gan', [c.verdict, c.reason, c.final_summary, c.final_description]);
console.log('when the engineer is still asked');
c = cc(B, { summary: 'VIOLET / X', session_type: 'VO Recording', description: TR('Japs Concepcion'), requester_text: 'Book Studio F for japs next Tuesday from 1pm to 4pm\nvo recording, project violet, client none', asked_text: 'x' });
ok(c.reason === 'NEED_ENGINEER', 'for a colleague who is not an engineer (Japs, Accounts Lead) -> asked', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'NET-BUGHAW / X', session_type: 'Localization Dubbing', rooms: 'Studio 1', description: TR('Alec Elijah Gan'), requester_text: 'book studio 1 for elijah next tuesday 1-4pm localization dubbing project NET-BUGHAW', asked_text: 'x' });
ok(/engineer/i.test(relay(c.human) || '') && !/Engineer: Alec/.test(String(c.final_description || '')), 'an engineer colleague whose role does not fit (Post / Music for Localization Dubbing) -> asked', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'VIOLET / DR', engineer: 'Drey', session_type: 'VO Recording', description: 'Engineer: Drey | ' + TR('Alec Elijah Gan'), requester_text: T1 + '\nvo recording, project violet, client none, engineer drey', asked_text: 'x' });
ok(c.verdict === 'CLEAR' && /\/ DR$/.test(c.final_summary), 'another engineer named ("engineer drey") -> that one, not the colleague', [c.verdict, c.final_summary]);
c = cc(B, { summary: 'VIOLET / X', session_type: 'VO Recording', description: TR(''), requester_text: 'Book Studio F next Tuesday from 1pm to 4pm\nvo recording, project violet, client none', asked_text: 'x' });
ok(c.reason === 'NEED_ENGINEER', 'no colleague at all -> asked, as in v94', c.reason);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
