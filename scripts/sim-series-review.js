#!/usr/bin/env node
// PENDING 150 (4 Nov, Howard's "C"): a series from the review screen to the DM, through the real nodes - Room Availability v26's
// span answer, Book Series v9's prepare (Span Input, First Date, Aggregate; Book Session's prepare answer stubbed), Slack
// Interactions v66's review screen, the picks, To Book Series, Book Series' book-mode dates, and the result DM with Find another time.
//   node scripts/sim-series-review.js [slack-interactions v66] [book-series v9] [room-availability v26]
const fs = require('fs');
const load = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const SI = load(process.argv[2], 'workflows/slack-interactions-v66.json'), BSR = load(process.argv[3], 'workflows/book-series-v9.json'), RA = load(process.argv[4], 'workflows/room-availability-v26.json');
if (!SI.nodes.some(n => n.name === 'Spread Dates') || !BSR.nodes.some(n => n.name === 'Span Check')) { console.log('0 ok, 0 failed (older builds: SI v66 / Book Series v9 not in them)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a, last: () => a[a.length - 1] });
const runC = (w, name, input, outs) => new Function('$', '$input', node(w, name).parameters.jsCode)(n => { if (!(n in outs)) throw new Error('not run: ' + n); return wrap(outs[n]); }, wrap(input));
const j1 = (...a) => ((runC(...a) || [])[0] || {}).json;
Date.now = () => Date.parse('2026-11-04T06:00:00Z');

// ---- the calendar: Studio 1 + Studio A booked on Nov 5; Nov 26 every Localization studio taken 1-5 PM
const RES = n => (node(RA, 'Compute Availability').parameters.jsCode.match(new RegExp("'" + n + "':\\s*'([^']+@resource[^']+)'")) || [])[1];
const ev = (id, rooms, d, a, b) => ({ id, summary: id, location: rooms.join(', '), start: { dateTime: d + 'T' + a + ':00+08:00' }, end: { dateTime: d + 'T' + b + ':00+08:00' },
  attendees: rooms.map(r => ({ email: RES(r), resource: true, responseStatus: 'accepted' })), description: 'ref: U9' });
const CAL = [ev('BONJOUR', ['Studio 1', 'Studio A'], '2026-11-05', '11:00', '17:00'), ev('ISLA', ['Studio 2'], '2026-11-05', '13:00', '23:00'),
  ev('X1', ['Studio 1'], '2026-11-26', '13:00', '17:00'), ev('X2', ['Studio 2'], '2026-11-26', '13:00', '17:00'), ev('X6', ['Studio 6'], '2026-11-26', '12:00', '18:00')];
const NAMES = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 4', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio A', 'Studio B', 'Studio C', 'Studio D', 'Studio E', 'Studio F', 'Studio M',
  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'Salin', 'Katha', 'Likha', 'Lobby'];
const REFO = { rooms: NAMES.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: /^Studio [ABDE]$/.test(n), booth: /^Studio [ABDE]$/.test(n), common: /Salin|Katha|Likha|Lobby/.test(n) })),
  types: [{ type: 'Localization Dubbing', priority: ['r0', 'r1', 'r5'], last: ['r6'] }] };
const REF = JSON.stringify(REFO);
const ra = trig => runC(RA, 'Compute Availability', [{ json: { items: JSON.parse(JSON.stringify(CAL)) } }], { 'When Executed by Another Workflow': [{ json: trig }], 'Room Free Busy': [{ json: {} }] })[0].json;

// ---- Book Series v9, prepare
const DATES = ['2026-11-05', '2026-11-12', '2026-11-19', '2026-11-26'];
const PREP = { mode: 'prepare', confirmed: false, dates: DATES.join(','), time_start: '14:00', time_end: '16:00', all_day: false, summary: 'NET-KUBA / JL', rooms: 'Studio 1, Studio A',
  session_type: 'Localization Dubbing', client: '', engineer: 'Josiah Lateo', description: 'Engineer: Josiah Lateo | Booked by: Howard Luistro | ref: U1', bookingType: '', department: 'Localization',
  reference_data: REF, requester_text: '', asked_text: '', staff_data: '', authority: '', room_override: false, frequency: '', by_days: '', start_date: '', count: null, until_date: '', changes: '', per_date: '' };
