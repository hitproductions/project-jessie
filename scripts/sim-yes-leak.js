#!/usr/bin/env node
// Offline tests for main v210 + Book Session v83 (live 2 Oct 01:50: "ye" not a yes; at the yes a new client the card
// had already passed was refused CLIENT_UNVERIFIED, and the refusal - written for the model - reached Slack).
//   node scripts/sim-yes-leak.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v210.json'), B = WF(process.env.BOOK || 'book-session-v83.json'), OB = WF('book-session-v82.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
console.log('Book Direct Reply - nothing meant for the model reaches Slack');
const bdr = r => new Function('$input', '$', code(M, 'Book Direct Reply'))(wrap([{ json: r }]), () => wrap([{ json: {} }]))[0].json.output;
let o = bdr({ verdict: 'REJECTED', reason: 'CLIENT_UNVERIFIED', human: 'Nothing was booked. "ruff lopez" is not in the Clients list and is not a name the requester gave. Ask the requester who the client is, use the name exactly as they type it, and present the summary again. If there is no client, leave it empty.' });
ok(!/requester|Ask |present the summary|leave it empty/i.test(o) && /^Nothing was booked/.test(o), 'live 01:50 refusal -> plain text', o);
o = bdr({ verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'That overlaps a booking you already have: "CATS / HL" (Studio 8, 3:00 PM - 6:00 PM). Nothing was booked. Ask the requester whether they want to move that booking to the new time instead of making a second one; if they do, call Move Booking for it.' });
ok(o === 'That overlaps a booking you already have: "CATS / HL" (Studio 8, 3:00 PM - 6:00 PM). Nothing was booked.', 'ROOM_OCCUPIED -> the overlap, no instruction', o);
o = bdr({ verdict: 'REJECTED', reason: 'MISSING_CLIENT', human: 'Nothing was booked. Japs is who this session is booked FOR, not the client - so Japs must not be the client and must not appear in the calendar title. Ask the requester who the client is. Present the summary again.' });
ok(!/must not|requester|summary/i.test(o), 'MISSING_CLIENT -> no model talk', o);
ok(bdr({ status: 'CREATED', human: 'Booked.' }) === 'Booked.', '"Booked." unchanged');
console.log('Book Session v83 - a yes to a verified card is not re-checked for the client');
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const cuBlock = w => { const s = code(w, 'Check Conflicts'), i = s.indexOf('// --- a new client must be one the requester actually typed (v50)'), j = s.indexOf('// Rooms and session types are passed in by Room Table');
  return new Function('REQ', '$', s.slice(i, j) + '\nreturn null;'); };
const cu = (w, req) => { const r = cuBlock(w)({ ...REQ0, ...req }, n => wrap(n === 'Get Client' ? [{ json: {} }] : [])); return r ? r[0].json.reason : 'CLEAR'; };
const YES = { mode: '', prepared_ok: true, require_prepared: true, client: 'ruff lopez', summary: 'THANK YOU / ruff lopez / HL x BPV', requester_text: 'yes' };
ok(cu(B, YES) === 'CLEAR', 'live 01:50: the yes to the card -> booked, not CLIENT_UNVERIFIED', cu(B, YES));
ok(cu(OB, YES) === 'CLIENT_UNVERIFIED', '  (v82: refused)');
ok(cu(B, { ...YES, mode: 'prepare', prepared_ok: false }) === 'CLIENT_UNVERIFIED', 'preparing the card still refuses a client nobody typed');
ok(cu(B, { ...YES, mode: 'prepare', prepared_ok: false, requester_text: 'book thank you for ruff lopez' }) === 'CLEAR', '... and accepts one they typed (a new client, logged)');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
