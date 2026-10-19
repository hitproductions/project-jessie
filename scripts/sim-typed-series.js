#!/usr/bin/env node
// Typed series -> the form, offline (main v268 + Slack Interactions v14): Form Offer reads the pattern (how often, the days,
// how many times or until when, the first date) into the reply and the button; step 1 opens with Repeats ticked and filled
// in; Read Step 1 turns that into the dates.
// Usage: node scripts/sim-typed-series.js [main v268] [slack interactions v14]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v269.json', 'utf8'));
const V275 = /Hi, I’m Jessie!/.test(JSON.stringify(main.nodes));   // main v275: short menu lines, "Your booking details so far:"
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v17.json', 'utf8'));
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
  const rooms = [{ fields: { 'Room Name': 'Studio 7' } }, { fields: { 'Room Name': 'Likha', 'Room Type': ['Conference Room'] } }];
  const TYPES = ['VO Recording', 'Localization Dubbing', 'Meeting'];
  const offer = async (text, dates, bf) => (await j1(main, 'Form Offer', [{ json: {} }], {
    'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': TYPES.map(t => ({ json: { fields: { Type: t } } })), 'All Bookers': [],
    'Slack Trigger': [{ json: { text, channel: 'D1', ts: '1' } }],
    'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-15', confirmed: false, gate: {} } }],   // Fri 15 Oct 2027
    'Booked For': [{ json: Object.assign({ requesterText: text }, bf || {}) }], 'Get Recent Messages': [] })).formOffer;
  const tm = { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' };

  let F = await offer('book studio 7 every monday 2-4pm for 4 weeks', '2027-10-18', tm);
  ok(F.offer && JSON.stringify(F.prefill.rep) === '{"f":"weekly","days":["MO"],"n":4}' && F.prefill.d === '2027-10-18' && F.prefill.r === 'Studio 7',
     'every Monday, 4 weeks: weekly MO, 4 times, from Mon Oct 18 - ' + JSON.stringify(F.prefill));
  ok(F.text === (V275 ? 'Your booking details so far:' : 'Here’s what I have so far:') + '\n🗓️ *Studio 7 · from Monday, October 18 · 2:00 PM – 4:00 PM*\n🔁 Every Monday · 4 times', 'the reply shows the pattern - ' + F.text.replace(/\n/g, ' | '));
  ok(JSON.parse(F.blocks[1].elements[0].value).rep.n === 4, 'the button carries it');
  F = await offer('book studio 7 every monday 2-4pm for 4 weeks', '', tm);
  ok(F.prefill.d === '2027-10-18', 'no date named: the next Monday after today');
  F = await offer('book a dubbing session every weekday until nov 30', '2027-11-30');
  ok(JSON.stringify(F.prefill.rep) === '{"f":"weekdays","u":"2027-11-30"}' && F.prefill.d === '2027-10-18' && F.prefill.p === 'Localization Dubbing'
     && /🔁 Every weekday · until Tuesday, November 30/.test(F.text), 'every weekday until Nov 30: from the next weekday (Mon Oct 18)');
  F = await offer('book likha every tuesday and thursday 10-11am, 6 times', '2027-10-19', { timeInNewest: true, timeStart: '10:00', timeEnd: '11:00' });
  ok(JSON.stringify(F.prefill.rep) === '{"f":"weekly","days":["TU","TH"],"n":6}' && F.prefill.p === 'Meeting' && /Every Tuesday and Thursday · 6 times/.test(F.text), 'Tue and Thu, 6 times');
  F = await offer('book studio 7 daily from oct 20 until oct 29', '2027-10-20,2027-10-29');
  ok(F.prefill.rep.f === 'daily' && F.prefill.d === '2027-10-20' && F.prefill.rep.u === '2027-10-29', 'daily from a date until a date');
  F = await offer('book studio 7 mondays 2-4pm, 3 sessions', '', tm);
  ok(F.prefill.rep.days.join() === 'MO' && F.prefill.rep.n === 3, '"mondays" counts as every Monday');
  F = await offer('book studio 7 every friday until friday nov 26', '2027-11-26');
  ok(F.prefill.rep.days.join() === 'FR' && F.prefill.rep.u === '2027-11-26' && F.prefill.d === '2027-10-22', 'a day named after "until" is the end, not another day');
  if (/v269/.test(main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode)) {
    // v269 (live 14:55): Gate resolved only "thursday" (Oct 21) - the series starts on the first named day after today
    F = await offer('book likha every tuesday and thursday 10-11am, 4 times', '2027-10-21', { timeInNewest: true, timeStart: '10:00', timeEnd: '11:00' });
    ok(F.prefill.d === '2027-10-19' && /from Tuesday, October 19/.test(F.text), 'v269: Tue and Thu -> from Tue Oct 19 (live 14:55 said Thu Oct 21)');
    F = await offer('book studio 7 every monday starting oct 25 2-4pm, 3 times', '2027-10-25', tm);
    ok(F.prefill.d === '2027-10-25', 'v269: a typed calendar date is still the start');
    F = await offer('book studio 7 every friday until friday nov 26', '2027-11-26');
    ok(F.prefill.d === '2027-10-22' && F.prefill.rep.u === '2027-11-26', 'v269: until a date - from the next Friday');
    ok(F.blocks[1].elements.map(e => e.action_id).join() === 'open_book,my_bookings', 'v269: My bookings beside Book a room');
  }
  F = await offer('book studio 7 tomorrow 2-4pm', '2027-10-16', tm);
  ok(!F.prefill.rep && F.prefill.d === '2027-10-16', 'a single booking: no pattern, as before');
  F = await offer('book studio 7 every monday for 40 weeks', '2027-10-18');
  ok(F.prefill.rep && !F.prefill.rep.n, 'more than 16: left for the form to ask');

  // ---- Slack Interactions v14: step 1 filled in
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: [], sessionTypes: TYPES.map(t => ({ fields: { Type: t } })), bookers: [] }) } }];
  const step1 = async (pre) => (await j1(si, 'Build Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }], 'Read Cache': cache,
    'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: pre ? JSON.stringify(pre) : 'menu' }] } } }] })).view;
  let V = await step1({ d: '2027-10-18', s: '14:00', e: '16:00', r: 'Studio 7', rep: { f: 'weekly', days: ['MO', 'WE'], n: 4 } });
  const B = id => V.blocks.find(b => b.block_id === id);
  ok(B('repeat_toggle').elements[0].initial_options.length === 1 && B('rep_freq').element.initial_option.value === 'weekly'
     && B('rep_days').element.initial_options.map(o => o.value).join() === 'MO,WE' && B('rep_count').element.initial_option.value === '4' && B('rep_until').element.initial_date === '2027-11-15',
     'step 1: Repeats ticked - every week, Mon and Wed, 4 times (Or until starts 4 weeks out, in 2027)');
  V = await step1({ d: '2027-10-18', rep: { f: 'weekdays', u: '2027-11-30' } });
  ok(B('rep_freq').element.initial_option.value === 'weekdays' && B('rep_until').element.initial_date === '2027-11-30' && !B('rep_count').element.initial_option, 'every weekday until Nov 30');
  V = await step1({ d: '2027-10-18' });
  ok(!B('rep_freq') && !B('repeat_toggle').elements[0].initial_options, 'no pattern: Repeats not ticked');
  V = await step1(null);
  ok(!B('rep_freq'), "the menu's button: as before");
  // the ticked box still builds the same fields
  const t = await j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'repeat_toggle', selected_options: [{ value: 'rep' }] }],
    view: { id: 'V', callback_id: 'book_step1', title: V.title, close: V.close, submit: V.submit, blocks: V.blocks, state: { values: { date: { date_pick: { selected_date: '2027-10-21' } } } } } } } }] });
  ok(t.view.blocks.find(b => b.block_id === 'rep_days').element.initial_options.map(o => o.value).join() === 'TH', 'ticking the box: the first date\'s day (Thu)');

  // step 1 read: the filled-in pattern gives the dates
  V = await step1({ d: '2027-10-18', s: '14:00', e: '16:00', p: 'VO Recording', r: 'Studio 7', rep: { f: 'weekly', days: ['MO'], n: 4 } });
  const vals = { date: { date_pick: { selected_date: '2027-10-18' } }, start: { start_pick: { selected_option: { value: '14:00' } } }, end: { end_pick: { selected_option: { value: '16:00' } } },
    purpose: { purpose_pick: { selected_option: { value: 'VO Recording' } } }, repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } },
    rep_freq: { rep_freq_pick: { selected_option: B('rep_freq').element.initial_option } }, rep_days: { rep_days_pick: { selected_options: B('rep_days').element.initial_options } },
    rep_count: { rep_count_pick: { selected_option: B('rep_count').element.initial_option } } };
  const r1 = await j1(si, 'Read Step 1', [], { 'Check Signature': [{ json: { user: 'U1', channel: 'D1' } }], 'Read Request': [{ json: { payload: { view: { private_metadata: V.private_metadata, state: { values: vals } } } } }] });
  ok(r1.valid && r1.s.series.dates.join() === '2027-10-18,2027-10-25,2027-11-01,2027-11-08' && r1.s.pre.r === 'Studio 7', 'Find rooms: the 4 Mondays; the room asked for carried to step 2');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
