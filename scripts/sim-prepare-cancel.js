#!/usr/bin/env node
// Offline tests for Prepare Cancel (Cancel Booking v18 + main v177). No calendar is touched.
//
//   node scripts/sim-prepare-cancel.js <main-execution.json>
//
// The main execution supplies real inputs for Guard Probe. The card round trip is the core check: Cancel Booking
// renders a card, main's Prepared Cancel reads that exact text back, and Cancel Booking accepts it only while the
// booking is unchanged.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(__dirname, '..', 'workflows', f)));
const C18 = WF('cancel-booking-v18.json'), C17 = WF('cancel-booking-v17.json'), M = WF(process.env.MAIN || 'project-jessie-v177.json'), M175 = WF('project-jessie-v175.json');
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const node = (w, n) => w.nodes.find(x => x.name === n);
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const ME = 'U026N6E1R', S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const ev = (id, summary, ref, s, e, extra = {}) => ({ id, summary, status: 'confirmed', description: 'Engineer: Tara Lim | Booked by: Tara Lim | ref: ' + ref + ' | Dept: Audio Post',
  start: { dateTime: s }, end: { dateTime: e }, attendees: [{ email: S7, displayName: 'KDC Plaza-Top Level-Studio 7 (7)', resource: true }], location: 'KDC Plaza-Top Level-Studio 7 (7)', ...extra });
const A = ev('a1', 'QATEST / Jem Lim / TL', ME, '2027-10-07T14:00:00+08:00', '2027-10-07T15:00:00+08:00');
const OTHER = ev('o1', 'THEIRS / Y / KS', 'U999', '2027-10-07T10:00:00+08:00', '2027-10-07T11:00:00+08:00');
const co = (w, req, items) => new Function('$', '$input', code(w, 'Check Ownership'))(() => ({ first: () => ({ json: req }) }), { first: () => ({ json: { items } }) })[0].json;
const base = { requester: ME, booking_date: '2027-10-07', event_id: '', authority: '', department: 'Audio Post' };

console.log('Cancel Booking v18 - prepare mode');
let r = co(C18, { ...base, mode: 'prepare', confirmed: false, title: 'QATEST / Jem Lim / TL' }, [A, OTHER]);
ok(r.verdict === 'PREPARED' && r.event_id === 'a1', 'own booking -> PREPARED, nothing deleted', r);
const card = r.card_text;
ok(/^\*QATEST \/ Jem Lim \/ TL\*/.test(card) && /\*Date:\* Thursday, October 7, 2027/.test(card) && /\*Time:\* 2:00 PM – 3:00 PM/.test(card)
   && /\*Room:\* Studio 7/.test(card) && /\*Booked by:\* Tara Lim/.test(card) && /_check [0-9a-f]{8}_/.test(card) && /Confirm to cancel\.$/.test(card), 'card: title, date, time, room, booked by, check code, marker', card);
ok(co(C18, { ...base, mode: 'prepare', confirmed: false, title: 'THEIRS / Y / KS' }, [A, OTHER]).reason === 'NOT_YOURS', "someone else's booking -> refused, no card");
ok(co(C18, { ...base, mode: 'prepare', confirmed: false, title: 'NOREF' }, [ev('n1', 'NOREF', '', '2027-10-07T09:00:00+08:00', '2027-10-07T10:00:00+08:00', { description: 'no marker' })]).reason === 'NO_REFERENCE', 'no booker reference -> refused, no card');
ok(co(C18, { ...base, mode: 'prepare', confirmed: false, title: 'QATEST' }, [A]).reason === 'AMBIGUOUS_TITLE', 'a partial title is not prepared (v17 rule kept)');
ok(co(C18, { ...base, confirmed: false, title: 'QATEST / Jem Lim / TL' }, [A]).reason === 'NOT_CONFIRMED', 'outside prepare mode, no yes -> NOT_CONFIRMED as before');

