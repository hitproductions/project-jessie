#!/usr/bin/env node
// Offline tests for Book Session v93 + Book Series v6 + main v227 (series alternatives; decided 6 Oct): a taken series date
// gets another usual room at the same time, else the same room at the nearest free time 8 AM - 10 PM, else it is left out;
// single dates are changed before the yes; the yes books each date in its own room and time. Real ranking data.
//   node scripts/sim-series-alternatives.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v227.json'), S = WF(process.env.SERIES || 'book-series-v6.json'), B = WF(process.env.BOOK || 'book-session-v93.json');
const OB = WF('book-session-v92.json'), OS = WF('book-series-v5.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 900))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const recM = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
Date.now = () => Date.parse('2026-10-06T07:48:30Z');
const ME = 'U08V3CKDGJF';
const REF = recM('Room Table')[0].json.referenceData, R = JSON.parse(REF);
const VO = R.types.find(t => t.type === 'VO Recording'), nameById = Object.fromEntries(R.rooms.map(r => [r.id, r.name]));
const VOROOMS = [...new Set([].concat(VO.priority || [], VO.last || []).map(id => nameById[id]).filter(Boolean))];
const RID = (w, n) => (code(w, 'Check Conflicts').match(new RegExp("'" + n + "':\\s*'([^']+@resource[^']+)'")) || [])[1];
const ev = (room, d, a, b, id) => ({ id: id || room + d + a, summary: 'BUSY / X / DR', start: { dateTime: d + 'T' + a + ':00+08:00' }, end: { dateTime: d + 'T' + b + ':00+08:00' }, attendees: [{ email: RID(B, room) }] });
const RT = 'book studio 7 every friday for the next three weeks for project dinos 3-6pm. client john estrada for vo recordings';
const PS_IN = { frequency: 'weekly', by_days: 'FR', start_date: '2027-10-08', count: 3, until_date: '', all_day: false, time_start: '15:00', time_end: '18:00',
  summary: 'DINOS / John Estrada / HL', rooms: 'Studio 7', session_type: 'VO Recording', client: 'John Estrada', engineer: 'Howard Luistro',
  description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, bookingType: '', department: 'Audio Post', reference_data: REF,
  confirmed: false, requester_text: RT, mode: 'prepare', asked_text: '', staff_data: '', authority: 'Standard', room_override: false, dates: '', changes: '', per_date: '' };
const bookSession = (w, req, events) => {
  const Rq = [{ json: req }], O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(Rq) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { items: events } }]), () => ({}))[0].json;
  if (c.verdict !== 'CLEAR') return { status: c.verdict || 'REJECTED', reason: c.reason, human: c.human };
  if (String(req.mode) !== 'prepare') return { status: 'CREATED', human: 'Booked.', _req: req, _cc: c };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(Rq) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json; };
// the day's events a series date reads: in v93 the whole day for series_alt, else only the window (overlap decides either way)
const series = (Sw, Bw, input, evs = []) => {
  const T = [{ json: input }];
  const items = new Function('$', code(Sw, 'Expand Dates'))(n => wrap(T)).map(i => i.json);
  if (!items[0]._go) return { agg: items[0], items };
  const res = items.map(j => ({ json: bookSession(Bw, j, evs.filter(e => e.start.dateTime.slice(0, 10) === j._date)) }));
  const agg = new Function('$', '$input', code(Sw, 'Aggregate'))(n => n === 'Expand Dates' ? wrap(items.map(j => ({ json: j }))) : wrap(T), wrap(res))[0].json;
  return { agg, items, res }; };
const D2 = '2027-10-15', line = s => (s.agg.card_text || '').split('\n').find(l => /15 October/.test(l)) || '';