const T = [{ json: PREP }];
console.log('Book Series v9 - prepare');
const items = runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': T });
ok(items.length === 4 && items.every(i => i.json._go && i.json.mode === 'prepare'), 'Expand Dates: four dates to prepare');
const SIn = j1(BSR, 'Span Input', items, { 'When Executed by Another Workflow': T });
ok(SIn.dates === DATES.join(',') && SIn.t0 === '14:00' && SIn.t1 === '16:00' && SIn.watch === 'Studio 1, Studio A' && SIn.start_iso === '2026-11-05T14:00:00+08:00' && SIn.end_iso === '2026-11-26T16:00:00+08:00',
  'Span Input: one call - the dates, the time, the booking\'s rooms watched', SIn);
const SPAN = ra(SIn);
ok(SPAN.span && SPAN.status === 'OK' && SPAN.per_date.length === 4, 'Room Availability v26 answers all four in one call', SPAN.status);
const FD = j1(BSR, 'First Date', [], { 'Expand Dates': items, 'Span Check': [{ json: SPAN }], 'When Executed by Another Workflow': T });
ok(FD._date === '2026-11-12', 'First Date: Book Session checks the first date with both rooms free (Nov 12, not Nov 5)', FD._date);
const F = { Title: 'NET-KUBA / JL', Time: '2:00 PM – 4:00 PM', Room: 'Studio 1, Studio A', 'Session Type': 'Localization Dubbing', Client: 'None', Engineer: 'Josiah Lateo', 'Booking Type': 'Entertainment',
  Department: 'Localization', Override: 'no', 'Booked by': 'Howard Luistro' };
const BSRES = { status: 'PREPARED', prep_payload: JSON.stringify({ F, ref: 'U1' }), summary_text: '*NET-KUBA / JL*\n\nConfirm to book.' };
const agg = (bsres, span, fd, trig) => j1(BSR, 'Aggregate', [{ json: bsres }], { 'Expand Dates': items, 'Span Check': [{ json: span }], 'First Date': [{ json: fd }], 'When Executed by Another Workflow': [{ json: trig || PREP }] });
const A = agg(BSRES, SPAN, FD);
const K = Object.fromEntries((A.review || { items: [] }).items.map(x => [x.d, x]));
ok(A.status === 'PREPARED' && A.review && A.review.items.length === 4, 'PREPARED, with a review of every date', A.status + ' ' + (A.human || ''));
ok(K['2026-11-12'].kind === 'ok' && K['2026-11-19'].kind === 'ok', 'Nov 12, Nov 19: free - booked as asked');
ok(K['2026-11-05'].kind === 'moved' && K['2026-11-05'].note === 'Studio 6 instead of Studio 1, Studio B instead of Studio A',
  'Nov 5 (Studio 1 + A taken, Studio 2 too): "Studio 6 instead of Studio 1, Studio B instead of Studio A" - a usual studio and a free booth', K['2026-11-05']);
ok(K['2026-11-26'].kind === 'choose' && K['2026-11-26'].options.map(o => o.label).join(' | ') === '11:00 AM – 1:00 PM (earlier) | 5:00 PM – 7:00 PM (later) | Skip – find another time later',
  'Nov 26 (every usual studio taken): pick - 11 AM - 1 PM earlier, 5 - 7 PM later, or skip', K['2026-11-26']);
const inp = JSON.parse(A.prep_payload).inputs;
ok(inp.dates === '2026-11-05,2026-11-12,2026-11-19' && JSON.parse(inp.per_date)['2026-11-05'].rooms === 'Studio 6, Studio B' && JSON.parse(inp.choices)['2026-11-26'].length === 3,
  'the stored series: three dates now, Nov 5 in its rooms, Nov 26\'s options stored with it', { dates: inp.dates, per: inp.per_date });
