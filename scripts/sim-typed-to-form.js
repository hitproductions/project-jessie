#!/usr/bin/env node
// Typed booking -> form, offline (main v263 + Slack Interactions v9): main's Form Offer on different messages (offer or
// agent; what it read; the reply and the button), a second message after an offer, Turn Log Row's path, the wiring; then
// the form: step 1 filled in from the button, step 1 read carries it, step 2 with the room asked for (free / taken / not
// usual / not a room for this) and the details filled in.
// Usage: node scripts/sim-typed-to-form.js [main v263] [slack interactions v9]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v268.json', 'utf8'));
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v10.json', 'utf8'));
let pass = 0, fail = 0;
const M264 = /Project: /.test(main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode), V10 = si.nodes.some(n => n.name === 'Note Toggle');
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}

(async () => {
  const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
  const rooms = [R('r7', 'Studio 7'), R('r8', 'Studio 8'), R('rf', 'Studio F'), R('rc', 'Studio C'), R('r4', 'Studio 4'),
    R('rl', 'Likha', { 'Room Type': ['Conference Room'] }), R('m4', 'M4', { 'Room Type': ['M Booth'] })];
  const TYPES = ['VO Recording', 'Music Mixing', 'Post Mixing', 'Localization Dubbing', 'Celebrity Recording', 'Meeting', 'Event'];
  const bookers = [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer' } },
    { fields: { Name: 'Daryl Reyes', Initials: 'DR', 'Slack User ID': 'U2\n', Info: 'Music Engineer' } },
    { fields: { Name: 'Peter Legaste', Initials: 'PL', 'Slack User ID': 'U4', Info: 'Music Arranger' } }];
  const base = {
    'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': TYPES.map(t => ({ json: { fields: { Type: t } } })),
    'All Bookers': bookers.map(b => ({ json: b }))
  };
  // Form Offer for one message: gate / Booked For as they would read it, and the history (newest first)
  const offer = async (text, o) => {
    o = o || {};
    const outs = Object.assign({}, base, {
      'Slack Trigger': [{ json: { text, channel: 'D1', ts: '100.1' } }],
      'Gate Context': [{ json: Object.assign({ datesInMessage: o.dates || '', confirmed: false, gate: o.gate || {} }, o.g || {}) }],
      'Booked For': [{ json: Object.assign({ requesterText: text }, o.bf || {}) }],
      'Get Recent Messages': (o.history || []).map(m => ({ json: m }))
    });
    return (await run(main, 'Form Offer', [{ json: { keep: 1 } }], outs))[0].json;
  };

  // ---- a typed booking request -> an offer
  let r = await offer('book studio 7 tomorrow 2-4pm, VO recording for ORANGE, client Jem Lim, engineer Howard', { dates: '2027-10-14',
    bf: { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00', project: 'ORANGE', client: 'Jem Lim', clientPhrase: 'client Jem Lim', engineer: 'Howard Luistro', engineerResolved: true, engineerPhrase: 'engineer Howard' } });
  let F = r.formOffer;
  ok(r.keep === 1 && F.offer && F.why === 'a booking request', 'a booking request -> an offer (the item passes through)');
  ok(JSON.stringify(F.prefill) === JSON.stringify({ d: '2027-10-14', s: '14:00', e: '16:00', r: 'Studio 7', p: 'VO Recording', pj: 'ORANGE', c: 'Jem Lim', en: 'U1', enN: 'Howard Luistro' }),
     'read by code: date, times, room, type, project, client, engineer - ' + JSON.stringify(F.prefill));
  ok(F.text === 'Here’s what I have so far:\n🗓️ *Studio 7 · Thursday, October 14 · 2:00 PM – 4:00 PM*\nVO Recording · Project' + (M264 ? ': ' : ' ') + 'ORANGE · Client' + (M264 ? ': ' : ' ') + 'Jem Lim · Engineer' + (M264 ? ': ' : ' ') + 'Howard Luistro',
     'the reply, written by code - ' + F.text.replace(/\n/g, ' | '));
  const btn = F.blocks[1].elements[0];
  ok(btn.action_id === 'open_book' && JSON.parse(btn.value).r === 'Studio 7' && btn.value.length < 1900 && F.blocks[0].text.text === F.text, 'Book a room button carries the prefill');
  ok(!/Confirm to book|yes\/no|Reply yes/i.test(JSON.stringify(F.blocks)), 'no chat card, no yes/no');

  if (M264) {
    // v264: "for X" as the project (the live 01:30 message), never a colleague / room / type / date word
    const ask = async (text, bf) => (await offer(text, { dates: '2027-10-16', bf })).formOffer.prefill;
    let q = await ask('book studio 7 tomorrow 2-4pm VO recording for ORANGE, client Jem Lim', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00', client: 'Jem Lim', clientPhrase: 'client Jem Lim' });
    ok(q.pj === 'ORANGE' && q.c === 'Jem Lim', 'v264: "for ORANGE, client Jem Lim" -> project ORANGE (the live 01:30 message)');
    q = await ask('book studio 7 tomorrow for orange, client Jem Lim', { client: 'Jem Lim', clientPhrase: 'client Jem Lim' });
    ok(q.pj === 'orange', 'v264: client named separately -> "for orange" is the project as typed');
    q = await ask('book studio 7 tomorrow for BLUE BIRD', {});
    ok(q.pj === 'BLUE BIRD', 'v264: capitals, no client -> the project');
    q = await ask('book studio 7 tomorrow for Jem Lim', { forClient: 'Jem Lim' });
    ok(!q.pj && q.c === 'Jem Lim', 'v264: "for Jem Lim", no client named -> still the client');
    q = await ask('book studio 7 for daryl tomorrow, client Jem Lim', { client: 'Jem Lim', bookedFor: 'Daryl Reyes', matched: 'daryl' });
    ok(!q.pj, 'v264: "for daryl" is a colleague, not a project');
    q = await ask('book a room for tomorrow 2pm, client Jem Lim', { client: 'Jem Lim' });
    ok(!q.pj, 'v264: "for tomorrow" is not a project');
    q = await ask('book studio 7 for VO recording tomorrow, client Jem Lim', { client: 'Jem Lim' });
    ok(!q.pj, 'v264: "for VO recording" is not a project');
    q = await ask('book a room for STUDIO 7 tomorrow', {});
    ok(!q.pj, 'v264: "for STUDIO 7" is a room, not a project');
    q = await ask('book studio 7 for project KIWI, client Jem Lim', { client: 'Jem Lim', project: 'KIWI' });
    ok(q.pj === 'KIWI', 'v264: Booked For\'s project wins');
  }
  // v266 (live 15 Oct 11:05): "book me a studio" right after a form booking - Booked For read back into the earlier request
  if (/v266/.test(main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode)) {
    r = await offer('book me a studio', { bf: { requesterText: 'book me a studio\nbook studio 8 sat 4-6pm for LEMON ADE, client harold orozcor', timeInNewest: false,
      timeStart: '16:00', timeEnd: '18:00', client: 'harold orozcor', clientPhrase: 'client harold orozcor', engineer: 'Howard Luistro', engineerResolved: true, engineerPhrase: 'engineer howard', project: 'LEMON ADE' } });
    ok(r.formOffer.offer && JSON.stringify(r.formOffer.prefill) === '{}' && r.formOffer.text === 'Let’s book it with the form.',
       'v266: "book me a studio" -> nothing from the earlier booking (live 11:05) - ' + JSON.stringify(r.formOffer.prefill));
    r = await offer('book a vo session in studio 7', { bf: { requesterText: 'book a vo session in studio 7\nbook studio 8 4-6pm', timeInNewest: false, timeStart: '16:00', timeEnd: '18:00' } });
    ok(r.formOffer.prefill.r === 'Studio 7' && !r.formOffer.prefill.s && r.formOffer.prefill.p === 'VO Recording', 'v266: only what this message says');
  }
  r = await offer('book a room', {});
  ok(r.formOffer.offer && r.formOffer.text === 'Let’s book it with the form.' && /Pick the date/.test(r.formOffer.blocks[2].elements[0].text), 'nothing read -> the form, plainly');
  r = await offer('pls book M4 tomorrow 10-12', { dates: '2027-10-14', bf: { timeInNewest: true, timeStart: '10:00', timeEnd: '12:00' } });
  ok(r.formOffer.prefill.p === '__booth' && /M booth/.test(r.formOffer.text), 'an M booth -> M booth');
  r = await offer('book likha friday 3-4pm', { dates: '2027-10-15', bf: { timeInNewest: true, timeStart: '15:00', timeEnd: '16:00' } });
  ok(r.formOffer.prefill.p === 'Meeting' && r.formOffer.prefill.r === 'Likha', 'a conference room, no type -> Meeting');
  r = await offer('book a vo session tomorrow', { dates: '2027-10-14' });
  ok(r.formOffer.prefill.p === 'VO Recording', '"vo" -> VO Recording (the only type with that word)');
  r = await offer('book a dubbing session tomorrow', { dates: '2027-10-14' });
  ok(r.formOffer.prefill.p === 'Localization Dubbing', '"dubbing" -> Localization Dubbing');
  r = await offer('book a mixing session tomorrow', { dates: '2027-10-14' });
  ok(r.formOffer.offer && !r.formOffer.prefill.p, '"mixing" fits several -> left for the form');
  r = await offer('book studio 7 or studio 8 tomorrow', { dates: '2027-10-14' });
  ok(!r.formOffer.prefill.r, 'two rooms -> no room chosen');
  r = await offer('book studio 7 for peter', { bf: { arranger: 'Peter Legaste', arrangerResolved: true, arrangerPhrase: 'for peter', engineer: 'Drey', engineerResolved: false } });
  ok(r.formOffer.prefill.ar === 'U4' && !r.formOffer.prefill.en, 'only names Bookers resolved are filled in');

  // ---- still the agent's
  const agent = async (text, o, why) => { const x = await offer(text, o); ok(!x.formOffer.offer && x.formOffer.why === why, JSON.stringify(text) + ' -> agent (' + why + '), got ' + x.formOffer.why); };
  await agent('is studio 7 free friday?', { dates: '2027-10-15' }, 'an availability question');
  await agent('cancel ORANGE tomorrow', {}, 'a cancel or move');
  await agent('can you move my booking to 3pm', {}, 'a cancel or move');
  if (/v268/.test(main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode)) {
    const sr = await offer('book studio 7 every monday 10-12', {});
    ok(sr.formOffer.offer && sr.formOffer.prefill.rep && sr.formOffer.prefill.rep.days.join() === 'MO', 'v268: a typed series -> the form with Repeats (no chat card)');
  } else await agent('book studio 7 every monday 10-12', {}, 'a series');
  await agent('what did I book tomorrow?', {}, 'not a booking request');
  await agent('what do i have this week?', {}, 'not a booking request');
  await agent('yes', { g: { confirmed: true } }, 'a yes to a chat card');
  await agent('book it in studio 8 instead', { gate: { presentedBook: true } }, 'answering a chat card');

  // ---- after an offer
  const prev = { d: '2027-10-14', s: '14:00', e: '16:00', r: 'Studio 7', p: 'VO Recording' };
  const offerMsg = { ts: '99.1', bot_id: 'B1', text: 'Here’s what I have so far', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Here’s what I have so far:\n🗓️ *Studio 7 · Thursday, October 14 · 2:00 PM – 4:00 PM*' } },   // as Slack returns it (v273 reads it)
    { type: 'actions', elements: [{ type: 'button', action_id: 'open_book', value: JSON.stringify(prev) }] }] };
  r = await offer('make it 3-5pm', { history: [{ ts: '100.1', text: 'make it 3-5pm' }, offerMsg], bf: { timeInNewest: true, timeStart: '15:00', timeEnd: '17:00' } });
  ok(r.formOffer.offer && r.formOffer.why === 'more details after an offer' && r.formOffer.prefill.s === '15:00' && r.formOffer.prefill.d === '2027-10-14'
     && r.formOffer.prefill.r === 'Studio 7', 'a new time after an offer -> a new offer, the rest kept');
  r = await offer('client is Jem Lim', { history: [offerMsg], bf: { client: 'Jem Lim', clientPhrase: 'client is Jem Lim' } });
  ok(r.formOffer.offer && r.formOffer.prefill.c === 'Jem Lim' && r.formOffer.prefill.s === '14:00', 'a client after an offer -> added');
  r = await offer('thanks', { history: [offerMsg] });
  ok(!r.formOffer.offer && r.formOffer.why === 'nothing new after an offer', 'nothing new after an offer -> agent');
  r = await offer('is studio 8 free then?', { history: [offerMsg] });
  ok(!r.formOffer.offer, 'a question after an offer -> agent');
  r = await offer('thanks', { history: [{ ts: '99.5', bot_id: 'B1', text: 'Sure!' }, offerMsg] });
  ok(!r.formOffer.offer && r.formOffer.why === 'not a booking request', 'an offer that is not the newest message is not built on');
  r = await offer('book studio 8 friday 10-11', { dates: '2027-10-15', history: [offerMsg], bf: { timeInNewest: true, timeStart: '10:00', timeEnd: '11:00' } });
  ok(r.formOffer.prefill.r === 'Studio 8' && r.formOffer.prefill.d === '2027-10-15' && !r.formOffer.prefill.p, 'a new request after an offer starts over');

  // never throws
  const bad = (await run(main, 'Form Offer', [{ json: {} }], {}))[0].json;
  ok(bad.formOffer && bad.formOffer.offer === false && /^error/.test(bad.formOffer.why), 'never throws: on an error, the agent');

  // ---- Turn Log Row + wiring
  const tl = async (o) => (await run(main, 'Turn Log Row', [{ json: { message: { text: 'x' } } }], Object.assign({ 'Slack Trigger': [{ json: { text: 'x', ts: '1' } }] }, o)))[0].json;
  ok((await tl({ 'Send Form Offer': [{ json: { ok: true } }] })).Path === 'form offer' && (await tl({ 'Send Menu': [{ json: { ok: true } }] })).Path === 'menu'
     && (await tl({})).Path === 'agent', 'Turn Log: form offer / menu / agent');
  const C = main.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
  ok(nx('Already Done?') === 'Already Done Reply | Form Offer' && nx('Form Offer') === 'Form Offer?' && ['Send Form Offer | Early Room Plan', 'Send Form Offer | Change Offer'].indexOf(nx('Form Offer?')) !== -1
     && nx('Send Form Offer') === 'Turn Log Row+Clear Ack', 'wiring: Already Done? -> Form Offer -> Form Offer? (offer: Send Form Offer; else Early Room Plan)');
  const sfo = main.nodes.find(n => n.name === 'Send Form Offer');
  ok(sfo.credentials.slackApi.id === 'EcX8szEJrOLYLUfl' && /chat\.postMessage/.test(sfo.parameters.url), 'Send Form Offer posts with Jessie\'s Slack credential');

  // ---- Slack Interactions v9: step 1 from the button
  const sessionTypes = [{ id: 'st1', fields: { Type: 'VO Recording', Priority: ['r7', 'r8'], 'Last Resort': ['r4'] } }, { id: 'st2', fields: { Type: 'Meeting', Priority: ['rl'] } },
    { id: 'st3', fields: { Type: 'Music Mixing', Priority: ['rf'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];
  const step1 = async (value) => (await run(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache,
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'open_book', value }] } } }] }))[0].json.view;
  let v = await step1(JSON.stringify({ d: '2027-10-14', s: '14:00', e: '16:00', p: 'VO Recording', r: 'Studio 7', pj: 'ORANGE', c: 'Jem Lim', en: 'U1' }));
  const el = id => v.blocks.find(b => b.block_id === id).element;
  ok(el('date').initial_date === '2027-10-14', 'step 1: the date');
  ok(el('start').initial_option.value === '14:00' && el('start').options.includes(el('start').initial_option) && el('end').initial_option.value === '16:00', 'step 1: start and end chosen (one of the options)');
  ok(el('purpose').initial_option.value === 'VO Recording' && el('purpose').option_groups[0].options.some(o => o === el('purpose').initial_option), 'step 1: the session type chosen');
  ok(JSON.parse(v.private_metadata).pre.r === 'Studio 7', 'step 1 carries what was read');
  v = await step1(JSON.stringify({ s: '14:15', e: '15:45', p: '__booth' }));
  const o = el('start').options.map(x => x.value);
  ok(o.length === 50 && o.indexOf('14:15') === o.indexOf('14:00') + 1 && o.indexOf('15:45') === o.indexOf('15:30') + 1 && el('start').initial_option.text.text === '2:15 PM',
     'an off-half-hour time is added in its place');
  ok(el('purpose').initial_option.value === '__booth', 'M booth chosen');
  v = await step1('menu');
  ok(!el('start').initial_option && !el('purpose').initial_option && el('start').options.length === 48 && !JSON.parse(v.private_metadata).pre, "the menu's button: an empty form, as before");
  v = await step1(JSON.stringify({ d: 'tomorrow', s: '25:00', p: 'Nope' }));
  ok(/^\d{4}-\d{2}-\d{2}$/.test(el('date').initial_date) && el('date').initial_date !== 'tomorrow' && !el('start').initial_option && !el('purpose').initial_option, 'bad values are ignored');

  // step 1 read carries it; step 2 fills in
  const meta1 = { requester: 'U1', channel: 'D1', pre: { r: 'Studio 7', pj: 'ORANGE', c: 'Jem Lim', en: 'U2', ar: 'U4' } };
  const vals = { date: { date_pick: { selected_date: '2027-10-14' } }, start: { start_pick: { selected_option: { value: '14:00' } } },
    end: { end_pick: { selected_option: { value: '16:00' } } }, purpose: { purpose_pick: { selected_option: { value: 'VO Recording' } } } };
  const r1 = (await run(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: { private_metadata: JSON.stringify(meta1), state: { values: vals } } } } }] }))[0].json;
  ok(r1.valid && r1.s.pre.pj === 'ORANGE' && JSON.parse(r1.answer.view.private_metadata).pre.r === 'Studio 7', 'step 1 read: carried to step 2');
  const step2 = async (s, ra) => (await run(si, 'Build Step 2', [{ json: ra }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache }))[0].json.view;
  let v2 = await step2(r1.s, { status: 'OK', free_priority: ['Studio 8', 'Studio 7'], free_last_resort: ['Studio 4'], free_rooms: ['Studio 8', 'Studio 7', 'Studio 4'] });
  const b2 = id => v2.blocks.find(b => b.block_id === id);
  ok(b2('room').element.initial_option.value === 'Studio 7' && !/taken/.test(JSON.stringify(v2)), 'step 2: the room asked for, chosen (free)');
  ok(b2('project').element.initial_value === 'ORANGE' && b2('client').element.initial_value === 'Jem Lim' && b2('engineer').element.initial_option.value === 'U2'
     && b2('engineer').hint.text === 'As you typed it.', 'step 2: project, client, engineer filled in');
  v2 = await step2(r1.s, { status: 'OK', free_priority: ['Studio 8'], free_last_resort: ['Studio 4'], free_rooms: ['Studio 8', 'Studio 4'], busy: ['Studio 7 (GOLDFISH / X / HL)'] });
  ok(v2.blocks.some(b => b.text && b.text.text === '⚠️ Studio 7 is taken then. These are free:') && b2('room').element.initial_option.value === 'Studio 8', 'step 2: taken -> said, the free ones offered');
  v2 = await step2(Object.assign({}, r1.s, { pre: { r: 'Studio 4' } }), { status: 'OK', free_priority: ['Studio 8'], free_last_resort: ['Studio 4'], free_rooms: ['Studio 8', 'Studio 4'] });
  ok(b2('room').element.initial_option.value === 'Studio 4' && /not a usual room/.test(b2('room').element.initial_option.description.text), 'step 2: a free room that is not usual -> offered as such, chosen');
  v2 = await step2(Object.assign({}, r1.s, { pre: { r: 'Likha' } }), { status: 'OK', free_priority: ['Studio 8'], free_last_resort: [], free_rooms: ['Studio 8', 'Likha'] });
  ok(v2.blocks.some(b => b.text && b.text.text === '⚠️ Likha isn’t a room for VO Recording. These are free:'), 'step 2: free but not a room for this -> said');
  v2 = await step2(r1.s, { status: 'OK', free_priority: [], free_last_resort: [], free_rooms: [], busy: ['Studio 7 (GOLDFISH / X / HL)', 'Studio 8 (X)'] });
  ok(v2.blocks.some(b => b.text && b.text.text === '⚠️ Studio 7 is taken then.') && !v2.submit, 'step 2: nothing free -> taken said, no Book');
  v2 = await step2(Object.assign({}, r1.s, { purpose: 'Music Mixing', pre: { ar: 'U4', en: 'U9' } }), { status: 'OK', free_priority: ['Studio F'], free_last_resort: [] });
  ok(b2('arranger').element.initial_option.value === 'U4' && b2('engineer').element.initial_option.value === 'U1', 'step 2: arranger filled in; an engineer not on the list falls back to the requester');
  if (V10) {
    // v10: the note on the top room only; not-usual rooms remembered in the form
    v2 = await step2(Object.assign({}, r1.s, { pre: undefined }), { status: 'OK', free_priority: ['Studio 7', 'Studio 8', 'Studio F', 'Studio C'], free_last_resort: [] });
    const ro = b2('room').element.options;
    ok(ro[0].description.text === 'Recommended · usual for VO Recording' && ro.slice(1).every(o => !o.description), 'v10: only the top room has a note');
    ok(!JSON.parse(v2.private_metadata).nu, 'v10: usual rooms -> nothing remembered as not usual');
    v2 = await step2(Object.assign({}, r1.s, { pre: undefined }), { status: 'OK', free_priority: [], free_last_resort: ['Studio 4', 'Studio C'] });
    ok(/not a usual room/.test(b2('room').element.options[0].description.text) && !b2('room').element.options[1].description
       && JSON.parse(v2.private_metadata).nu.join() === 'Studio 4,Studio C', 'v10: not-usual rooms -> one note, all remembered');
    v2 = await step2(Object.assign({}, r1.s, { pre: { r: 'Studio 4' } }), { status: 'OK', free_priority: ['Studio 8'], free_last_resort: ['Studio 4'], free_rooms: ['Studio 8', 'Studio 4'] });
    ok(JSON.parse(v2.private_metadata).nu.join() === 'Studio 4', 'v10: the typed not-usual room remembered');
    // Read Step 2: a not-usual room picked from the list (no note on it) is booked as asked
    const cache3 = cache;
    const meta2 = Object.assign({}, r1.s, { when: 'Saturday, Oct 16 · 2:00 PM–4:00 PM', label: 'VO Recording', nu: ['Studio 4', 'Studio C'] });
    const sub = { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta2), blocks: [],
      state: { values: { room: { room_radio: { selected_option: { value: 'Studio C' } } }, project: { project_in: { value: 'X' } }, engineer: { engineer_pick: { selected_option: { value: 'U1' } } } } } } };
    const rd = (await run(si, 'Read Step 2', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: sub } }], 'Read Cache 3': cache3 }))[0].json;
    ok(rd.prep.room_override === true, 'v10: a not-usual room without a note on it -> booked as asked (room_override)');
    ok(/This takes a few seconds\.|Your booking is being processed\. You may close/.test(JSON.stringify(rd.answer.view)) && !/writing it to the calendar/.test(JSON.stringify(rd.answer.view)), 'v10: "This takes a few seconds."');
    // the note checkbox
    v2 = await step2(Object.assign({}, r1.s, { pre: undefined }), { status: 'OK', free_priority: ['Studio 7'], free_last_resort: [] });
    const nt = b2('note_toggle');
    if (JSON.stringify(si).indexOf('function typeRoles(') !== -1) ok(!nt && b2('notes') && b2('notes').optional, 'v24: the Note shown, no box');   // v24 (sim-round-7)
    else { ok(nt && nt.type === 'actions' && nt.elements[0].type === 'checkboxes' && nt.elements[0].options[0].text.text === 'Add a note' && !b2('notes'), 'v10: "Add a note" checkbox, no Notes field');
    const tog = async (checked, blocks, values) => (await run(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions',
      actions: [{ action_id: 'note_toggle', selected_options: checked ? [{ value: 'note' }] : [] }],
      view: { id: 'V9', hash: 'h1', callback_id: 'book_step2', title: v2.title, close: v2.close, submit: v2.submit, private_metadata: v2.private_metadata, blocks, state: { values } } } } }] }))[0].json;
    let tg = await tog(true, v2.blocks, { project: { project_in: { value: 'KIWI' } }, room: { room_radio: { selected_option: { value: 'Studio 7' } } } });
    const ti = tg.view.blocks.findIndex(b => b.block_id === 'note_toggle');
    ok(tg.ok && tg.view_id === 'V9' && tg.hash === 'h1' && tg.view.blocks[ti + 1].block_id === 'notes' && tg.view.blocks[ti + 1].optional
       && tg.view.blocks[ti].elements[0].initial_options.length === 1, 'v10: ticked -> the Note field under it, the box stays ticked');
    ok(tg.view.blocks.find(b => b.block_id === 'project').element.initial_value === 'KIWI' && tg.view.private_metadata === v2.private_metadata && tg.view.submit.text === 'Book',
       'v10: entries, metadata and Book kept');
    tg = await tog(false, tg.view.blocks, {});
    ok(!tg.view.blocks.some(b => b.block_id === 'notes') && !tg.view.blocks.find(b => b.block_id === 'note_toggle').elements[0].initial_options, 'v10: unticked -> the field goes'); }
    const ck = await run(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)),
      payload: { type: 'block_actions', actions: [{ action_id: 'note_toggle' }] } } }] });
    ok(ck[0].json.route === 8 && si.connections['Route'].main[8][0].node === 'Ack Note' && si.connections['Note Toggle'].main[0][0].node === 'Show Note', 'v10: route 8 -> Ack Note -> Note Toggle -> Show Note');
  }
  v2 = await step2(Object.assign({}, r1.s, { pre: undefined }), { status: 'OK', free_priority: ['Studio 8', 'Studio 7'], free_last_resort: [] });
  ok(b2('room').element.initial_option.value === 'Studio 8' && !b2('project').element.initial_value, 'no prefill: as v8');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
