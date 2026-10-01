#!/usr/bin/env node
// Offline tests for main v202 (move direct + me fix) - PENDING 68 and 71. Real main execution 16685 for the nodes not
// replayed here.   node scripts/sim-move-direct.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v202.json'), O = WF('imported/project-jessie-v201-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const ME = 'U08V3CKDGJF'; let T = 1790900000;
const U = text => ({ json: { ts: String(T++) + '.1', text, user: ME } }), B = text => ({ json: { ts: String(T++) + '.1', text, bot_id: 'B1' } });
const bf = (w, convo) => { const h = convo.slice().reverse();
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const ev = (expr, ctx) => new Function('$', 'return ' + expr.replace(/^=\{\{ /, '').replace(/ \}\}$/, ''))(n => ({ first: () => ({ json: ctx[n] || {} }) }));
const node = n => M.nodes.find(x => x.name === n);

const CARD = '*QAONE / DR*\n*Now:* Tuesday, November 2, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 7\n\nMove it? Reply yes or no.';
const conv = [U('book qaone ...'), B('*QAONE / DR*\n*Date:* Tuesday, November 2, 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.'), U('yes'), B('Booked.'), U('move it to studio 7 at 3pm'), B(CARD), U('yes')];
const b = bf(M, conv);

console.log('Move Direct? - which yes goes straight to Move Booking');
const cond = node('Move Direct?').parameters.conditions.conditions[0].leftValue;
ok(ev(cond, { 'Gate Context': { confirmedMove: true }, 'Booked For': b }) === 'yes', 'a confirmed yes to a move card -> Move Direct');
ok(ev(cond, { 'Gate Context': { confirmedMove: false }, 'Booked For': b }) === 'no', 'not confirmed -> the model, as before');
ok(ev(cond, { 'Gate Context': { confirmedMove: true }, 'Booked For': {} }) === 'no', 'confirmed but no card read (a model-written move) -> the model, as before');

console.log('Move Direct - the inputs (the card, not the model)');
const V = node('Move Direct').parameters.workflowInputs.value, ctx = { 'Booked For': b, 'Gate Context': { confirmedMove: true }, 'Slack Trigger': { user: ME },
  'Get Booker': { fields: { Name: 'Howard Luistro', Department: ['Audio Post'], Authority: [] } }, 'Room Table': { referenceData: '{}' } };
const got = {}; for (const k of Object.keys(V)) got[k] = typeof V[k] === 'string' && V[k].startsWith('=') ? ev(V[k], ctx) : V[k];
ok(got.title === 'QAONE / DR' && got.booking_date === '2027-11-02' && got.new_start_iso === '2027-11-02T15:00:00+08:00' && got.new_end_iso === '2027-11-02T17:00:00+08:00' && got.new_rooms === 'Studio 7'
   && got.confirmed === true && got.requester === ME && got.event_id === '', 'title, date, new times, new room and the requester - from the card', got);
ok(node('Move Direct').parameters.workflowId.value === 't7lwR2km4tfN8DbM', 'it calls Move Booking (t7lwR2km4tfN8DbM)');
ok(node('Move Direct').onError === 'continueRegularOutput', 'a failure reaches the reply, not a crash');

console.log('Move Direct Reply - written in code');
const reply = (res, bfo = b) => new Function('$', '$input', node('Move Direct Reply').parameters.jsCode)(n => ({ first: () => ({ json: n === 'Booked For' ? bfo : {} }) }), wrap([{ json: res }]))[0].json.output;
ok(reply({ status: 'MOVED' }) === 'Moved "QAONE / DR" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 7.', 'MOVED -> one line, the card\'s new time', reply({ status: 'MOVED' }));
ok(/on the calendar twice/.test(reply({ status: 'PARTIAL' })), 'PARTIAL -> said plainly');
ok(/taken now, so nothing was moved/.test(reply({ status: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'Tell the requester ...' })) && !/requester/.test(reply({ status: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'Tell the requester ...' })), 'a refusal -> plain words, never the model-facing text');
ok(/couldn't confirm/.test(reply({})), 'nothing back -> "couldn\'t confirm", never "Moved"');
{ const NC = '*QASER / HL*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.';
  ok(reply({ status: 'MOVED' }, { ...b, seriesNextCard: NC }).endsWith('\n\n' + NC), 'a series -> the next date\'s card follows'); }

console.log('Wiring');
const to = (n, i = 0) => ((((M.connections[n] || {}).main || [])[i]) || []).map(t => t.node);
ok(JSON.stringify(to('Cancel Direct?', 1)) === '["Move Direct?"]' && JSON.stringify(to('Move Direct?', 0)) === '["Move Direct"]' && JSON.stringify(to('Move Direct?', 1)) === '["Already Done?"]'
   && JSON.stringify(to('Move Direct')) === '["Move Direct Reply"]' && JSON.stringify(to('Move Direct Reply')) === '["Send Reply"]',
   'Cancel Direct? (no) -> Move Direct? -> (yes) Move Direct -> Move Direct Reply -> Send Reply / (no) Already Done?');
ok(JSON.stringify(((O.connections['Cancel Direct?'] || {}).main || [])[1].map(t => t.node)) === '["Already Done?"]', '  (v201: straight to Already Done? and the model)');
ok(/md \? 'move direct'/.test(code(M, 'Turn Log Row')), 'the Turn Log shows "move direct"');

console.log('"me" as the engineer (PENDING 71)');
const ask = [U('book studio 8 for me tomorrow 3-6pm, project dashing for anj'), B('Just to check - by Anj, ...?'), U('angela'), B('Who is the engineer for this session?')];
let r = bf(M, [...ask, U('me')]);
ok(r.engineer === 'Howard Luistro' && r.engineerResolved && r.engineerIsMe, 'the live case: "me" to "Who is the engineer...?" -> Howard Luistro', [r.engineer, r.engineerIsMe]);
ok(bf(O, [...ask, U('me')]).engineer !== 'Howard Luistro', '  (v201: not read)');
for (const t of ["book studio 8 tomorrow 3-6pm, vo recording, i'm the engineer", 'book studio 8 tomorrow 3-6pm, engineer me', "studio 8 tomorrow 3pm, I'll engineer", 'studio 8 bukas 3pm, ako ang engineer'])
  ok(bf(M, [U(t)]).engineer === 'Howard Luistro', '"' + t.split(', ').pop() + '" -> the requester');
ok(!bf(M, [U('book studio 8 tomorrow 3-6pm for me')]).engineerIsMe, '"for me" alone is who it is for, not "I engineer" (an engineer requester may still be put in by default - v203)');
ok(bf(M, [...ask, U('drey')]).engineer === 'Daryl Reyes', 'a name to the engineer question -> that person, as before');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
