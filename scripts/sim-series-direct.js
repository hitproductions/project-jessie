#!/usr/bin/env node
// Offline round trip for Book Series v5 + main v226 (v4 / v225 + review fixes) (deterministic series; PENDING 90): Prepare Series runs every date
// through Book Session's real prepare code and writes the card; Guard Probe sends it as written; at the yes Prepared Key
// + Prepared Series read the stored series back, and Series Direct books exactly the dates on the card - no model.
//   node scripts/sim-series-direct.js <main-execution.json>   (its All Bookers output feeds Book Session)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v226.json'), S = WF(process.env.SERIES || 'book-series-v5.json'), B = WF(process.env.BOOK || 'book-session-v92.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const recM = (run => n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null)(JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData);
Date.now = () => Date.parse('2026-10-06T07:13:20Z');
const ME = 'U08V3CKDGJF', S7 = (code(B, 'Check Conflicts').match(/'Studio 7':\s*'([^']+)'/) || [])[1];
const REF = JSON.stringify({ rooms: [{ id: 'r7', name: 'Studio 7', common: false }], types: [{ type: 'VO Recording', typical: 60, min: 60, max: 180, ranked: ['Studio 7'], priority: ['Studio 7'] }] });
const RT = 'book studio 7 every friday for the next three weeks for project asim kilig 3-6pm. client john estrada for vo reecordings';
const PS_IN = { frequency: 'weekly', by_days: 'FR', start_date: '2027-10-08', count: 3, until_date: '', all_day: false, time_start: '15:00', time_end: '18:00',
  summary: 'ASIM KILIG / John Estrada / HL', rooms: 'Studio 7', session_type: 'VO Recording', client: 'John Estrada', engineer: 'Howard Luistro',
  description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: ' + ME, bookingType: '', department: 'Audio Post', reference_data: REF,
  confirmed: false, requester_text: RT, mode: 'prepare', asked_text: '', staff_data: '', authority: 'Standard', room_override: false, dates: '' };
// one Book Session run (prepare or book) with the real Check Conflicts + Render Summary
const bookSession = (req, events) => {
  const R = [{ json: req }], O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [] };
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : O[n] ? wrap(O[n]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : wrap([{ json: {} }]);
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(B, 'Check Conflicts'))($, wrap([{ json: { items: events || [] } }]), () => ({}))[0].json;
  if (c.verdict !== 'CLEAR') return { status: c.verdict || 'REJECTED', reason: c.reason, human: c.human };
  if (String(req.mode) !== 'prepare') return { status: 'CREATED', human: 'Booked.', _req: req };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(recM(n) || [{ json: {} }]);
  return new Function('$', '$input', code(B, 'Render Summary'))($r, wrap([{ json: c }]))[0].json; };
const busy = d => ({ id: 'x' + d, summary: 'OTHER / X / DR', start: { dateTime: d + 'T14:00:00+08:00' }, end: { dateTime: d + 'T16:00:00+08:00' }, attendees: [{ email: S7 }] });
// Book Series: Expand Dates -> Book Session per date -> Aggregate
const series = (input, takenOn = []) => {
  const T = [{ json: input }];
  const items = new Function('$', code(S, 'Expand Dates'))(n => wrap(T)).map(i => i.json);
  if (!items[0]._go) return { agg: items[0], items };
  const res = items.map(j => ({ json: bookSession(j, takenOn.includes(j._date) ? [busy(j._date)] : []) }));
  const agg = new Function('$', '$input', code(S, 'Aggregate'))(n => n === 'Expand Dates' ? wrap(items.map(j => ({ json: j }))) : wrap(T), wrap(res))[0].json;
  return { agg, items, res }; };