console.log('The card round trip (Cancel -> Slack text -> main -> Cancel)');
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const pcRun = (text, gate = { confirmedCancel: true }, ageS = 60) => new Function('$', '$input', code(M, 'Prepared Cancel'))(
  n => n === 'Gate Context' ? wrap([{ json: gate }]) : n === 'Get Recent Messages' ? wrap([{ json: { user: ME, text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text, ts: String(Date.now() / 1000 - ageS) } }]) : wrap(rec(n) || []),
  wrap([{ json: { roomTable: 'kept' } }]))[0].json;
const gpSend = txt => new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output: 'x', intermediateSteps: [{ action: { tool: 'Prepare_Cancel' }, observation: JSON.stringify([{ status: 'PREPARED', card_text: txt }]) }] } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
const sent = gpSend(card);
ok(sent === card.replace(/\n\nReply only with[^\n]*\nConfirm to cancel\.$/, '\n\nCancel it? Reply yes or no.'), 'Guard Probe sends the card with only its last line shortened (booking lines and code unchanged)', sent);
let p = pcRun(sent);
ok(p._cancelDirect.use === true && p._cancelDirect.title === 'QATEST / Jem Lim / TL' && p._cancelDirect.booking_date === '2027-10-07', 'main reads title, date and code back off the card', p._cancelDirect);
ok(p.roomTable === 'kept', 'Prepared Cancel passes its input through unchanged');
const yes = (items, over = {}) => co(C18, { ...base, confirmed: true, title: p._cancelDirect.title, booking_date: p._cancelDirect.booking_date, check_code: p._cancelDirect.check_code, ...over }, items);
r = yes([A, OTHER]); ok(r.verdict === 'CLEAR' && r.event_id === 'a1' && r.matched_on === 'card', 'yes -> the booking on the card is cleared for deletion', r);
r = yes([{ ...A, end: { dateTime: '2027-10-07T16:00:00+08:00' } }]); ok(r.reason === 'CHANGED', 'booking changed after the card (end time) -> CHANGED, nothing cancelled');
r = yes([{ ...A, attendees: [{ email: 'x@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio 8 (8)', resource: true }], location: 'KDC Plaza-Top Level-Studio 8 (8)' }]); ok(r.reason === 'CHANGED', 'room changed after the card -> CHANGED');
r = yes([{ ...A, id: 'a9' }]); ok(r.reason === 'CHANGED', 'deleted and re-created with the same details (new event) -> CHANGED');
r = yes([OTHER]); ok(r.reason === 'NOT_ON_CALENDAR', 'booking gone (e.g. a repeated yes) -> NOT_ON_CALENDAR');
const A2 = { ...A, id: 'a2', start: { dateTime: '2027-10-07T16:00:00+08:00' }, end: { dateTime: '2027-10-07T17:00:00+08:00' } };
r = yes([A2, A]); ok(r.verdict === 'CLEAR' && r.event_id === 'a1', 'two bookings share the title -> the code picks the one on the card');
r = yes([A], { requester: 'U555' }); ok(r.reason === 'NOT_YOURS', 'a yes from someone without authority -> refused (ownership rechecked live)');
r = yes([A], { confirmed: false }); ok(r.reason === 'NOT_CONFIRMED', 'code but no confirmed yes -> NOT_CONFIRMED');
r = yes([A], { check_code: 'deadbeef' }); ok(r.reason === 'CHANGED', 'a wrong code never cancels');

{ const AMP = { ...A, id: 'amp1', summary: 'R&B / Jem Lim / TL' };
  const c2 = co(C18, { ...base, mode: 'prepare', confirmed: false, title: 'R&B / Jem Lim / TL' }, [AMP]).card_text;
  const p2 = pcRun(c2.replace(/&/g, '&amp;'))._cancelDirect;
  ok(co(C18, { ...base, confirmed: true, title: p2.title, booking_date: p2.booking_date, check_code: p2.check_code }, [AMP]).verdict === 'CLEAR', 'a title with "&" survives Slack\'s &amp; escaping'); }