ok(A.prep_key && /^prep-s/.test(A.prep_key), 'stored under a key (as before)');
let B2 = agg({ status: 'REJECTED', reason: 'NEED_DEPARTMENT', human: 'Which department?' }, SPAN, FD);
ok(B2.status === 'REJECTED' && B2.reason === 'NEED_DEPARTMENT', 'Book Session asks something -> that question, as before');
B2 = agg(BSRES, { status: 'CALENDAR_ERROR', span: true, per_date: [] }, FD);
ok(B2.status === 'REJECTED' && B2.reason === 'CALENDAR_ERROR', 'the span read failed -> nothing prepared (CALENDAR_ERROR), never "free"');
// Howard's Slack test 4 Nov (Book Series v10): Mon 9 Nov, Studio 6 taken 9 AM - 10 PM -> the later option ends at 11:59 PM, never "24:00"
if (/v10 \(v9 fixed\)/.test(JSON.stringify(BSR.nodes))) {
  const D9 = ['2026-11-05', '2026-11-09'], P9 = Object.assign({}, PREP, { dates: D9.join(','), rooms: 'Studio 6', summary: 'NET-TESTT / HL' });
  const it9 = runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: P9 }] });
  const cal9 = [ev('ISLA6', ['Studio 6'], '2026-11-09', '09:00', '22:00'), ev('B6', ['Studio 2'], '2026-11-09', '09:00', '21:00'), ev('BG', ['Studio 1'], '2026-11-09', '10:00', '22:00')];
  const sp9 = runC(RA, 'Compute Availability', [{ json: { items: cal9 } }], { 'When Executed by Another Workflow': [{ json: { dates: D9.join(','), t0: '14:00', t1: '16:00', start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-09T16:00:00+08:00',
    session_type: 'Localization Dubbing', room: '', scope: '', hours: '', reference_data: REF, watch: 'Studio 6' } }], 'Room Free Busy': [{ json: {} }] })[0].json;
  const fd9 = j1(BSR, 'First Date', [], { 'Expand Dates': it9, 'Span Check': [{ json: sp9 }], 'When Executed by Another Workflow': [{ json: P9 }] });
  const a9 = j1(BSR, 'Aggregate', [{ json: Object.assign({}, BSRES, { prep_payload: JSON.stringify({ F: Object.assign({}, F, { Title: 'NET-TESTT / HL', Room: 'Studio 6' }), ref: 'U1' }) }) }],
    { 'Expand Dates': it9, 'Span Check': [{ json: sp9 }], 'First Date': [{ json: fd9 }], 'When Executed by Another Workflow': [{ json: P9 }] });
  const k9 = (a9.review.items.find(x => x.d === '2026-11-09') || {}), o9 = JSON.parse(JSON.parse(a9.prep_payload).inputs.choices)['2026-11-09'] || [];
  ok(k9.kind === 'choose' && k9.options.map(o => o.label).join(' | ') === '7:00 AM – 9:00 AM (earlier) | 10:00 PM – 11:59 PM (later) | Skip – find another time later' && o9[1].end === '23:59',
    'v10: Mon 9 Nov (Studio 6 taken 9 AM - 10 PM) -> 7-9 AM or 10 PM - 11:59 PM (never "24:00")', { opts: k9.options, stored: o9 });
}
if (/v11 \(Howard, 4 Nov/.test(JSON.stringify(BSR.nodes))) {   // Howard's Tue 10 Nov: Studio 6 taken -> every other usual studio free then is offered
  const D10 = ['2026-11-05', '2026-11-10'], P10 = Object.assign({}, PREP, { dates: D10.join(','), rooms: 'Studio 6', summary: 'NET-TESTT / HL' });
  const it10 = runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: P10 }] });
  const cal10 = [ev('T6', ['Studio 6'], '2026-11-10', '13:00', '17:00')];
  const sp10 = runC(RA, 'Compute Availability', [{ json: { items: cal10 } }], { 'When Executed by Another Workflow': [{ json: { dates: D10.join(','), t0: '14:00', t1: '16:00', start_iso: '2026-11-05T14:00:00+08:00', end_iso: '2026-11-10T16:00:00+08:00',
    session_type: 'Localization Dubbing', room: '', scope: '', hours: '', reference_data: REF, watch: 'Studio 6' } }], 'Room Free Busy': [{ json: {} }] })[0].json;
  const fd10 = j1(BSR, 'First Date', [], { 'Expand Dates': it10, 'Span Check': [{ json: sp10 }], 'When Executed by Another Workflow': [{ json: P10 }] });
  const a10 = j1(BSR, 'Aggregate', [{ json: Object.assign({}, BSRES, { prep_payload: JSON.stringify({ F: Object.assign({}, F, { Title: 'NET-TESTT / HL', Room: 'Studio 6' }), ref: 'U1' }) }) }],
    { 'Expand Dates': it10, 'Span Check': [{ json: sp10 }], 'First Date': [{ json: fd10 }], 'When Executed by Another Workflow': [{ json: P10 }] });
  const k10 = a10.review.items.find(x => x.d === '2026-11-10') || {};
  ok(k10.kind === 'moved' && k10.dflt === 'r0' && k10.options.map(o => o.label).join(' | ') === 'Studio 1 instead of Studio 6 | Studio 2 instead of Studio 6 | Studio 6 · 11:00 AM – 1:00 PM (earlier) | Studio 6 · 5:00 PM – 7:00 PM (later) | Skip – find another time later',
    'v11: Tue 10 Nov (Studio 6 taken) -> Studio 1 picked, Studio 2 offered too, Studio 6 at 11-1 or 5-7, or skip', k10.options);
}
console.log('Book Series v9 - six months');
const ex = d => runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: Object.assign({}, PREP, { dates: d.join(',') }) }] })[0].json;
const wk = n => Array.from({ length: n }, (_, i) => new Date(Date.parse('2026-11-05T12:00:00Z') + i * 7 * 86400000).toISOString().slice(0, 10));
ok(ex(wk(26))._go === true, '26 weekly dates (six months) -> fine (was over 16)');
ok(ex(wk(28)).status === 'TOO_LONG' && /six months/.test(ex(wk(28)).human), '28 weekly dates (past six months) -> TOO_LONG, said', ex(wk(28)));