console.log('Book Series v4 - Prepare Series writes the card');
let P = series(PS_IN);
ok(P.items.every(j => j.mode === 'prepare' && j.series === false && j.expected_date === j._date && j.confirmed === false), 'each date runs through Book Session in prepare mode, as a single booking on that date');
ok(P.agg.status === 'PREPARED' && /^\*ASIM KILIG \/ John Estrada \/ HL\*\n\*Dates \(3\):\*\n- Friday, 8 October 2027\n- Friday, 15 October 2027\n- Friday, 22 October 2027\n\*Time:\* 3:00 PM – 6:00 PM\n\*Room:\* Studio 7/.test(P.agg.card_text) && /Confirm to book\.$/.test(P.agg.card_text), 'the card: title, 3 dates, time, room - written in code', P.agg.card_text || P.agg);
ok(/^prep-s[0-9a-f]{8}$/.test(P.agg.prep_key) && JSON.parse(P.agg.prep_payload).inputs.dates === '2027-10-08,2027-10-15,2027-10-22', 'stored under a series key, with the three dates', [P.agg.prep_key, P.agg.prep_payload && JSON.parse(P.agg.prep_payload).inputs]);
const T2 = series(PS_IN, ['2027-10-15']);
const ALTS = /series_alt/.test(JSON.stringify(B));   // Book Session v93 / Book Series v6: a taken date gets another room or time
if (ALTS) ok(/\*Dates \(3\):\*\n- Friday, 8 October 2027\n- Friday, 15 October 2027 · 4:00 PM – 7:00 PM \(Studio 7 is already booked 3:00 PM – 6:00 PM\)\n- Friday, 22 October 2027\n/.test(T2.agg.card_text), 'v6: a taken date (Studio 7 busy 2-4 PM, the only usual room here) -> moved to 4-7 PM, said', T2.agg.card_text);
else ok(/\*Dates \(2\):\*\n- Friday, 8 October 2027\n- Friday, 22 October 2027\n/.test(T2.agg.card_text) && /Heads up: Studio 7 is taken on Friday, 15 October 2027 - that date left out\./.test(T2.agg.card_text), 'a date whose room is taken is left out and named', T2.agg.card_text);
const Q = series({ ...PS_IN, session_type: '', requester_text: 'book studio 7 every friday for the next three weeks for project asim kilig 3-6pm. client john estrada' });
ok(Q.agg.status === 'REJECTED' && /Ask exactly this/.test(Q.agg.human), 'a question (no session type) goes back as Book Session wrote it', [Q.agg.reason, Q.agg.human]);
const ALL = series(PS_IN, ['2027-10-08', '2027-10-15', '2027-10-22']);
if (ALTS) ok(ALL.agg.status === 'PREPARED' && (ALL.agg.card_text.match(/· 4:00 PM – 7:00 PM/g) || []).length === 3, 'v6: taken 2-4 PM on every date -> each moved to 4-7 PM', ALL.agg.card_text);
else ok(ALL.agg.status === 'REJECTED' && /taken on every one/.test(ALL.agg.human), 'taken on every date -> nothing prepared, says so', ALL.agg.human);

console.log('main v225 Guard Probe - the card is the reply');
const gp = (output, steps) => new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: { output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: RT, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { datesUnderDiscussion: '' } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(recM(n) || [{ json: {} }]))[0].json.output;
const STEP = o => [{ action: { tool: 'Prepare_Series' }, observation: JSON.stringify([o]) }];
const sent = gp('Here is your series! *ASIM KILIG*...', STEP(P.agg));
ok(sent === P.agg.card_text.replace(/\n*Confirm to book\.$/, '\n\nBook it? Reply yes or no.'), 'Guard Probe sends the card exactly (with the usual last line)', sent);
ok(/^What kind of session is this\?/.test(gp('anything', STEP({ status: 'REJECTED', reason: 'NEED_SESSION_TYPE', human: Q.agg.human }))), 'its question goes out word for word');

console.log('main v225 - the yes books exactly the card, in code');
const yesTurn = (cardText, storedRows, confirmed = true) => {
  const hist = [{ json: { user: ME, text: 'yes', ts: '1791270813.1' } }, { json: { bot_id: 'B1', text: cardText, ts: '1791270807.1' } }];
  const $k = n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: { user: ME } }]) : wrap([{ json: {} }]);
  const key = new Function('$', '$input', code(M, 'Prepared Key'))($k, wrap([{ json: {} }]))[0].json.prep_key;
  const rows = storedRows(key);
  const $p = n => n === 'Get Recent Messages' ? wrap(hist) : n === 'Slack Trigger' ? wrap([{ json: { user: ME } }]) : n === 'Gate Context' ? wrap([{ json: { confirmed } }])
    : n === 'Prepared Key' ? wrap([{ json: { prep_key: key } }]) : n === 'Read Prepared' ? wrap(rows.map(r => ({ json: r }))) : wrap([{ json: {} }]);
  return { key, sd: new Function('$', '$input', code(M, 'Prepared Series'))($p, wrap([{ json: { _alreadyDone: false } }]))[0].json }; };
