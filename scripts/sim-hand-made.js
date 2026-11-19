#!/usr/bin/env node
// The 19 Nov round (PENDING 155 / 156), through the real nodes:
//  155 - a booking made by hand in Google Calendar belongs to whoever made it (the event's creator is one of their Bookers emails):
//        Slack Interactions v81 My bookings and main v293 (Mine Reply, Change Reply) list it; Cancel v35 / Move v44 let its creator
//        cancel / change it (no ref: needed); Move v44's replacement carries "Booked by | ref | Dept".
//  156 - an event with no room on it ("New Event", 24 Nov 9-10 AM) no longer refuses a booking when every room's free/busy was read
//        (Book Session v130); when it does refuse, the form says so in words (Slack Interactions v81).
//   node scripts/sim-hand-made.js [si v81] [main v293] [cancel v35] [move v44] [book-session v130] [book-session v129]
const fs = require('fs');
const L = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const SI = L(process.argv[2], 'workflows/slack-interactions-v81.json'), MAIN = L(process.argv[3], 'workflows/project-jessie-v293.json');
const CX = L(process.argv[4], 'workflows/cancel-booking-v35.json'), MV = L(process.argv[5], 'workflows/move-booking-v44.json');
const BS = L(process.argv[6], 'workflows/book-session-v130.json'), BS0 = L(process.argv[7], 'workflows/book-session-v129.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const run = (w, name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(w, name).parameters.jsCode + '\n})();')(
  n => { if (!(n in outs)) throw new Error('not run: ' + n); return wrap(outs[n]); }, wrap(input));
const FX = require('./sim-fixture-rooms.js');
const LETTY = { Name: 'Coord Person', Initials: 'CP', Email: 'coord@example.com', 'Alt email': 'coord.alt@example.com', 'Slack User ID': 'UCOORD01', Department: ['Music'], Authority: ['Standard', 'Client Booking'] };
const OTHER = { Name: 'Other Person', Initials: 'OP', Email: 'other@example.com', 'Slack User ID': 'UOTHER01', Department: ['Music'] };
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: [LETTY, OTHER].map((f, i) => ({ id: 'rec' + i, fields: f })) }) } }];
const S_F = 'c_188em7d58podeju3i8q6juqlufkls@resource.calendar.google.com';
const ev = (id, title, s, e, creator, desc) => ({ id, summary: title, start: { dateTime: s }, end: { dateTime: e }, creator: { email: creator }, description: desc || '',
  location: 'KDC Plaza-Top Level-Studio F (12)', attendees: [{ email: S_F, displayName: 'KDC Plaza-Top Level-Studio F (12)', resource: true, responseStatus: 'accepted' }] });
const HAND = ev('h1', 'TENTATIVE ISR - ARNOLD | ONE GYEOMI | Steve', '2026-11-19T14:00:00+08:00', '2026-11-19T22:00:00+08:00', 'coord.alt@example.com');
const JESSIE = ev('j1', 'SALIN - MUSIC DEPT', '2026-11-19T09:00:00+08:00', '2026-11-19T10:00:00+08:00', 'jessie-service@example.com', 'Booked by: Coord Person | ref: UCOORD01 | Dept: Music');
const THEIRS = ev('t1', 'ISR - JOAQUIN', '2026-11-20T09:00:00+08:00', '2026-11-20T11:00:00+08:00', 'other@example.com');
const NOREF_OTHERS = ev('n1', 'SOMEONE ELSE BY HAND', '2026-11-21T09:00:00+08:00', '2026-11-21T11:00:00+08:00', 'third@example.com');

