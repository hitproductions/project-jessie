#!/usr/bin/env node
// Guests on meetings and events (PENDING 160 (c), decided 20 Nov), through the real nodes:
//   Slack Interactions v83 - the Guests / Other guests (emails) fields (meetings and events only), Read Step 2 (Bookers email, typed
//   emails, refusals), the Booked card's Guests line, the guests' Slack message (Bookers only), the series too;
//   Book Session v133 - Create Event's attendees = rooms + guests, sendUpdates; Book Series v13 - guests stored and passed per date;
//   Move v47 - guests kept on a change (rooms swapped), updates sent; Cancel v36 / Room Check v5 - updates sent.
//   node scripts/sim-guests.js [si v83] [book-session v133] [book-series v13] [move v47] [cancel v36] [room-check v5]
// Every name, email and Slack id here is made up.
const fs = require('fs');
const L = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const SI = L(process.argv[2], 'workflows/slack-interactions-v84.json'), BS = L(process.argv[3], 'workflows/book-session-v133.json');
const BSER = L(process.argv[4], 'workflows/book-series-v13.json'), MV = L(process.argv[5], 'workflows/move-booking-v47.json');
const CX = L(process.argv[6], 'workflows/cancel-booking-v36.json'), RC = L(process.argv[7], 'workflows/room-check-v5.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const run = (w, name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(w, name).parameters.jsCode + '\n}).call(this);').call({ helpers: {} },
  n => { if (!(n in outs)) throw new Error('not run: ' + n); return wrap(outs[n]); }, wrap(input));
const j1 = async (...a) => (await run(...a))[0].json;
const FX = require('./sim-fixture-rooms.js');
const P = (id, name, dept, email, alt) => ({ id: 'r' + id, fields: Object.assign({ Name: name, Initials: name.split(' ').map(x => x[0]).join(''), 'Slack User ID': id, Department: [dept], Info: 'Account Manager' },
  email ? { Email: email } : {}, alt ? { 'Alt email': alt } : {}) });
const BOOKERS = [P('UBOOK01', 'Booker Person', 'Sales & Accounts', 'booker@example.com'), P('UANA01', 'Ana Guest', 'Marketing', 'ana@example.com'),
  P('UBEN01', 'Ben Guest', 'Business Development', 'ben@example.com', 'ben.alt@example.com'), P('UNOEM1', 'No Email', 'Marketing'),
  P('UCARL1', 'Carla Alt', 'Marketing', '', 'carla.alt@example.com'), P('UENG01', 'Eng Person', 'Audio Post', 'eng@example.com')];
const ST = t => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': '', Priority: [], 'Last Resort': [], 'Engineer Role Required': [] } });
const types = FX.sessionTypes.filter(x => !/^(Meeting|Event)$/.test(x.fields.Type)).concat([ST('Meeting'), ST('Event')]);
const cacheOf = bookers => [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: types, bookers }) } }];
const cache = cacheOf(BOOKERS);
const S = (purpose, kind, extra) => Object.assign({ date: '2026-11-24', t0: '10:00', t1: '11:00', purpose, kind, requester: 'UBOOK01', channel: 'D1', ext: 'x', when: 'x' }, extra || {});
const FREE = ['Likha', 'Katha', 'Salin', 'Lobby', 'Studio 7', 'Studio 8', 'Studio F', 'M1', 'M2'];
const step2 = async (s, bookers) => (await j1(SI, 'Build Step 2', [{ json: { status: 'OK', busy: [], free_priority: ['Likha', 'Katha'], free_rooms: FREE } }],
  { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': bookers ? cacheOf(bookers) : cache, 'Loc Projects 2': [] })).view;
const blk = (v, id) => v.blocks.find(b => b.block_id === id);
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const tv = v => ({ selected_option: { value: v } }), ms = a => ({ selected_options: a.map(value => ({ value })) });
const read2 = async (vv, s) => j1(SI, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'UBOOK01', channel: 'D1' } }], 'Read Cache 3': cache, 'Timings 2': [],
  'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', blocks: [], private_metadata: JSON.stringify(Object.assign({ label: s.purpose }, s)), state: { values: vv } } } } }] });
const MEET = (extra) => Object.assign({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'weekly sync' } }, department: { department_pick: tv('Marketing') } }, extra || {});

