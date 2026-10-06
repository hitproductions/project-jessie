#!/usr/bin/env node
// QA bug 17 (29 Sep): a bare "yes" right after a reported result is answered in code, not by the model.
//
//   node scripts/sim-repeat-yes.js <main.json>
const fs = require('fs');
const M = JSON.parse(fs.readFileSync(process.argv[2]));
const node = n => M.nodes.find(x => x.name === n);
const wrap = it => ({ first: () => it[0], all: () => it });
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d))); } };
const run = (said, saidYes, lastBot, confirmedCancel = false) => new Function('$', '$input', node('Prepared Cancel').parameters.jsCode)(
  n => n === 'Gate Context' ? wrap([{ json: { confirmedCancel, gate: { said, saidYes } } }])
     : n === 'Get Recent Messages' ? wrap([{ json: { user: 'U1', text: said, ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text: lastBot, ts: String(Date.now() / 1000 - 30) } }])
     : wrap([{ json: {} }]), wrap([{ json: { x: 1 } }]))[0].json;
ok(/already booked/.test(run('yes', true, 'Booked.')._alreadyDone), 'yes after "Booked." -> "That\'s already booked"');
ok(/already booked/.test(run('yes', true, 'Booked 4 sessions:\n- November 2, 2027 (Tue)')._alreadyDone), 'yes after a series result -> already booked');
ok(/already cancelled/.test(run('yes', true, 'Cancelled "QATEST / Jem Lim / TL".')._alreadyDone), 'yes after "Cancelled ..." -> already cancelled');
ok(/already moved/.test(run('yes', true, 'Moved "QATEST / Jem Lim / TL" to Friday, October 8, 2027, 5:00 PM – 7:00 PM.')._alreadyDone), 'yes after "Moved ..." -> already moved');
ok(run('book studio 7 tomorrow at 2pm', false, 'Booked.')._alreadyDone === '', 'a new request after "Booked." is not caught');
ok(run('yes', true, 'Which room would you like?')._alreadyDone === '', 'a yes to a question is not caught');
ok(run('yes', true, 'Nothing was booked. What would you like changed?')._alreadyDone === '', '"Nothing was booked" is not a completed result');
const card = '*QATEST / Jem Lim / TL*\n*Date:* Thursday, October 7, 2027\n*Time:* 2:00 PM – 3:00 PM\n*Room:* Studio 7\n*Booked by:* Tara Lim\n_check 1234abcd_\n\nCancel it? Reply yes or no.';
const c = run('yes', true, card, true);
ok(c._cancelDirect.use === true && c._alreadyDone === '', 'a yes to a cancel card still goes to Cancel Direct');
ok(run('yes', true, 'Booked.').x === 1, 'input passed through unchanged');
const to = (n, b = 0) => ((((M.connections[n] || {}).main || [])[b]) || []).map(t => t.node);
// v202: Move Direct? sits between Cancel Direct? and Already Done? (a confirmed move card goes to Move Booking directly)
const _afterCancel = JSON.stringify(to('Cancel Direct?', 1)) === '["Already Done?"]' || (JSON.stringify(to('Cancel Direct?', 1)) === '["Move Direct?"]' && JSON.stringify(to('Move Direct?', 1)) === '["Already Done?"]')
  // v225: Prepared Series / Series Direct? sit between Move Direct? and Already Done? (a confirmed series card is booked directly)
  || (JSON.stringify(to('Cancel Direct?', 1)) === '["Move Direct?"]' && JSON.stringify(to('Move Direct?', 1)) === '["Prepared Series"]' && JSON.stringify(to('Prepared Series')) === '["Series Direct?"]' && (JSON.stringify(to('Series Direct?', 1)) === '["Already Done?"]'
       || (JSON.stringify(to('Series Direct?', 1)) === '["Series Busy?"]' && JSON.stringify(to('Series Busy?', 1)) === '["Already Done?"]')));   // v226: Series Busy?
ok(_afterCancel && JSON.stringify(to('Already Done?', 0)) === '["Already Done Reply"]'
   && JSON.stringify(to('Already Done Reply')) === '["Send Reply"]' && JSON.stringify(to('Already Done?', 1)) === '["Jessie AI Agent"]',
   'wiring: Cancel Direct? -> Already Done? -> reply | AI Agent');
ok(/seriesNotice/.test(node('Jessie AI Agent').parameters.options.systemMessage), 'the prompt carries the series notice');
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
