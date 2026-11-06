#!/usr/bin/env node
// The Localization coordinator's first week (3 Nov) - main v289, Slack Interactions v64, Book Session v126, through the real nodes:
// "book studio 1 and a" -> the form opens with Studio 1 and Studio A (booths to Vocal booths, other studios to + Multiple studios);
// "my bookings for november next year" / "nov 2027"; the My bookings headline and Jump to a date; the "Picked:" line under a
// multi-select; no "You can close this window" while dates or rooms are checked; Studio E as a booth (and still Post Processing's room).
//   node scripts/sim-loc-feedback.js [main v289] [slack-interactions v64] [book-session v126]
const fs = require('fs');
const W = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const MAIN = W(process.argv[2] || 'workflows/project-jessie-v289.json');
const SI = W(process.argv[3] || 'workflows/slack-interactions-v64.json');
const BS = W(process.argv[4] || 'workflows/book-session-v126.json');
const has = (wf, s) => JSON.stringify(wf.nodes).indexOf(s) !== -1;
const M289 = has(MAIN, 'v289 (Localization, 3 Nov'), S64 = has(SI, 'v64 (Localization, 3 Nov)'), B126 = has(BS, 'v126 (4 Nov)');
if (!M289 && !S64 && !B126) { console.log('0 ok, 0 failed (older builds: main v289 / SI v64 / Book Session v126 not in them)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const run = async (wf, name, input, O) => new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n})();')($f(O), { first: () => input[0], all: () => input });
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
// Rooms as in Airtable since 3 Nov: Studio E is a vocal booth
const rooms = JSON.parse(JSON.stringify(FX.rooms));
rooms.find(r => r.fields['Room Name'] === 'Studio E').fields['Vocal Booth'] = true;
const STAFF = FX.bookers.map(b => b.fields);
const opt = n => ({ text: { type: 'plain_text', text: n }, value: n });

(async () => {
  if (M289) {
    console.log('main v289: rooms typed in one message');
    const bfOuts = text => ({ 'Slack Trigger': [{ json: { text, user: 'U1', ts: '100.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '100.1', text, user: 'U1' } }],
      'Gate Context': [{ json: { epoch: '', gate: {} } }], 'Get Booker': [{ json: { fields: STAFF[0] } }], 'All Bookers': STAFF.map(f => ({ json: { fields: f } })),
      'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': FX.sessionTypes.map(t => ({ json: t })) });
    const bookedFor = text => new Function('$', '$input', jsOf(MAIN, 'Booked For'))($f(bfOuts(text)), { first: () => ({ json: {} }) })[0].json;
    const offer = async text => { const O = bfOuts(text), bf = bookedFor(text);
      Object.assign(O, { 'Booked For': [{ json: bf }], 'Gate Context': [{ json: { datesInMessage: '2026-11-05', confirmed: false, gate: {}, todayIso: '2026-11-04' } }], 'Get Recent Messages': [] });
      return (await j1(MAIN, 'Form Offer', [{ json: { keep: 1 } }], O)).formOffer; };
    for (const [q, want] of [['book studio 1 and a tomorrow 2-4pm', 'Studio 1, Studio A'], ['book studio 1 and a', 'Studio 1, Studio A'], ['studio 1 and a please', 'Studio 1, Studio A'],
      ['studio 7, 8 and a on friday', 'Studio 7, Studio 8, Studio A'], ['book studio 2 and e tomorrow', 'Studio 2, Studio E'], ['studios 1 and a, 3-5pm', 'Studio 1, Studio A']])
      ok(bookedFor(q).askedRooms === want, JSON.stringify(q) + ' -> ' + want, bookedFor(q).askedRooms);
    for (const q of ['is studio 7 and a vocal booth free tomorrow?', 'book studio 7 and a booth', 'studio 7 and a half hours'])
      ok(bookedFor(q).askedRooms === '', JSON.stringify(q) + ' -> "a" is a word (no list)', bookedFor(q).askedRooms);
    let F = await offer('book studio 1 and a tomorrow 2-4pm');
    ok(F.prefill.r === 'Studio 1' && F.prefill.bo === 'Studio A' && !F.prefill.mr, 'Studio 1 + Studio A -> the room Studio 1, Vocal booths Studio A', F.prefill);
    ok(/🗓️ \*Studio 1 \+ Studio A\*/.test(F.text), 'the offer shows both rooms', F.text);
    F = await offer('book studio 1, 2 and a tomorrow 2-4pm');
    ok(F.prefill.r === 'Studio 1' && F.prefill.mr === 'Studio 2' && F.prefill.bo === 'Studio A', 'Studio 1, 2 and A -> room 1, + Multiple studios 2, booth A', F.prefill);
    F = await offer('book studio a and 1 tomorrow 2-4pm');
    ok(F.prefill.r === 'Studio 1' && F.prefill.bo === 'Studio A', 'a booth typed first -> still the booth (Studio 1 is the room)', F.prefill);
    F = await offer('book studio 2 and e tomorrow 2-4pm for dubbing');
    ok(F.prefill.r === 'Studio 2' && F.prefill.bo === 'Studio E' && F.prefill.p !== 'Post Processing', 'Studio 2 + Studio E -> E is the booth, not Post Processing', F.prefill);
    F = await offer('book studio e tomorrow 2-4pm');
    ok(F.prefill.r === 'Studio E' && F.prefill.p === 'Post Processing', 'Studio E alone -> Post Processing, as before', F.prefill);
    for (const [l, k, room] of [['b', 'bo', 'Studio B'], ['c', 'mr', 'Studio C'], ['d', 'bo', 'Studio D'], ['e', 'bo', 'Studio E'], ['f', 'mr', 'Studio F']]) {
      const G = await offer('book studio 1 and ' + l); ok(G.prefill.r === 'Studio 1' && G.prefill[k] === room, '"book studio 1 and ' + l + '" -> Studio 1 + ' + room + (k === 'bo' ? ' (booth)' : ' (+ Multiple studios)'), G.prefill); }
    if (has(MAIN, 'v290 (Howard, 4 Nov)')) {   // main v290: Studio M is only for Van Recording - said, not dropped silently
      rooms.push({ id: 'rm', fields: { 'Room Name': 'Studio M' } });
      let G = await offer('book studio 1 and m tomorrow 2-4pm');
      ok(G.prefill.r === 'Studio 1' && !G.prefill.mr && !G.prefill.bo && /⚠️ Studio M is only for Van Recording, so it’s left off\./.test(G.text), '"studio 1 and m" -> Studio 1, and the offer says Studio M is only for Van Recording', G);
      G = await offer('book studio m and 1 tomorrow 2-4pm');
      ok(G.prefill.r === 'Studio 1' && /Studio M is only for Van Recording/.test(G.text), '"studio m and 1" -> the same (Studio M typed first)', G.prefill);
      G = await offer('book studio m and studio 1 for van recording tomorrow 2-4pm');
      ok(G.prefill.r === 'Studio M' && !G.prefill.mr && /Van Recording is in Studio M only/.test(G.text), 'Van Recording with another room -> Studio M only, said', G);
      G = await offer('book studio m tomorrow 2-4pm');
      ok(G.prefill.r === 'Studio M' && G.prefill.p === 'Van Recording' && !/⚠️/.test(G.text), 'Studio M alone -> Van Recording, no note (as before)', G);
      G = await offer('book studio 1 and b tomorrow 2-4pm');
      ok(!/⚠️/.test(G.text), 'no Studio M -> no note');
      rooms.pop();
    }
    F = await offer('book studio 1 or a tomorrow 2-4pm');
    ok(!F.prefill.r && !F.prefill.bo, '"studio 1 or a" -> a choice, left to the form (as before)', F.prefill);
    F = await offer('book studio 7 tomorrow 2-4pm');
    ok(F.prefill.r === 'Studio 7' && !F.prefill.bo && !F.prefill.mr, 'one room -> as before', F.prefill);

    console.log('main v289: My bookings far ahead');
    const mine = async (text, today) => (await j1(MAIN, 'Mine Check', [{ json: {} }], { 'Gate Context': [{ json: { todayIso: today || '2026-11-04', gate: {}, datesInMessage: '' } }],
      'Slack Trigger': [{ json: { text, channel: 'D1', user: 'U1' } }] })).mineCheck;
    let mc = await mine('what are my bookings for november next year');
    ok(mc.go && mc.start === '2027-11-01' && mc.end === '2027-12-01', '"november next year" -> Nov 2027', mc);
    mc = await mine('my bookings nov 2027');
    ok(mc.go && mc.start === '2027-11-01' && mc.end === '2027-12-01', '"nov 2027" -> Nov 2027 (was a single day or nothing)', mc);
    mc = await mine('what do i have in november, 2027?');
    ok(mc.start === '2027-11-01', '"november, 2027" -> Nov 2027', mc);
    mc = await mine('what do I have in november?');
    ok(mc.start === '2026-11-04' && mc.end === '2026-12-01', '"in november" -> the rest of this November (as before)', mc);
    mc = await mine('my bookings in march');
    ok(mc.start === '2027-03-01', '"march" -> next March (as before)', mc);
    mc = await mine('my bookings nov 4');
    ok(mc.start === '2026-11-04' || mc.week === true, '"nov 4" is a date, not the month (as before)', mc);
    // Howard's Slack test, 4 Nov 3:56 PM: "show me bookings i made on december 2027" reached the AI (a list in words, no buttons)
    for (const [q, st] of [['show me bookings i made on december 2027', '2027-12-01'], ['bookings i made in december', '2026-12-01'], ['what bookings do i have in december 2027', '2027-12-01'],
      ['sessions i booked next month', '2026-12-01'], ['what have i booked for december', '2026-12-01'], ['bookings ive made', '2026-11-04'], ['bookings under my name', '2026-11-04'],
      ['list everything i booked', '2026-11-04'], ['what sessions am i in this week', '2026-11-04'], ['what are my reservations', '2026-11-04'], ['bookings ko sa december', '2026-12-01']]) {
      const m = await mine(q); ok(m.go && m.start === st, JSON.stringify(q) + ' -> my bookings from ' + st, m); }
    for (const q of ['is studio 7 free tomorrow', 'cancel my booking tomorrow', 'book studio 1 and b', 'what rooms have symphony', 'is anything free tomorrow'])
      ok(!(await mine(q)).go, JSON.stringify(q) + ' -> not my bookings');
    mc = await mine('what are my bookings for november next year');
    const mr = await j1(MAIN, 'Mine Reply', [{ json: { items: [{ id: 'a', summary: 'KUBA / HL', start: { dateTime: '2027-11-10T13:00:00+08:00' }, end: { dateTime: '2027-11-10T15:00:00+08:00' }, description: 'ref: U1' }] } }],
      { 'Mine Check': [{ json: { mineCheck: Object.assign({}, mc, { channel: 'D1', user: 'U1' }) } }] });
    ok(mr.blocks[0].text.text === '🗓️ *Your bookings:*\n*Nov 1 – Nov 30, 2027*', 'headline: "🗓️ *Your bookings:*" then the dates (the year: not this year)', mr.blocks[0].text.text);
    ok(mr.blocks.some(b => b.block_id === 'bka_a'), 'each booking with Change / Cancel', mr.blocks.map(b => b.block_id));
    const nav = mr.blocks.find(b => b.block_id === 'my_nav');
    ok(nav && nav.elements.map(e => e.action_id).join() === 'my_page_jump' && nav.elements[0].type === 'datepicker' && nav.elements[0].initial_date === '2027-11-01', 'a month: Jump to a date (no Previous / Next)', nav);
    const wk = await j1(MAIN, 'Mine Reply', [{ json: { items: [] } }], { 'Mine Check': [{ json: { mineCheck: Object.assign(await mine('my bookings'), { channel: 'D1', user: 'U1' }) } }] });
    ok(wk.blocks[0].text.text === '🗓️ *Your bookings:*\n*Nov 4 – Nov 10*' && wk.blocks.find(b => b.block_id === 'my_nav').elements.map(e => e.action_id).join() === 'my_page_prev,my_page_next,my_page_jump',
      'a week: "*Nov 4 – Nov 10*" (this year: no year), Previous / Next / Jump to a date', wk.blocks[0].text.text);
  }

  if (S64) {
    console.log('Slack Interactions v64: the Picked: line');
    const cs = jsOf(SI, 'Check Signature');
    ok(['booth_pick', 'more_rooms_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick', 'more_c_pick'].every(a => cs.indexOf("'" + a + "'") !== -1), 'Check Signature sends the six multi-selects to Note Toggle');
    const blocks = [{ type: 'actions', block_id: 'room', elements: [{ type: 'radio_buttons', action_id: 'room_radio', options: ['Studio 1'].map(opt) }] },
      { type: 'input', dispatch_action: true, block_id: 'booth~12', optional: true, label: { type: 'plain_text', text: 'Vocal booths' }, element: { type: 'multi_static_select', action_id: 'booth_pick', options: ['Studio A', 'Studio B', 'Studio E'].map(opt) } },
      { type: 'input', block_id: 'project', label: { type: 'plain_text', text: 'Project title' }, element: { type: 'plain_text_input', action_id: 'project_in' } }];
    const nt = async (sel, bl, st) => j1(SI, 'Note Toggle', [{ json: {} }], { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'booth_pick', type: 'multi_static_select', selected_options: sel.map(opt) }],
      view: { id: 'V1', hash: 'h1', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Back' }, submit: { type: 'plain_text', text: 'Book' },
        private_metadata: '{}', blocks: bl || blocks, state: { values: st || {} } } } } }] });
    let r = await nt(['Studio A', 'Studio E']);
    const ids = r.view.blocks.map(b => b.block_id);
    ok(r.ok && r.view_id === 'V1' && ids.join() === 'room,booth~12,booth_picked,project', 'two booths picked -> the same form, "Picked:" under Vocal booths', ids);
    ok(r.view.blocks[2].elements[0].text === 'Picked: Studio A, Studio E' && r.view.submit.text === 'Book' && r.view.callback_id === 'book_step2', '"Picked: Studio A, Studio E"; the Book button and the form kept');
    ok(JSON.stringify(r.view.blocks[1]) === JSON.stringify(blocks[1]), 'the field itself untouched (same block_id - Slack keeps the picks)');
    r = await nt(['Studio A'], r.view.blocks);
    ok(r.view.blocks.map(b => b.block_id).join() === 'room,booth~12,project', 'down to one pick -> the line goes (one pick shows its name)', r.view.blocks.map(b => b.block_id));
    r = await nt(['Studio A', 'Studio B', 'Studio E'], JSON.parse(JSON.stringify(blocks)).concat([{ type: 'context', block_id: 'more_rooms_picked', elements: [{ type: 'mrkdwn', text: 'Picked: X, Y' }] }]));
    ok(!r.view.blocks.some(b => b.block_id === 'more_rooms_picked') && /Studio A, Studio B, Studio E/.test(JSON.stringify(r.view.blocks)), 'a stale line with no field above it is dropped');

    console.log('Slack Interactions v64: step 2 drawn with picks - the line, dispatch_action');
    const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes: FX.sessionTypes, bookers: FX.bookers }) } }];
    const step2 = async (s, ra) => (await j1(SI, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] })).view;
    const FREE = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio F', 'Studio C', 'Studio A', 'Studio B', 'Studio D', 'Studio E', 'Likha', 'Katha', 'Salin'];
    const S = { date: '2026-11-05', t0: '13:00', t1: '16:00', kind: 'loc', purpose: 'Localization Dubbing', requester: 'U1', when: 'x' };
    let v = await step2(Object.assign({}, S, { pre: { r: 'Studio 1', bo: 'Studio A,Studio E' } }), { free_priority: ['Studio 1', 'Studio 2'], free_rooms: FREE });
    const bb = v.blocks.find(b => /^booth/.test(b.block_id || '') && b.type === 'input');
    ok(bb && bb.dispatch_action === true && (bb.element.initial_options || []).map(o => o.value).join() === 'Studio A,Studio E', 'Localization Dubbing in Studio 1: Studio A + Studio E picked as booths (E is a booth now)', bb);
    const bi = v.blocks.indexOf(bb);
    ok(v.blocks[bi + 1] && v.blocks[bi + 1].block_id === 'booth_picked' && v.blocks[bi + 1].elements[0].text === 'Picked: Studio A, Studio E', 'drawn with two picks -> the line is there from the start', v.blocks[bi + 1]);
    if (has(SI, 'v65 (Howard')) {   // v65: Howard's Slack test 4 Nov - Studio 1 + Studio A both held by an 11 AM - 5 PM booking
      const FREE2 = FREE.filter(n => n !== 'Studio 1' && n !== 'Studio A' && n !== 'Studio 2');
      const note = v => (v.blocks.find(b => b.block_id === 'pre_note') || { text: {} }).text.text;
      let w = await step2(Object.assign({}, S, { pre: { r: 'Studio 1', bo: 'Studio A' } }), { free_priority: ['Studio 6'], free_rooms: FREE2, busy: ['Studio 1 (NRT-BONJOUR6)', 'Studio A (NRT-BONJOUR6)', 'Studio 2 (X)'] });
      ok(note(w) === '⚠️ Studio 1 and Studio A are taken then. These are free:', 'room and booth taken -> "Studio 1 and Studio A are taken then. These are free:"', note(w));
      w = await step2(Object.assign({}, S, { pre: { r: 'Studio 1', bo: 'Studio A,Studio B' } }), { free_priority: ['Studio 1'], free_rooms: FREE.filter(n => n !== 'Studio A'), busy: ['Studio A (X)'] });
      ok(note(w) === '⚠️ Studio A is taken then.' && /"value":"Studio 1"/.test(JSON.stringify(w.blocks)), 'room free, one booth taken -> "Studio A is taken then." (no "These are free:")', note(w));
      w = await step2(Object.assign({}, S, { pre: { r: 'Studio 1', bo: 'Studio A' } }), { free_priority: ['Studio 1'], free_rooms: FREE });
      ok(!note(w), 'everything free -> no line (as before)', note(w));
      w = await step2(Object.assign({}, S, { pre: { r: 'Studio 1' } }), { free_priority: ['Studio 6'], free_rooms: FREE2, busy: ['Studio 1 (X)'] });
      ok(note(w) === '⚠️ Studio 1 is taken then. These are free:', 'one room taken -> as before', note(w));
    }
    const mrb = v.blocks.find(b => b.block_id === 'more_rooms');
    if (/v74 \(Howard\): not people/.test(JSON.stringify(SI.nodes))) ok(!mrb || (!mrb.dispatch_action && !v.blocks.some(b => b.block_id === 'more_rooms_picked')), 'v74: + Multiple studios - no "Picked:" line, no dispatch');
    else ok(!mrb || mrb.dispatch_action === true, '+ Multiple studios sends its changes too');
    const ro = v.blocks.find(b => b.block_id && /^room/.test(b.block_id) && b.elements);
    ok(!ro || !JSON.stringify(ro).includes('"Studio E"'), 'Studio E is not offered as the room for Localization Dubbing', ro);
    v = await step2({ date: '2026-11-05', t0: '13:00', t1: '16:00', kind: 'post', purpose: 'Post Processing', requester: 'U1', when: 'x' }, { free_priority: ['Studio E'], free_rooms: FREE });
    ok(/"value":"Studio E"/.test(JSON.stringify(v.blocks.filter(b => b.block_id && /^room/.test(b.block_id)))), 'Post Processing: Studio E still its room (a booth for everything else)', v.blocks.map(b => b.block_id));
    ok(jsOf(SI, 'Build Change').indexOf("!(/^studio e$/i.test(n) && /^post processing$/i.test(String(T0 || '')))") !== -1, 'Change: Studio E is a studio for Post Processing');

    console.log('Slack Interactions v64: My bookings');
    const mw = await j1(SI, 'My Window', [{ json: {} }], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Request': [{ json: { payload: { actions: [{ action_id: 'my_page_jump', type: 'datepicker', selected_date: '2027-11-15' }], container: { channel_id: 'D1', message_ts: '5.5' } } } }] });
    ok(mw.page && mw.start === '2027-11-15' && mw.end === '2027-11-22', 'Jump to a date -> that date, 7 days', mw);
    const rmb = await j1(SI, 'Render My Bookings', [{ json: { items: [] } }], { 'My Window': [{ json: Object.assign({}, mw, { channel: 'D1' }) }], 'Read Cache 5': cache, 'Read Cache': cache, 'Read Cache 4': cache, 'Read Cache 6': cache });
    ok(rmb.blocks[0].text.text === '🗓️ *Your bookings:*\n*Nov 15 – Nov 21, 2027*', 'headline "🗓️ *Your bookings:*" then "*Nov 15 – Nov 21, 2027*"', rmb.blocks[0].text.text);
    const n2 = rmb.blocks.find(b => b.block_id === 'my_nav');
    ok(n2.elements.map(e => e.action_id).join() === 'my_page_prev,my_page_next,my_page_jump' && n2.elements[2].initial_date === '2027-11-15', 'Previous / Next 7 days / Jump to a date');

    console.log('Slack Interactions v64: when the window can be closed');
    ok(/Keep this window open(?: – the dates show here)?\./.test(jsOf(SI, 'Read Step 2')) && !/Checking availability for each date\. ' \+ _wait \+ ' You can close/.test(jsOf(SI, 'Read Step 2')), 'checking the dates of a series: keep it open (closing lost the check)');
    ok(/Keep this window open(?: – the free rooms show here)?\./.test(jsOf(SI, 'Read Step 1')), 'finding free rooms: keep it open');
    ok(/_wait \+ ' You can close this window – we’ll let you know in your DM once it’s done\.'/.test(jsOf(SI, 'Read Step 2')) && /You can close this window/.test(jsOf(SI, 'Read Series Confirm')) && /You can close this window/.test(jsOf(SI, 'Read Change')),
      'booking, booking a series and Change still say it (each has a DM)');
  }

  if (B126) {
    console.log('Book Session v126: Studio E as a booth');
    const CC = jsOf(BS, 'Check Conflicts');
    const cc = REQ => { const outs = { 'When Executed by Another Workflow': [Object.assign({ staff_data: JSON.stringify(STAFF) }, REQ)], 'Get Events In Window': [{ items: [] }], 'All Bookers': STAFF.map(f => ({ fields: f })),
        'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
      const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
      return new Function('$', '$input', CC)($, { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json; };
    const refRooms = rooms.map(r => ({ id: r.id, name: r.fields['Room Name'], vocalBooth: r.fields['Vocal Booth'] === true, booth: r.fields['Vocal Booth'] === true || [].concat(r.fields['Room Type'] || []).indexOf('Recording Booth') !== -1 }));
    const refTypes = FX.sessionTypes.map(t => ({ type: t.fields.Type, priority: [].concat(t.fields.Priority || []), lastResort: [].concat(t.fields['Last Resort'] || []) }));
    const REQ = (st, r) => ({ confirmed: true, mode: 'book', session_type: st, rooms: r, summary: 'NET-KUBA / HL', start_iso: '2026-11-05T13:00:00+08:00', end_iso: '2026-11-05T15:00:00+08:00',
      booker_name: 'Howard Luistro', booker_id: 'U1', engineer: 'Howard Luistro', department: 'Localization', room_override: true, reference_data: JSON.stringify({ rooms: refRooms, types: refTypes }) });
    let c = cc(REQ('Localization Dubbing', 'Studio 1, Studio E'));
    ok(!(c.reason === 'ROOM_UNSUITABLE' && /Studio E/.test(c.human || '')), 'Studio 1 + Studio E (Localization Dubbing) -> not refused for Studio E', { v: c.verdict, r: c.reason, h: c.human });
    c = cc(REQ('Localization Dubbing', 'Studio E'));
    ok(c.reason === 'ROOM_UNSUITABLE' && /Studio E is only for Post Processing/.test(c.human || ''), 'Studio E as the room (not Post Processing) -> still refused', { v: c.verdict, r: c.reason, h: c.human });
    c = cc(REQ('Post Processing', 'Studio E'));
    ok(!(c.reason === 'ROOM_UNSUITABLE' && /Studio E/.test(c.human || '')), 'Post Processing in Studio E -> as before', { v: c.verdict, r: c.reason });
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
