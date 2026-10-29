#!/usr/bin/env node
// Slack Interactions v58 + Open Consent Request v13 (29 Oct):
//  1. a day ticked / unticked under On relabels How often (Mon-Fri Weekdays, all seven Daily, else Weekly), through the real Check
//     Signature, Note Toggle and Read Step 1 (How often redrawn as "rep_freq~<ms>");
//  2. the deadline the form shows ("Jessie will ask them ... by …") is the one Open Consent Request stores: the same function in
//     Build Step 2, Note Toggle and Build Request, all-day aware, worked out on the real-year date while YEAR_SHIFT is 1.
// Usage: node scripts/sim-ticks-deadlines.js [slack interactions] [open consent request]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v58.json', 'utf8'));
const oc = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/open-consent-request-v13.json', 'utf8'));
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

  // ---- 1. ticks -> How often
  const route = async (payload) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'rep_days_pick' }] }) === 8, 'a tick under On -> the toggles (route 8)');
  const s1 = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ value: 'menu' }] } } }] })).view;
  const vals = { date: { date_pick: { selected_date: '2027-11-12' } }, start: { start_pick: { selected_option: { value: '14:00' } } }, end: { end_pick: { selected_option: { value: '16:00' } } },
    purpose: { purpose_pick: { selected_option: { value: 'Localization Dubbing' } } } };
  const act = async (action, blocks, values) => (await j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [action],
    view: { id: 'V1', hash: 'h', callback_id: 'book_step1', title: s1.title, close: s1.close, submit: s1.submit, private_metadata: s1.private_metadata, blocks, state: { values } } } } }] })).view;
  const blk = (view, re) => view.blocks.find(b => re.test(b.block_id || ''));
  let v = await act({ action_id: 'repeat_toggle', selected_options: [{ value: 'rep' }] }, s1.blocks, vals);
  ok(blk(v, /^rep_days$/).dispatch_action === true, 'On sends each tick (dispatch_action)');
  const freqOf = view => blk(view, /^rep_freq(~\d+)?$/).element.initial_option.value;
  const state = (view, freq, days) => Object.assign({}, vals, { repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } },
    [blk(view, /^rep_freq(~\d+)?$/).block_id]: { rep_freq_pick: { selected_option: { value: freq } } },
    [blk(view, /^rep_days(~\d+)?$/).block_id]: { rep_days_pick: { selected_options: days.map(d => ({ value: d })) } } });
  const tick = async (view, freq, days) => act({ action_id: 'rep_days_pick', selected_options: days.map(d => ({ value: d })) }, view.blocks, state(view, freq, days));
  // Daily, then Tue / Thu / Sat / Sun unticked (the screenshot: Mon, Wed, Fri)
  const vd = await act({ action_id: 'rep_freq_pick', selected_option: { value: 'daily' } }, v.blocks, state(v, 'daily', ['FR']));
  ok(freqOf(vd) === 'daily', 'picked Daily');
  let vt = await tick(vd, 'daily', ['MO', 'WE', 'FR']);
  ok(freqOf(vt) === 'weekly' && /^rep_freq~\d+$/.test(blk(vt, /^rep_freq/).block_id), 'Daily, then only Mon / Wed / Fri ticked -> How often says Weekly (redrawn: ' + blk(vt, /^rep_freq/).block_id + ')');
  ok(!(blk(vt, /^rep_days(~\d+)?$/).element.initial_options || []).length || (blk(vt, /^rep_days(~\d+)?$/).element.initial_options || []).map(o => o.value).join() === 'MO,WE,FR',
     'the ticks stay as picked (Slack keeps them; nothing different drawn)');
  vt = await tick(vt, 'weekly', ['MO', 'TU', 'WE', 'TH', 'FR']);
  ok(freqOf(vt) === 'weekdays', 'Mon to Fri ticked -> Weekdays');
  const b1 = blk(vt, /^rep_freq/).block_id;
  vt = await tick(vt, 'weekdays', ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']);
  ok(freqOf(vt) === 'daily' && blk(vt, /^rep_freq/).block_id !== b1, 'all seven -> Daily (a new block_id again)');
  const b2 = blk(vt, /^rep_freq/).block_id;
  const vs = await tick(vt, 'daily', ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']);
  ok(freqOf(vs) === 'daily' && blk(vs, /^rep_freq/).block_id === b2, 'nothing changes -> How often is left alone (same block)');
  const v0 = await tick(vt, 'daily', []);
  ok(freqOf(v0) === 'weekly', 'nothing ticked -> Weekly (step 1 then asks for a day)');
  const vf = await act({ action_id: 'rep_freq_pick', selected_option: { value: 'weekdays' } }, vt.blocks, state(vt, 'weekdays', ['MO']));
  ok(freqOf(vf) === 'weekdays' && (blk(vf, /^rep_days/).element.initial_options || []).map(o => o.value).join() === 'MO,TU,WE,TH,FR', 'v57 still: Weekdays picked on a redrawn How often -> Mon-Fri ticked');
  const vu = await act({ action_id: 'repeat_toggle', selected_options: [] }, vt.blocks, vals);
  ok(!vu.blocks.some(b => /^rep_/.test(b.block_id || '')), 'Repeats unticked -> a redrawn How often goes too');
  // step 1 reads How often by its stem
  const r1 = await j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }),
    state: { values: Object.assign({}, vals, { repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } }, 'rep_freq~1730000000001': { rep_freq_pick: { selected_option: { value: 'weekly' } } },
      'rep_days~1730000000002': { rep_days_pick: { selected_options: [{ value: 'MO' }, { value: 'WE' }, { value: 'FR' }] } }, rep_count: { rep_count_pick: { selected_option: { value: '4' } } } }) } } } } }] });
  ok(r1.valid && r1.s.series && r1.s.series.dates.join() === '2027-11-12,2027-11-15,2027-11-17,2027-11-19', 'step 1 on a redrawn How often + On: Fri, Mon, Wed, Fri');

  // ---- 2. deadlines: one function, three places
  const fnOf = code => { const i = code.indexOf('const MNL_TZ'), c = code.indexOf('function computeDeadline'), j = code.indexOf('function requestDeadline');
    const cEnd = code.indexOf('\n', c), jEnd = code.indexOf('\n}\n', j) + 3;
    return new Function('Date', code.slice(c, cEnd) + '\n' + code.slice(i, jEnd) + '\nreturn requestDeadline;'); };
  const texts = ['Build Step 2', 'Note Toggle'].map(n => jsOf(si, n)).concat([jsOf(oc, 'Build Request')]);
  const blockOf = code => code.slice(code.indexOf('const MNL_TZ'), code.indexOf('\n}\n', code.indexOf('function requestDeadline')) + 3);
  ok(blockOf(texts[0]) === blockOf(texts[2]) && blockOf(texts[1]) === blockOf(texts[2]), 'the form\'s preview and the stored deadline use the same code');
  ok(texts.every(t => /const YEAR_SHIFT = 1;/.test(t)), 'each has the YEAR_SHIFT launch switch (1 while testing)');
  ok(['Build Step 2', 'Note Toggle'].every(n => jsOf(si, n).indexOf("new Date().toISOString(), start, !!m.allDay)") !== -1), 'the form passes all day');
  const rd = fnOf(texts[2])(Date);
  const D = (kind, now, start, allDay) => new Date(Date.parse(rd(kind, now, start, allDay)) + 8 * 3600e3).toISOString().slice(0, 16).replace('T', ' ');
  const Q = '2026-10-28T14:00:00+08:00';
  ok(D('MBOOTH', Q, '2027-10-28T00:00:00+08:00', true) === '2026-10-28 15:00', 'QA: M booth all day "today" -> 3:00 PM (1 h), was "tomorrow 2:00 PM" - ' + D('MBOOTH', Q, '2027-10-28T00:00:00+08:00', true));
  ok(D('MBOOTH', Q, '2027-10-29T00:00:00+08:00', true) === '2026-10-28 18:00', 'QA: all day tomorrow -> 6:00 PM today');
  ok(D('MBOOTH', Q, '2027-10-28T18:00:00+08:00', false) === '2026-10-28 17:00', 'QA: today 6-9 PM -> 5:00 PM (3 h)');
  ok(D('MBOOTH', Q, '2027-10-29T13:00:00+08:00', false) === '2026-10-29 10:00', 'QA: tomorrow 1-4 PM -> 10:00 AM tomorrow');
  ok(D('MBOOTH', Q, '2027-11-05T13:00:00+08:00', false) === '2026-10-29 14:00', 'QA: a week ahead -> 24 h');
  ok(D('PREEMPT', Q, '2027-10-28T16:00:00+08:00') === '2026-10-28 15:00', 'QA: a priority request today 4 PM -> 3:00 PM (start - 1 h)');
  ok(D('MBOOTH', Q, '2027-01-05T00:00:00+08:00', true) === '2026-10-29 14:00', 'QA: a 2027 date already past in the real year -> not shifted (24 h)');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
