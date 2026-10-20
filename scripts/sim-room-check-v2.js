#!/usr/bin/env node
// Jessie — Room Check v2 + Move Booking v34 (20 Oct): a change's rooms are checked after it goes through; a room that turns the
// new time down is reported (DM with Change / My bookings) and never deleted - the old event is gone already. A new booking as
// in v1 (deleted, DM'd). "Book a room" on a declined Post Processing booking reads "POST PROCESSING - <PROJECT> / <who>".
// Usage: node scripts/sim-room-check-v2.js [room-check v2] [move-booking v34]
const fs = require('fs');
const RC = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/room-check-v2.json', 'utf8'));
const MV = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/move-booking-v34.json', 'utf8'));
if (!RC.nodes.some(n => n.name === 'Delete?')) { console.log('0 ok, 0 failed (Room Check v2 on; this build is older)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const nx = (wf, k) => ((wf.connections[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
const T = 'When Executed by Another Workflow';
const run = async (name, input, outs) => { const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(RC, name).parameters.jsCode + '\n})();')($, $input); };
const expr = (e, outs) => { const body = String(e).replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''); const $ = n => ({ first: () => (outs[n] || [])[0] }); return new Function('$', 'return (' + body + ');')($); };
(async () => {
  ok(node(RC, T).parameters.workflowInputs.values.map(v => v.name).join() === 'event_id,title,rooms,requester,start_iso,end_iso,all_day,session_type,kind', 'Room Check takes kind');
  ok(nx(RC, 'Decide') === 'Delete?' && nx(RC, 'Delete?') === 'Delete Declined | Build DM' && nx(RC, 'Delete Declined') === 'Build DM', 'Decide -> Delete? -> (a new booking) Delete Declined -> Build DM | (a change) Build DM');
  const cond = node(RC, 'Delete?').parameters.conditions.conditions[0].leftValue;
  ok(expr(cond, { [T]: [{ json: { kind: 'move' } }] }) === false && expr(cond, { [T]: [{ json: { kind: '' } }] }) === true && expr(cond, { [T]: [{ json: {} }] }) === true, 'a change is never deleted; a new booking (no kind - Book Session\'s call) is');
  const D = { event_id: 'ev9', declined: ['Studio 7'], title: 'ORANGE / Jem Lim / HL', requester: 'U1' };
  const TI = { event_id: 'ev9', title: 'ORANGE / Jem Lim / HL', rooms: 'Studio 7', requester: 'U1', start_iso: '2027-10-22T15:00:00+08:00', end_iso: '2027-10-22T17:00:00+08:00', all_day: 'false', session_type: 'VO Recording', kind: 'move' };
  let dm = (await run('Build DM', [{ json: { event_id: 'ev9' } }], { [T]: [{ json: TI }], 'Decide': [{ json: D }] }))[0].json;
  const b = dm.blocks[1].elements;
  ok(/^⚠️ \*Studio 7 turned down this change\*.*The booking is on the calendar at the new time, but the room hasn’t accepted it/.test(dm.blocks[0].text.text) && dm.isMove && !dm.removed, 'a change: "turned down this change … still on the calendar at the new time"', dm.blocks[0].text.text);
  const bv = JSON.parse(b[0].value);
  ok(b[0].action_id === 'bk_change' && bv.id === 'ev9' && bv.d === '2027-10-22' && bv.s === '15:00' && bv.r === 'Studio 7' && bv.st === 'VO Recording' && b[1].action_id === 'my_bookings', 'Change opens the booking (id, date, times, room, type) + My bookings', bv);
  const lr = (await run('Declined Row', [{ json: {} }], { [T]: [{ json: TI }], 'Decide': [{ json: D }], 'Build DM': [{ json: dm }] }))[0].json;
  ok(/a change; the booking kept at the new time/.test(lr.Note), 'the Log row says the change was kept', lr.Note);
  dm = (await run('Build DM', [{ json: {} }], { [T]: [{ json: Object.assign({}, TI, { kind: '' }) }], 'Decide': [{ json: D }] }))[0].json;
  ok(/^❌ \*Studio 7 turned this booking down\*.*It was taken off the calendar/.test(dm.blocks[0].text.text) && dm.blocks[1].elements[0].action_id === 'open_book', 'a new booking: as in v1 (taken off, Book a room)');
  const PP = Object.assign({}, TI, { kind: '', title: 'POST PROCESSING - TRAILER / Dilan', rooms: 'Studio E', session_type: 'Post Processing' });
  dm = (await run('Build DM', [{ json: {} }], { [T]: [{ json: PP }], 'Decide': [{ json: Object.assign({}, D, { title: PP.title, declined: ['Studio E'] }) }] }))[0].json;
  const ag = JSON.parse(dm.blocks[1].elements[0].value);
  ok(ag.p === 'Post Processing' && ag.pj === 'TRAILER' && ag.fn === 'Dilan', 'a declined Post Processing booking: Book a room fills the project (TRAILER) and the name (Dilan)', ag);
  dm = (await run('Build DM', [{ json: {} }], { [T]: [{ json: Object.assign({}, PP, { title: 'POST PROCESSING - Dilan' }) }], 'Decide': [{ json: Object.assign({}, D, { title: 'POST PROCESSING - Dilan' }) }] }))[0].json;
  ok(JSON.parse(dm.blocks[1].elements[0].value).fn === 'Dilan' && !JSON.parse(dm.blocks[1].elements[0].value).pj, 'no project -> only the name');
  console.log('Move Booking v34');
  const rcn = node(MV, 'Room Check');
  ok(nx(MV, 'Notify?') === 'Lookup Engineer | Room Check' && nx(MV, 'Send DMs') === 'Room Check' && nx(MV, 'Room Check') === 'Return Moved', 'after the notices (or none) -> Room Check -> Return Moved');
  ok(rcn.parameters.workflowId.value === 'CB3JPU052OfHFIQr' && rcn.parameters.options.waitForSubWorkflow === false && rcn.executeOnce === true && rcn.onError === 'continueRegularOutput', 'Room Check (CB3JPU052OfHFIQr), not waited on, once per change, never fails the change');
  const outs = { 'Resolve Booking': [{ json: { title: 'ORANGE / Jem Lim / HL', location: 'Studio 7', new_start: '2027-10-22T15:00:00+08:00', new_end: '2027-10-22T17:00:00+08:00', description: 'Engineer: Howard | ref: U1 | SType: VO Recording' } }],
    'Create Replacement': [{ json: { id: 'evNEW', summary: 'ORANGE / Jem Lim / HL' } }], [T]: [{ json: { requester: 'U5', new_rooms: 'Studio 7' } }] };
  const got = Object.fromEntries(Object.entries(rcn.parameters.workflowInputs.value).map(([k, e]) => [k, /^=/.test(e) ? expr(e, outs) : e]));
  ok(got.event_id === 'evNEW' && got.rooms === 'Studio 7' && got.requester === 'U5' && got.session_type === 'VO Recording' && got.all_day === 'false' && got.kind === 'move' && got.start_iso === '2027-10-22T15:00:00+08:00',
     'it passes the new event, its room, the person who changed it, the type, kind "move"', got);
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
