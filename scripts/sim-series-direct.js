#!/usr/bin/env node
// Offline round trip for Book Series v4 + main v225 (deterministic series; PENDING 90): Prepare Series runs every date
// through Book Session's real prepare code and writes the card; Guard Probe sends it as written; at the yes Prepared Key
// + Prepared Series read the stored series back, and Series Direct books exactly the dates on the card - no model.
//   node scripts/sim-series-direct.js <main-execution.json>   (its All Bookers output feeds Book Session)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v225.json'), S = WF(process.env.SERIES || 'book-series-v4.json'), B = WF(process.env.BOOK || 'book-session-v92.json');
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
ok(/\*Dates \(2\):\*\n- Friday, 8 October 2027\n- Friday, 22 October 2027\n/.test(T2.agg.card_text) && /Heads up: Studio 7 is taken on Friday, 15 October 2027 - that date left out\./.test(T2.agg.card_text), 'a date whose room is taken is left out and named', T2.agg.card_text);
const Q = series({ ...PS_IN, session_type: '', requester_text: 'book studio 7 every friday for the next three weeks for project asim kilig 3-6pm. client john estrada' });
ok(Q.agg.status === 'REJECTED' && /Ask exactly this/.test(Q.agg.human), 'a question (no session type) goes back as Book Session wrote it', [Q.agg.reason, Q.agg.human]);
const ALL = series(PS_IN, ['2027-10-08', '2027-10-15', '2027-10-22']);
ok(ALL.agg.status === 'REJECTED' && /taken on every one/.test(ALL.agg.human), 'taken on every date -> nothing prepared, says so', ALL.agg.human);

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
console.log('wiring');
const C = M.connections;
ok(JSON.stringify(C['Move Direct?'].main[1]) === JSON.stringify([{ node: 'Prepared Series', type: 'main', index: 0 }]) && C['Series Direct?'].main[1][0].node === 'Already Done?' && C['Series Direct'].main[0][0].node === 'Series Direct Reply' && C['Series Direct Reply'].main[0][0].node === 'Send Reply', 'Move Direct? (no) -> Prepared Series -> Series Direct? -> Series Direct -> Series Direct Reply -> Send Reply; else Already Done?');
ok(C['Prepare Series'].ai_tool[0][0].node === 'Jessie AI Agent', 'Prepare Series is a tool of the agent');
const SC = S.connections; ok(SC['Aggregate'].main[0][0].node === 'Series Prepared?' && SC['Series Prepared?'].main[0][0].node === 'Store Series' && SC['Store Series'].main[0][0].node === 'Series Out' && SC['Series Prepared?'].main[1][0].node === 'Series Result', 'Book Series: Aggregate -> Series Prepared? -> Store Series -> Series Out | Series Result');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
