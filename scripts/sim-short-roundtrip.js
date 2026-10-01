#!/usr/bin/env node
// Offline round trip for Book Session v73 + main v203 (short summary, PENDING 69): the card Book Session renders and
// the record it stores -> the yes -> main's Prepared Key / Read Prepared / Prepared Booking -> what Book Direct books.
// Plus main v203's small fixes.   node scripts/sim-short-roundtrip.js <book-prepare-exec.json> <main-exec.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v73.json'), M = WF(process.env.MAIN || 'project-jessie-v203.json'), OM = WF('imported/project-jessie-v202-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const brun = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData, mrun = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
const brec = n => brun[n] ? (((brun[n][0].data || {}).main || [[]])[0] || []) : null, mrec = n => mrun[n] ? (((mrun[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = brec('When Executed by Another Workflow')[0].json, ME = 'U08V3CKDGJF';
// Book Session: prepare
const prepare = req => { const R = [{ json: { ...REQ0, ...req } }]; const O = { 'Get Client': brec('Get Client'), 'Client Aliases': [{ json: {} }] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : wrap(brec(n) || [{ json: {} }]);
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(B, 'Check Conflicts'))($, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const $r = n => n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : $(n);
  return new Function('$', '$input', code(B, 'Render Summary'))($r, wrap([{ json: c }]))[0].json; };
// Guard turns "Confirm to book." into the one-line confirmation, as sent to Slack
const sent = o => o.summary_text.replace(/\n*Confirm to book\.\s*$/, '\n\nBook it? Reply yes or no.');
// main at the yes
const atYes = (w, botText, rows, user = ME, confirmed = true) => {
  const hist = [{ json: { text: 'yes', user, ts: '1790900002.1' } }, { json: { text: botText, bot_id: 'B1', ts: '1790900001.1' } }];
  const base = n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: { user, text: 'yes', ts: '1790900002.1' } }]) : n === 'Gate Context' ? wrap([{ json: { confirmed } }]) : wrap(mrec(n) || [{ json: {} }]);
  const pk = w.nodes.some(n => n.name === 'Prepared Key') ? new Function('$', '$input', code(w, 'Prepared Key'))(base, wrap([]))[0].json : {};
  const $ = n => n === 'Prepared Key' ? wrap([{ json: pk }]) : n === 'Read Prepared' ? wrap(rows.filter(r => r.cache_key === pk.prep_key).map(r => ({ json: r })).concat([]).length ? rows.filter(r => r.cache_key === pk.prep_key).map(r => ({ json: r })) : [{ json: {} }]) : base(n);
  return { pk, pb: new Function('$', '$input', code(w, 'Prepared Booking'))($, wrap([]))[0].json }; };
const store = o => [{ cache_key: o.prep_key, payload: o.prep_payload, refreshed_at: new Date().toISOString() }];

console.log('The round trip');
const o = prepare({ summary: 'QART / Jem Lim / DR', client: 'Jem Lim', engineer: 'Drey', session_type: 'VO Recording', rooms: 'Studio 8', bookingType: '',
  description: 'Engineer: Drey | Booked by: Howard Luistro | ref: ' + ME, requester_text: 'book qart studio 8 nov 18 2-4pm vo recording, client jem lim, engineer drey', asked_text: '' });
const msg = sent(o);
ok(msg === '*QART / Jem Lim / DR*\n*Date:* Thursday, November 18, 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.', 'the card as sent', msg);
let y = atYes(M, msg, store(o));
ok(y.pk.prep_key === o.prep_key, 'at the yes, main works out the same key from the message', [y.pk.prep_key, o.prep_key]);
ok(y.pb.use === true && y.pb.p.summary === 'QART / Jem Lim / DR' && y.pb.p.client === 'Jem Lim' && y.pb.p.rooms === 'Studio 8' && y.pb.p.start_iso === '2027-11-18T14:00:00+08:00'
   && y.pb.p.end_iso === '2027-11-18T16:00:00+08:00' && y.pb.p.session_type === 'VO Recording' && /Daryl Reyes/.test(y.pb.p.engineer) && y.pb.p.bookingType === 'Advertising' && y.pb.p.department === 'Audio Post',
   'Prepared Booking books every stored detail - client, engineer, session type, type, department', y.pb);
ok(atYes(OM, msg, store(o)).pb.use === false, '  (v202: "no check code - it was not prepared")');
ok(atYes(M, msg, []).pb.use === false && /nothing intact was stored/.test(atYes(M, msg, []).pb.reason), 'nothing stored (the save failed) -> not booked; Book Session refuses NOT_PREPARED and it is prepared again');
ok(atYes(M, msg.replace('2:00 PM – 4:00 PM', '3:00 PM – 5:00 PM'), store(o)).pb.use === false, 'a card that was changed after it was prepared -> another key, not booked');
ok(atYes(M, msg, store(o), 'U0SOMEONE').pb.use === false, 'someone else saying yes to it -> their key differs, not booked');
{ const P = JSON.parse(o.prep_payload); P.F.Client = 'Tampered'; ok(atYes(M, msg, [{ ...store(o)[0], payload: JSON.stringify(P) }]).pb.use === false, 'a stored record that does not match its own code -> not booked'); }
ok(atYes(M, msg, [{ ...store(o)[0], refreshed_at: new Date(Date.now() - 13 * 3600000).toISOString() }]).pb.use === false, 'a record over 12 hours old -> not booked');
ok(atYes(M, msg, store(o), ME, false).pb.use === false, 'not a confirmed yes -> not used');
{ const OB = WF('imported/book-session-v72-imported.json');
  const $o = n => n === 'When Executed by Another Workflow' ? wrap([{ json: { ...REQ0 } }]) : wrap(brec(n) || [{ json: {} }]);
  const c0 = new Function('$', '$input', '$getWorkflowStaticData', code(OB, 'Check Conflicts'))($o, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const old = new Function('$', '$input', code(OB, 'Render Summary'))(n => n === 'Check Conflicts' ? wrap([{ json: c0 }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : $o(n), wrap([{ json: c0 }]))[0].json;
  const om = old.summary_text.replace(/\n*Reply only with[^\n]*\nConfirm to book\.\s*$/, '\n\nBook it? Reply yes or no.');
  ok(/_check /.test(om) && atYes(M, om, []).pb.use === true, 'a summary sent before this build (with its printed code) still books the old way'); }

console.log('Guard Probe - a "no" to the same summary is still recognised');
{ const gp = (w, bt, out) => new Function('$input', '$', code(w, 'Guard Probe'))(
    wrap([{ json: { output: 'x', intermediateSteps: [{ action: { tool: 'Prepare_Booking' }, observation: JSON.stringify([{ status: 'PREPARED', summary_text: out }]) }] } }]),
    n => n === 'Gate Context' ? wrap([{ json: { declineNotice: 'THEY SAID NO' } }]) : n === 'Booked For' ? wrap([{ json: { botText: bt } }]) : wrap(mrec(n) || [{ json: {} }]))[0].json.output;
  ok(/nothing was booked\. What would you like to change\?/.test(gp(M, msg, o.summary_text)), 'the refused card prepared again -> "No problem - nothing was booked. What would you like to change?"');
  ok(/^\*QART/.test(gp(M, 'something else', o.summary_text)), 'a different card -> sent as is'); }

console.log('main v203 - small fixes');
{ const gp2 = (out, steps = []) => new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output: out, intermediateSteps: steps } }]),
    n => wrap(mrec(n) || [{ json: {} }]))[0].json.output;
  const same = '*QAMD / HL*\n*Now:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nConfirm to move.';
  const o2 = gp2('x', [{ action: { tool: 'Move_Booking' }, observation: JSON.stringify([{ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: same }]) }]);
  ok(o2 === 'That’s already at November 2, 2027, 3:00 PM – 5:00 PM, Studio 8 - nothing to change.', 'a move card that moves nothing -> "That’s already at ..."', o2); }
