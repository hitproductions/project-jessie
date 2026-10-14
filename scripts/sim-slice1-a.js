#!/usr/bin/env node
// Slice 1 step A offline: main v262's Menu Check on different messages, and Slack Interactions v3's booking-form steps
// (routes, step 1 from the cache, step 1 checks, Room Availability input, step 2 for studio / meeting / booth / errors,
// step 2 checks and the calendar title). Usage: node scripts/sim-slice1-a.js [main v262] [slack interactions v3]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v262.json', 'utf8'));
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v3.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  const fn = new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);');
  return fn.call({ helpers: {} }, $, $input);
}

(async () => {
  // ---- main v262: Menu Check
  const menuFor = async (text) => (await run(main, 'Menu Check', [], {
    'Slack Trigger': [{ json: { text, channel: 'D1' } }], 'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }] }))[0].json;
  for (const t of ['hi', 'Hi Jessie!', 'menu', 'help', 'good morning po', 'hello there', 'heyyy', 'Hi\n*Sent using* <@U0AVDBNH1K4|Claude>', ':wave:'])
    ok((await menuFor(t)).menu === true, 'menu for ' + JSON.stringify(t));
  for (const t of ['hi, book studio 7 tomorrow 2-4pm', 'yes', 'ok', 'no', 'what do i have this week?', 'cancel my friday booking', ''])
    ok((await menuFor(t)).menu === false, 'no menu for ' + JSON.stringify(t));
  const mm = await menuFor('hi');
  ok(/Hi Howard!/.test(mm.blocks[0].text.text) && mm.blocks[1].elements.map(e => e.action_id).join() === 'open_book,my_bookings', 'menu text and buttons');
  const C = main.connections;
  ok(C['Duplicate?'].main[1][0].node === 'Menu Check' && C['Menu?'].main[1][0].node === 'All Rooms' && C['Menu?'].main[0][0].node === 'Send Menu',
     'wiring: not-duplicate -> Menu Check -> Menu? (yes: Send Menu, no: All Rooms)');

  // ---- v3: routes
  const check = async (payload) => (await run(si, 'Check Signature', [{ json: { computed: 'abc' } }], {
    'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload, rawSource: 'binary', rawLength: 1, payloadSource: 'parsed-body' } }] }))[0].json;
  ok((await check({ type: 'block_actions', user: { id: 'U1' }, actions: [{ action_id: 'open_book' }] })).route === 4, 'Book a room -> 4');
  ok((await check({ type: 'view_submission', view: { callback_id: 'book_step1' } })).route === 5, 'step 1 submit -> 5');
  ok((await check({ type: 'view_submission', view: { callback_id: 'book_step2' } })).route === 6, 'step 2 submit -> 6');
  ok((await check({ type: 'block_actions', actions: [{ action_id: 'my_bookings' }] })).route === 7, 'My bookings -> 7');
  ok((await check({ type: 'block_actions', actions: [{ action_id: 'room_radio' }] })).route === 3, 'a radio change -> just acknowledged');

  // fake cache
  const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
  const rooms = [R('r7', 'Studio 7'), R('r8', 'Studio 8'), R('rf', 'Studio F'), R('rc', 'Studio C'), R('r4', 'Studio 4'),
    R('rl', 'Likha', { 'Room Type': ['Conference Room'] }), R('m4', 'M4', { 'Room Type': ['M Booth'] }), R('ra', 'Studio A', { 'Vocal Booth': true })];
  const ST = (t, pri, last) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': last || [] } });
  const sessionTypes = [ST('VO Recording', ['r7', 'r8', 'rf', 'rc'], ['r4']), ST('Meeting', ['rl']), ST('Event', ['rl']), ST('Music Mixing', ['rf'], ['rc'])];
  const bookers = [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1' } },
                   { id: 'b2', fields: { Name: 'Daryl Reyes', Initials: 'DR', 'Slack User ID': 'U2\n' } }];
  const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };

  // step 1
  const s1 = (await run(si, 'Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow }))[0].json;
  const grp = s1.view.blocks[4].element.option_groups;
  ok(s1.cacheOk && grp[0].options.map(o => o.value).join() === 'Music Mixing,VO Recording', 'step 1: sessions from the cache, sorted');
  ok(grp[1].options.map(o => o.value).join() === 'Meeting,Event,__booth', 'step 1: not-a-session group');
  ok(s1.view.blocks[1].element.initial_date.startsWith(String(new Date(Date.now() + 8 * 3600e3).getUTCFullYear() + 1)), 'step 1: date a year ahead');

  const sub1 = (vals) => ({ type: 'view_submission', view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: vals } } });
  const vals = (d, a, b, p) => ({ date: { date_pick: { selected_date: d } }, start: { start_pick: { selected_time: a } }, end: { end_pick: { selected_time: b } },
    purpose: { purpose_pick: { selected_option: p ? { value: p } : null } } });
  const read1 = async (payload) => (await run(si, 'Read Step 1', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload } }] }))[0].json;
  let r1 = await read1(sub1(vals('2027-10-15', '16:00', '14:00', 'VO Recording')));
  ok(!r1.valid && r1.answer.response_action === 'errors' && /after the start/.test(r1.answer.errors.end), 'step 1: end before start -> error on End');
  r1 = await read1(sub1(vals('2027-10-15', '14:00', '16:00', '')));
  ok(!r1.valid && r1.answer.errors.purpose, "step 1: what it's for missing -> error");
  r1 = await read1(sub1(vals('2027-10-15', '14:00', '16:00', 'VO Recording')));
  ok(r1.valid && r1.answer.response_action === 'push' && r1.answer.view.external_id === r1.s.ext && r1.s.kind === 'studio', 'step 1 ok -> push "finding rooms"');

  const toRA = (await run(si, 'To Room Availability', [], { 'Read Step 1': [{ json: r1 }], 'Read Cache 2': cacheRow }))[0].json;
  const ref = JSON.parse(toRA.reference_data);
  ok(toRA.start_iso === '2027-10-15T14:00:00+08:00' && toRA.end_iso === '2027-10-15T16:00:00+08:00' && toRA.session_type === 'VO Recording', 'RA window and type');
  ok(ref.rooms.find(r => r.name === 'Likha').common && ref.rooms.find(r => r.name === 'Studio A').booth && ref.types.find(t => t.type === 'VO Recording').priority.length === 4, 'RA reference data like Room Table');

  const step2 = async (r1j, ra) => (await run(si, 'Build Step 2', [{ json: ra }], { 'Read Step 1': [{ json: r1j }], 'Read Cache 2': cacheRow }))[0].json;
  let s2 = await step2(r1, { status: 'OK', free_priority: ['Studio 8', 'Studio F'], free_last_resort: ['Studio 4'] });
  const radio = s2.view.blocks.find(b => b.block_id === 'room').element;
  ok(radio.options.map(o => o.value).join() === 'Studio 8,Studio F' && /Recommended/.test(radio.options[0].description.text), 'step 2: usual free rooms, top recommended');
  ok(JSON.stringify(s2.view).indexOf('Not free then: Studio 7, Studio C') !== -1, 'step 2: names the usual rooms not free');
  ok(['project', 'client', 'engineer', 'notes'].every(b => s2.view.blocks.some(x => x.block_id === b)) && s2.view.submit && s2.external_id === r1.s.ext, 'step 2: studio fields, Book, same external_id');
  ok(s2.view.blocks.find(b => b.block_id === 'engineer').element.initial_user === 'U1', 'step 2: engineer set to the requester');
  s2 = await step2(r1, { status: 'OK', free_priority: [], free_last_resort: ['Studio 4'] });
  ok(/not a usual room/.test(JSON.stringify(s2.view)), 'step 2: last resort only when no usual room is free');
  s2 = await step2(r1, { status: 'OK', free_priority: [], free_last_resort: [] });
  ok(!s2.view.submit && /Nothing that does VO Recording is free/.test(JSON.stringify(s2.view)), 'step 2: nothing free -> no Book, go Back');
  s2 = await step2(r1, { status: 'CALENDAR_ERROR' });
  ok(!s2.view.submit && /could not be checked/.test(JSON.stringify(s2.view)), 'step 2: calendar error -> no Book');
  const rMeet = await read1(sub1(vals('2027-10-15', '15:00', '16:00', 'Meeting')));
  s2 = await step2(rMeet, { status: 'OK', free_priority: ['Likha'], free_last_resort: [] });
  ok(rMeet.s.kind === 'meeting' && s2.view.blocks.some(b => b.block_id === 'title') && !s2.view.blocks.some(b => b.block_id === 'engineer'), 'meeting: title, no engineer');
  const rBooth = await read1(sub1(vals('2027-10-15', '15:00', '16:00', '__booth')));
  s2 = await step2(rBooth, { status: 'OK', free_rooms: ['Likha', 'M4', 'Studio 7'] });
  ok(s2.view.blocks.find(b => b.block_id === 'room').element.options.map(o => o.value).join() === 'M4', 'booth time: only M booths');
  const rMus = await read1(sub1(vals('2027-10-15', '13:00', '17:00', 'Music Mixing')));
  s2 = await step2(rMus, { status: 'OK', free_priority: ['Studio F'], free_last_resort: [] });
  ok(s2.view.blocks.some(b => b.block_id === 'arranger'), 'music: arranger field');

  // step 2 submit (dry run)
  const meta = Object.assign({}, r1.s, { when: 'Friday, Oct 15 · 2:00 PM–4:00 PM', label: 'VO Recording' });
  const sub2 = (v, m) => ({ type: 'view_submission', view: { private_metadata: JSON.stringify(m || meta), state: { values: v } } });
  const read2 = async (payload) => (await run(si, 'Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload } }], 'Read Cache 3': cacheRow }))[0].json;
  const V = (o) => { const v = {}; for (const [b, [a, val]] of Object.entries(o)) v[b] = { [a]: val }; return v; };
  let r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'Studio 8' } }], project: ['project_in', { value: 'project qaw1' }],
    client: ['client_in', { value: 'Sasa Abella' }], engineer: ['engineer_pick', { selected_user: 'U1' }] })));
  ok(r2.valid && r2.calTitle === 'QAW1 / Sasa Abella / HL' && r2.answer.response_action === 'update' && r2.answer.view.clear_on_close, 'dry run: title by code, "project" dropped, closes the stack');
  r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'Studio 8' } }], engineer: ['engineer_pick', { selected_user: 'U1' }] })));
  ok(!r2.valid && r2.answer.errors.project, 'missing project -> error on Project');
  r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'Studio 8' } }], project: ['project_in', { value: 'X' }], engineer: ['engineer_pick', { selected_user: 'U9' }] })));
  ok(!r2.valid && /Bookers/.test(r2.answer.errors.engineer), 'engineer not in Bookers -> error');
  r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'Studio F' } }], project: ['project_in', { value: 'jingle' }],
    engineer: ['engineer_pick', { selected_user: 'U2' }], arranger: ['arranger_pick', { selected_user: 'U1' }] }), Object.assign({}, meta, { purpose: 'Music Mixing' })));
  ok(r2.calTitle === 'JINGLE / DR x HL', 'no client: PROJECT / engineer x arranger');
  r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'Likha' } }], title: ['title_in', { value: 'Q4 planning' }] }), Object.assign({}, meta, { kind: 'meeting' })));
  ok(r2.valid && r2.calTitle === 'LIKHA - Q4 planning', 'meeting title');
  r2 = await read2(sub2(V({ room: ['room_radio', { selected_option: { value: 'M4' } }] }), Object.assign({}, meta, { kind: 'booth' })));
  ok(r2.calTitle === 'M4 - Howard', 'booth title: room - first name');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