console.log('Book Session v93 - the day is read for a series date');
const q = B.nodes.find(n => n.name === 'Get Events In Window').parameters.queryParameters.parameters;
const qv = (k, j) => new Function('$', 'return (' + q.find(p => p.name === k).value.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => wrap([{ json: j }]));
const W = { start_iso: '2027-10-15T15:00:00+08:00', end_iso: '2027-10-15T18:00:00+08:00' };
ok(qv('timeMin', { ...W, mode: 'prepare', series_alt: true }) === '2027-10-15T08:00:00+08:00' && qv('timeMax', { ...W, mode: 'prepare', series_alt: true }) === '2027-10-15T22:00:00+08:00', 'series_alt prepare -> 8 AM to 10 PM');
ok(qv('timeMin', { ...W, mode: 'prepare' }) === W.start_iso && qv('timeMax', { ...W, mode: '' , series_alt: true }) === W.end_iso, 'a single booking, or booking (not preparing) -> the window only, as before');

console.log('1. another usual room at the same time (VO Recording rooms: ' + VOROOMS.join(', ') + ')');
const BLK = [ev('Studio 7', D2, '16:00', '17:00', 'blocker')];
let P = series(S, B, PS_IN, BLK);
const ALT = P.res[1].json.swap && P.res[1].json.swap.to_rooms;
ok(P.agg.status === 'PREPARED' && /\*Dates \(3\):\*/.test(P.agg.card_text) && line(P) === '- Friday, 15 October 2027 · ' + ALT + ' (Studio 7 is taken)' && VOROOMS.indexOf(ALT) !== -1,
  'Studio 7 taken 4-5 PM on 15 Oct -> "· ' + ALT + ' (Studio 7 is taken)", all three dates kept', P.agg.card_text || P.agg);
ok(/\*Time:\* 3:00 PM – 6:00 PM\n\*Room:\* Studio 7/.test(P.agg.card_text) && !/left out/.test(P.agg.card_text), 'the series\' own Time and Room lines stay', P.agg.card_text);
const inp = JSON.parse(P.agg.prep_payload).inputs, per = JSON.parse(inp.per_date);
ok(inp.dates === '2027-10-08,2027-10-15,2027-10-22' && per[D2] && per[D2].rooms === ALT && per[D2].start === '15:00' && per[D2].end === '18:00' && Object.keys(per).length === 1, 'stored: 3 dates, 15 Oct in ' + ALT + ' at 15:00-18:00', [inp.dates, per]);
ok(/taken on Friday, 15 October 2027/.test(series(OS, OB, PS_IN, BLK).agg.card_text || ''), '  (v5 / v92: 15 Oct left out)');

console.log('2. every usual room busy then -> the same room at the nearest free time (8 AM - 10 PM)');
const ALLBUSY = VOROOMS.map(r => ev(r, D2, '15:00', '18:00'));
P = series(S, B, PS_IN, ALLBUSY.concat([ev('Studio 7', D2, '18:00', '19:00')]));
ok(line(P) === '- Friday, 15 October 2027 · 12:00 PM – 3:00 PM (Studio 7 is taken 3:00 PM – 6:00 PM)',
  'all VO rooms busy 3-6 PM and Studio 7 also 6-7 PM -> 12:00 - 3:00 PM (3 h earlier beats 7-10 PM, 4 h later)', line(P));
P = series(S, B, PS_IN, ALLBUSY);
ok(line(P) === '- Friday, 15 October 2027 · 6:00 PM – 9:00 PM (Studio 7 is taken 3:00 PM – 6:00 PM)', 'busy exactly 3-6 PM -> 6:00 - 9:00 PM (nearest; later wins a tie with 12-3)', line(P));
const per2 = JSON.parse(JSON.parse(P.agg.prep_payload).inputs.per_date);
ok(per2[D2].rooms === 'Studio 7' && per2[D2].start === '18:00' && per2[D2].end === '21:00', 'stored: 15 Oct in Studio 7 at 18:00-21:00', per2);
const NOROOM = [{ id: 'nr', summary: 'Something', start: { dateTime: D2 + 'T18:00:00+08:00' }, end: { dateTime: D2 + 'T21:00:00+08:00' } }];
P = series(S, B, PS_IN, ALLBUSY.concat(NOROOM));
ok(!/6:00 PM – 9:00 PM/.test(line(P)), 'an event with no room counts as busy for the time search', line(P));

