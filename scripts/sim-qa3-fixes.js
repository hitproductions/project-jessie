#!/usr/bin/env node
// Offline tests for Book Session v94 + main v228 (QA round 3 fixes, 6 Oct): the engineer is asked of a requester who is not
// an engineer, with the first questions; and a past date shows its heads-up during the QA year shift.
//   node scripts/sim-qa3-fixes.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v94.json'), OB = WF('book-session-v93.json');
const M = WF(process.env.MAIN || 'project-jessie-v228.json'), OM = WF('project-jessie-v227.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData; const rec = n => run[n] ? run[n][0].data.main[0] : null;
Date.now = () => Date.parse('2026-10-06T08:00:00Z');
const REF = rec('Room Table')[0].json.referenceData;
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const cc = (w, req) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF, rooms: 'Studio 7', expected_date: '2027-10-14', start_iso: '2027-10-14T14:00:00+08:00', end_iso: '2027-10-14T17:00:00+08:00', client: '', asked_text: '', engineer: '', ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(rec('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
const by = (n, r) => 'Booked by: ' + n + ' | ref: ' + r;
const T1 = 'Book Studio 7 next Thursday from 2pm to 5pm', T2 = T1 + '\nvo recording, project orange, client none';
console.log('Book Session v94 - QA B1 as Trish, Jess and Camy (none of them engineers)');
for (const [n, r] of [['Tricia Rumbaoa', 'U098UFMKQHZ'], ['Jess Barbosa', 'U0B4S0EKSAY'], ['Camy Caridad', 'U08JL17A50A']]) {
  let c = cc(B, { summary: 'SESSION / X', session_type: '', description: by(n, r), requester_text: T1 });
  ok(relay(c.human) === 'What kind of session is this? What’s the project, who’s the engineer, and who’s the client? (or "none")', n + ': the first question asks the engineer too', relay(c.human));
  c = cc(B, { summary: 'ORANGE / X', session_type: 'VO Recording', description: by(n, r), requester_text: T2, asked_text: 'x' });
  ok(c.reason === 'NEED_ENGINEER' && relay(c.human) === 'Who’s the engineer?', n + ': the engineer skipped -> asked on its own, no card', [c.reason, relay(c.human)]);
  ok(cc(OB, { summary: 'ORANGE / X', session_type: 'VO Recording', description: by(n, r), requester_text: T2, asked_text: 'x' }).verdict === 'CLEAR', '  (v93: the card, with no engineer)');
  c = cc(B, { summary: 'ORANGE / DR', session_type: 'VO Recording', engineer: 'Drey', description: 'Engineer: Drey | ' + by(n, r), requester_text: T2 + '\nengineer drey', asked_text: 'x' });
  ok(c.verdict === 'CLEAR' && /\/ DR$/.test(c.final_summary), n + ': "engineer drey" -> the card, titled ... / DR', [c.verdict, c.reason, c.final_summary]);
}
console.log('Book Session v94 - when the engineer is not asked');
const TR = by('Tricia Rumbaoa', 'U098UFMKQHZ');
let c = cc(B, { summary: 'ORANGE / X', session_type: 'VO Recording', description: TR, requester_text: T2 + '\nno engineer', asked_text: 'x' });
ok(c.verdict === 'CLEAR', '"no engineer" -> not asked again', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'SESSION / HL', session_type: '', description: by('Howard Luistro', 'U08V3CKDGJF'), requester_text: T1 });
ok(relay(c.human) === 'What kind of session is this? What’s the project, and who’s the client? (or "none")', 'an engineer requester (Howard) -> not asked, as before', relay(c.human));
c = cc(B, { summary: 'LIKHA - Finance', session_type: '', rooms: 'Likha', description: TR, requester_text: 'book likha next thursday 2-5pm for a meeting' });
ok(!/engineer/i.test(String(c.human || '')), 'a conference room -> not asked', [c.verdict, c.reason, relay(c.human)]);
c = cc(B, { summary: 'M3 - Tricia', session_type: '', rooms: 'M3', all_day: true, start_iso: '2027-10-14', end_iso: '2027-10-15', description: TR, requester_text: 'book m3 for me next thursday' });
ok(!/engineer/i.test(String(c.human || '')), 'an M booth -> not asked', [c.verdict, c.reason, relay(c.human)]);
c = cc(B, { summary: 'NET-BUGHAW / X', session_type: 'Localization Editing', rooms: 'Studio 1', description: TR, requester_text: 'book studio 1 next thursday 2-5pm localization editing project NET-BUGHAW', asked_text: 'x' });
ok(/engineer/i.test(relay(c.human) || ''), 'a Localization session -> the engineer is asked too', [c.reason, relay(c.human)]);

console.log('main v228 - a past date shows its heads-up during the QA year shift');
const gate = text => { const store = {}; const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: 'U098UFMKQHZ', ts: '1791275000.1', channel: 'D1' } : n === 'Get Booker' ? { fields: { Name: 'Tricia Rumbaoa', Department: ['Finance'] } } : {} }), all: () => [] });
  return new Function('$', '$getWorkflowStaticData', code(M, 'Gate Context'))($, () => store)[0].json; };
const G = gate('book studio 7 last monday 2-5pm');
ok(G.todayIso === '2027-10-06' && G.datesUnderDiscussion === '2027-10-04', 'Gate Context: today 2027-10-06 (year shift), "last monday" = 2027-10-04', [G.todayIso, G.datesUnderDiscussion]);
const card = d => '*ORANGE / DR*\n*Date:* ' + d + '\n*Time:* 2:00 PM – 5:00 PM\n*Room:* Studio 7\n\nConfirm to book.';
const gp = (W, out, todayIso) => new Function('$input', '$', code(W, 'Guard Probe'))(wrap([{ json: { output: 'x', intermediateSteps: [{ action: { tool: 'Prepare_Booking' }, observation: JSON.stringify([{ status: 'PREPARED', summary_text: out }]) }] } }]),
  n => n === 'Gate Context' ? wrap([{ json: { todayIso } }]) : n === 'Booked For' ? wrap([{ json: { requesterText: 'x' } }]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Tricia Rumbaoa' } } }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
let o = gp(M, card('Monday, October 4, 2027'), '2027-10-06');
ok(/\*Room:\* Studio 7\n\nHeads up: this date has already passed\.\n\nBook it\? Reply yes or no\.$/.test(o), 'E2 "last Monday" (4 Oct 2027) -> the card says it has passed', o);
ok(!/already passed/.test(gp(OM, card('Monday, October 4, 2027'), '2027-10-06')), '  (v227: no heads-up during the year shift)');
ok(!/already passed/.test(gp(M, card('Thursday, October 14, 2027'), '2027-10-06')), 'a future date -> nothing added');
o = gp(M, card('Monday, October 4, 2027').replace('\n\nConfirm', '\n\nNot a usual VO Recording room - booking it as asked.\n\nConfirm'), '2027-10-06');
ok(/booking it as asked\.\nHeads up: this date has already passed\.\n\nBook it\?/.test(o), 'with other notes -> added under them', o);
o = gp(M, card('Thursday, October 1, 2026').replace('\n\nConfirm', '\n\nHeads up: this date has already passed.\n\nConfirm'), '2027-10-06');
ok((o.match(/already passed/g) || []).length === 1, 'Book Session already said it -> not twice', o);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