console.log('Slack Interactions v66 - Find rooms in one call, Spread Dates');
const sp = runC(SI, 'Spread Dates', [{ json: SPAN }], {}).map(i => i.json);
ok(sp.length === 4 && sp.map(x => x.date).join() === DATES.join() && sp.every(x => x.status === 'OK'), 'one answer -> one item per date, for Build Step 2');
ok(JSON.stringify(runC(SI, 'Spread Dates', [{ json: { status: 'CALENDAR_ERROR', span: true, per_date: [] } }], {}).map(i => i.json)) === '[{"status":"CALENDAR_ERROR"}]', 'a failed span -> one CALENDAR_ERROR item');
ok(JSON.stringify(runC(SI, 'Spread Dates', [{ json: { status: 'OK', free_priority: ['Studio 7'] } }], {}).map(i => i.json)) === '[{"status":"OK","free_priority":["Studio 7"]}]', 'one window passes through');
{ const js = node(SI, 'Build Step 2').parameters.jsCode; const _a = js.indexOf('function __packS'), _e = js.indexOf('series: ser }); }', js.indexOf('function __unpackS')) + 'series: ser }); }'.length;
  const f = new Function(js.slice(_a, _e) + '\nreturn { __packS, __unpackS };');
  let P; try { P = f(); } catch (e) { P = null; }
  if (P) { const ds = Array.from({ length: 183 }, (_, i) => new Date(Date.parse('2026-11-05T12:00:00Z') + i * 86400000).toISOString().slice(0, 10));
    const s = { date: ds[0], series: { freq: 'daily', days: [], dates: ds } }, pk = P.__packS(s);
    ok(!pk.series.dates && JSON.stringify(pk).length < 800 && JSON.stringify(P.__unpackS(pk).series.dates) === JSON.stringify(ds), 'six months of daily dates fit the metadata (' + JSON.stringify(pk).length + ' chars) and come back exactly'); }
  else ok(false, 'pack / unpack functions found'); }