console.log('3. no other room and no other time -> left out, and said');
P = series(S, B, PS_IN, VOROOMS.map(r => ev(r, D2, '08:00', '22:00')));
ok(/\*Dates \(2\):\*/.test(P.agg.card_text) && /Studio 7 is taken on Friday, 15 October 2027, and no other usual room or time that day is free - that date left out\./.test(P.agg.card_text), 'every VO room busy 8 AM - 10 PM -> left out with the reason', P.agg.card_text);

console.log('4. the first date is the one moved');
P = series(S, B, PS_IN, [ev('Studio 7', '2027-10-08', '16:00', '17:00')]);
ok(/\*Time:\* 3:00 PM – 6:00 PM\n\*Room:\* Studio 7/.test(P.agg.card_text) && /- Friday, 8 October 2027 · \S.* \(Studio 7 is taken\)/.test(P.agg.card_text), 'the base lines are still Studio 7 / 3-6 PM; 8 Oct shows its swap', P.agg.card_text);

console.log('5. changes before the yes');
P = series(S, B, { ...PS_IN, changes: '2027-10-15 skip' });
ok(/\*Dates \(2\):\*/.test(P.agg.card_text) && /Left out as asked: Friday, 15 October 2027\./.test(P.agg.card_text), '"skip the 15th" -> 2 dates, named', P.agg.card_text);
P = series(S, B, { ...PS_IN, changes: '2027-10-15 room Studio F' });
ok(line(P) === '- Friday, 15 October 2027 · Studio F' && P.items.find(j => j._date === D2).series_alt === false, '"use Studio F on the 15th" -> "· Studio F", checked as asked (no swap)', [line(P), P.items.map(j => [j._date, j.rooms, j.series_alt])]);
P = series(S, B, { ...PS_IN, changes: '2027-10-15 19:00-22:00' });
ok(line(P) === '- Friday, 15 October 2027 · 7:00 PM – 10:00 PM', '"make the 15th 7-10pm" -> "· 7:00 PM – 10:00 PM"', line(P));
P = series(S, B, { ...PS_IN, changes: '2027-10-15 room Studio F' }, [ev('Studio F', D2, '15:00', '18:00')]);
ok(/\*Dates \(2\):\*/.test(P.agg.card_text) && /left out/.test(P.agg.card_text), 'a room they chose that is taken -> left out and said, not swapped behind their back', P.agg.card_text);
P = series(S, B, { ...PS_IN, changes: 'the fifteenth, no' });
ok(/\*Dates \(3\):\*/.test(P.agg.card_text), 'a change line that does not read right is ignored (the card shows the result before any yes)');
ok(series(S, B, { ...PS_IN, changes: '2027-10-08 skip\n2027-10-15 skip\n2027-10-22 skip' }).agg.status === 'MISSING_DETAILS', 'every date skipped -> nothing to book, said');

console.log('6. the yes books each date in its own room and time');
P = series(S, B, PS_IN, BLK);
const gp = out => new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output: 'x', intermediateSteps: [{ action: { tool: 'Prepare_Series' }, observation: JSON.stringify([out]) }] } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: RT } }]) : n === 'Gate Context' ? wrap([{ json: {} }]) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(recM(n) || [{ json: {} }]))[0].json.output;
const sent = gp(P.agg);
ok(sent === P.agg.card_text.replace(/\n*Confirm to book\.$/, '\n\nBook it? Reply yes or no.'), 'Guard Probe sends the card as written', sent);
const hist = [{ json: { user: ME, text: 'yes', ts: '1791272990.1' } }, { json: { bot_id: 'B1', text: sent, ts: '1791272980.1' } }];
const key = new Function('$', '$input', code(M, 'Prepared Key'))(n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: { user: ME } }]) : wrap([{ json: {} }]), wrap([{ json: {} }]))[0].json.prep_key;
const rows = [{ cache_key: P.agg.prep_key, payload: P.agg.prep_payload, refreshed_at: new Date(Date.now() - 15000).toISOString() }];
const sd = new Function('$', '$input', code(M, 'Prepared Series'))(n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: { user: ME } }]) : n === 'Gate Context' ? wrap([{ json: { confirmed: true } }])
  : n === 'Prepared Key' ? wrap([{ json: { prep_key: key } }]) : n === 'Read Prepared' ? wrap(rows.map(r => ({ json: r }))) : wrap([{ json: {} }]), wrap([{ json: {} }]))[0].json;
