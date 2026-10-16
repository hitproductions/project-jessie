#!/usr/bin/env node
// Build B offline (Slack Interactions v18 + Move Booking v31 + Cancel Booking v28): free stretches when a room is taken;
// "Change other session details" (the form, the new title, the client check, Move's new title / details on the replacement);
// the engineer / arranger notices (booked, series, added in a change); everyone on a session told of a change / cancel.
// Usage: node scripts/sim-build-b.js [slack interactions v18] [move v31] [cancel v28]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v18.json', 'utf8'));
const mv = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/move-booking-v31.json', 'utf8'));
const cx = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/cancel-booking-v28.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

const V24 = JSON.stringify(si).indexOf('function typeRoles(') !== -1;   // v24: details shown at once, no box (sim-round-7)
(async () => {
  const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
  // ---- Move v31: free stretches (the live case: ORANGE 12-2 PM, GOLDFISH 10-12 in Studio 7, asked 11-1)
  const R = { original_id: 'evO', attendees: [{ email: S7 }], location: '', new_start: '2027-10-16T11:00:00+08:00', new_end: '2027-10-16T13:00:00+08:00', title: 'ORANGE / Jem Lim / HL' };
  const ev = (id, s, e) => ({ id, summary: id, start: { dateTime: '2027-10-16T' + s + ':00+08:00' }, end: { dateTime: '2027-10-16T' + e + ':00+08:00' }, attendees: [{ email: S7 }] });
  const cnw = await j1(mv, 'Check New Window', [{ json: { items: [ev('evO', '12:00', '14:00'), ev('GOLDFISH', '10:00', '12:00')] } }], { 'Resolve Booking': [{ json: R }] });
  ok(cnw.reason === 'ROOM_OCCUPIED' && JSON.stringify(cnw.free_gaps) === JSON.stringify([{ start: '2027-10-16T08:00:00+08:00', end: '2027-10-16T10:00:00+08:00' }, { start: '2027-10-16T12:00:00+08:00', end: '2027-10-16T22:00:00+08:00' }]),
     'Move v31: every free stretch that day (8-10 AM, 12 PM-10 PM; the booking itself not blocking) - ' + JSON.stringify(cnw.free_gaps));
  const rj = await j1(mv, 'Return Rejection', [{ json: Object.assign({}, cnw, { offer: false }) }], {});
  ok(rj.free_gaps.length === 2 && rj.same_day_slots, 'Move v31: passed back with the nearest slots');
  const cnw2 = await j1(mv, 'Check New Window', [{ json: { items: [ev('evO', '12:00', '14:00'), ev('A', '08:00', '12:00'), ev('B', '13:00', '22:00')] } }], { 'Resolve Booking': [{ json: R }] });
  ok(JSON.stringify(cnw2.free_gaps) === '[]', 'Move v31: no stretch long enough -> none');

  // ---- Move v31: a new title and details on the replacement; ownership read from the booking as it is
  const DESC = 'Engineer: Howard Luistro | Arranger: Peter Legaste | Booked by: Howard Luistro | ref: U1 | team: U1 U4 | Notes: bring cans | Type: Advertising | Dept: Music';
  const day = { items: [{ id: 'evO', summary: 'ORANGE / Jem Lim / HL x PL', start: { dateTime: '2027-10-16T12:00:00+08:00' }, end: { dateTime: '2027-10-16T14:00:00+08:00' }, description: DESC, attendees: [{ email: S7 }] }] };
  const resolve = async (req) => j1(mv, 'Resolve Booking', [{ json: day }], { 'When Executed by Another Workflow': [{ json: Object.assign({ event_id: 'evO', booking_date: '2027-10-16', title: 'ORANGE / Jem Lim / HL x PL',
    new_start_iso: '2027-10-16T12:00:00+08:00', new_end_iso: '2027-10-16T14:00:00+08:00', confirmed: true, requester: 'U1', authority: 'Standard', department: 'Music' }, req) }] });
  let rb = await resolve({ new_summary: 'ORANGE / Jem Lim / DR', new_details: JSON.stringify({ Engineer: 'Daryl Reyes', Arranger: '', team: 'U2' }) });
  ok(rb.verdict === 'CLEAR' && rb.title === 'ORANGE / Jem Lim / DR' && rb.description === 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | Notes: bring cans | Type: Advertising | Dept: Music | team: U2',
     'Move v31: the replacement gets the new title, engineer and team; the booker, notes, type and department stay - ' + rb.description);
  rb = await resolve({});
  ok(rb.title === 'ORANGE / Jem Lim / HL x PL' && rb.description === DESC, 'Move v31: no new details -> as before');
  rb = await resolve({ requester: 'U9', new_summary: 'HIJACK / X / ZZ' });
  ok(rb.reason === 'NOT_YOURS', 'Move v31: someone not on the booking still cannot change it');
  rb = await resolve({ requester: 'U4' });
  ok(rb.verdict === 'CLEAR' && rb.notify === true && rb.team.join() === 'U1,U4', 'Move v31: the arranger may change it; the booker and the rest of the team are told');

  // ---- Cancel v28: everyone on it told
  const co = await j1(cx, 'Check Ownership', [{ json: day }], { 'When Executed by Another Workflow': [{ json: { event_id: 'evO', booking_date: '2027-10-16', title: 'ORANGE / Jem Lim / HL x PL', confirmed: true, requester: 'U1', authority: 'Standard' } }], 'Find By Title': [{ json: { items: [] } }] });
  ok(co.verdict === 'CLEAR' && co.notify === true && co.team.join() === 'U1,U4', 'Cancel v28: the booker cancels -> the arranger (team) is told');
  const recips = await run(cx, 'Build Recipients', [], { 'Check Ownership': [{ json: co }], 'When Executed by Another Workflow': [{ json: { requester: 'U1', requester_name: 'Howard Luistro', booking_date: '2027-10-16' } }], 'Lookup Engineer': [{ json: {} }] });
  ok(recips.length === 1 && recips[0].json.to === 'U08V3CKDGJF' && /\[DEV\] would notify a team member \(U4\)/.test(recips[0].json.text) && /a session you are on, was cancelled by Howard Luistro/.test(recips[0].json.text),
     'Cancel v28: only the arranger, redirected during QA - ' + JSON.stringify(recips[0].json).slice(0, 140));

  // ---- Slack Interactions v18
  const rooms = [{ id: 'r7', fields: { 'Room Name': 'Studio 7' } }, { id: 'r8', fields: { 'Room Name': 'Studio 8' } }, { id: 'rl', fields: { 'Room Name': 'Likha', 'Room Type': ['Conference Room'] } }, { id: 'rs', fields: { 'Room Name': 'Salin', 'Room Type': ['Conference Room'] } }];
  const bookers = [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer' } }, { fields: { Name: 'Daryl Reyes', Initials: 'DR', 'Slack User ID': 'U2', Info: 'Music Engineer' } },
    { fields: { Name: 'Peter Legaste', Initials: 'PL', 'Slack User ID': 'U4', Info: 'Music Arranger' } }, { fields: { Name: 'Mike Villegas', Initials: 'MV', 'Slack User ID': 'U5', Info: 'Head of Music, Arranger, Goes by Mike.' } },
    { fields: { Name: 'Tara Lim', Initials: 'TL', 'Slack User ID': 'U026N6E1R', Info: 'Post Engineer' } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes: [], bookers }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];
  const B = { id: 'evO', d: '2027-10-16', s: '12:00', e: '14:00', r: 'Studio 7', t: 'ORANGE / Jem Lim / HL x PL' };
  const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');

  // the form: a details checkbox, and its fields filled in from the booking
  const bc = await j1(si, 'Build Change', [], { 'Check Signature': chk, 'Read Cache 6': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(B) }], container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  const dt = bc.view.blocks.find(b => b.block_id === 'details_toggle');
  if (V24) ok(!dt && bc.view.blocks.some(b => b.block_id === 'det_project'), 'v24: the details shown at once - no box');
  else ok(dt && dt.elements[0].options[0].text.text === 'Change other session details' && !bc.view.blocks.some(b => /^det_/.test(b.block_id || '')) && !bc.view.blocks.some(b => b.type === 'context' && /checked before/.test(JSON.stringify(b))),
     'v18: "Change other session details" box, fields hidden; no bottom note');
  const route = async (payload) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'details_toggle' }] }) === 8 && nx('Ack Note') === 'Read Cache 9' && (nx('Read Cache 9') === 'Note Toggle' || (nx('Read Cache 9') === 'Loc Projects 9' && nx('Loc Projects 9') === 'Note Toggle')), 'v18: the box goes to route 8, which reads Bookers');
  const tog = await j1(si, 'Note Toggle', [], { 'Read Cache 9': cache, 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'details_toggle', selected_options: [{ value: 'det' }] }],
    view: { id: 'V5', callback_id: 'change_booking', title: bc.view.title, close: bc.view.close, submit: bc.view.submit, private_metadata: bc.view.private_metadata, blocks: bc.view.blocks, state: { values: {} } } } } }] });
  const T = id => (V24 ? bc : tog).view.blocks.find(b => b.block_id === id);   // v24: already on the form
  ok(T('det_project').element.initial_value === 'ORANGE' && T('det_client').element.initial_value === 'Jem Lim' && T('det_engineer').element.initial_option.value === 'U1' && T('det_arranger').element.initial_option.value === 'U4',
     'v18: ticked -> Project, Client, Engineer, Arranger filled in from the title and Bookers');
  ok(T('det_arranger').element.options.map(o => o.text.text).join() === 'No arranger,Mike Villegas,Peter Legaste', 'v18: arrangers include "Head of Music, Arranger" (Mike Villegas)');

  // reading the change
  const meta = JSON.parse(bc.view.private_metadata);
  const sub = (extra) => ({ type: 'view_submission', view: { id: 'V5', private_metadata: JSON.stringify(Object.assign({}, meta, extra && extra.meta)), state: { values: Object.assign({
    date: { date_pick: { selected_date: '2027-10-16' } }, start: { start_pick: { selected_option: { value: '12:00' } } }, end: { end_pick: { selected_option: { value: '14:00' } } }, room: { room_pick: { selected_option: { value: 'Studio 7' } } } }, extra && extra.v) } } });
  const det = (p, c, en, ar) => ({ det_project: { det_project_in: { value: p } }, det_client: { det_client_in: { value: c } }, det_engineer: { det_engineer_pick: { selected_option: en ? { value: en } : null } }, det_arranger: { det_arranger_pick: { selected_option: ar ? { value: ar } : null } } });
  const readC = async (pl) => j1(si, 'Read Change', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: pl } }], 'Read Cache 10': cache });
  let rc = await readC(sub({ v: det('ORANGE', 'Jem Lim', 'U1', 'U4') }));
  ok(!rc.valid && /Nothing changed - change the date, time, room or a detail/.test(rc.answer.errors.date), 'v18: details open but unchanged -> "Nothing changed"');
  rc = await readC(sub({ v: det('ORANGE', 'Jem Lim', 'U2', 'none') }));
  ok(rc.valid && rc.newTitle === 'ORANGE / Jem Lim / DR' && JSON.stringify(rc.newDetails) === '{"Engineer":"Daryl Reyes","Arranger":"","team":"U2"}' && rc.oldTeam.join() === 'U1,U4' && !rc.clientTyped,
     'v18: a new engineer, no arranger -> the new title, Engineer / Arranger / team');
  rc = await readC(sub({ v: det('', 'Jem Lim', 'U1', 'U4') }));
  ok(!rc.valid && rc.answer.errors.det_project, 'v18: no project -> asked');
  rc = await readC(sub({ v: det('apple', 'jem lim', 'U1', 'U4') }));
  ok(rc.valid && ['APPLE / jem lim / HL x PL', 'APPLE / Jem Lim / HL x PL'].indexOf(rc.newTitle) !== -1 && !rc.newDetails && !rc.clientTyped, 'v18: a new project (caps); the same client in other case is not a new client');
  // To Move: the client check
  const toMove = async (r, names) => j1(si, 'To Move', [], { 'Read Change': [{ json: r }], 'Read Cache 7': cache, 'Client Names': (names || ['Jem Lim', 'Sasa Abella', 'Harold Orozco']).map(n => ({ json: { fields: { Name: n } } })) });
  rc = await readC(sub({ v: det('ORANGE', 'sasa abela', 'U1', 'U4') }));
  let tm = await toMove(rc);
  ok(tm.go === false && /"sasa abela" isn’t in the client list\. Did you mean \*Sasa Abella\*\?/i.test(tm.view.blocks.find(b => b.block_id === 'problem').text.text)
     && /^sasa abela$/i.test(tm.view.blocks.find(b => b.block_id === 'det_client').element.initial_value) && /^sasa abela$/i.test(JSON.parse(tm.view.private_metadata).askedClient), 'v18: a near-miss client -> "Did you mean Sasa Abella?" on the form, entries kept');
  rc = await readC(sub({ v: det('ORANGE', 'sasa abela', 'U1', 'U4'), meta: { askedClient: si.nodes.some(n => n.name === 'DM Changed') ? 'Sasa Abela' : 'sasa abela' } }));
  tm = await toMove(rc);
  ok(tm.go && /^ORANGE \/ sasa abela \/ HL x PL$/i.test(tm.new_summary), 'v18: pressed again -> kept as a new client');
  rc = await readC(sub({ v: det('ORANGE', 'harold orozco', 'U2', 'U4') }));
  tm = await toMove(rc);
  ok(tm.go && tm.new_summary === 'ORANGE / Harold Orozco / DR x PL' && JSON.parse(tm.new_details).team === 'U2 U4', 'v18: a client on the list -> its own spelling; the new engineer');
  // the form's inputs reach Move v31 and land on the replacement
  rb = await resolve({ new_summary: tm.new_summary, new_details: tm.new_details });
  ok(rb.title === 'ORANGE / Harold Orozco / DR x PL' && /^Engineer: Daryl Reyes \| Arranger: Peter Legaste \| Booked by: Howard Luistro \| ref: U1/.test(rb.description) && /team: U2 U4$/.test(rb.description),
     'v18 -> Move v31: the replacement gets the new title and team - ' + rb.description);
  // a meeting moved to another room takes that room in its title
  const BM = { id: 'evM', d: '2027-10-16', s: '15:00', e: '16:00', r: 'Likha', t: 'LIKHA - Q4 planning' };
  const subM = { type: 'view_submission', view: { id: 'V6', private_metadata: JSON.stringify({ b: BM }), state: { values: {
    date: { date_pick: { selected_date: '2027-10-16' } }, start: { start_pick: { selected_option: { value: '15:00' } } }, end: { end_pick: { selected_option: { value: '16:00' } } }, room: { room_pick: { selected_option: { value: 'Salin' } } } } } } };
  rc = await readC(subM);
  ok(rc.valid && rc.newTitle === 'SALIN - Q4 planning', 'v18: a meeting moved to Salin -> "SALIN - Q4 planning"');
  // free stretches on the form
  rc = await readC(sub({ v: {} }));
  const am = await j1(si, 'After Move', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', free_gaps: cnw.free_gaps, same_day_slots: [{ start: '2027-10-16T12:00:00+08:00', end: '2027-10-16T14:00:00+08:00' }] } }],
    { 'Read Change': [{ json: Object.assign({}, sub && rc, { n: { d: '2027-10-16', s: '11:00', e: '13:00', r: 'Studio 7' } }) }], 'Read Cache 7': cache, 'To Move': [{ json: { new_summary: '' } }] });
  ok(am.view.blocks.find(b => b.block_id === 'problem').text.text === '⚠️ Studio 7 is taken then. Free that day: 8:00 AM – 10:00 AM, 12:00 PM – 10:00 PM.', 'v18: a taken room -> every free stretch (live: two slots)');
  // notices
  const rcN = await readC(sub({ v: det('ORANGE', 'Jem Lim', 'U2', 'U5') }));
  const amOk = { ok: true, card: '✅ *Changed.*\n\n*ORANGE / Jem Lim / DR x MV*\n*Date:* Saturday, October 16, 2027\n*Time:* 12:00 PM – 2:00 PM\n*Room:* Studio 7' };
  const cn = await run(si, 'Change Notices', [], { 'Read Change': [{ json: rcN }], 'After Move': [{ json: amOk }], 'Read Cache 7': cache });
  ok(cn.length === 2 && cn.every(x => x.json.channel === 'U08V3CKDGJF') && /\[DEV\] would notify Daryl Reyes \(U2\):\n👋 \*Howard Luistro added you as the engineer\.\*\n\n\*ORANGE/.test(cn[0].json.text)
     && /added you as the arranger/.test(cn[1].json.text) && cn[0].json.blocks[1].elements.map(e => e.action_id).join() === 'my_bookings,open_book', 'v18: a change adds an engineer and an arranger -> both told (to Howard in QA)');
  const R2 = { s: { requester: 'U1' }, engineerId: 'U026N6E1R', arrangerId: '' };
  const bn = await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: R2 }], 'After Book': [{ json: { text: '✅ *Booked.*\n\n*KIWI / TL*\n*Date:* x' } }], 'Read Cache 3': cache });
  ok(bn.length === 1 && bn[0].json.channel === 'U026N6E1R' && bn[0].json.text === '👋 *Howard Luistro booked you as the engineer.*\n\n*KIWI / TL*\n*Date:* x', 'v18: booked with Tara as engineer -> Tara told (on ALLOW: her own DM)');
  ok((await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: { s: { requester: 'U1' }, engineerId: 'U1', arrangerId: '' } }], 'After Book': [{ json: { text: 'x' } }], 'Read Cache 3': cache })).length === 0, 'v18: booked as your own engineer -> nobody told');
  const sn = await run(si, 'Series Notices', [], { 'Read Series Confirm': [{ json: { user: 'U1' } }], 'To Book Series': [{ json: { go: true, description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2 U4' } }],
    'After Book Series': [{ json: { text: '✅ *Booked 3 dates.*\n\n*SER / DR x PL*\n*Dates:*\n- Tue, Oct 19' } }], 'Read Cache 8': cache });
  ok(sn.length === 2 && /booked you as the engineer for 3 dates/.test(sn[0].json.text) && /booked you as the arranger for 3 dates/.test(sn[1].json.text) && /\n\n\*SER \/ DR x PL\*/.test(sn[0].json.text), 'v18: a series -> its engineer and arranger told once, with the dates');
  // wiring
  ok(nx('Read Cache 10') === 'Read Change' && C.Route.main[11][0].node === 'Read Cache 10' && nx('Change OK?') === 'Client Names' && nx('Read Cache 7') === 'To Move' && nx('To Move') === 'Go Move?'
     && nx('Go Move?') === 'Move | Ask Again' && nx('Ask Again') === 'Restore Asked' && ['Get Message+Change Notices | Restore Message', 'Get Message+Change Notices+DM Changed | Restore Message'].indexOf(nx('Moved?')) !== -1, 'v18 wiring: route 11');
  ok(nx('DM Booked') === 'Booked Notices' && nx('Booked Notices') === 'Send Booked Notices' && nx('DM Series') === 'Series Notices', 'v18 wiring: notices after booking');
  const cnn = si.nodes.find(n => n.name === 'Client Names');
  ok(cnn.credentials.airtableTokenApi.id === 'S0hmu58Rb55jqAv0' && cnn.parameters.table.value === 'tblJCgcluYhli6kHH', 'v18: Client Names reads Clients with Book Session\'s Airtable credential');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
