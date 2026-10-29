#!/usr/bin/env node
// Slack Interactions v56 (29 Oct): All day + Repeats - an M booth (or an Event) held all day on several dates. Through the real
// nodes: step 1 takes it (v21-v55 refused it), Room Availability once per date over the whole day, To Prepare Series passes
// all_day, Book Series' own Expand Dates makes each date the same 12:00 AM - 12:00 AM event a single all-day booking makes,
// the confirm meta says all day, and the Booking… message and the result say "All day". A timed series is unchanged.
// Usage: node scripts/sim-allday-series.js [slack interactions] [book series]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v56.json', 'utf8'));
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
  const rooms = [R('m1', 'M1', { 'Room Type': ['Recording Booth'] }), R('m2', 'M2', { 'Room Type': ['Recording Booth'] }), R('lk', 'Likha', { 'Room Type': ['Conference Room'] }),
    R('r7', 'Studio 7'), R('r8', 'Studio 8')];
  const sessionTypes = [{ id: 'st1', fields: { Type: 'Localization Dubbing', Priority: ['r7', 'r8'] } }];
  const bookers = [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Loc Engineer', Authority: ['HAIST Dev'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];
  const rep = (freq, days, count) => Object.assign({ repeat_toggle: { repeat_toggle: { selected_options: [{ value: 'rep' }] } }, rep_freq: { rep_freq_pick: { selected_option: { value: freq } } } },
    days ? { rep_days: { rep_days_pick: { selected_options: days.map(d => ({ value: d })) } } } : {}, count ? { rep_count: { rep_count_pick: { selected_option: { value: String(count) } } } } : {});
  const read1 = async (purpose, allDay, repV, times) => j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: {
    private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: Object.assign({ date: { date_pick: { selected_date: '2027-11-08' } },
      purpose: { purpose_pick: { selected_option: { value: purpose } } } },
      allDay ? { allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } } } : {},
      times ? { start: { start_pick: { selected_option: { value: times[0] } } }, end: { end_pick: { selected_option: { value: times[1] } } } } : {},
      repV || {}) } } } } }] });

  // ---- step 1: the screenshot (M booth, All day, Repeats weekly on Mon)
  let r1 = await read1('__booth', true, rep('weekly', ['MO'], 4));
  ok(r1.valid && r1.s.allDay === true && r1.s.series && r1.s.series.dates.join() === '2027-11-08,2027-11-15,2027-11-22,2027-11-29',
     'M booth all day + weekly Mon x4 -> accepted, 4 dates (v55: "All day books one date") - ' + JSON.stringify((r1.answer || {}).errors || ''));
  ok(!/All day books one date/.test(JSON.stringify(r1)), 'the old refusal is gone');
  ok(r1.s.t0 === '00:00' && r1.s.t1 === '23:59', 'times: the whole day, as a single all-day booking');
  const ev = await read1('Event', true, rep('daily', null, 3));
  ok(ev.valid && ev.s.allDay && ev.s.series.dates.length === 3, 'an Event all day, every day x3 -> accepted');
  const one = await read1('__booth', true);
  ok(one.valid && one.s.allDay && !one.s.series, 'All day without Repeats: one date, as before');
  const timed = await read1('Localization Dubbing', false, rep('weekly', ['MO'], 3), ['14:00', '16:00']);
  ok(timed.valid && !timed.s.allDay && timed.s.series.dates.length === 3 && timed.s.t0 === '14:00', 'a timed series: as before');
  const bad = await read1('__booth', true, rep('weekly', [], 4));
  ok(!bad.valid && /at least one day/.test(JSON.stringify(bad.answer.errors)), 'the series checks still run with All day (no day picked)');

  // ---- Room Availability: once per date, the whole day
  const ra = await run(si, 'To Room Availability', [], { 'Read Step 1': [{ json: r1 }], 'Read Cache 2': cache });
  ok(ra.length === 4 && ra.every((x, i) => x.json.start_iso === r1.s.series.dates[i] + 'T00:00:00+08:00' && x.json.end_iso === r1.s.series.dates[i] + 'T23:59:00+08:00'),
     'one Room Availability call per date, 12:00 AM - 11:59 PM');

  // ---- step 2 submitted -> To Prepare Series (fed as Read Step 2 / To Prepare would hand it)
  const T0 = { summary: 'M1 - Howard', rooms: 'M1', session_type: '', client: '', engineer: '', description: 'Booked by: Howard Luistro | ref: U1',
    bookingType: '', department: '', reference_data: '{}', requester_text: 'M booth', asked_text: '', staff_data: '[]', authority: 'HAIST Dev', room_override: false };
  const R2 = s => ({ s, viewId: 'V2', channel: 'D1', rooms: 'M1' });
  const tps = await j1(si, 'To Prepare Series', [], { 'To Prepare': [{ json: T0 }], 'Read Step 2': [{ json: R2(r1.s) }] });
  ok(tps.all_day === true && tps.time_start === '' && tps.time_end === '' && tps.dates === r1.s.series.dates.join(','), 'To Prepare Series: all_day, no times (v55: all_day false, 00:00-23:59)');
  const tpt = await j1(si, 'To Prepare Series', [], { 'To Prepare': [{ json: T0 }], 'Read Step 2': [{ json: R2(timed.s) }] });
  ok(tpt.all_day === false && tpt.time_start === '14:00' && tpt.time_end === '16:00', 'a timed series: times, not all day');

  // ---- Book Series (live v8) Expand Dates: prepare, then book from the stored inputs
  const occ = await run(bs, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: tps }] });
  ok(occ.length === 4 && occ.every((o, i) => o.json._go !== false && o.json.all_day === true && o.json.mode === 'prepare'
     && o.json.start_iso === r1.s.series.dates[i] + 'T00:00:00+08:00' && o.json.end_iso === new Date(Date.parse(r1.s.series.dates[i] + 'T12:00:00Z') + 86400000).toISOString().slice(0, 10) + 'T00:00:00+08:00'),
     'Book Series prepares each date as 12:00 AM - 12:00 AM next day, all day - ' + JSON.stringify(occ.map(o => [o.json.start_iso, o.json.end_iso, o.json.all_day])));
  // the single all-day booking from the form, for comparison (Read Step 2's prepare: start 00:00, end the next day 00:00, all_day)
  const rs2 = jsOf(si, 'Read Step 2');
  ok(/end_iso: s\.allDay \? new Date\(Date\.parse\(s\.date \+ 'T12:00:00Z'\) \+ 86400000\)/.test(rs2) && /all_day: !!s\.allDay/.test(rs2), 'the same event shape as a single all-day booking');
  const stored = { summary: 'M1 - Howard', rooms: 'M1', dates: r1.s.series.dates.join(','), all_day: true, time_start: '', time_end: '', confirmed: true, mode: '', per_date: '{}', description: 'ref: U1' };
  const occB = await run(bs, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: stored }] });
  ok(occB.length === 4 && occB.every(o => o.json.all_day === true && o.json.series === true && /T00:00:00\+08:00$/.test(o.json.start_iso) && o.json.mode === ''), 'booking from the stored series: 4 all-day dates, confirmed');

  // ---- the confirm meta, the Booking… message, the result
  const PB_SALT = '4539361661025d1d';
  const pbHash = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
  const payload = { v: 1, kind: 'series', ref: 'U1', code: pbHash(PB_SALT + '|series-code|' + JSON.stringify(stored)), inputs: stored };
  const card = '*M1 - Howard*\n*Dates (4):*\n- Monday, 8 November 2027\n- Monday, 15 November 2027\n- Monday, 22 November 2027\n- Monday, 29 November 2027\n*Time:* All day\n*Room:* M1\n\nConfirm to book.';
  const prep = { status: 'PREPARED', card_text: card, title: 'M1 - Howard', dates: r1.s.series.dates, skipped: [], prep_key: 'prep-m1', prep_payload: JSON.stringify(payload), prep_stored: true };
  const sub2 = { type: 'view_submission', view: { id: 'V2', private_metadata: JSON.stringify(r1.s), blocks: [], state: { values: {} } } };
  const aps = async (s) => j1(si, 'After Prepare Series', [{ json: prep }], { 'Read Step 2': [{ json: Object.assign(R2(s), { s: Object.assign({ requester: 'U1' }, s) }) }], 'Read Request': [{ json: { payload: sub2 } }] });
  const A = await aps(r1.s);
  const meta = JSON.parse(A.view.private_metadata);
  ok(meta.ad === 1 && meta.time === '' && A.view.submit.text === 'Book 4 dates' && /\*Time:\* All day/.test(JSON.stringify(A.view)), 'confirm screen: "Time: All day", meta all day, no time');
  const At = await aps(timed.s);
  ok(JSON.parse(At.view.private_metadata).time === '14:00-16:00' && !JSON.parse(At.view.private_metadata).ad, 'a timed series: meta time as before');

  const rsc = { key: 'prep-m1', meta: Object.assign({}, meta, { channel: 'D1', msg: { ts: '1.2', text: 'x' } }), user: 'U1', viewId: 'V3' };
  const abs = async (rs) => j1(si, 'After Book Series', [{ json: { status: 'BOOKED_SERIES', booked: r1.s.series.dates, skipped: [], failed: [] } }],
    { 'Read Series Confirm': [{ json: rs }], 'To Book Series': [{ json: Object.assign({ go: true }, stored) }] });
  const X = await abs(rsc);
  ok(/✅ \*Booked 4 dates\.\*/.test(X.text) && /\n\*Time:\* All day\n/.test(X.text) && !/12:00 AM|11:59 PM/.test(X.text), 'the result: "Time: All day" - ' + X.text.replace(/\n/g, ' | '));
  const Xt = await abs(Object.assign({}, rsc, { meta: Object.assign({}, rsc.meta, { ad: 0, time: '14:00-16:00' }) }));
  ok(/\*Time:\* 2:00 PM – 4:00 PM/.test(Xt.text), 'a timed series result: as before');

  const msrc = async (m) => { try { return await j1(si, 'Mark Source Series', [{ json: { ok: true, messages: [{ ts: '1.2', text: 'x', blocks: [] }] } }], { 'Read Series Confirm': [{ json: Object.assign({}, rsc, { meta: m }) }] }); } catch (e) { return { err: e.message }; } };
  const M1 = await msrc(rsc.meta), Mt = await msrc(Object.assign({}, rsc.meta, { ad: 0, time: '14:00-16:00' }));
  ok(/All day/.test(JSON.stringify(M1)) && !/12:00 AM/.test(JSON.stringify(M1)), 'the Booking… message: "4 dates · All day" - ' + JSON.stringify(M1).slice(0, 300));
  ok(/2:00 PM – 4:00 PM/.test(JSON.stringify(Mt)), 'a timed series Booking… message: as before');

  // ---- only these five nodes changed since v55
  const old = JSON.parse(fs.readFileSync('workflows/imported/slack-interactions-v55-imported.json', 'utf8'));
  const OB = Object.fromEntries(old.nodes.map(n => [n.name, JSON.stringify(n.parameters)]));
  const changed = si.nodes.filter(n => OB[n.name] !== JSON.stringify(n.parameters)).map(n => n.name).sort();
  const V56N = ['After Book Series', 'After Prepare Series', 'Mark Source Series', 'Read Step 1', 'To Prepare Series'], V57N = ['Build Step 1', 'Check Signature', 'Note Toggle'];   // v57: How often ticks its days (sim-repeat-days)
  ok(V56N.every(n => changed.indexOf(n) !== -1) && changed.every(n => V56N.indexOf(n) !== -1 || V57N.indexOf(n) !== -1) && si.nodes.length === old.nodes.length
     && JSON.stringify(si.connections) === JSON.stringify(old.connections), 'only the v56 nodes (and v57\'s) changed, wiring the same: ' + changed.join(', '));

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
