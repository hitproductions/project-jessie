#!/usr/bin/env node
// Series in the form, offline (Slack Interactions v13 + the live Book Series v8): the Repeats box (route 8), the dates
// worked out in step 1 (and every refusal), Room Availability once per date, step 2's "free on k of N dates", Book Series
// prepare -> the confirm screen ("Book N dates"), the stored series read back and checked, Book Series' own Expand Dates
// on what the form passes, and the result on the form / in the DM.
// Usage: node scripts/sim-series-form.js [slack interactions v13] [book series]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v17.json', 'utf8'));
const V15 = si.nodes.some(n => n.name === 'Read Cache 8'), V17 = si.nodes.some(n => n.name === 'Mark Cancelling');
const bs = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/imported/book-series-v8-imported.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

(async () => {
  const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
  const rooms = [R('r7', 'Studio 7'), R('r8', 'Studio 8'), R('rf', 'Studio F'), R('r4', 'Studio 4')];
  const sessionTypes = [{ id: 'st1', fields: { Type: 'Localization Dubbing', Priority: ['r7', 'r8', 'rf'], 'Last Resort': ['r4'] } }];
  const bookers = [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Loc Engineer', Authority: ['HAIST Dev'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];

  // ---- routes + the Repeats box
  const route = async (payload) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'repeat_toggle' }] }) === 8 && await route({ type: 'view_submission', view: { callback_id: 'series_confirm' } }) === 13, 'routes: Repeats 8, series confirm 13');
  const s1 = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ value: 'menu' }] } } }] })).view;
  const rt = s1.blocks.find(b => b.block_id === 'repeat_toggle');
  ok(rt && rt.type === 'actions' && rt.elements[0].options[0].text.text === 'Repeats' && s1.blocks[s1.blocks.length - 1] === rt, 'step 1: a small Repeats box under the rest');
  const tog = async (on, blocks, values) => j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions',
    actions: [{ action_id: 'repeat_toggle', selected_options: on ? [{ value: 'rep' }] : [] }],
    view: { id: 'V1', hash: 'h', callback_id: 'book_step1', title: s1.title, close: s1.close, submit: s1.submit, private_metadata: s1.private_metadata, blocks, state: { values } } } } }] });
  const vals1 = { date: { date_pick: { selected_date: '2027-10-19' } }, start: { start_pick: { selected_option: { value: '14:00' } } }, end: { end_pick: { selected_option: { value: '16:00' } } },
    purpose: { purpose_pick: { selected_option: { value: 'Localization Dubbing' } } } };
  let tg = await tog(true, s1.blocks, vals1);
  const ids = tg.view.blocks.map(b => b.block_id);
  ok(ids.slice(ids.indexOf('repeat_toggle')).join() === 'repeat_toggle,rep_freq,rep_days,rep_count,rep_until,rep_note' && tg.view.callback_id === 'book_step1' && tg.view.submit.text === 'Find rooms',
     'ticked -> How often, On, How many times, Or until under it; still step 1');
  const B = id => tg.view.blocks.find(b => b.block_id === id);
  ok(B('rep_days').element.initial_options.map(o => o.value).join() === 'TU' && B('rep_freq').element.initial_option.value === 'weekly', 'On: the first date\'s day (Tue) ticked; every week');
  ok(B('date').element.initial_date === '2027-10-19' && B('start').element.initial_option.value === '14:00' && B('purpose').element.initial_option.value === 'Localization Dubbing'
     && B('repeat_toggle').elements[0].initial_options.length === 1, 'entries kept; the box stays ticked');
  tg = await tog(false, tg.view.blocks, vals1);
  ok(!tg.view.blocks.some(b => /^rep_/.test(b.block_id || '')) && !B('repeat_toggle').elements[0].initial_options, 'unticked -> they go');

  // ---- step 1: the dates
  const read1 = async (rep) => {
    const v = Object.assign({}, vals1, rep ? Object.assign({ repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } } }, rep) : {});
    return j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: v } } } } }] });
  };
  const F = (freq, days, count, until) => Object.assign({ rep_freq: { rep_freq_pick: { selected_option: { value: freq } } } },
    days ? { rep_days: { rep_days_pick: { selected_options: days.map(d => ({ value: d })) } } } : {},
    count ? { rep_count: { rep_count_pick: { selected_option: { value: String(count) } } } } : {}, until ? { rep_until: { rep_until_pick: { selected_date: until } } } : {});
  let r1 = await read1(F('weekly', ['TU'], 4));
  ok(r1.valid && r1.s.series.dates.join() === '2027-10-19,2027-10-26,2027-11-02,2027-11-09' && /Checking 4 dates/.test(JSON.stringify(r1.answer.view)), 'every Tuesday, 4 times');
  ok((await read1(F('weekly', ['TU', 'TH'], 4))).s.series.dates.join() === '2027-10-19,2027-10-21,2027-10-26,2027-10-28', 'Tue and Thu, 4 times');
  ok((await read1(F('weekdays', null, null, '2027-10-25'))).s.series.dates.join() === '2027-10-19,2027-10-20,2027-10-21,2027-10-22,2027-10-25', 'every weekday until Mon Oct 25');
  ok((await read1(F('daily', null, 3))).s.series.dates.join() === '2027-10-19,2027-10-20,2027-10-21', 'every day, 3 times');
  ok(!(await read1()).s.series, 'Repeats not ticked -> one booking, as before');
  if (V15) {
    ok((await read1(F('weekly', ['TU'], 3, '2027-12-31'))).s.series.dates.length === 3, 'v15: both set -> How many times wins');
    ok((await read1(F('weekly', ['TU'], 3, '2027-10-10'))).valid, 'v15: an end date before the start is ignored when How many times is set');
    const tgu = await tog(true, s1.blocks, vals1);
    ok(tgu.view.blocks.find(b => b.block_id === 'rep_until').element.initial_date === '2027-11-16' && (V17 ? tgu.view.blocks.find(b => b.block_id === 'rep_until').hint.text === 'Only applies if "How many times" is empty.' : /How many times is empty/.test(tgu.view.blocks.find(b => b.block_id === 'rep_until').hint.text)),
       'v15: Or until starts 4 weeks after the first date (2027, not the real year), and says when it is used');
    const pur = s1.blocks.find(b => b.block_id === 'purpose');
    ok(pur.hint.text === 'A room will be recommended to you based on your session details.' && pur.element.option_groups.map(g => g.label.text).join() === 'Sessions,Other bookings', 'v15: step 1 wording');
  }
  const err = async (rep, bid, re) => { const x = await read1(rep); ok(!x.valid && x.answer.response_action === 'errors' && re.test(x.answer.errors[bid] || ''), bid + ': ' + JSON.stringify(x.answer.errors)); };
  await err(F('weekly', [], 4), 'rep_days', /at least one day/);
  await err(F('weekly', ['TU']), 'rep_count', /How many times/);
  await err(F('weekly', ['TU'], null, '2027-10-10'), 'rep_until', /after the first date/);
  await err(F('daily', null, null, '2027-12-31'), 'rep_until', /more than 16/);
  await err(F('weekly', ['TU'], null, '2027-10-20'), 'rep_until', /only one date/);

  // ---- Room Availability once per date; step 2
  r1 = await read1(F('weekly', ['TU'], 3));
  const ra = await run(si, 'To Room Availability', [], { 'Read Step 1': [{ json: r1 }], 'Read Cache 2': cache });
  ok(ra.length === 3 && ra.map(x => x.json.start_iso).join() === '2027-10-19T14:00:00+08:00,2027-10-26T14:00:00+08:00,2027-11-02T14:00:00+08:00', 'one Room Availability call per date');
  const step2 = async (answers, s) => j1(si, 'Build Step 2', answers.map(a => ({ json: a })), { 'Read Step 1': [{ json: { s: s || r1.s } }], 'Read Cache 2': cache });
  let s2 = await step2([{ status: 'OK', free_priority: ['Studio 7', 'Studio 8'], free_last_resort: ['Studio 4'] }, { status: 'OK', free_priority: ['Studio 8'], free_last_resort: ['Studio 4'] },
    { status: 'OK', free_priority: ['Studio 7', 'Studio 8', 'Studio F'], free_last_resort: ['Studio 4'] }]);
  const radio = s2.view.blocks.find(b => b.block_id === 'room').element;
  ok(radio.options.map(o => o.value).join() === 'Studio 8,Studio 7,Studio F', 'rooms free on more dates first: ' + radio.options.map(o => o.value).join());
  ok(radio.options[0].description.text === 'Recommended · usual for Localization Dubbing · free on all 3 dates' && radio.options[1].description.text === 'free on 2 of 3 dates'
     && radio.options[2].description.text === 'free on 1 of 3 dates', 'each says on how many dates it is free');
  ok(/🗓️ \*3 dates · 2:00 PM–4:00 PM · Localization Dubbing\*/.test(JSON.stringify(s2.view.blocks[1])) && s2.view.blocks[2].elements[0].text === 'Tue Oct 19 · Tue Oct 26 · Tue Nov 2'
     && s2.view.submit.text === 'Check 3 dates', 'header, the dates, "Check 3 dates"');
  s2 = await step2([{ status: 'OK', free_priority: ['Studio 7'] }, { status: 'CALENDAR_ERROR' }, { status: 'OK', free_priority: ['Studio 7'] }]);
  ok(!s2.view.submit && /could(?: not|n’t) be checked/.test(JSON.stringify(s2.view)) && !/CALENDAR_ERROR/.test(JSON.stringify(s2.view)), 'a date not checked -> no button, no code');
  s2 = await step2([{ status: 'OK', free_priority: ['Studio 7', 'Studio 8'] }], { date: '2027-10-19', t0: '14:00', t1: '16:00', purpose: 'Localization Dubbing', kind: 'loc', requester: 'U1', ext: 'x' });
  ok(s2.view.submit.text === 'Book' && !s2.view.blocks.find(b => b.block_id === 'room').element.options[1].description, 'a single booking: as v12');

  // ---- step 2 submitted: Book Series prepare
  const meta2 = Object.assign({}, r1.s, { when: 'x', label: 'Localization Dubbing' });
  const sub2 = { type: 'view_submission', view: { id: 'V2', private_metadata: JSON.stringify(meta2), blocks: [{ type: 'input', block_id: 'room', element: { type: 'radio_buttons', action_id: 'room_radio', options: [{ value: 'Studio 8' }] } }],
    state: { values: { room: { room_radio: { selected_option: { value: 'Studio 8' } } }, code: { code_in: { value: 'NFX-ABC-01' } }, engineer: { engineer_pick: { selected_option: { value: 'U1' } } } } } } };
  const r2 = await j1(si, 'Read Step 2', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: sub2 } }], 'Read Cache 3': cache });
  ok(r2.valid && /Checking 3 dates in Studio 8/.test(JSON.stringify(r2.answer.view)) && (V17 ? /Checking availability for each date\. This takes a few seconds\./.test(JSON.stringify(r2.answer.view)) : /Nothing is booked yet/.test(JSON.stringify(r2.answer.view))), 'Check: "Checking 3 dates…" at once');
  const tp = await j1(si, 'To Prepare', [], { 'Read Step 2': [{ json: r2 }], 'Read Cache 3': cache });
  const tps = await j1(si, 'To Prepare Series', [], { 'To Prepare': [{ json: tp }], 'Read Step 2': [{ json: r2 }] });
  ok(tps.mode === 'prepare' && tps.dates === '2027-10-19,2027-10-26,2027-11-02' && tps.time_start === '14:00' && tps.rooms === 'Studio 8' && tps.summary === 'NFX-ABC-01 / HL'
     && /ref: U1/.test(tps.description) && tps.confirmed === false, 'Book Series prepare inputs: the dates, the times, the booking');
  // Book Series' own Expand Dates on those inputs: the given dates, each as a prepare call
  const occ = await run(bs, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: tps }] });
  ok(occ.length === 3 && occ.every(o => o.json._go && o.json.mode === 'prepare' && o.json.rooms === 'Studio 8') && occ[1].json.start_iso === '2027-10-26T14:00:00+08:00', 'Book Series (live v8) expands exactly those dates');
  const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
  ok(nx('To Prepare') === 'Series?' && nx('Series?') === 'To Prepare Series | Prepare' && nx('Prepare Series') === 'After Prepare Series' && nx('After Prepare Series') === 'Show Series Step'
     && si.nodes.find(n => n.name === 'Prepare Series').parameters.workflowId.value === 'UAwFoifgkfL1xNP2', 'wiring: a series goes to Book Series');

  // prepared -> the confirm screen
  const PB_SALT = '4539361661025d1d';
  const pbHash = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
  const inputs = { summary: 'NFX-ABC-01 / HL', rooms: 'Studio 8', dates: '2027-10-19,2027-11-02', time_start: '14:00', time_end: '16:00', description: 'ref: U1', per_date: '{}' };
  const payload = { v: 1, kind: 'series', ref: 'U1', code: pbHash(PB_SALT + '|series-code|' + JSON.stringify(inputs)), inputs };
  const card = '*NFX-ABC-01 / HL*\n*Dates (2):*\n- Tuesday, 19 October 2027\n- Tuesday, 2 November 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n\n❌ Heads up: *Studio 8 is already booked on Tuesday, 26 October 2027* - no other usual room or time that day is free, so that date is left out.\n\nConfirm to book.';
  const prep = { status: 'PREPARED', card_text: card, title: 'NFX-ABC-01 / HL', dates: ['2027-10-19', '2027-11-02'], skipped: ['2027-10-26'], prep_key: 'prep-sabc', prep_payload: JSON.stringify(payload), prep_stored: true };
  const aps = async (res) => j1(si, 'After Prepare Series', [{ json: res }], { 'Read Step 2': [{ json: r2 }], 'Read Request': [{ json: { payload: sub2 } }] });
  let A = await aps(prep);
  ok(A.view_id === 'V2' && A.view.callback_id === 'series_confirm' && A.view.submit.text === 'Book 2 dates' && !/Confirm to book/.test(A.view.blocks[0].text.text)
     && /left out/.test(A.view.blocks[0].text.text) && JSON.parse(A.view.private_metadata).key === 'prep-sabc', 'the confirm screen: the dates, what was left out, "Book 2 dates"');
  A = await aps(Object.assign({}, prep, { prep_stored: false }));
  ok(JSON.parse(A.view.private_metadata).inputs.dates === '2027-10-19,2027-11-02' && A.view.submit, 'not stored -> the series rides on the form itself');
  A = await aps({ status: 'REJECTED', reason: 'CLIENT_CHECK', human: 'Nothing was prepared - "jem lin" is not in the client list, but it is close to Jem Lim. Ask the requester once…' });
  ok(A.view.callback_id === 'book_step2' && /Did you mean \*Jem Lim\*/.test(A.view.blocks[0].text.text), 'a question -> the step-2 form again (read from Book Series\' sentence)');

  // ---- confirmed: read back, checked, booked
  const confPay = m => ({ type: 'view_submission', view: { id: 'V3', private_metadata: JSON.stringify(m) } });
  const meta3 = { key: 'prep-sabc', n: 2, title: 'NFX-ABC-01 / HL', requester: 'U1', channel: 'D1', time: '14:00-16:00' };
  const rsc = await j1(si, 'Read Series Confirm', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: confPay(meta3) } }] });
  ok(rsc.key === 'prep-sabc' && rsc.answer.response_action === 'update' && /Booking 2 dates/.test(JSON.stringify(rsc.answer.view)) && (V17 ? /Processing your series of bookings\. This may take a while, so you can close this window for now\. You will be notified once finished\./.test(JSON.stringify(rsc.answer.view)) : /result comes to your DM/.test(JSON.stringify(rsc.answer.view))), '"Booking 2 dates…" at once');
  const tbs = async (rows, R) => j1(si, 'To Book Series', V15 ? cache : rows.map(x => ({ json: x })), { 'Read Series Confirm': [{ json: R || rsc }], 'Read Saved Series': rows.map(x => ({ json: x })), 'Read Cache 8': cache });
  let T = await tbs([{ cache_key: 'prep-sabc', payload: JSON.stringify(payload) }]);
  ok(T.go && T.confirmed === true && T.mode === '' && T.dates === '2027-10-19,2027-11-02' && T.rooms === 'Studio 8', 'the stored series, checked, booked as stored');
  const occB = await run(bs, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: T }] });
  ok(occB.length === 2 && occB.every(o => o.json.confirmed === true && o.json.series === true && o.json.mode === ''), 'Book Series (live v8) books exactly those 2 dates, confirmed');
  if (V15) {
    // v15 (Slack test): every date was refused NO_REFERENCE_DATA - Book Session must get the room list through Book Series
    const ref = (() => { try { return JSON.parse(occB[0].json.reference_data || 'null'); } catch (e) { return null; } })();
    ok(ref && ref.rooms.length === 4 && ref.types[0].type === 'Localization Dubbing' && ref.types[0].priority.join() === 'r7,r8,rf', 'v15: each date reaches Book Session with the room list (the NO_REFERENCE_DATA bug)');
    ok(JSON.parse(occB[0].json.staff_data)[0].Name === 'Howard Luistro' && occB[0].json.authority === 'HAIST Dev', 'v15: and the staff list and who is booking');
  }
  T = await tbs([{ cache_key: 'prep-sabc', payload: JSON.stringify(Object.assign({}, payload, { inputs: Object.assign({}, inputs, { dates: '2027-10-19,2027-10-26,2027-11-02' }) })) }]);
  ok(!T.go && /did not check out/.test(T.why), 'changed after it was shown -> nothing booked');
  T = await tbs([]);
  ok(!T.go && /not found/.test(T.why), 'not found -> nothing booked');
  T = await tbs([{ cache_key: 'prep-sabc', payload: JSON.stringify(payload) }], Object.assign({}, rsc, { user: 'U9' }));
  ok(!T.go && /someone else/.test(T.why), 'someone else\'s -> nothing booked');
  T = await tbs([], Object.assign({}, rsc, { meta: Object.assign({}, meta3, { key: '', inputs }) }));
  ok(T.go && T.dates === inputs.dates, 'carried on the form -> booked from there');
  ok(nx('Read Series Confirm') === 'Answer Series' && nx('Answer Series') === 'Read Saved Series' && nx('To Book Series') === 'Series Go?' && nx('Series Go?') === 'Book Series | After Book Series'
     && nx('Book Series') === 'After Book Series' && nx('Show Series Result') === 'DM Series', 'wiring: route 13');

  // ---- the result
  const abs = async (res, Tx) => j1(si, 'After Book Series', [{ json: res }], { 'Read Series Confirm': [{ json: Object.assign({}, rsc, { viewId: 'V3' }) }], 'To Book Series': [{ json: Tx || Object.assign({ go: true }, inputs) }] });
  let X = await abs({ status: 'BOOKED_SERIES', booked: ['2027-10-19', '2027-11-02'], skipped: [], failed: [] });
  ok(X.text === '✅ *Booked 2 dates.*\n\n*NFX-ABC-01 / HL*\n*Dates:*\n- Tue, Oct 19\n- Tue, Nov 2\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8' && X.view.close.text === 'Done' && X.channel === 'D1'
     && /My bookings/.test(JSON.stringify(X.blocks)), 'all booked -> the card, form and DM - ' + X.text.replace(/\n/g, ' | '));
  X = await abs({ status: 'BOOKED_SERIES', booked: ['2027-10-19'], skipped: ['2027-11-02'], failed: [] });
  ok(/Booked 1 of 2 dates/.test(X.text) && /Not booked - the room was taken: Tue, Nov 2/.test(X.text), 'part booked -> says which were not');
  X = await abs({ status: 'NONE_BOOKED', booked: [], skipped: ['2027-10-19', '2027-11-02'] });
  ok(/^❌ \*Nothing was booked\.\*/.test(X.text) && !/Change or cancel a date/.test(JSON.stringify(X.blocks)), 'none booked -> said (no "change or cancel" line)');
  if (V17) { const Xa = await abs({ status: 'BOOKED_SERIES', booked: ['2027-10-19'], skipped: [], failed: [] });
    const act = Xa.blocks.find(b => b.type === 'actions');
    ok(act && act.elements.map(e => e.action_id).join() === 'open_book,my_bookings' && !Xa.view.blocks.some(b => b.type === 'actions'), 'v17: the series DM has Book a room / My bookings (the form does not)'); }
  if (V15) {
    X = await abs({ status: 'NONE_BOOKED', booked: [], skipped: [], failed: [{ date: '2027-10-19', why: 'NO_REFERENCE_DATA' }, { date: '2027-10-26', why: 'NO_REFERENCE_DATA' }, { date: '2027-11-02', why: 'SOMETHING_ODD' }] });
    ok(!/[A-Z]{2,}_[A-Z]{2,}/.test(X.text) && /Tue, Oct 19, Tue, Oct 26 - the room list couldn’t be read/.test(X.text) && /Tue, Nov 2 - it couldn’t be booked/.test(X.text),
       'v15: the reason in words, never the code (live: NO_REFERENCE_DATA shown) - ' + X.text.replace(/\n/g, ' | '));
  }
  X = await abs({}, { go: false, why: 'the saved series was not found' });
  ok(/Nothing was booked\* - the saved series was not found/.test(X.text), 'not read back -> said, nothing booked');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