ok(key === P.agg.prep_key && sd._seriesDirect.use === true, 'the card with a swapped date is read back at the yes (key matches, use)', [key, P.agg.prep_key, sd._seriesDirect.reason]);
const sdIn = Object.fromEntries(Object.entries(M.nodes.find(n => n.name === 'Series Direct').parameters.workflowInputs.value).map(([k, v]) => {
  const e = String(v); if (!/^=\{\{/.test(e)) return [k, e];
  return [k, new Function('$', 'return (' + e.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => n === 'Prepared Series' ? wrap([{ json: sd }]) : n === 'Gate Context' ? wrap([{ json: { confirmed: true } }]) : n === 'Room Table' ? wrap([{ json: { referenceData: REF } }]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : n === 'Get Booker' ? wrap([{ json: { fields: { Authority: ['Standard'] } } }]) : wrap([{ json: {} }]))];
}));
const BK = series(S, B, sdIn, BLK);
const it15 = BK.items.find(j => j._date === D2);
ok(BK.items.length === 3 && it15.rooms === ALT && it15.start_iso === D2 + 'T15:00:00+08:00' && BK.items.filter(j => j._date !== D2).every(j => j.rooms === 'Studio 7') && BK.items.every(j => j.confirmed === true && j.series === true && !j.series_alt),
  'Series Direct -> 8 / 22 Oct in Studio 7, 15 Oct in ' + ALT + ' (no swapping at booking time)', BK.items.map(j => [j._date, j.rooms, j.start_iso, j.series_alt]));
ok(BK.agg.status === 'BOOKED_SERIES' && BK.agg.booked.length === 3, 'all three pass Book Session at the yes (the 4-5 PM blocker does not touch ' + ALT + ')', BK.agg);
P = series(S, B, PS_IN, ALLBUSY);
const per3 = JSON.parse(JSON.parse(P.agg.prep_payload).inputs.per_date);
const BK2 = series(S, B, { ...sdIn, per_date: JSON.stringify(per3) }, ALLBUSY);
const it2 = BK2.items.find(j => j._date === D2);
ok(it2.rooms === 'Studio 7' && it2.start_iso === D2 + 'T18:00:00+08:00' && it2.end_iso === D2 + 'T21:00:00+08:00' && BK2.agg.booked.length === 3, 'a time swap books 15 Oct at 6-9 PM, the others at 3-6 PM', BK2.items.map(j => [j._date, j.rooms, j.start_iso]));

console.log('7. a single booking is unchanged');
const single = bookSession(B, { ...PS_IN, mode: 'prepare', series: false, series_alt: false, expected_date: D2, start_iso: D2 + 'T15:00:00+08:00', end_iso: D2 + 'T18:00:00+08:00' }, BLK);
ok(single.reason === 'ROOM_OCCUPIED', 'a single booking over a taken room -> ROOM_OCCUPIED as before (no swap)', single.reason);
console.log('wiring / inputs');
const pv = M.nodes.find(n => n.name === 'Prepare Series').parameters.workflowInputs;
ok(/series_changes/.test(pv.value.changes) && pv.schema.some(c => c.id === 'changes'), 'Prepare Series takes the changes');
ok(/per_date/.test(M.nodes.find(n => n.name === 'Series Direct').parameters.workflowInputs.value.per_date), 'Series Direct passes the stored per_date');
ok(S.nodes.find(n => n.name === 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'per_date') && B.nodes.find(n => n.name === 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'series_alt'), 'trigger inputs: Book Series changes / per_date, Book Session series_alt');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