(async () => {
  console.log('PENDING 155 - Slack Interactions v81: My bookings');
  const rmb = async user => (await run(SI, 'Render My Bookings', [{ json: { items: [HAND, JESSIE, THEIRS, NOREF_OTHERS] } }],
    { 'My Window': [{ json: { user, start: '2026-11-19', end: '2026-11-26', channel: 'D1' } }], 'Read Cache 4': cache }))[0].json;
  let r = await rmb('UCOORD01'); const ids = b => b.blocks.filter(x => /^bk_/.test(x.block_id || '')).map(x => x.block_id.slice(3)).join();
  ok(ids(r) === 'j1,h1', 'the coordinator: her Jessie booking (ref:) and the one she made by hand (creator = her Alt email); not others\'', ids(r));
  ok(/bk_cancel/.test(JSON.stringify(r.blocks.filter(x => x.block_id === 'bka_h1'))), 'the hand-made one has Change / Cancel too');
  r = await rmb('UOTHER01');
  ok(ids(r) === 't1', 'someone else: only what they made (creator = their Email)', ids(r));

  console.log('PENDING 155 - Slack Interactions v81: To Cancel / To Move send my_emails');
  const tc = (await run(SI, 'To Cancel', [], { 'Check Signature': [{ json: { user: 'UCOORD01' } }], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify({ id: 'h1', d: '2026-11-19', t: HAND.summary, s: '14:00' }) }] } } }], 'Read Cache 5': cache }))[0].json;
  ok(tc.my_emails === 'coord@example.com,coord.alt@example.com' && tc.event_id === 'h1', 'To Cancel: my_emails = Email, Alt email', tc);
  ok(/my_emails: me\.emails \|\| ''/.test(node(SI, 'To Move').parameters.jsCode), 'To Move: my_emails on the call');
  for (const [w, nm] of [[CX, 'Cancel v35'], [MV, 'Move v44']])
    ok(node(w, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'my_emails'), nm + ': my_emails is an input of the trigger');

  console.log('PENDING 155 - Cancel Booking v35 (Check Ownership)');
  const base = { requester: 'UCOORD01', confirmed: true, authority: 'Standard, Client Booking', department: 'Music', requester_name: 'Coord Person', mode: '', booking_date: '2026-11-19' };
  const co = (req, day) => new Function('$', '$input', node(CX, 'Check Ownership').parameters.jsCode)(n => n === 'Find By Title' ? wrap([{ json: { items: [] } }]) : wrap([{ json: req }]), wrap([{ json: { items: day } }]))[0].json;
  let c = co(Object.assign({}, base, { event_id: 'h1', title: HAND.summary, my_emails: 'coord@example.com,coord.alt@example.com' }), [HAND]);
  ok(c.verdict !== 'REJECTED', 'her hand-made booking: allowed (was NO_REFERENCE "has to be cancelled by hand")', c);
  c = co(Object.assign({}, base, { event_id: 'h1', title: HAND.summary, my_emails: '' }), [HAND]);
  ok(c.verdict === 'REJECTED' && c.reason === 'NO_REFERENCE', 'no my_emails (an older caller) -> NO_REFERENCE, as before', c.reason);
  c = co(Object.assign({}, base, { event_id: 't1', title: THEIRS.summary, booking_date: '2026-11-20', my_emails: 'coord@example.com,coord.alt@example.com' }), [THEIRS]);
  ok(c.verdict === 'REJECTED' && c.reason === 'NO_REFERENCE', 'someone else\'s hand-made booking -> still NO_REFERENCE', c.reason);
  c = co(Object.assign({}, base, { event_id: 'j1', title: JESSIE.summary, my_emails: 'coord@example.com' }), [JESSIE]);
  ok(c.verdict !== 'REJECTED', 'her Jessie booking (ref:) -> allowed, as before', c);

  console.log('PENDING 155 - Move Booking v44 (Resolve Booking)');
  const mreq = (o) => [{ json: Object.assign({ event_id: 'h1', booking_date: '2026-11-19', title: HAND.summary, new_start_iso: '2026-11-19T15:00:00+08:00', new_end_iso: '2026-11-19T23:00:00+08:00',
    confirmed: true, requester: 'UCOORD01', authority: 'Standard, Client Booking', department: 'Music', requester_name: 'Coord Person', new_summary: '', new_details: '' }, o) }];
  const rv = (o, e) => new Function('$', '$input', node(MV, 'Resolve Booking').parameters.jsCode)(n => wrap(n === 'When Executed by Another Workflow' ? mreq(o) : []), wrap([{ json: { items: [e || HAND] } }]))[0].json;
  let m = rv({ my_emails: 'coord@example.com,coord.alt@example.com' });
  ok(m.verdict === 'CLEAR' && m.description === 'Booked by: Coord Person | ref: UCOORD01 | Dept: Music', 'her hand-made booking: moved; the replacement carries "Booked by | ref | Dept" (Jessie is its creator now)', m);
  m = rv({ my_emails: 'coord.alt@example.com' }, Object.assign({}, HAND, { description: 'call time 1pm' }));
  ok(m.verdict === 'CLEAR' && m.description === 'Booked by: Coord Person | ref: UCOORD01 | Dept: Music\n\nNotes: call time 1pm', 'its own text kept under Notes:', m.description);
  m = rv({ my_emails: '' });
  ok(m.verdict === 'REJECTED' && m.reason === 'NO_REFERENCE', 'no my_emails -> NO_REFERENCE, as before', m.reason);
  m = rv({ my_emails: 'coord@example.com', event_id: 'j1', title: JESSIE.summary, new_start_iso: '2026-11-19T10:00:00+08:00', new_end_iso: '2026-11-19T11:00:00+08:00' }, JESSIE);
  ok(m.verdict === 'CLEAR' && m.description === JESSIE.description, 'a Jessie booking (ref:) -> its description unchanged', m.description);

  console.log('PENDING 155 - main v293: typed "my bookings" and typed changes');
  const mine = (await run(MAIN, 'Mine Reply', [{ json: { items: [HAND, JESSIE, THEIRS] } }], { 'Mine Check': [{ json: { mineCheck: { user: 'UCOORD01', start: '2026-11-19', end: '2026-11-26', channel: 'D1' } } }],
    'Get Booker': [{ json: { id: 'rec0', fields: LETTY } }] }))[0].json;
  const mids = JSON.stringify(mine.blocks || []);
  ok(/bk_h1/.test(mids) && /bk_j1/.test(mids) && !/bk_t1/.test(mids), 'Mine Reply: hers by ref: and by creator; not someone else\'s', (mine.blocks || []).map(b => b.block_id));
  const chg = (await run(MAIN, 'Change Reply', [{ json: { items: [HAND, THEIRS] } }], { 'Change Offer': [{ json: { changeOffer: { kind: 'change', user: 'UCOORD01', channel: 'D1', words: ['gyeomi'], fDates: [], fRooms: [], n: {}, today: '2026-11-19' } } }],
    'Get Booker': [{ json: { id: 'rec0', fields: LETTY } }] }))[0].json;
  ok(chg.count === 1 && chg.blocks[1].block_id === 'bk_h1', 'Change Reply: "change the gyeomi booking" finds her hand-made one', chg.blocks.map(b => b.block_id));

  console.log('PENDING 156 - Book Session v130: an event with no room on it');
  const RES = { 'Studio 2': 'c_18871bprki2umhrkjc4qcaldse1f8@resource.calendar.google.com', 'Studio B': 'c_1881vgb66tkpujjelnn3rniugd9pk@resource.calendar.google.com' };
  const refRooms = FX.rooms.map(x => ({ id: x.id, name: x.fields['Room Name'], vocalBooth: !!x.fields['Vocal Booth'], booth: false, common: /conference|lobby/i.test(String(x.fields['Room Type'] || '')) }));
  const refTypes = FX.sessionTypes.map(s => ({ type: s.fields.Type, priority: [].concat(s.fields.Priority || []).map(id => (FX.rooms.find(x => x.id === id) || { fields: {} }).fields['Room Name']).filter(Boolean), lastResort: [], min: 60, max: 900, requirements: s.fields['Room Requirements'] || '' }));
  const STAFF = [{ Name: 'Eng Person', Initials: 'EP', 'Slack User ID': 'U9', Info: 'Recordist', Department: ['Localization'] }, { Name: 'Booker Person', Initials: 'BP', 'Slack User ID': 'UBOOKER1', Department: ['Localization'] }];
  const req = { mode: 'prepare', confirmed: false, summary: 'VSI-TRES / EP', start_iso: '2026-11-24T09:00:00+08:00', end_iso: '2026-11-24T23:00:00+08:00', rooms: 'Studio 2, Studio B', all_day: false,
    session_type: 'Localization Dubbing', client: '', engineer: 'Eng Person', bookingType: '', department: 'Localization', authority: '', expected_date: '2026-11-24',
    requester_text: 'Localization Dubbing in Studio 2 on 2026-11-24 9:00 am-11:00 pm, code VSI-TRES, engineer Eng Person', staff_data: JSON.stringify(STAFF),
    reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: {} }), description: 'Engineer: Eng Person | Booked by: Booker Person | ref: UBOOKER1 | Dept: Localization', exclude_event_id: '', room_override: false, series: true };
  const NEW_EVENT = { id: 'ne', summary: 'New Event', start: { dateTime: '2026-11-24T09:00:00+08:00' }, end: { dateTime: '2026-11-24T10:00:00+08:00' }, creator: { email: 'someone@example.com' } };
  const cc = (w, events, fb) => { const outs = { 'When Executed by Another Workflow': [req], 'Get Events In Window': [{ items: events }], 'Room Free Busy': [fb || {}], 'All Bookers': STAFF.map(f => ({ fields: f })),
      'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
    return new Function('$', '$input', node(w, 'Check Conflicts').parameters.jsCode)(n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) }),
      wrap([{ json: { items: JSON.parse(JSON.stringify(events)) } }]))[0].json; };
  const FBOK = { calendars: { [RES['Studio 2']]: { busy: [] }, [RES['Studio B']]: { busy: [] } } };
  let b0 = cc(BS0, [NEW_EVENT], FBOK);
  ok(b0.verdict === 'REJECTED' && b0.reason === 'UNVERIFIABLE', 'v129 (live): "New Event" with no room -> UNVERIFIABLE (the 15 Nov refusal)', b0.reason);
  let b1 = cc(BS, [NEW_EVENT], FBOK);
  ok(b1.reason !== 'UNVERIFIABLE', 'v130: both rooms read free on their own calendars -> "New Event" no longer refuses', { v: b1.verdict, r: b1.reason, h: String(b1.human || '').slice(0, 200) });
  ok(cc(BS, [NEW_EVENT], { calendars: { [RES['Studio 2']]: { busy: [] } } }).reason === 'UNVERIFIABLE', 'v130: one room\'s free/busy missing -> UNVERIFIABLE, as before');
  ok(cc(BS, [NEW_EVENT], { error: { message: 'timeout' } }).reason === 'UNVERIFIABLE', 'v130: the free/busy read failed -> UNVERIFIABLE, as before');
  const b2 = cc(BS, [NEW_EVENT], { calendars: { [RES['Studio 2']]: { busy: [{ start: '2026-11-24T01:00:00Z', end: '2026-11-24T02:00:00Z' }] }, [RES['Studio B']]: { busy: [] } } });
  ok(b2.verdict === 'REJECTED' && b2.reason === 'ROOM_OCCUPIED', 'v130: if the room\'s own calendar is busy then -> taken (ROOM_OCCUPIED), not free', b2.reason);
  const strip = o => JSON.stringify(Object.assign({}, o, { human: '', prep_payload: '' }));
  ok(strip(cc(BS, [], FBOK)) === strip(cc(BS0, [], FBOK)), 'v130 = v129 on an empty calendar');

  console.log('PENDING 156 - Slack Interactions v81: the refusal in words');
  for (const nd of ['After Prepare', 'After Book', 'After Prepare Series'])
    ok(/An event in the calendar then has no room on it \('\n    \+ human\.match\(\/cannot identify a room for \\\(\(\.\+\)\\\), so\/\)\[1\]/.test(node(SI, nd).parameters.jsCode), nd + ': UNVERIFIABLE names the event');
  const human = 'There is an event in that window I cannot identify a room for ("New Event"), so I could not confirm the room is free. Nothing was booked - ask the requester to check Google Calendar.';
  const m2 = human.match(/cannot identify a room for \((.+)\), so/);
  ok(m2 && m2[1] === '"New Event"', 'the event name is read from Book Session\'s answer: ' + (m2 && m2[1]));

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
