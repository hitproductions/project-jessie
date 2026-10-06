#!/usr/bin/env node
// Offline tests for main v218 + Book Session v89 (client asked first; live 6 Oct 13:32-13:33 PHT on main v217 / v88):
// "book studio 8 next thu 3-5pm" was asked the session type and project but not the client, and after "post mixing" the
// reply was the refusal's own instruction: "Nothing was booked. If there is no client, leave it empty."
//   node scripts/sim-ask-client-first.js <main-execution.json>   (its All Bookers output feeds Book Session too)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v218.json'), OM = WF('project-jessie-v217.json');
const B = WF(process.env.BOOK || 'book-session-v89.json'), OB = WF('book-session-v88.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
const ME = 'U08V3CKDGJF';
const REF = JSON.stringify({ rooms: [{ id: 'r8', name: 'Studio 8', common: false }, { id: 'rl', name: 'Likha', common: true }],
  types: ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording', 'Localization Mixing', 'Localization Atmos Mixing', 'Music Mixing', 'Localization Dubbing', 'Meeting']
    .map(t => ({ type: t, typical: 120, ranked: ['Studio 8'] })) });
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const cc = (w, req, client = [{ json: {} }]) => {
  const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF,
    expected_date: '2027-10-14', start_iso: '2027-10-14T15:00:00+08:00', end_iso: '2027-10-14T17:00:00+08:00', rooms: 'Studio 8', engineer: 'Howard Luistro',
    description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, asked_text: '', client: '', ...req } }];
  const O = { 'Get Client': client, 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };

console.log('Book Session v89 - the live conversation, turn by turn');
const T1 = 'book studio 8 next thu 3-5pm';
let c = cc(B, { summary: 'SESSION / HL', session_type: '', requester_text: T1 });
ok(relay(c.human) === 'What kind of session is this? What’s the project, and who’s the client? (or "none")', 'turn 1: the client is asked with the session type and project', relay(c.human));
ok(relay(cc(OB, { summary: 'SESSION / HL', session_type: '', requester_text: T1 }).human) === 'What kind of session is this? What’s the project?', '  (v88: no client - live 13:32)');
const A1 = 'What kind of session is this? What’s the project, and who’s the client? (or "none")';
const T2 = T1 + '\nmixing. for proj runway';
c = cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T2, asked_text: A1 });
ok(/^Which one - .*\? Who’s the client\? \(or "none"\)$/.test(relay(c.human) || ''), 'turn 2: passed by once -> asked again with "Which one"', relay(c.human));
const A2 = relay(c.human) + '\n' + A1;
const T3 = T2 + '\npost mixing';
c = cc(B, { summary: 'RUNWAY / Runway Productions / HL', client: 'Runway Productions', session_type: 'Post Mixing', requester_text: T3, asked_text: A1 });
ok(relay(c.human) === 'Who’s the client? (or "none")', 'live 13:33: a client nobody typed -> dropped and asked, not CLIENT_UNVERIFIED', [c.reason, relay(c.human)]);
const o88 = cc(OB, { summary: 'RUNWAY / Runway Productions / HL', client: 'Runway Productions', session_type: 'Post Mixing', requester_text: T3, asked_text: 'What kind of session is this? What’s the project?' });
ok(o88.reason === 'CLIENT_UNVERIFIED', '  (v88: CLIENT_UNVERIFIED, an instruction with no question)', o88.reason);
c = cc(B, { summary: 'RUNWAY / HL', session_type: 'Post Mixing', requester_text: T3, asked_text: A2 });
ok(c.verdict === 'CLEAR', 'passed by twice -> no client, the card', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'RUNWAY / John Ableton / HL', client: 'John Ableton', session_type: 'Post Mixing', requester_text: T3 + '\nclient is john ableton', asked_text: A2 });
ok(c.verdict === 'CLEAR' && /John Ableton/.test(c.final_summary), 'the client given -> the card with it', [c.reason, c.final_summary]);

