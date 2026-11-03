#!/usr/bin/env node
// Slack Interactions v60 (3 Nov): repeats counted live. Every Repeats field and the first date redraw step 1 (no stale error), the
// line under Repeats says what it books ("Books 4 dates: Tue 2, Wed 3, Thu 4, Fri 5 Nov") or the problem; no pre-filled
// "Or until"; the chosen date is always the first booking, then the days ticked after it. Through the real Check Signature,
// Build Step 1, Note Toggle and Read Step 1.
// Usage: node scripts/sim-repeat-live.js [slack interactions]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v62.json', 'utf8'));
const VER = Number((String(si.name || '').match(/— v(\d+)/) || [])[1] || 0);   // v61: How many times / Or until / On re-keyed on every redraw
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => { const r = await run(...a); return r && r[0] ? r[0].json : null; };

(async () => {
  const R = (id, name) => ({ id, fields: { 'Room Name': name } });
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({
    rooms: [R('r1', 'Studio 1')], sessionTypes: [{ id: 'st1', fields: { Type: 'Localization Dubbing', Priority: ['r1'] } }],
    bookers: [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Loc Engineer' } }] }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];
  const route = async (action) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)),
    payload: { type: 'block_actions', actions: [{ action_id: action }] } } }] })).route;
  for (const a of ['rep_count_pick', 'rep_until_pick', 'date_pick', 'rep_freq_pick', 'rep_days_pick']) ok(await route(a) === 8, a + ' -> the toggles (route 8)');

  const s1 = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ value: 'menu' }] } } }] })).view;
  const blk = (view, re) => view.blocks.find(b => re.test(b.block_id || ''));
  ok(blk(s1, /^date$/).dispatch_action === true, 'the first date sends its pick (dispatch_action)');
  const act = async (action, blocks, values) => j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [action],
    view: { id: 'V1', hash: 'h', callback_id: 'book_step1', title: s1.title, close: s1.close, submit: s1.submit, private_metadata: s1.private_metadata, blocks, state: { values } } } } }] });
  const base = (d) => ({ date: { date_pick: { selected_date: d } }, start: { start_pick: { selected_option: { value: '10:00' } } }, end: { end_pick: { selected_option: { value: '18:00' } } },
    purpose: { purpose_pick: { selected_option: { value: 'Localization Dubbing' } } } });
  const note = view => blk(view, /^rep_note$/).elements[0].text;

  // Repeats ticked on Tue 2 Nov 2027: no pre-filled end date, both end fields send their pick, the line asks for an end
  let r = await act({ action_id: 'repeat_toggle', selected_options: [{ value: 'rep' }] }, s1.blocks, base('2027-11-02'));
  let v = r.view;
  ok(r.ok && !blk(v, /^rep_until(~\d+)?$/).element.initial_date, 'Or until is empty (no four-week default)');
  ok(blk(v, /^rep_count(~\d+)?$/).dispatch_action === true && blk(v, /^rep_until(~\d+)?$/).dispatch_action === true, 'How many times / Or until send their pick');
  ok(/Pick \*How many times\* or an end date/.test(note(v)), 'the line asks for a number or an end date: ' + note(v));

  // Howard's case: Weekdays, Mon-Fri ticked, Or until Fri 5 Nov -> Tue-Fri, 4 dates, no error on the redrawn form
  const state = (view, d, freq, days, extra) => { const st = Object.assign(base(d), { repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } },
    [blk(view, /^rep_freq(~\d+)?$/).block_id]: { rep_freq_pick: { selected_option: { value: freq } } },
    [blk(view, /^rep_days(~\d+)?$/).block_id]: { rep_days_pick: { selected_options: days.map(x => ({ value: x })) } } });
    for (const [k, val] of Object.entries(extra || {})) { const b = blk(view, new RegExp('^' + k + '(~\\d+)?$')); st[b ? b.block_id : k] = val; }   // Slack keys state by the drawn block_id
    return st; };
  const WD = ['MO', 'TU', 'WE', 'TH', 'FR'];
  r = await act({ action_id: 'rep_freq_pick', selected_option: { value: 'weekdays' } }, v.blocks, state(v, '2027-11-02', 'weekdays', ['TU']));
  v = r.view;
  r = await act({ action_id: 'rep_until_pick', selected_date: '2027-11-05' }, v.blocks, state(v, '2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } }));
  ok(r.ok && note(r.view) === '🔁 *Books 4 dates:* Tue 2, Wed 3, Thu 4, Fri 5 Nov', 'Nov 2 - 5, Weekdays: ' + note(r.view));
  ok(!('errors' in r) && !('errors' in r.view), 'a redraw carries no error (the old "more than 16" is gone)');
  ok(blk(r.view, /^rep_until(~\d+)?$/).element.initial_date === '2027-11-05', 'the picked end date kept');
  if (VER >= 61) {   // v61: new ids on every redraw, values kept, strictly increasing
    const ids = view => ['rep_count', 'rep_until', 'rep_days'].map(k => blk(view, new RegExp('^' + k + '(~\\d+)?$')).block_id);
    const a1 = ids(r.view);
    ok(a1.every(x => /~\d+$/.test(x)), 'v61: How many times / Or until / On redrawn under new ids: ' + a1.join(', '));
    const r2 = await act({ action_id: 'rep_until_pick', selected_date: '2027-11-05' }, r.view.blocks, state(r.view, '2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } }));
    const a2 = ids(r2.view);
    ok(r2.ok && a2.every((x, i) => Number(x.split('~')[1]) > Number(a1[i].split('~')[1])), 'v61: a second redraw at once gets newer ids still (an old error never reattaches)');
    ok(blk(r2.view, /^rep_until(~\d+)?$/).element.initial_date === '2027-11-05' && (blk(r2.view, /^rep_days(~\d+)?$/).element.initial_options || []).map(o => o.value).join() === 'MO,TU,WE,TH,FR', 'v61: values kept across re-keys');
  }
  v = r.view;
  if (VER >= 62) {   // v62: the pick arrives on the action only (the saved state does not have it yet) - kept on screen and counted
    const e0 = (await act({ action_id: 'repeat_toggle', selected_options: [{ value: 'rep' }] }, s1.blocks, base('2027-11-02'))).view;   // Or until still empty
    const e1 = (await act({ action_id: 'rep_freq_pick', selected_option: { value: 'weekdays' } }, e0.blocks, state(e0, '2027-11-02', 'weekdays', ['TU']))).view;
    ok(!blk(e1, /^rep_until(~\d+)?$/).element.initial_date, 'v62 setup: Or until empty before the pick');
    const r3 = await act({ action_id: 'rep_until_pick', selected_date: '2027-11-05' }, e1.blocks, state(e1, '2027-11-02', 'weekdays', WD));
    ok(blk(r3.view, /^rep_until(~\d+)?$/).element.initial_date === '2027-11-05' && note(r3.view) === '🔁 *Books 4 dates:* Tue 2, Wed 3, Thu 4, Fri 5 Nov', 'v62: an end date only on the action stays picked: ' + note(r3.view));
    const r4 = await act({ action_id: 'rep_count_pick', selected_option: { value: '3' } }, v.blocks, state(v, '2027-11-02', 'weekdays', WD));
    ok(((blk(r4.view, /^rep_count(~\d+)?$/).element.initial_option) || {}).value === '3' && note(r4.view) === '🔁 *Books 3 dates:* Tue 2, Wed 3, Thu 4 Nov', 'v62: How many times only on the action stays picked');
    const r5 = await act({ action_id: 'date_pick', selected_date: '2027-11-03' }, v.blocks, state(v, '2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } }));
    ok(blk(r5.view, /^date$/).element.initial_date === '2027-11-03' && note(r5.view) === '🔁 *Books 3 dates:* Wed 3, Thu 4, Fri 5 Nov', 'v62: a new first date only on the action counts');
  }
  // the end date moved out -> the line says it in words; back -> fine again
  r = await act({ action_id: 'rep_until_pick', selected_date: '2027-11-30' }, v.blocks, state(v, '2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-30' } } }));
  ok(note(r.view) === '⚠️ That’s 21 dates – the most is 16. Pick an earlier end date or a number.', 'too many, counted: ' + note(r.view));
  // the first date changed (2026 -> 2027 was the likely cause): redrawn with the new count
  r = await act({ action_id: 'date_pick', selected_date: '2027-11-03' }, v.blocks, state(v, '2027-11-03', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } }));
  ok(r.ok && note(r.view) === '🔁 *Books 3 dates:* Wed 3, Thu 4, Fri 5 Nov', 'a new first date re-counts: ' + note(r.view));
  r = await act({ action_id: 'date_pick', selected_date: '2026-11-02' }, v.blocks, state(v, '2026-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } }));
  ok(/That’s \d+ dates – the most is 16/.test(note(r.view)), 'first date a year before the end -> too many, said in the line');
  // How many times wins over the end date
  r = await act({ action_id: 'rep_count_pick', selected_option: { value: '3' } }, v.blocks, state(v, '2027-11-02', 'weekdays', WD,
    { rep_count: { rep_count_pick: { selected_option: { value: '3' } } }, rep_until: { rep_until_pick: { selected_date: '2027-11-30' } } }));
  ok(note(r.view) === '🔁 *Books 3 dates:* Tue 2, Wed 3, Thu 4 Nov', 'How many times wins: ' + note(r.view));
  // the chosen date is always the first booking: a Tuesday start with only Mon / Wed ticked
  r = await act({ action_id: 'rep_days_pick', selected_options: [{ value: 'MO' }, { value: 'WE' }] }, v.blocks, state(v, '2027-11-02', 'weekly', ['MO', 'WE'],
    { rep_count: { rep_count_pick: { selected_option: { value: '4' } } } }));
  ok(note(r.view) === '🔁 *Books 4 dates:* Tue 2, Wed 3, Mon 8, Wed 10 Nov', 'chosen date first, then the ticked days after it: ' + note(r.view));
  // more than 8 dates -> a range
  r = await act({ action_id: 'rep_count_pick', selected_option: { value: '12' } }, v.blocks, state(v, '2027-11-02', 'weekdays', WD, { rep_count: { rep_count_pick: { selected_option: { value: '12' } } } }));
  ok(note(r.view) === '🔁 *Books 12 dates:* Tue 2 Nov – Wed 17 Nov', 'a long series as a range: ' + note(r.view));
  // a new first date with Repeats off - no redraw
  const off = await run(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'date_pick', selected_date: '2027-11-03' }],
    view: { id: 'V1', hash: 'h', callback_id: 'book_step1', title: s1.title, close: s1.close, submit: s1.submit, private_metadata: s1.private_metadata, blocks: s1.blocks, state: { values: base('2027-11-03') } } } } }] });
  ok(Array.isArray(off) && off.length === 0, 'Repeats off: a new date redraws nothing');

  // step 1 read: the same rule
  const read1 = async (d, freq, days, extra) => j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: {
    private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: Object.assign(base(d), {
      repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } }, 'rep_freq~1': { rep_freq_pick: { selected_option: { value: freq } } },
      'rep_days~2': { rep_days_pick: { selected_options: days.map(x => ({ value: x })) } } }, extra) } } } } }] });
  const DS = x => (x.s && x.s.series ? x.s.series.dates.join() : 'invalid ' + JSON.stringify((x.answer || {}).errors || ''));
  ok(DS(await read1('2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-05' } } })) === '2027-11-02,2027-11-03,2027-11-04,2027-11-05', 'Find rooms: Nov 2 - 5 -> Tue-Fri');
  const e = await read1('2027-11-02', 'weekdays', WD, { rep_until: { rep_until_pick: { selected_date: '2027-11-30' } } });
  ok(!e.valid && e.answer.errors.rep_until === 'That’s 21 dates – the most is 16. Pick an earlier end date or a number.', 'Find rooms backstop says the count');
  ok(DS(await read1('2027-11-02', 'weekly', ['MO', 'WE'], { rep_count: { rep_count_pick: { selected_option: { value: '4' } } } })) === '2027-11-02,2027-11-03,2027-11-08,2027-11-10', 'Find rooms: chosen date first');
  ok(DS(await read1('2027-11-05', 'weekly', ['FR'], { rep_count: { rep_count_pick: { selected_option: { value: '3' } } } })) === '2027-11-05,2027-11-12,2027-11-19', 'a Friday start on Fridays: as before');
  ok(DS(await read1('2027-11-05', 'weekdays', WD, { rep_count: { rep_count_pick: { selected_option: { value: '5' } } } })) === '2027-11-05,2027-11-08,2027-11-09,2027-11-10,2027-11-11', 'Weekdays from a Friday: as before (Fri, Mon-Thu)');
  if (VER >= 61) {
    ok(DS(await read1('2027-11-02', 'weekdays', WD, { 'rep_until~1730000000009': { rep_until_pick: { selected_date: '2027-11-05' } } })) === '2027-11-02,2027-11-03,2027-11-04,2027-11-05', 'v61: Find rooms reads a re-keyed Or until');
    ok(DS(await read1('2027-11-02', 'weekdays', WD, { 'rep_count~1730000000008': { rep_count_pick: { selected_option: { value: '3' } } } })) === '2027-11-02,2027-11-03,2027-11-04', 'v61: Find rooms reads a re-keyed How many times');
    const e2 = await read1('2027-11-05', 'weekdays', WD, { 'rep_until~1730000000009': { rep_until_pick: { selected_date: '2027-11-03' } } });
    ok(!e2.valid && e2.answer.errors['rep_until~1730000000009'] === 'The end date has to be after the first date.' && !('rep_until' in e2.answer.errors), 'v61: the error lands on the field as drawn (rep_until~…)');
    const e3 = await read1('2027-11-02', 'weekdays', WD, { 'rep_count~1730000000008': {} });
    ok(!e3.valid && e3.answer.errors['rep_count~1730000000008'] === 'How many times - or pick an end date.', 'v61: nothing picked -> the error on the drawn How many times');
  }

  // the line and the check share one rule (same code in all three nodes)
  const fn = n => { const s = jsOf(si, n); const i = s.indexOf('function repSeries'); return s.slice(i, s.indexOf('function repNote', i)); };
  ok(fn('Build Step 1') === fn('Note Toggle') && fn('Note Toggle') === fn('Read Step 1'), 'one rule in Build Step 1, Note Toggle and Read Step 1');

  // only these nodes changed since v59, wiring the same
  const old = JSON.parse(fs.readFileSync(VER >= 62 ? 'workflows/imported/slack-interactions-v61-imported.json' : VER >= 61 ? 'workflows/imported/slack-interactions-v60-imported.json' : 'workflows/imported/slack-interactions-v59-imported.json', 'utf8'));
  const OB = Object.fromEntries(old.nodes.map(n => [n.name, JSON.stringify(n.parameters)]));
  const changed = si.nodes.filter(n => OB[n.name] !== JSON.stringify(n.parameters)).map(n => n.name).sort();
  ok(changed.join() === (VER >= 62 ? 'Note Toggle' : VER >= 61 ? 'Note Toggle,Read Step 1' : 'Build Step 1,Check Signature,Note Toggle,Read Step 1') && JSON.stringify(si.connections) === JSON.stringify(old.connections), 'only this build\'s nodes changed, wiring the same: ' + changed.join(', '));

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