const bf = (w, convo) => { const h = convo.slice().reverse();
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(mrec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
let TS = 1790900000; const U = t => ({ json: { ts: String(TS++) + '.1', text: t, user: ME } }), J = t => ({ json: { ts: String(TS++) + '.1', text: t, bot_id: 'B1' } });
let r = bf(M, [U('book qamd studio 8 every tuesday 10am to 12pm on nov 2 and nov 9, vo recording, no client, external')]);
ok(r.engineer === 'Howard Luistro' && /THE ENGINEER IS Howard Luistro/.test(r.notice || ''), 'a series by an engineer who named no one -> the model is told he is the engineer (no question)', [r.engineer, (r.notice || '').slice(0, 120)]);
ok(!bf(OM, [U('book qamd studio 8 every tuesday 10am to 12pm on nov 2 and nov 9, vo recording, no client, external')]).engineerDefault, '  (v202: nothing said - the model asked)');
ok(bf(M, [U('book qamd studio 8 nov 2, engineer drey')]).engineer === 'Daryl Reyes', 'an engineer named -> that one');
ok(!bf(M, [U('book qamd studio 8 nov 2 10am, no engineer')]).engineerDefault, '"no engineer" -> not put in');
{ const SUM = '*QAMD / HL*\n*Dates (2):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027\n*Time:* 3:00 PM – 5:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.';
  r = bf(M, [U('book qamd ...'), J(SUM), U('yes'), J('Booked 2 sessions:\n- November 2, 2027 (Tue)\n- November 9, 2027 (Tue)'), U('make it 3pm instead'), J('That was a series of 2. ...'), U('all'),
    J('*QAMD / HL*\n*Now:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.'), U('yes'),
    J('Moved "QAMD / HL" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8.\n\n*QAMD / HL*\n*Now:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.'), U('move to 10am instead')]);
  ok(r.justBooked && r.justBooked.iso === '2027-11-09' && r.moveStart === '10:00' && r.moveEnd === '12:00', 'the live 11:18 case: "move to 10am instead" while the 9 Nov card shows -> 9 Nov, 10-12', [r.justBooked, r.moveStart]); }

console.log('The prompt and the tools');
const sm = M.nodes.find(n => n.name === 'Jessie AI Agent').parameters.options.systemMessage;
ok(/## Booking type/.test(sm) && !/External or Personal/.test(sm) && /Advertising\*, \*Entertainment\*, \*Internal\* or \*Personal/.test(sm), 'the prompt: four types, worked out by Prepare Booking');
ok(/Who's engineering\?/.test(sm) && /in as few words as possible/.test(sm), 'the prompt: short questions');
ok(['Prepare Booking', 'Book Session', 'Book Series'].every(t => /Advertising, Entertainment, Internal or Personal/.test(M.nodes.find(n => n.name === t).parameters.workflowInputs.value.bookingType)), 'the three bookingType inputs');
const to = n => ((((M.connections[n] || {}).main || [])[0]) || []).map(t => t.node);
ok(JSON.stringify(to('Booked For')) === '["Prepared Key"]' && JSON.stringify(to('Prepared Key')) === '["Read Prepared"]' && JSON.stringify(to('Read Prepared')) === '["Prepared Booking"]', 'wiring: Booked For -> Prepared Key -> Read Prepared -> Prepared Booking');
const RP = M.nodes.find(n => n.name === 'Read Prepared');
ok(RP.parameters.operation === 'get' && RP.parameters.dataTableId.value === 'CsdJhgDxCsqq9K9j' && RP.alwaysOutputData && RP.onError === 'continueRegularOutput', 'Read Prepared: the reference-cache table, never stops the turn');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