console.log('Slack Interactions v66 - the review screen');
const again = { d: '2026-11-05', s: '14:00', e: '16:00', p: 'Localization Dubbing', r: 'Studio 1', bo: 'Studio A', cd: 'NET-KUBA', en: 'U3' };
const R2 = { s: { requester: 'U1', allDay: false, t0: '14:00', t1: '16:00', msg: null, series: { dates: DATES } }, channel: 'D1', viewId: 'V1', rooms: 'Studio 1, Studio A', again };
const ap = j1(SI, 'After Prepare Series', [{ json: Object.assign({}, A, { prep_stored: true }) }], { 'Read Step 2': [{ json: R2 }], 'Read Request': [{ json: { payload: { view: {} } } }] });
const V = ap.view, bid = id => V.blocks.find(b => b.block_id === id);
ok(V.callback_id === 'series_confirm' && V.submit.text === 'Book all', 'the review: "Book all"');
ok(/^\*NET-KUBA \/ JL\*\n2:00 PM – 4:00 PM · Studio 1 \+ Studio A$/.test(V.blocks[0].text.text), 'the title, the time and the rooms on top', V.blocks[0].text.text);
ok(/✅ \*Free \(2\):\*\n\*Nov:\* Thu 12, Thu 19/.test(bid('free').text.text), '"✅ Free (2): Nov: Thu 12, Thu 19"', bid('free').text.text);
const V67 = SI.nodes.some(n => /v67 \(Howard, 4 Nov/.test(n.parameters.jsCode || '')) && /v11 \(Howard, 4 Nov/.test(JSON.stringify(BSR.nodes));
if (!V67) ok(/🔄 \*Another room \(1\):\*\n- Thu 5 Nov · Studio 6 instead of Studio 1, Studio B instead of Studio A/.test(bid('moved').text.text), '"🔄 Another room (1): Thu 5 Nov · Studio 6 instead of Studio 1, …"', bid('moved').text.text);
else { const mv = bid('mv_2026-11-05');
  ok(/Another room \(1\) – change it if you like/.test(bid('moved').text.text) && mv && mv.type === 'input' && mv.element.initial_option.value === 'r0'
    && mv.element.initial_option.text.text === 'Studio 6 instead of Studio 1, Studio B instead of Studio A' && mv.label.text === 'Thu 5 Nov – Studio 1 and Studio A are taken then',
    'v67: Thu 5 Nov - a dropdown set to Jessie\'s rooms ("Studio 6 instead of Studio 1, Studio B instead of Studio A")', mv);
  ok(mv.element.options.map(o => o.text.text).join(' | ') === 'Studio 6 instead of Studio 1, Studio B instead of Studio A | Studio 1 + Studio A · 9:00 AM – 11:00 AM (earlier) | Studio 1 + Studio A · 5:00 PM – 7:00 PM (later) | Skip – find another time later',
    'v67: the other choices - the rooms asked at the nearest free times, or skip', mv.element.options.map(o => o.text.text)); }
const ch = bid('ch_2026-11-26');
ok(ch && ch.type === 'input' && !ch.optional && ch.element.action_id === 'ch_pick' && ch.element.options.map(o => o.value).join() === 'a,b,skip' && /Thu 26 Nov – Studio 1 is taken then/.test(ch.label.text),
  'Nov 26: a required pick - earlier, later or skip', ch);
ok(!bid('many'), 'under 20 appointments: no "Are you sure?"');
const meta = JSON.parse(V.private_metadata);
ok(meta.key === A.prep_key && meta.ag && meta.ag.cd === 'NET-KUBA' && V.private_metadata.length < 3000, 'the metadata keeps the key and the form\'s answers (for Find another time)', meta);
{ const many = Object.assign({}, A, { prep_stored: true, review: Object.assign({}, A.review, { items: wk(21).map(d => ({ d, kind: 'ok' })) }) });
  const vm = j1(SI, 'After Prepare Series', [{ json: many }], { 'Read Step 2': [{ json: R2 }], 'Read Request': [{ json: { payload: { view: {} } } }] }).view;
  ok(/⚠️ \*Are you sure\? You’re about to book 21 appointments\.\*/.test((vm.blocks.find(b => b.block_id === 'many') || { text: {} }).text.text), '21 dates -> "Are you sure? You’re about to book 21 appointments."'); }

console.log('Slack Interactions v66 - Book all: the picks, To Book Series, the book-mode dates');
const confirm = pick => j1(SI, 'Read Series Confirm', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Timings 13': [],
  'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: V.private_metadata, state: { values: pick ? { 'ch_2026-11-26': { ch_pick: { selected_option: { value: pick } } } } : {} } } } } }] });
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: FX.bookers }) } }];
const toBook = rsc => j1(SI, 'To Book Series', [], { 'Read Series Confirm': [{ json: rsc }], 'Read Saved Series': [{ json: { cache_key: A.prep_key, payload: A.prep_payload } }], 'Read Cache 8': cache });
let C1 = confirm('b');
ok(C1.choices['2026-11-26'] === 'b' && /Booking 4 dates/.test(JSON.stringify(C1.answer)), 'picked "later" -> 4 dates booking', C1.choices);
let TB = toBook(C1);
ok(TB.go && TB.dates === '2026-11-05,2026-11-12,2026-11-19,2026-11-26' && JSON.parse(TB.per_date)['2026-11-26'].start === '17:00' && !TB.skipped_review.length && TB.choices === undefined,
  'To Book Series: Nov 26 added at 5:00-7:00 PM, the saved series checked first', { d: TB.dates, per: TB.per_date, sk: TB.skipped_review });
