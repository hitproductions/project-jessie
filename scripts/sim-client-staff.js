#!/usr/bin/env node
// sim-client-staff (Book Session v107, PENDING 82): a client given as a nickname that is also a staff member's is asked.
//   node scripts/sim-client-staff.js <main-execution.json>     (BOOK=book-session-vN.json)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f))), code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v107.json');
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData, rec = n => run[n] ? run[n][0].data.main[0] : null;
const REF = rec('Room Table')[0].json.referenceData, wrap = it => ({ first: () => it[0], all: () => it });
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const AL = [{ json: { fields: { Name: 'Angela dela Calzada', Notes: 'Producer. Goes by Anj.', 'Booker Type': 'Producer' } } }];
const cc = (client, txt) => { const R = [{ json: { mode: 'prepare', series: false, department: '', arranger: '', booked_for: '', all_day: false, bookingType: '', reference_data: REF, rooms: 'Studio 7',
    engineer: 'Howard Luistro', session_type: 'VO Recording', client, expected_date: '2027-10-13', start_iso: '2027-10-13T14:00:00+08:00', end_iso: '2027-10-13T16:00:00+08:00',
    summary: 'ORANGE / ' + client + ' / HL', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U08V3CKDGJF', asked_text: txt, requester_text: txt } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': AL, 'All Client Names': [{ json: { fields: { Name: 'Angela dela Calzada' } } }] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(rec('All Bookers')) : wrap([{ json: {} }]);
  return new Function('$', '$input', '$getWorkflowStaticData', code(B, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
const T = 'book studio 7 tomorrow 2-4pm, vo recording, project orange, ';
let r = cc('Anj', T + 'client is anj');
ok(r.reason === 'AMBIGUOUS_PERSON' && /Ask exactly this, in one message: "Just to check - by Anj, do you mean Angelo Villegas \(Music Arranger\) or Angela dela Calzada \(Producer, a client\)\?"/.test(r.human), '"client is anj" -> asked which (live 4 Oct)', [r.reason, r.human]);
r = cc('Anj', T + 'client is anj, the producer');
ok(r.reason !== 'AMBIGUOUS_PERSON', '"anj, the producer" -> not asked (the client side is said)', r.reason);
r = cc('Anj', T + 'client is anj villegas');
ok(r.reason !== 'AMBIGUOUS_PERSON', '"anj villegas" -> not asked (the staff side is said)', r.reason);
r = cc('Angela dela Calzada', T + 'client is angela dela calzada');
ok(r.reason !== 'AMBIGUOUS_PERSON', 'the full client name -> not asked', r.reason);
r = cc('Jem Lim', T + 'client is jem lim');
ok(r.reason !== 'AMBIGUOUS_PERSON', 'a client with no staff namesake -> not asked', r.reason);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
