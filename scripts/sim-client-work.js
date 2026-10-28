#!/usr/bin/env node
// The 28 Oct round, through the real nodes: PENDING 135 (a new client is client work - Book Session v124 is in test-nodes; here the
// Change path: Slack Interactions v51 To Move -> Move v41 Resolve Booking), PENDING 124 (a booking with no ref: is asked for by its
// "Booked by" name - Book Session v124 Decide Preempt, Room Availability v24 + Slack Interactions v51 "Booked – ask to use"),
// PENDING 136 (Atmos Mixing: its own form from step 1, with a Department dropdown).
// Usage: node scripts/sim-client-work.js [book-session v124] [move v41] [room-availability v24] [slack-interactions v51]
const fs = require('fs');
const A = process.argv.slice(2);
const load = (i, f) => JSON.parse(fs.readFileSync((A[i] && A[i].length) ? A[i] : f, 'utf8'));
const BS = load(0, 'workflows/book-session-v124.json'), MV = load(1, 'workflows/move-booking-v41.json'), RA = load(2, 'workflows/room-availability-v24.json'), SI = load(3, 'workflows/slack-interactions-v51.json');
if (!/PENDING 124/.test(JSON.stringify(SI.nodes))) { console.log('0 ok, 0 failed (an older build: the 28 Oct round not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const run = async (wf, name, input, outs) => {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(wf, name).parameters.jsCode + '\n}).call(this);').call({ helpers: {} }, $, $input); };
const j1 = async (...a) => (await run(...a))[0].json;
const B = (name, slack, info, auth, dept) => ({ id: 'b' + slack, fields: { Name: name, 'Slack User ID': slack, Info: info, Authority: auth ? [auth] : [], Department: [dept || 'Music'], Initials: 'X' } });
const bookers = [B('Howard Luistro', 'U08V3CKDGJF', 'Post Engineer', 'HAIST Dev', 'Audio Post'), B('Celeste Cruz', 'U7', 'Producer', 'Dept Head', 'Audio Post'),
  B('Daryl Reyes', 'U2', 'Music Engineer'), B('Angelo Villegas', 'U3', 'Music Arranger, Goes by Anj, Gelo.\n'), B('Daryl Santos', 'U5', 'Loc Engineer, Goes by Gelo.', '', 'Localization'),
  B('Kristine Trocino', 'U092HJLQT9B', 'BD Associate, Goes by Kristine, Tin.', 'Client Booking', 'Business Development')];
const ST = (t, pri, rank, roles) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Preemption Rank': rank, 'Engineer Role Required': roles || ['Music Engineer'] } });
const sessionTypes = [ST('Celebrity Recording', ['rf', 'rc'], 3), ST('VO Recording', ['r7', 'rf'], 1, ['Post Engineer']), ST('Atmos Mixing', ['rc'], 2, ['Loc Engineer', 'Post Engineer', 'Music Engineer'])];
const rooms = [['rf', 'Studio F'], ['rc', 'Studio C'], ['r7', 'Studio 7']].map(([id, n]) => ({ id, fields: { 'Room Name': n, 'Room Type': ['Recording Control Room'] } }));
rooms.push(...['M1', 'M4'].map(n => ({ id: 'm' + n, fields: { 'Room Name': n, 'Room Type': ['M Booth'] } })));
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];