const store = key => [{ cache_key: P.agg.prep_key, payload: P.agg.prep_payload, refreshed_at: new Date(Date.now() - 20000).toISOString() }];
let Y = yesTurn(sent, store);
ok(Y.key === P.agg.prep_key, 'Prepared Key works out the same key from the message', [Y.key, P.agg.prep_key]);
ok(Y.sd._seriesDirect.use === true && Y.sd._seriesDirect.p.dates === '2027-10-08,2027-10-15,2027-10-22', 'Prepared Series: use, with the three dates', Y.sd._seriesDirect);
ok(Y.sd._alreadyDone === false, 'its input passes through (Already Done? still sees it)');
const sdIn = Object.fromEntries(Object.entries(M.nodes.find(n => n.name === 'Series Direct').parameters.workflowInputs.value).map(([k, v]) => {
  const e = String(v); if (!/^=\{\{/.test(e)) return [k, e];
  return [k, new Function('$', 'return (' + e.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => n === 'Prepared Series' ? wrap([{ json: Y.sd }]) : n === 'Gate Context' ? wrap([{ json: { confirmed: true } }]) : n === 'Room Table' ? wrap([{ json: { referenceData: REF } }]) : n === 'All Bookers' ? wrap(recM('All Bookers')) : n === 'Get Booker' ? wrap([{ json: { fields: { Authority: ['Standard'] } } }]) : wrap([{ json: {} }]))];
}));
const BK = series(sdIn);
ok(BK.items.length === 3 && BK.items.every(j => j.series === true && j.confirmed === true && j.mode === '') && BK.items.map(j => j._date).join(',') === '2027-10-08,2027-10-15,2027-10-22', 'Series Direct -> Book Series books exactly those 3 dates (confirmed, series)', BK.items.map(j => [j._date, j.confirmed, j.series, j.mode]));
ok(BK.items[0].summary === 'ASIM KILIG / John Estrada / HL' && BK.items[0].start_iso === '2027-10-08T15:00:00+08:00' && BK.items[0].end_iso === '2027-10-08T18:00:00+08:00' && BK.items[0].session_type === 'VO Recording', 'with the card\'s title, times and session type', BK.items[0]);
ok(BK.agg.status === 'BOOKED_SERIES' && BK.agg.booked.length === 3, 'all three pass Book Session\'s checks at the yes', BK.agg);
const reply = new Function('$', '$input', code(M, 'Series Direct Reply'))(() => wrap([{ json: {} }]), wrap([{ json: BK.agg }]))[0].json.output;
ok(/^Booked 3 sessions:/.test(reply), 'the reply is Book Series\' own text', reply);
const Y2 = yesTurn(sent.replace('22 October', '29 October'), store);
ok(Y2.sd._seriesDirect.use === false, 'a card that differs from what was stored -> no direct booking (the model handles it)', Y2.sd._seriesDirect.reason);
ok(yesTurn(sent, () => []).sd._seriesDirect.use === false, 'nothing stored -> no direct booking');
ok(yesTurn(sent, store, false).sd._seriesDirect.use === false, 'no yes (the gate) -> no direct booking');
const old = k => [{ cache_key: P.agg.prep_key, payload: P.agg.prep_payload, refreshed_at: new Date(Date.now() - 13 * 3600000).toISOString() }];
ok(yesTurn(sent, old).sd._seriesDirect.use === false, 'stored over 12 hours ago -> no direct booking');
const bad = k => [{ cache_key: P.agg.prep_key, payload: P.agg.prep_payload.replace('Studio 7"', 'Studio 8"'), refreshed_at: new Date().toISOString() }];
ok(yesTurn(sent, bad).sd._seriesDirect.use === false, 'stored series altered -> no direct booking', yesTurn(sent, bad).sd._seriesDirect.reason);
const single = '*ASIM KILIG / HL*\n*Date:* Friday, 8 October 2027\n*Time:* 3:00 PM – 6:00 PM\n*Room:* Studio 7\n\nBook it? Reply yes or no.';
ok(yesTurn(single, store).sd._seriesDirect.use === false, 'a single-booking card -> not a series');


console.log('review (v226) - a second yes while the series is being booked');
const withLock = ageMs => key => store(key).concat([{ cache_key: 'lock-' + P.agg.prep_key, payload: '{"lock":true}', refreshed_at: new Date(Date.now() - ageMs).toISOString() }]);
let YL = yesTurn(sent, withLock(40000));
ok(YL.sd._seriesDirect.use === false && YL.sd._seriesDirect.busy === true, 'a yes 40 s after the first started booking -> busy, not a second booking', YL.sd._seriesDirect);
ok(yesTurn(sent, withLock(16 * 60000)).sd._seriesDirect.use === true, 'a lock older than 15 minutes is ignored');
ok(yesTurn(sent, withLock(40000), false).sd._seriesDirect.busy === false, 'no yes -> not busy either');
const busyOut = new Function('$', '$input', code(M, 'Series Busy Reply'))(() => wrap([{ json: {} }]), wrap([{ json: {} }]))[0].json.output;
ok(/^Still booking that series/.test(busyOut), 'the busy reply', busyOut);
const sdq = M.nodes.find(n => n.name === 'Series Busy?').parameters.conditions.conditions[0].leftValue;
ok(new Function('$', 'return (' + sdq.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(n => wrap([{ json: YL.sd }])) === 'yes', 'Series Busy? routes it to the busy reply');

console.log('review (v5 / v226) - paths the first sim did not cover');
{ // a date prepared in a different room (Book Session moved it) counts as taken for the series - the card's room is one room
  const res2 = P.res.map((r, k) => { if (k !== 1) return r; const pp = JSON.parse(r.json.prep_payload); pp.F.Room = 'Studio 8';
    return { json: Object.assign({}, r.json, { prep_payload: JSON.stringify(pp) }) }; });
  const agg2 = new Function('$', '$input', code(S, 'Aggregate'))(n => n === 'Expand Dates' ? wrap(P.items.map(j => ({ json: j }))) : wrap([{ json: PS_IN }]), wrap(res2))[0].json;
  ok(/\*Dates \(2\):\*\n- Friday, 8 October 2027\n- Friday, 22 October 2027/.test(agg2.card_text) && /Studio 7 is already booked on Friday, 15 October 2027/.test(agg2.card_text) && JSON.parse(agg2.prep_payload).inputs.dates === '2027-10-08,2027-10-22',
    'a date prepared in Studio 8 while the series is in Studio 7 -> left out and named', agg2.card_text);
  const agg4 = new Function('$', '$input', code(WF('book-series-v4.json'), 'Aggregate'))(n => n === 'Expand Dates' ? wrap(P.items.map(j => ({ json: j }))) : wrap([{ json: PS_IN }]), wrap(res2))[0].json;
  ok(/\*Dates \(3\):\*/.test(agg4.card_text), '  (v4: all three under "Studio 7")');
}
{ // a conference-room series: no engineer -> no "Engineer: " segment
  const REF3 = JSON.stringify({ rooms: [{ id: 'rl', name: 'Likha', common: true }], types: [] });
  const CR = series({ ...PS_IN, rooms: 'Likha', session_type: '', summary: 'LIKHA - Audio Post', client: '', engineer: '', description: 'Booked by: Howard Luistro | ref: ' + ME,
    reference_data: REF3, requester_text: 'book likha every friday for the next three weeks 3-6pm for our team meeting' });
  const inp = CR.agg.prep_payload ? JSON.parse(CR.agg.prep_payload).inputs : {};
  ok(CR.agg.status === 'PREPARED' && !/Engineer:\s*(\||$)/.test(inp.description || '') && /^Booked by: Howard Luistro \| ref: /.test(inp.description || ''), 'a conference-room series: description without an empty "Engineer:"', [CR.agg.status, CR.agg.reason, inp.description, CR.agg.human]);
}
{ // an M booth all-day series
  const REF4 = JSON.stringify({ rooms: [{ id: 'm3', name: 'M3', common: false }], types: [] });
  const MB = series({ ...PS_IN, rooms: 'M3', session_type: '', summary: 'M3 - Howard', client: '', engineer: '', all_day: true, time_start: '', time_end: '', description: 'Booked by: Howard Luistro | ref: ' + ME,
    reference_data: REF4, requester_text: 'book m3 for me every friday for the next three weeks' });
  ok(MB.agg.status === 'PREPARED' && /\*Dates \(3\):\*/.test(MB.agg.card_text) && /\*Time:\* All day/i.test(MB.agg.card_text), 'an M booth all-day series -> a 3-date card, all day', [MB.agg.status, MB.agg.reason, MB.agg.human, MB.agg.card_text]);
  if (MB.agg.status === 'PREPARED') {
    const inp = JSON.parse(MB.agg.prep_payload).inputs;
    const BKM = series({ ...inp, frequency: '', by_days: '', start_date: '', count: 0, until_date: '', mode: '', confirmed: true, reference_data: REF4, staff_data: '', authority: 'Standard', asked_text: '' });
    ok(BKM.items.length === 3 && BKM.items.every(j => j.all_day === true && /T00:00:00\+08:00$/.test(j.start_iso)) && BKM.agg.status === 'BOOKED_SERIES', '... and its yes books 3 all-day events', BKM.items.map(j => [j._date, j.all_day, j.start_iso]));
  }
}
{ // the model can only show a series through Prepare Series
  ok(!M.connections['Expand Series'], 'Expand Series is no longer a tool of the agent');
  const facing = M.nodes.filter(n => n.name !== 'Expand Series' && !/stickyNote/.test(n.type)).filter(n => { const p = n.parameters || {}; return /Expand Series/.test(JSON.stringify(Object.fromEntries(Object.entries(p).filter(([k]) => k !== 'jsCode')))); }).map(n => n.name);
  ok(!facing.length, 'nothing the model reads mentions Expand Series', facing);
}
console.log('wiring');
const C = M.connections;
ok(JSON.stringify(C['Move Direct?'].main[1]) === JSON.stringify([{ node: 'Prepared Series', type: 'main', index: 0 }]) && C['Series Direct?'].main[0][0].node === 'Lock Series' && C['Lock Series'].main[0][0].node === 'Series Direct'
  && C['Series Direct'].main[0][0].node === 'Series Direct Reply' && C['Series Direct Reply'].main[0][0].node === 'Send Reply'
  && C['Series Direct?'].main[1][0].node === 'Series Busy?' && C['Series Busy?'].main[0][0].node === 'Series Busy Reply' && C['Series Busy Reply'].main[0][0].node === 'Send Reply' && C['Series Busy?'].main[1][0].node === 'Already Done?',
  'Move Direct? (no) -> Prepared Series -> Series Direct? -> Lock Series -> Series Direct -> reply; else Series Busy? -> busy reply | Already Done?');
const RP = M.nodes.find(n => n.name === 'Read Prepared').parameters, LK = M.nodes.find(n => n.name === 'Lock Series');
ok(RP.matchType === 'anyCondition' && RP.filters.conditions.some(c => /'lock-' \+/.test(c.keyValue)) && LK.onError === 'continueRegularOutput' && /'lock-' \+/.test(LK.parameters.columns.value.cache_key), 'Read Prepared also reads the lock row; Lock Series never stops the booking');
ok(C['Prepare Series'].ai_tool[0][0].node === 'Jessie AI Agent', 'Prepare Series is a tool of the agent');
const SC = S.connections; ok(SC['Aggregate'].main[0][0].node === 'Series Prepared?' && SC['Series Prepared?'].main[0][0].node === 'Store Series' && SC['Store Series'].main[0][0].node === 'Series Out' && SC['Series Prepared?'].main[1][0].node === 'Series Result', 'Book Series: Aggregate -> Series Prepared? -> Store Series -> Series Out | Series Result');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