console.log('main - when the direct path is used');
ok(pcRun(card, { confirmedCancel: false })._cancelDirect.use === false, 'no confirmed yes (a conditional reply such as "yes but..." is not one) -> not used');
ok(pcRun(card.replace(/_check [0-9a-f]{8}_\n/, ''))._cancelDirect.use === false, 'a card the model wrote (no check code) -> not used, model handles it');
p = pcRun(card, { confirmedCancel: true }, 5 * 3600);
ok(p._cancelDirect.use === false && p._cancelDirect.card_code === pcRun(card)._cancelDirect.check_code, 'a card over 4 hours old -> not used directly, but the model\'s own call is still held to it');
ok(pcRun('*QATEST / Jem Lim / TL*\n*Date:* Thursday, October 7, 2027\n_check 1234abcd_\n\nConfirm to book. (yes/no)')._cancelDirect.use === false, 'the last message is a booking summary -> not used');
const tool = node(M, 'Cancel Booking').parameters.workflowInputs.value;
ok(/card_code/.test(tool.check_code), "the model's Cancel Booking call carries the card code");

console.log('main - wiring and replies');
const to = (w, n, b = 0) => ((((w.connections[n] || {}).main || [])[b]) || []).map(t => t.node);
ok(JSON.stringify(to(M, 'Book Direct?', 1)) === '["Prepared Cancel"]' && JSON.stringify(to(M, 'Prepared Cancel')) === '["Cancel Direct?"]', 'after Book Direct? declines: Prepared Cancel -> Cancel Direct?');
// v187 (PENDING 55) puts Next Cancel? between Cancel Direct and its reply (sim-two-cancels.js covers that branch)
const _cd = JSON.stringify(to(M, 'Cancel Direct'));
ok(JSON.stringify(to(M, 'Cancel Direct?', 0)) === '["Cancel Direct"]' && (_cd === '["Cancel Direct Reply"]' || (_cd === '["Next Cancel?"]' && JSON.stringify(to(M, 'Next Cancel?', 1)) === '["Cancel Direct Reply"]')) && JSON.stringify(to(M, 'Cancel Direct Reply')) === '["Send Reply"]', 'direct path: Cancel Direct -> reply -> Send Reply, the AI Agent is not on it');
// v230: Already Done? reaches the agent through the early room check (both its branches end at the agent)
const _adAgent = JSON.stringify(to(M, 'Already Done?', 1)) === '["Jessie AI Agent"]' || (JSON.stringify(to(M, 'Already Done?', 1)) === '["Early Room Plan"]'
  && JSON.stringify(to(M, 'Early Room Plan')) === '["Early Room Check?"]' && JSON.stringify(to(M, 'Early Room Check?', 1)) === '["Jessie AI Agent"]'
  && JSON.stringify(to(M, 'Early Room Check')) === '["Early Room Result"]' && JSON.stringify(to(M, 'Early Room Result')) === '["Jessie AI Agent"]');
const _rest = to(M, 'Cancel Direct?', 1);   // v178 puts Already Done? (bug 17) between Cancel Direct? and the agent
ok(JSON.stringify(_rest) === '["Jessie AI Agent"]' || (JSON.stringify(_rest) === '["Already Done?"]' && _adAgent)
   || (JSON.stringify(_rest) === '["Move Direct?"]' && JSON.stringify(to(M, 'Move Direct?', 1)) === '["Already Done?"]' && _adAgent)   // v202: via Move Direct?
   || (JSON.stringify(_rest) === '["Move Direct?"]' && JSON.stringify(to(M, 'Move Direct?', 1)) === '["Prepared Series"]' && JSON.stringify(to(M, 'Prepared Series', 0)) === '["Series Direct?"]' && (JSON.stringify(to(M, 'Series Direct?', 1)) === '["Already Done?"]' || (JSON.stringify(to(M, 'Series Direct?', 1)) === '["Series Busy?"]' && JSON.stringify(to(M, 'Series Busy?', 1)) === '["Already Done?"]')) && _adAgent),   // v225: via Series Direct?; v226: Series Busy?
   'everything else goes to the AI Agent as before');