console.log('Book Session v89 - when the client is not asked');
c = cc(B, { summary: 'RUNWAY / HL', session_type: '', requester_text: T1 + ', no client' });
ok(relay(c.human) === 'What kind of session is this? What’s the project?', '"no client" -> not asked', relay(c.human));
c = cc(B, { summary: 'RUNWAY / HL', session_type: '', requester_text: T1 + ', my own project runway' });
ok(!/client/i.test(relay(c.human) || ''), '"my own project" (Personal) -> not asked', relay(c.human));
c = cc(B, { summary: 'RUNWAY / Jem Lim / HL', client: 'Jem Lim', session_type: '', requester_text: T1 + ' for jem lim' }, [{ json: { id: 'rec1', fields: { Name: 'Jem Lim' } } }]);
ok(!/client/i.test(relay(c.human) || ''), 'a client named -> not asked', relay(c.human));
c = cc(B, { summary: 'LIKHA - Audio Post', session_type: '', rooms: 'Likha', requester_text: 'book likha next thu 3-5pm for a meeting' });
ok(!/client/i.test(String(c.human || '')), 'a conference room -> not asked', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'NET-KUBA / HL', session_type: 'Localization Mixing', requester_text: T1 + ' loc mixing project net-kuba' });
ok(!/client/i.test(relay(c.human) || ''), 'Localization (a project code) -> not asked', [c.reason, relay(c.human)]);
c = cc(B, { summary: 'SESSION / HL', session_type: '', requester_text: 'book studio 8 next thu' });
ok(/^What kind of session is this\? What’s the project, and who’s the client\? \(or "none"\) And what time\?$/.test(relay(c.human) || ''), 'with the time missing too -> one message', relay(c.human));
c = cc(B, { summary: 'SESSION / HL', session_type: '', requester_text: 'book studio 8 3-5pm', expected_date: '' });
ok(c.reason !== 'MISSING_DATE' || /who’s the client/.test(relay(c.human) || ''), 'no day: the client rides on the day question', [c.reason, relay(c.human)]);

console.log('Book Session v89 - the refusals outside prepare mode carry a question');
c = cc(B, { mode: '', summary: 'RUNWAY / Runway Productions / HL', client: 'Runway Productions', session_type: 'Post Mixing', requester_text: T3, bookingType: 'Advertising' });
ok(c.reason === 'CLIENT_UNVERIFIED' && relay(c.human) === 'Who’s the client? (or "none")' && !/leave it empty/.test(c.human), 'CLIENT_UNVERIFIED -> "Who’s the client? (or \\"none\\")"', [c.reason, c.human]);

console.log('Guard Probe v218 - an instruction never reaches the requester');
const gp = (W, output, said, steps = [], bf = {}) => new Function('$input', '$', code(W, 'Guard Probe'))(
  wrap([{ json: { output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '', ...bf } }]) : n === 'Gate Context' ? wrap([{ json: { datesUnderDiscussion: '2027-10-14' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(recM(n) || [{ json: {} }]))[0].json.output;
const UNV = 'Nothing was booked. "Runway Productions" is not in the Clients list and is not a name the requester gave. Ask the requester who the client is, use the name exactly as they type it, and present the summary again. If there is no client, leave it empty.';
const STEP = [{ action: { tool: 'Prepare_Booking' }, observation: JSON.stringify([{ status: 'REJECTED', reason: 'CLIENT_UNVERIFIED', human: UNV }]) }];
let o = gp(M, UNV, T3, STEP);
ok(o === 'Who’s the client? (or "none")', 'live 13:33: the pasted instruction -> the client question', o);
ok(gp(OM, UNV, T3, STEP) === 'Nothing was booked. If there is no client, leave it empty.', '  (v217: the leak)', gp(OM, UNV, T3, STEP));
o = gp(M, 'Nothing was booked. Ask exactly this, in one message: "Which day?" Then prepare it again.', T3, [{ action: { tool: 'Book_Session' }, observation: JSON.stringify([{ status: 'REJECTED', reason: 'X', human: 'x' }]) }]);
ok(!/Ask exactly|prepare it again/.test(o) && o.length > 0, 'any other pasted instruction -> never the instruction', o);
o = gp(M, 'Nothing was booked - Studio 8 is taken then. Studio 7 is free.', T3);
ok(o === 'Nothing was booked - Studio 8 is taken then. Studio 7 is free.', 'a real reply is left alone', o);
console.log('Guard Probe v218 - the model\'s own booking question asks for the client too');
o = gp(M, 'What kind of session is this?', 'book studio 8 next thu 3-5pm');
ok(o === 'What kind of session is this? What’s the project, and who’s the client? (or "none")', 'live turn 1, model-written -> project and client', o);
o = gp(M, 'What kind of session is this?', 'book studio 8 next thu 3-5pm project runway, no client');
ok(o === 'What kind of session is this?', '"no client" -> nothing added', o);
o = gp(M, 'What kind of session is this?', 'book studio 8 next thu 3-5pm project runway for Spotify', [], { forClient: 'Spotify' });
ok(o === 'What kind of session is this?', 'a "for <client>" -> nothing added', o);
o = gp(M, 'What time works?', 'book likha next thu for a meeting');
ok(!/client/.test(o), 'a meeting room -> no client asked', o);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