(async () => {
  console.log('Book Session v124 - Decide Preempt: a booking with no ref: (PENDING 124)');
  const REQ = o => Object.assign({ session_type: 'Celebrity Recording', rooms: 'Studio F', description: 'Booked by: Celeste Cruz | ref: U7', authority: 'Dept Head', start_iso: 'a', end_iso: 'b',
    request_ok: true, reference_data: JSON.stringify({ preemptionRanks: { 'Celebrity Recording': 3, 'VO Recording': 1 } }) }, o || {});
  const dp = async (desc, o) => j1(BS, 'Decide Preempt', [{ json: { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ id: 'e1', summary: 'SONG / DR', room: 'Studio F', description: desc }] } }],
    { 'When Executed by Another Workflow': [{ json: REQ(o) }], 'All Bookers': bookers.map(b => ({ json: b })) });
  let d = await dp('Engineer: Daryl Reyes | Booked by: Daryl Reyes | Type: Advertising\nSType: VO Recording');
  ok(d.offer && d.open.approver === 'U2', 'no ref:, "Booked by: Daryl Reyes" -> asked of Daryl (U2)', d.open || d);
  d = await dp('Booked by: Daryl Reyes (for Angelo Villegas)\nSType: VO Recording');
  ok(d.offer && d.open.approver === 'U2', '"Booked by: Daryl Reyes (for …)" -> Daryl, not who it is for');
  d = await dp('Booked by: Anj\nSType: VO Recording');
  ok(d.offer && d.open.approver === 'U3', 'a "Goes by" alias one person has (Anj) -> Angelo (U3)', d.open || d);
  d = await dp('Booked by: Gelo\nSType: VO Recording');
  ok(!d.offer && d.preemptReason === 'NO_INCUMBENT_BOOKER', 'an alias two people have (Gelo) -> nobody (never a guess)', d);
  d = await dp('Booked by: Someone Else\nSType: VO Recording');
  ok(!d.offer && d.preemptReason === 'NO_INCUMBENT_BOOKER', 'a name not in Bookers -> nobody, as before');
  d = await dp('Booked by: Daryl Reyes | ref: U3\nSType: VO Recording');
  ok(d.offer && d.open.approver === 'U3', 'ref: is still read first (ref: U3 wins over the name)');
  d = await dp('Booked by: Celeste Cruz\nSType: VO Recording');
  ok(!d.offer && d.preemptReason === 'SELF_BOOKING', 'your own booking found by name -> "You already have …", as with ref:');
  const mb = await j1(BS, 'Decide Preempt', [{ json: { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ id: 'h1', summary: 'M4 - Anj', room: 'M4', recurring: true, description: 'Booked by: Angelo Villegas' }] } }],
    { 'When Executed by Another Workflow': [{ json: REQ({ session_type: '', rooms: 'M4', summary: 'M4 - Celeste' }) }], 'All Bookers': bookers.map(b => ({ json: b })) });
  ok(mb.offer && mb.open.kind === 'MBOOTH' && mb.open.approver === 'U3', 'an M booth standing hold with no ref: -> asked of its holder by name', mb.open || mb);

  console.log('Room Availability v24 - each booking\'s Booked by name');
  const raJs = node(RA, 'Compute Availability').parameters.jsCode;
  const bbx = (raJs.match(/bookedBy: (\(\(d\.split[^\n]*?\.trim\(\)) \};/) || [])[1];
  const bb = new Function('d', 'return ' + bbx + ';');
  ok(!!bbx && bb('Engineer: X | Booked by: Daryl Reyes (for Anj) | Type: Advertising\nSType: VO Recording') === 'Daryl Reyes' && bb('Booked by: Anj') === 'Anj' && bb('ref: U2') === ''
     && bb('Engineer: X | ref: U2\nSType: VO\n\nNotes:\nBooked by: Someone') === '', 'busy_detail events carry bookedBy - the first line only, "(for …)" left off', bbx);

  console.log('Slack Interactions v51 - Booked – ask to use, no ref: (PENDING 124)');
  const s = { date: '2027-10-22', t0: '14:00', t1: '16:00', purpose: 'Celebrity Recording', kind: 'studio', requester: 'U7', channel: 'D1', ext: 'x' };
  const RAres = (detail) => ({ status: 'OK', free_priority: ['Studio 7'], free_last_resort: [], busy: detail.map(x => x.room + ' (x)'), busy_detail: detail });
  const ev = o => Object.assign({ id: 'e1', title: 'SONG / DR', start: '2027-10-22T14:00:00+08:00', end: '2027-10-22T16:00:00+08:00', stype: 'VO Recording', ref: '', team: [], recurring: false }, o);
  const step2 = async (ss, ra) => (await j1(SI, 'Build Step 2', [{ json: ra }], { 'Read Step 1': [{ json: { s: ss } }], 'Read Cache 2': cache, 'Loc Projects 2': [] })).view;
  let v = await step2(s, RAres([{ room: 'Studio F', events: [ev({ bookedBy: 'Daryl Reyes' })] }]));
  ok(JSON.stringify(v).includes('ask:P|Studio F'), 'no ref:, Booked by Daryl Reyes -> Studio F can be asked for');
  v = await step2(s, RAres([{ room: 'Studio F', events: [ev({ bookedBy: 'Nobody Known' })] }]));
  ok(!JSON.stringify(v).includes('ask:'), 'a name not in Bookers -> not offered, as before');
  v = await step2(s, RAres([{ room: 'Studio F', events: [ev({ bookedBy: 'Celeste Cruz' })] }]));
  ok(!JSON.stringify(v).includes('ask:'), 'your own booking (by name) -> never offered');
  v = await step2(Object.assign({}, s, { purpose: '__booth', kind: 'booth' }), Object.assign(RAres([{ room: 'M4', events: [ev({ title: 'M4 - Anj', recurring: true, bookedBy: 'Angelo Villegas' })] }]), { free_priority: [], free_rooms: ['M1'] }));
  ok(JSON.stringify(v).includes('ask:M|M4'), 'an M booth hold with no ref: -> can be asked of its holder');
  v = await step2(Object.assign({}, s, { purpose: '__booth', kind: 'booth' }), Object.assign(RAres([{ room: 'M4', events: [ev({ title: 'M4 - Anj', recurring: true })] }]), { free_priority: [], free_rooms: ['M1'] }));
  ok(!JSON.stringify(v).includes('ask:M'), 'the same hold with no ref: and no Booked by -> not offered (as before)');
  ok(/PENDING 124/.test(node(SI, 'Note Toggle').parameters.jsCode), 'Note Toggle (the redrawn step 2) resolves names the same way');

  console.log('Slack Interactions v51 - Atmos Mixing (PENDING 136)');
  const k1 = node(SI, 'Read Step 1').parameters.jsCode.match(/const kind = purpose === '__booth'[^;]*;/g) || [];
  const kindOf = (expr, purpose) => new Function('purpose', 'return (' + expr.replace(/^const kind = /, '').replace(/;$/, '') + ');')(purpose);
  ok(k1.length === 2 && k1.every(e => kindOf(e, 'Atmos Mixing') === 'atmos' && kindOf(e, 'Localization Atmos Mixing') === 'atmos' && kindOf(e, 'Localization Dubbing') === 'loc'
     && kindOf(e, 'QC') === 'loc' && kindOf(e, 'VO Recording') === 'studio'), 'Read Step 1 (both paths): Atmos Mixing (and the old name) -> the Atmos form; Localization types as before');
  const as = { date: '2027-10-22', t0: '14:00', t1: '16:00', purpose: 'Atmos Mixing', kind: 'atmos', requester: 'U5', channel: 'D1', ext: 'x' };
  v = await step2(as, { status: 'OK', free_priority: ['Studio C'], free_last_resort: [], busy: [] });
  const dep = v.blocks.find(b => b.block_id === 'department');
  ok(dep && !dep.optional && dep.element.options.map(o => o.value).join() === 'Localization,Audio Post,Music' && dep.element.initial_option.value === 'Localization',
     'the Atmos form asks the Department: Localization, Audio Post, Music - set to the booker\'s own (Localization)', dep);
  v = await step2(Object.assign({}, as, { requester: 'U092HJLQT9B' }), { status: 'OK', free_priority: ['Studio C'], free_last_resort: [], busy: [] });
  const dep2 = v.blocks.find(b => b.block_id === 'department');
  ok(dep2 && !dep2.element.initial_option, 'a booker outside the three (Business Development) -> nothing picked, must choose');
  const ids = v.blocks.map(b => b.block_id);
  ok(ids.indexOf('project') !== -1 && ids.indexOf('department') === ids.indexOf('project') + 1 && ids.indexOf('client') === -1 && ids.indexOf('arranger') === -1, 'Project title or code, then Department, then the engineer - no client or arranger', ids);
  v = await step2(Object.assign({}, s, { requester: 'U2' }), { status: 'OK', free_priority: ['Studio F'], free_last_resort: [], busy: [] });
  ok(!v.blocks.some(b => b.block_id === 'department'), 'other studio types: no Department field, as before');
  const rs2 = async (vals) => j1(SI, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U5', triggerId: 'T', channel: 'D1' } }],
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(Object.assign({}, as, { label: 'Atmos Mixing' })), blocks: [], state: { values: vals } } } } }], 'Read Cache 3': cache });
  const r2 = await rs2({ room: { room_radio: { selected_option: { value: 'Studio C' } } }, project: { project_in: { value: 'Kuba' } }, department: { department_pick: { selected_option: { value: 'Music' } } },
    engineer: { engineer_pick: { selected_option: { value: 'U2' } } } });
  ok(r2.valid && r2.prep.department === 'Music' && r2.calTitle === 'KUBA / X', 'Book: the department picked is the booking\'s (Music), title PROJECT / initials', { v: r2.valid, d: r2.prep && r2.prep.department, t: r2.calTitle, e: r2.answer && r2.answer.errors });

  console.log('PENDING 135 on Change - Slack Interactions v51 To Move -> Move v41');
  const R = (client, asked) => ({ user: 'U092HJLQT9B', viewId: 'V1', b: { id: 'e1', d: '2027-10-09', s: '06:00', e: '12:00', r: 'Studio F', t: 'BACKYARD LIVE / AEG', st: 'Band Recording' },
    n: { d: '2027-10-09', s: '06:00', e: '12:00', r: 'Studio F' }, d: { project: 'BACKYARD LIVE', client, en: 'U2', ar: 'none' }, clientTyped: client, newTitle: 'BACKYARD LIVE / ' + client + ' / AEG',
    meta: { askedClient: asked ? client : '' }, newDetails: null, roomChanged: false, timeChanged: false, valid: true });
  const toMove = async (r, names) => j1(SI, 'To Move', [], { 'Read Change': [{ json: r }], 'Read Cache 7': cache, 'Client Names': names.map(n => ({ json: { fields: { Name: n } } })) });
  let tm = await toMove(R('Sony Music', true), ['Jem Lim']);
  ok(tm.go !== false && JSON.parse(tm.new_details || '{}').ClientWork === true, 'a new client kept (Change pressed again) -> ClientWork sent to Move', { go: tm.go, nd: tm.new_details });
  tm = await toMove(R('Jem Lim', false), ['Jem Lim']);
  ok(!/ClientWork/.test(String(tm.new_details || '')), 'a client Airtable knows -> no ClientWork (its own type stays)');
  const DESC = 'Engineer: Elijah Gan | Booked by: Kristine Trocino | ref: U092HJLQT9B | team: U2 | Type: Internal | Dept: Music\nSType: Band Recording\n\nNotes:\nType: Internal in a note';
  const day = { items: [{ id: 'e1', summary: 'BACKYARD LIVE / AEG', start: { dateTime: '2027-10-09T06:00:00+08:00' }, end: { dateTime: '2027-10-09T12:00:00+08:00' }, description: DESC, attendees: [] }] };
  const resolve = async (nd, desc) => j1(MV, 'Resolve Booking', [{ json: desc ? { items: [Object.assign({}, day.items[0], { description: desc })] } : day }], { 'When Executed by Another Workflow': [{ json: { event_id: 'e1', booking_date: '2027-10-09',
    title: 'BACKYARD LIVE / AEG', new_start_iso: '2027-10-09T06:00:00+08:00', new_end_iso: '2027-10-09T12:00:00+08:00', confirmed: true, requester: 'U092HJLQT9B', authority: 'Client Booking', department: 'Business Development',
    new_summary: 'BACKYARD LIVE / Sony Music / AEG', new_details: JSON.stringify(nd) } }] });
  let rb = await resolve({ ClientWork: true });
  ok(rb.verdict === 'CLEAR' && /\| Type: Advertising \| Dept: Music\nSType: Band Recording\n\nNotes:\nType: Internal in a note$/.test(rb.description), 'Internal + a new client -> Type: Advertising in place (the note untouched)', rb.description);
  rb = await resolve({ ClientWork: true }, DESC.replace('Dept: Music', 'Dept: Localization'));
  ok(/Type: Entertainment \| Dept: Localization/.test(rb.description), 'on a Localization booking -> Entertainment', rb.description);
  rb = await resolve({ ClientWork: true }, DESC.replace('Type: Internal', 'Type: Personal'));
  ok(/Type: Personal/.test(rb.description), 'a Personal booking stays Personal');
  rb = await resolve({ Notes: 'x' });
  ok(/Type: Internal \| Dept: Music/.test(rb.description), 'no new client -> Type unchanged');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + e.stack); process.exit(1); });