ok(node(M, 'Cancel Direct').parameters.workflowId.value === 'bAyDw7udhmY0NL38' && node(M, 'Cancel Direct').parameters.workflowInputs.value.event_id === '', 'Cancel Direct calls Cancel Booking with the card, never a model event id');
ok(JSON.stringify(M.connections['Prepare Cancel']) === JSON.stringify(M.connections['Cancel Booking']), 'Prepare Cancel is wired to the agent like the other tools');
const reply = res => new Function('$input', '$', code(M, 'Cancel Direct Reply'))(wrap([{ json: res }]), n => n === 'Cancel Direct' ? wrap([{ json: res }]) : wrap([{ json: {} }]))[0].json.output;   // v187 reads Cancel Direct by name
ok(reply({ status: 'CANCELLED', human: 'Cancelled "QATEST / Jem Lim / TL".' }) === 'Cancelled "QATEST / Jem Lim / TL".', 'CANCELLED -> "Cancelled ..."');
ok(/may already have been cancelled/.test(reply({ status: 'REJECTED', reason: 'NOT_ON_CALENDAR', human: 'Nothing was cancelled - call Cancel Booking again...' })), 'a repeated yes -> "may already have been cancelled", no model instructions leaked');
ok(/changed since I showed it/.test(reply({ status: 'REJECTED', reason: 'CHANGED' })), 'CHANGED -> asks them to ask again');
ok(/don't have authority/.test(reply({ status: 'REJECTED', reason: 'NOT_YOURS', human: 'BLOCKED - ... Say exactly that to the requester and stop.' })) && !/Say exactly/.test(reply({ status: 'REJECTED', reason: 'NOT_YOURS', human: 'BLOCKED - Say exactly' })), 'NOT_YOURS -> plain refusal, no "Say exactly that" leak');
ok(/couldn't confirm/.test(reply({ status: 'REJECTED', reason: 'FAILED' })) && /couldn't confirm/.test(reply({ error: { message: 'x' } })), 'a failed or errored delete -> never "Cancelled"');

console.log('Guard Probe - the card is the reply');
const gp = code(M, 'Guard Probe');
const gin = rec('Guard Probe') || [{ json: {} }];
const steps = [{ action: { tool: 'Find_Booking' }, observation: '[]' }, { action: { tool: 'Prepare_Cancel' }, observation: JSON.stringify([{ status: 'PREPARED', card_text: card }]) }];
const gout = new Function('$input', '$', gp)(wrap([{ json: { ...gin[0].json, output: 'Here is the booking. Want me to cancel it?', intermediateSteps: steps } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json;
ok(gout.output === sent, 'the model\'s own wording is replaced by the card', gout.output);
const gout2 = new Function('$input', '$', gp)(wrap([{ json: { ...gin[0].json, output: 'Which booking?', intermediateSteps: [{ action: { tool: 'Find_Booking' }, observation: '[]' }] } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json;
// Other Guard Probe rules may still add a line (e.g. its missing-date question, depending on the recording); the
// point is that no card replaces the model's reply.
ok(/^Which booking\?/.test(gout2.output) && !/_check /.test(gout2.output), 'no Prepare Cancel this turn -> the model\'s reply, no card', gout2.output);

console.log('Prompt');
const sm = node(M, 'Jessie AI Agent').parameters.options.systemMessage;
ok(/call Prepare Cancel/.test(sm) && /Never write a cancel confirmation yourself/.test(sm) && !/End with the line `Confirm to cancel/.test(sm), 'prompt: Prepare Cancel writes the card, the model never does');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