(async () => {
  console.log('Book a room, step 2: the guest fields');
  let v = await step2(S('Meeting', 'meeting'));
  const g = blk(v, 'guests'), ge = blk(v, 'guest_emails');
  ok(g && g.optional && g.label.text === 'Guests' && g.element.type === 'multi_static_select' && g.element.action_id === 'guests_pick' && g.element.placeholder.text === 'Select people' && !g.element.initial_options,
     'Meeting: "Guests" - optional, a multi-select of people, nothing picked', g);
  ok(g && g.element.options.map(o => o.text.text).join() === 'Ana Guest,Ben Guest,Booker Person,Carla Alt,Eng Person,No Email' && g.element.options[0].value === 'UANA01',
     'everyone in Bookers with a Slack id, by name; the value is the Slack id', g && g.element.options);
  ok(g && /invite/.test(g.hint.text) && /message from Jessie/.test(g.hint.text), 'its hint: the Google invite and a message from Jessie', g && g.hint);
  ok(ge && ge.optional && ge.label.text === 'Other guests (emails)' && ge.element.type === 'plain_text_input' && ge.element.action_id === 'guest_emails_in' && /outside Hit/.test(ge.hint.text) && /commas/.test(ge.hint.text) && /invite/.test(ge.hint.text),
     '"Other guests (emails)" - optional, typed; hint: outside Hit, the invite, commas', ge && ge.hint);
  ok(ids(v).indexOf('guests') > ids(v).indexOf('title') && ids(v).indexOf('guest_emails') === ids(v).indexOf('guests') + 1 && ids(v).indexOf('notes') === ids(v).indexOf('guest_emails') + 1,
     'after the title / department, before the note', ids(v));
  v = await step2(S('Event', 'meeting'));
  ok(blk(v, 'guests') && blk(v, 'guest_emails'), 'Event: the same two fields');
  for (const [p, k] of [['VO Recording', 'studio'], ['M booth', 'booth'], ['Localization Dubbing', 'loc']]) {
    v = await step2(S(p, k));
    ok(!blk(v, 'guests') && !blk(v, 'guest_emails'), p + ': no guest fields (meetings and events only)');
  }
  v = await step2(S('Meeting', 'meeting', { pre: { gu: 'UBEN01,UNOPE', ge: 'client@acme.example' } }));
  ok(blk(v, 'guests').element.initial_options.map(o => o.value).join() === 'UBEN01' && blk(v, 'guest_emails').element.initial_value === 'client@acme.example',
     'a form opened again (Continue booking) keeps the guests picked and typed', [blk(v, 'guests').element.initial_options, blk(v, 'guest_emails').element.initial_value]);
  const many = []; for (let i = 0; i < 130; i++) many.push(P('UM' + String(i).padStart(4, '0'), 'Person ' + String(i).padStart(3, '0'), ['Marketing', 'Music', 'Localization'][i % 3], 'p' + i + '@example.com'));
  v = await step2(S('Meeting', 'meeting'), many);
  const og = blk(v, 'guests').element.option_groups || [];
  ok(!blk(v, 'guests').element.options && og.map(x => x.label.text).join() === 'Localization,Marketing,Music' && og.reduce((a, x) => a + x.options.length, 0) === 130 && og.every(x => x.options.length <= 100),
     'more than 100 people: grouped by department (Slack shows at most 100 a list), nobody left out', og.map(x => [x.label.text, x.options.length]));

  console.log('Read Step 2: who is invited');
  let r = await read2(MEET({ guests: { guests_pick: ms(['UANA01', 'UBEN01']) }, guest_emails: { guest_emails_in: { value: 'client@acme.example, Carla <CARLA.ALT@example.com>; ana@example.com\nmore.person@outside.example.co' } } }), S('Meeting', 'meeting'));
  ok(r.valid && r.prep.guests === 'ana@example.com,ben@example.com,client@acme.example,carla.alt@example.com,more.person@outside.example.co',
     'picked: their Bookers Email; typed: every email (a name around one ignored, one picked twice once, lower case)', r.prep.guests);
  ok(r.guestIds === 'UANA01,UBEN01,UCARL1', 'the guests in Bookers - picked, or typed by an email of theirs (Alt email too) - get a message', r.guestIds);
  ok(r.guestNames === 'Ana Guest, Ben Guest, client@acme.example, Carla Alt, more.person@outside.example.co', 'names for the card: a Bookers name, else the email', r.guestNames);
  ok(r.again.gu === 'UANA01,UBEN01' && /client@acme\.example/.test(r.again.ge), 'kept for Book a room / Continue booking from the DM', r.again);
  ok(r.prep.rooms === 'Likha' && r.calTitle === 'LIKHA - Weekly sync' && !/guest/i.test(r.prep.description), 'the booking otherwise as before (title, room; guests are not written into the description)', [r.prep.rooms, r.calTitle, r.prep.description]);
  r = await read2(MEET({ guests: { guests_pick: ms(['UNOEM1']) } }), S('Meeting', 'meeting'));
  ok(!r.valid && r.answer.response_action === 'errors' && /No email on file for No Email/.test(r.answer.errors.guests) && /Other guests/.test(r.answer.errors.guests), 'someone with no email in Bookers -> "No email on file … type it under Other guests"', r.answer);
  r = await read2(MEET({ guest_emails: { guest_emails_in: { value: 'good@example.com, broken@example, x@@example.com' } } }), S('Meeting', 'meeting'));
  ok(!r.valid && /^Check these emails: /.test(r.answer.errors.guest_emails) && /broken@example/.test(r.answer.errors.guest_emails), 'a broken email -> "Check these emails: …" (nothing booked)', r.answer.errors);
  r = await read2(MEET({ guest_emails: { guest_emails_in: { value: 'Ana from Marketing' } } }), S('Meeting', 'meeting'));
  ok(r.valid && r.prep.guests === '', 'words with no email in them: no guests, no error');
  r = await read2(MEET({ guest_emails: { guest_emails_in: { value: 'c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com' } } }), S('Meeting', 'meeting'));
  ok(r.valid && r.prep.guests === '', 'a room\'s calendar address is not a guest');
  r = await read2(MEET(), S('Meeting', 'meeting'));
  ok(r.valid && r.prep.guests === '' && r.guestIds === '' && r.guestNames === '', 'no guests: as before');
  r = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'kuba' } }, guests: { guests_pick: ms(['UANA01']) }, guest_emails: { guest_emails_in: { value: 'x@example.com' } } }, S('VO Recording', 'studio'));
  ok(r.prep.guests === '' && r.guestIds === '', 'a studio booking: guests ignored even if sent', r.prep.guests);

  console.log('Through to Book Session / Book Series');
  r = await read2(MEET({ guests: { guests_pick: ms(['UANA01']) }, guest_emails: { guest_emails_in: { value: 'client@acme.example' } } }), S('Meeting', 'meeting'));
  const tp = await j1(SI, 'To Prepare', [], { 'Read Step 2': [{ json: r }], 'Read Cache 3': cache });
  ok(tp.guests === 'ana@example.com,client@acme.example', 'To Prepare passes guests to Book Session', tp.guests);
  const trig = n => n.parameters.workflowInputs.values.map(x => x.name);
  ok(trig(BS.nodes.find(n => n.type.endsWith('executeWorkflowTrigger'))).indexOf('guests') !== -1, 'Book Session takes a guests input');
  ok(trig(BSER.nodes.find(n => n.type.endsWith('executeWorkflowTrigger'))).indexOf('guests') !== -1, 'Book Series takes a guests input');
  const ser = Object.assign({}, r, { s: Object.assign({}, r.s, { series: { dates: ['2026-11-24', '2026-12-01'] } }) });
  const tps = await j1(SI, 'To Prepare Series', [], { 'To Prepare': [{ json: tp }], 'Read Step 2': [{ json: ser }] });
  ok(tps.guests === 'ana@example.com,client@acme.example', 'To Prepare Series passes them to Book Series', tps.guests);
  const occ = await run(BSER, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: Object.assign({}, tps, { mode: '', confirmed: true }) }] });
  ok(occ.length === 2 && occ.every(o => o.json.guests === 'ana@example.com,client@acme.example'), 'Book Series: every date\'s Book Session call gets the guests', occ.map(o => o.json.guests));
  ok(/guests: String\(REQ0\.guests \|\| ''\)/.test(node(BSER, 'Aggregate').parameters.jsCode), 'Book Series: the guests are stored with the prepared series (what the confirm screen books)');

  console.log('Book Session: the calendar event');
  const ce = node(BS, 'Create Event').parameters.additionalFields;
  const ev = (expr, req) => new Function('$', 'return ' + expr.replace(/^=\{\{/, '').replace(/\}\}$/, ''))(n => ({ first: () => ({ json: n === 'When Executed by Another Workflow' ? req : {} }) }));
  const LIKHA = 'c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com', KATHA = 'c_1881169pcpn12gsnm6i7sc0gjk7gk@resource.calendar.google.com';
  ok(ev(ce.attendees[0], { rooms: 'Likha, Katha', guests: 'ana@example.com,client@acme.example' }) === [LIKHA, KATHA, 'ana@example.com', 'client@acme.example'].join(','), 'attendees: the rooms, then the guests');
  ok(ev(ce.attendees[0], { rooms: 'Likha', guests: ' Ana@Example.com ; ana@example.com, bad@x, ' + KATHA }) === [LIKHA, 'ana@example.com'].join(','), 'cleaned again here: lower case, once each, broken ones and room addresses left out');
  ok(ev(ce.attendees[0], { rooms: 'Likha' }) === LIKHA && ev(ce.attendees[0], { rooms: 'Likha', guests: '' }) === LIKHA, 'no guests (every other booking): the rooms only, as before');
  let threw = ''; try { ev(ce.attendees[0], { rooms: 'Nowhere', guests: 'a@example.com' }); } catch (e) { threw = e.message; }
  ok(/Unrecognized room name/.test(threw), 'an unknown room still stops the booking');
  ok(ev(ce.sendUpdates, { guests: 'a@example.com' }) === 'all' && ev(ce.sendUpdates, { guests: '' }) === 'none' && ev(ce.sendUpdates, {}) === 'none', 'sendUpdates: "all" with guests (Google emails the invite), else "none" (as before)');

  console.log('The Booked card and the guests\' message');
  const ctx = { 'Read Step 2': [{ json: Object.assign({}, r, { viewId: 'V1', channel: 'D1' }) }], 'After Prepare': [{ json: { F: { Room: 'Likha' }, book: { description: '' } } }] };
  const ab = await j1(SI, 'After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: 'LIKHA - Weekly sync' } }], ctx);
  ok(/\*Room:\* Likha\n\*Guests:\* Ana Guest, client@acme\.example/.test(ab.text), 'the Booked card: "Guests: Ana Guest, client@acme.example" under the room', ab.text);
  const ab0 = await j1(SI, 'After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: 'LIKHA - Weekly sync' } }], { 'Read Step 2': [{ json: Object.assign({}, await read2(MEET(), S('Meeting', 'meeting')), { viewId: 'V1', channel: 'D1' }) }], 'After Prepare': ctx['After Prepare'] });
  ok(!/Guests/.test(ab0.text), 'no guests: no Guests line');
  const nb = async (R2, A) => (await run(SI, 'Booked Notices', [{ json: {} }], { 'Read Step 2': [{ json: R2 }], 'Read Cache 3': cache, 'After Book': [{ json: A }] })).map(x => x.json);
  r = await read2(MEET({ guests: { guests_pick: ms(['UANA01', 'UBEN01', 'UBOOK01']) }, guest_emails: { guest_emails_in: { value: 'client@acme.example, eng@example.com' } } }), S('Meeting', 'meeting'));
  const A1 = { text: '✅ *Booked.*\n\n*LIKHA - Weekly sync*\n*Date:* x', blocks: [{ type: 'actions', elements: [{ action_id: 'bk_change', value: JSON.stringify({ id: 'ev1', d: '2026-11-24', s: '10:00', e: '11:00', r: 'Likha', t: 'LIKHA - Weekly sync' }) }] }] };
  let out = await nb(r, A1);
  ok(out.map(x => x.channel).sort().join() === 'UANA01,UBEN01,UENG01', 'a message to each guest in Bookers (picked, or typed by their email) - not the booker, not the outside guest', out.map(x => x.channel));
  ok(out.every(x => /^👋 \*Booker Person invited you to a meeting\.\*/.test(x.text) && /LIKHA - Weekly sync/.test(x.text)), '"Booker Person invited you to a meeting." with the booking', out.map(x => x.text.split('\n')[0]));
  ok(out.every(x => !JSON.stringify(x.blocks).includes('bk_change') && !JSON.stringify(x.blocks).includes('bk_cancel') && JSON.stringify(x.blocks).includes('my_bookings')), 'no Change / Cancel (it is not theirs) - My bookings / Book a room only');
  out = await nb(Object.assign({}, r, { s: Object.assign({}, r.s, { purpose: 'Event' }), forId: 'UANA01' }), A1);
  ok(out.filter(x => x.channel === 'UANA01').length === 1 && /booked this for you/.test(out.find(x => x.channel === 'UANA01').text) && /invited you to an event/.test(out.find(x => x.channel === 'UBEN01').text),
     'an Event: "invited you to an event"; someone told already (who it is for) is not told twice', out.map(x => [x.channel, x.text.split('\n')[0]]));
  out = await nb(await read2(MEET(), S('Meeting', 'meeting')), A1);
  ok(out.length === 0, 'no guests: no messages (as before for a meeting)');

  console.log('A series: the card and the messages');
  const sn = async T => (await run(SI, 'Series Notices', [{ json: {} }], { 'Read Series Confirm': [{ json: { user: 'UBOOK01' } }], 'To Book Series': [{ json: T }],
    'After Book Series': [{ json: { text: '✅ *Booked 2 dates*\n\n*LIKHA - Weekly sync*' } }], 'Read Cache 8': cache })).map(x => x.json);
  out = await sn({ go: true, description: 'Booked by: Booker Person | ref: UBOOK01', guests: 'ana@example.com,ben.alt@example.com,client@acme.example', session_type: 'Meeting' });
  ok(out.map(x => x.channel).sort().join() === 'UANA01,UBEN01' && out.every(x => /invited you to a meeting on 2 dates/.test(x.text)), 'each guest in Bookers once: "invited you to a meeting on 2 dates" (Alt email matched; the outside guest gets the invites only)', out.map(x => [x.channel, x.text.split('\n')[0]]));
  out = await sn({ go: true, description: 'Booked by: Booker Person | ref: UBOOK01', guests: '', session_type: 'Meeting' });
  ok(out.length === 0, 'no guests: as before');
  ok(/\+ __gLine/.test(node(SI, 'After Book Series').parameters.jsCode) && /\*Guests:\*/.test(node(SI, 'After Book Series').parameters.jsCode), 'the series card gets the Guests line too');

  console.log('Move v47: the guests stay on a changed booking');
  const REQ = { event_id: 'm1', booking_date: '2026-11-24', title: 'LIKHA - Weekly sync', new_start_iso: '2026-11-24T14:00:00+08:00', new_end_iso: '2026-11-24T15:00:00+08:00',
    confirmed: true, requester: 'UBOOK01', authority: 'Standard', department: 'Sales & Accounts', requester_name: 'Booker Person', new_summary: '', new_details: '' };
  const MEV = { id: 'm1', status: 'confirmed', summary: 'LIKHA - Weekly sync', description: 'Booked by: Booker Person | ref: UBOOK01 | Dept: Sales & Accounts',
    start: { dateTime: '2026-11-24T10:00:00+08:00' }, end: { dateTime: '2026-11-24T11:00:00+08:00' }, location: 'Likha', creator: { email: 'kdc@example.com' },
    attendees: [{ email: LIKHA, resource: true, displayName: 'Likha', responseStatus: 'accepted' }, { email: 'ana@example.com', responseStatus: 'accepted' },
      { email: 'client@acme.example', responseStatus: 'needsAction', optional: true }, { email: 'kdc@example.com', self: true, organizer: true, responseStatus: 'accepted' }] };
  const rv = (o, e) => new Function('$', '$input', node(MV, 'Resolve Booking').parameters.jsCode)(n => wrap(n === 'When Executed by Another Workflow' ? [{ json: Object.assign({}, REQ, o) }] : []), wrap([{ json: { items: [e || MEV] } }]))[0].json;
  let m = rv({});
  ok(m.verdict === 'CLEAR' && JSON.stringify(m.attendees) === JSON.stringify([{ email: LIKHA }, { email: 'ana@example.com' }, { email: 'client@acme.example', optional: true }]),
     'a new time: the room and every guest on the replacement (the calendar itself left out)', m.attendees);
  m = rv({ new_rooms: 'Katha' });
  ok(m.verdict === 'CLEAR' && JSON.stringify(m.attendees.map(a => a.email)) === JSON.stringify([KATHA, 'ana@example.com', 'client@acme.example']), 'a new room: the room swapped, the guests kept', m.attendees);
  m = rv({}, Object.assign({}, MEV, { attendees: [MEV.attendees[0]] }));
  ok(JSON.stringify(m.attendees) === JSON.stringify([{ email: LIKHA }]), 'no guests: the rooms only, as before');
  ok(/\/events\?sendUpdates=all$/.test(node(MV, 'Create Replacement').parameters.url) && /original_id\) \}\}\?sendUpdates=all$/.test(node(MV, 'Delete Original').parameters.url),
     'Create Replacement / Delete Original send updates (Google tells the guests)');

  console.log('Cancel v36 / Room Check v5: the guests are told');
  ok(JSON.stringify(node(CX, 'Delete Event').parameters.options) === '{"sendUpdates":"all"}', 'Cancel: Delete Event sends updates (the guests get the cancellation)');
  ok(/event_id \|\| ''\)\) \}\}\?sendUpdates=all$/.test(node(RC, 'Delete Declined').parameters.url), 'Room Check: a declined booking deleted with updates (guests invited seconds before are told)');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
