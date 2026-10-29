#!/usr/bin/env node
// Slack Interactions v57 (29 Oct): How often? ticks its days under On - Weekly the first date's day, Weekdays Mon-Fri, Daily all
// seven - and step 1 books the days ticked (v13-v56 ignored the ticks for Weekdays / Daily: the form showed Fri, it booked Mon-Fri).
// Through the real Check Signature, Build Step 1, Note Toggle and Read Step 1.
// Usage: node scripts/sim-repeat-days.js [slack interactions]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v57.json', 'utf8'));
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
  const R = (id, name) => ({ id, fields: { 'Room Name': name } });
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({
    rooms: [R('r7', 'Studio 7')], sessionTypes: [{ id: 'st1', fields: { Type: 'Localization Dubbing', Priority: ['r7'] } }],
    bookers: [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Loc Engineer' } }] }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];

  // routes: picking How often goes to the toggles (route 8)
  const route = async (payload) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'rep_freq_pick' }] }) === 8, 'How often? picked -> the toggles (route 8)');

  // step 1, Repeats ticked (first date Fri Nov 12 2027)
  const s1 = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ value: 'menu' }] } } }] })).view;
  const vals = { date: { date_pick: { selected_date: '2027-11-12' } }, start: { start_pick: { selected_option: { value: '14:00' } } }, end: { end_pick: { selected_option: { value: '16:00' } } },
    purpose: { purpose_pick: { selected_option: { value: 'Localization Dubbing' } } } };
  const act = async (action, blocks, values) => (await j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [action],
    view: { id: 'V1', hash: 'h', callback_id: 'book_step1', title: s1.title, close: s1.close, submit: s1.submit, private_metadata: s1.private_metadata, blocks, state: { values } } } } }] })).view;
  let v = await act({ action_id: 'repeat_toggle', selected_options: [{ value: 'rep' }] }, s1.blocks, vals);
  const blk = (view, re) => view.blocks.find(b => re.test(b.block_id || ''));
  const ticks = view => ((blk(view, /^rep_days(~\d+)?$/).element.initial_options) || []).map(o => o.value).join();
  ok(blk(v, /^rep_freq$/).dispatch_action === true && blk(v, /^rep_freq$/).element.initial_option.value === 'weekly', 'How often? sends its pick at once; Weekly first');
  ok(ticks(v) === 'FR', 'Weekly: the first date\'s day ticked (Fri)');

  const pick = async (f, view) => act({ action_id: 'rep_freq_pick', selected_option: { value: f } }, view.blocks,
    Object.assign({}, vals, { repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } }, rep_freq: { rep_freq_pick: { selected_option: { value: f } } } },
      { [blk(view, /^rep_days(~\d+)?$/).block_id]: { rep_days_pick: { selected_options: [{ value: 'FR' }] } } }));
  const vw = await pick('weekdays', v);
  ok(ticks(vw) === 'MO,TU,WE,TH,FR', 'Weekdays -> Mon to Fri ticked (the screenshot: only Fri)');
  ok(/^rep_days~\d+$/.test(blk(vw, /^rep_days/).block_id), 'On redrawn under a new block_id, so Slack shows the new ticks (gotcha 47): ' + blk(vw, /^rep_days/).block_id);
  ok(blk(vw, /^rep_freq$/).element.initial_option.value === 'weekdays' && blk(vw, /^date$/).element.initial_date === '2027-11-12'
     && blk(vw, /^purpose$/).element.initial_option.value === 'Localization Dubbing' && blk(vw, /^repeat_toggle$/).elements[0].initial_options.length === 1, 'the rest of the form kept');
  const ids = vw.blocks.map(b => String(b.block_id).split('~')[0]);
  ok(ids.slice(ids.indexOf('repeat_toggle')).join() === 'repeat_toggle,rep_freq,rep_days,rep_count,rep_until,rep_note', 'On stays in its place');
  const vd = await pick('daily', vw);
  ok(ticks(vd) === 'MO,TU,WE,TH,FR,SA,SU' && blk(vd, /^rep_days/).block_id !== blk(vw, /^rep_days/).block_id, 'Daily -> all seven ticked, a new block_id again');
  const vk = await pick('weekly', vd);
  ok(ticks(vk) === 'FR', 'back to Weekly -> the first date\'s day');
  const vu = await act({ action_id: 'repeat_toggle', selected_options: [] }, vd.blocks, vals);
  ok(!vu.blocks.some(b => /^rep_/.test(b.block_id || '')), 'Repeats unticked -> a redrawn On goes too');
  const vn = await act({ action_id: 'note_toggle', selected_options: [] }, vw.blocks,
    Object.assign({}, vals, { [blk(vw, /^rep_days/).block_id]: { rep_days_pick: { selected_options: [{ value: 'MO' }, { value: 'WE' }] } } }));
  ok(ticks(vn) === 'MO,WE', 'another toggle after it keeps the person\'s own ticks');

  // step 1 read: the days ticked are the days booked
  const read1 = async (freq, days, key, count) => j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: {
    private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: Object.assign({}, vals, {
      repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } }, rep_freq: { rep_freq_pick: { selected_option: { value: freq } } },
      rep_count: { rep_count_pick: { selected_option: { value: String(count || 5) } } } },
      days ? { [key || 'rep_days~1730000000000']: { rep_days_pick: { selected_options: days.map(d => ({ value: d })) } } } : {}) } } } } }] });
  const DS = x => (x.s && x.s.series ? x.s.series.dates.join() : 'invalid ' + JSON.stringify((x.answer || {}).errors || ''));
  ok(DS(await read1('weekdays', ['MO', 'TU', 'WE', 'TH', 'FR'])) === '2027-11-12,2027-11-15,2027-11-16,2027-11-17,2027-11-18', 'Weekdays, Mon-Fri ticked: Fri, Mon, Tue, Wed, Thu');
  ok(DS(await read1('weekdays', ['MO', 'TU', 'TH', 'FR'])) === '2027-11-12,2027-11-15,2027-11-16,2027-11-18,2027-11-19', 'Weekdays with Wed unticked: no Wednesday');
  ok(DS(await read1('daily', ['MO', 'TU', 'WE', 'TH', 'FR', 'SA'], null, 7)) === '2027-11-12,2027-11-13,2027-11-15,2027-11-16,2027-11-17,2027-11-18,2027-11-19', 'Daily with Sun unticked: no Sunday');
  ok(DS(await read1('weekdays', null)) === '2027-11-12,2027-11-15,2027-11-16,2027-11-17,2027-11-18', 'Weekdays, nothing ticked: Mon-Fri (as before)');
  ok(DS(await read1('daily', null, null, 3)) === '2027-11-12,2027-11-13,2027-11-14', 'Daily, nothing ticked: every day (as before)');
  ok(DS(await read1('weekly', ['FR'], 'rep_days', 3)) === '2027-11-12,2027-11-19,2027-11-26', 'Weekly on Fri, the first-drawn block id: as before');
  ok(DS(await read1('weekly', ['TU', 'FR'], null, 4)) === '2027-11-12,2027-11-16,2027-11-19,2027-11-23', 'Weekly on Tue and Fri (redrawn block): as before');
  const e = await read1('weekly', [], 'rep_days~1730000000000');
  ok(!e.valid && e.answer.errors['rep_days~1730000000000'] === 'Pick at least one day.', 'Weekly, none ticked -> the error on the redrawn block');

  // a typed series ("every weekday") opens with Mon-Fri ticked
  const tb = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify({ d: '2027-11-12', s: '14:00', e: '16:00', rep: { f: 'weekdays', n: 5 } }) }] } } }] })).view;
  ok(tb.blocks.some(b => b.block_id === 'rep_days') && ticks(tb) === 'MO,TU,WE,TH,FR', 'a typed weekday series: Mon-Fri ticked - ' + ticks(tb));

  // only these nodes changed since v56
  const old = JSON.parse(fs.readFileSync('workflows/imported/slack-interactions-v56-imported.json', 'utf8'));
  const OB = Object.fromEntries(old.nodes.map(n => [n.name, JSON.stringify(n.parameters)]));
  const changed = si.nodes.filter(n => OB[n.name] !== JSON.stringify(n.parameters)).map(n => n.name).sort();
  ok(changed.join() === 'Build Step 1,Check Signature,Note Toggle,Read Step 1' && JSON.stringify(si.connections) === JSON.stringify(old.connections), 'only four nodes changed, wiring the same: ' + changed.join(', '));

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