const bk = runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: Object.assign({}, TB, { mode: '' }) }] }).map(i => i.json);
const b26 = bk.find(x => x._date === '2026-11-26'), b05 = bk.find(x => x._date === '2026-11-05');
ok(bk.length === 4 && b26.start_iso === '2026-11-26T17:00:00+08:00' && b26.end_iso === '2026-11-26T19:00:00+08:00' && b05.rooms === 'Studio 6, Studio B' && b05.start_iso === '2026-11-05T14:00:00+08:00',
  'Book Series books Nov 26 at 5-7 PM and Nov 5 in Studio 6 + Studio B', bk.map(x => x._date + ' ' + x.start_iso.slice(11, 16) + ' ' + x.rooms));
if (V67) {   // v67: a moved date's pick
  const cf = (vals) => j1(SI, 'Read Series Confirm', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Timings 13': [],
    'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: V.private_metadata, state: { values: vals } } } } }] });
  const sel = v => ({ ch_pick: { selected_option: { value: v } } });
  let c2 = cf({ 'mv_2026-11-05': sel('b'), 'ch_2026-11-26': sel('skip') }), t2 = toBook(c2);
  ok(t2.go && JSON.parse(t2.per_date)['2026-11-05'].start === '17:00' && JSON.parse(t2.per_date)['2026-11-05'].rooms === 'Studio 1, Studio A' && t2.dates === '2026-11-05,2026-11-12,2026-11-19' && /Booking 3 dates/.test(JSON.stringify(c2.answer)),
    'v67: Thu 5 Nov changed to Studio 1 + A at 5-7 PM; Nov 26 skipped - 3 dates', { per: t2.per_date, d: t2.dates });
  const bk2 = runC(BSR, 'Expand Dates', [], { 'When Executed by Another Workflow': [{ json: Object.assign({}, t2, { mode: '' }) }] }).map(i => i.json).find(x => x._date === '2026-11-05');
  ok(bk2.rooms === 'Studio 1, Studio A' && bk2.start_iso === '2026-11-05T17:00:00+08:00' && bk2.end_iso === '2026-11-05T19:00:00+08:00', 'v67: booked in the rooms asked at 5-7 PM', bk2);
  c2 = cf({ 'mv_2026-11-05': sel('skip'), 'ch_2026-11-26': sel('a') }); t2 = toBook(c2);
  ok(t2.go && t2.dates === '2026-11-12,2026-11-19,2026-11-26' && t2.skipped_review.join() === '2026-11-05' && /Booking 3 dates/.test(JSON.stringify(c2.answer)), 'v67: a moved date skipped -> taken out, in the DM', t2.skipped_review);
  c2 = cf({ 'ch_2026-11-26': sel('skip') }); t2 = toBook(c2);
  ok(JSON.parse(t2.per_date)['2026-11-05'].rooms === 'Studio 6, Studio B' && t2.dates.split(',').length === 3, 'v67: no pick on a moved date -> Jessie\'s rooms, as before');
  t2 = toBook(Object.assign({}, c2, { choices: { '2026-11-05': 'r9', '2026-11-26': 'skip' } }));
  ok(JSON.parse(t2.per_date)['2026-11-05'].rooms === 'Studio 6, Studio B', 'v67: a room the review never offered -> Jessie\'s rooms, never that room');
}
C1 = confirm('skip'); TB = toBook(C1);
ok(TB.go && TB.dates === '2026-11-05,2026-11-12,2026-11-19' && TB.skipped_review.join() === '2026-11-26', 'Skip -> three dates booked, Nov 26 skipped', TB.skipped_review);
TB = toBook(Object.assign({}, C1, { choices: { '2026-11-26': 'z' } }));
ok(TB.go && TB.skipped_review.join() === '2026-11-26' && TB.dates.split(',').length === 3, 'a pick the review never offered -> skipped, never booked');

console.log('Slack Interactions v66 - the result: Find another time');
const abs = (res, tb) => j1(SI, 'After Book Series', [{ json: res }], { 'Read Series Confirm': [{ json: C1 }], 'To Book Series': [{ json: tb }] });
let X = abs({ status: 'BOOKED_SERIES', booked: ['2026-11-05', '2026-11-12'], skipped: ['2026-11-19'], failed: [] }, TB);
const fat = X.blocks.filter(b => /^fat_/.test(b.block_id || ''));
ok(fat.map(b => b.elements[0].text.text).join(' | ') === 'Find another time – Thu, Nov 19 | Find another time – Thu, Nov 26', 'the DM: a Find another time for the date taken at booking and the one skipped on the review', fat.map(b => b.elements[0].text.text));
const v26 = JSON.parse(fat[1].elements[0].value);
ok(fat[1].elements[0].action_id === 'open_book' && v26.d === '2026-11-26' && v26.cd === 'NET-KUBA' && v26.r === 'Studio 1' && v26.s === '14:00' && !v26.rep, 'each opens Book a room filled in - that date, this booking\'s details, one booking', v26);
ok(/Skipped: Thu, Nov 26/.test(X.text) && /in your DM, each with \*Find another time\*/.test(JSON.stringify(X.view)) && !JSON.stringify(X.view).includes('fat_'), 'the window says the dates are in the DM (the buttons only in the DM)', X.text);
X = abs({}, { go: false, why: 'every date was skipped', skipped_review: ['2026-11-26'] });
ok(/Nothing was booked\* - every date was skipped/.test(X.text) && X.blocks.some(b => b.block_id === 'fat_2026-11-26'), 'every date skipped -> nothing booked, still a Find another time', X.text);
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
