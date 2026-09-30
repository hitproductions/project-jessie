#!/usr/bin/env node
// Offline tests for main v193 (turn log, PENDING 61, series labels, bug 10) and Book Session v67 (series booking type).
//   node scripts/sim-turn-log-bundle.js <execution-dir> <book-session-prepare-execution.json>
// <execution-dir>: real 29 Sep main executions named <id>.json - 16739 (agent turn, two Prepare Cancel calls),
// 16682 (a yes booked by Book Direct), 16685 (a change after "Booked."). Book Session: exec 16681.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v194.json'), OM = WF('imported/project-jessie-v192-imported.json');
const B = WF(process.env.BOOK || 'book-session-v67.json'), OB = WF('imported/book-session-v66-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const R = id => { const run = JSON.parse(fs.readFileSync(path.join(process.argv[2], id + '.json'))).data.resultData.runData;
  return n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null; };
const $of = (rec, over = {}) => n => { if (over[n]) return wrap(over[n]); const it = rec(n); if (!it || !it.length) throw new Error('unexecuted ' + n); return wrap(it); };

console.log('Turn Log Row');
// v194: the tool calls come from Guard Probe's toolsLog, so Guard runs first on the recorded agent output.
const gpOut = id => { const rec = R(id); const ag = rec('Jessie AI Agent'); if (!ag) return null;
  return new Function('$input', '$', code(M, 'Guard Probe'))(wrap([{ json: ag[0].json }]), $of(rec))[0].json; };
const tl = (id, input) => { const g = gpOut(id); return new Function('$', '$input', '$execution', '$workflow', code(M, 'Turn Log Row'))($of(R(id), g ? { 'Guard Probe': [{ json: g }] } : {}), wrap([{ json: input }]), { id: id }, { name: M.name })[0].json; };
let r = tl('16739', { ok: true, message: { text: '*QATIME / Jem Lim / DR*\n*Date:* ...' } });
ok(r.Exec === '16739' && r.User === 'Howard Luistro' && /qamove - november 17/.test(r.Message) && r.Path === 'agent', 'an agent turn: exec, who, their message, path', r);
ok(/Find_Booking\(booking_date=2027-11-17\) -> OK/.test(r.Tools) && /Prepare_Cancel\(title=QAMOVE \/ Jem Lim \/ DR, booking_date=2027-11-17\) -> PREPARED/.test(r.Tools), 'each tool with its key inputs and result', r.Tools);
ok(/QATIME/.test(r.Reply) && /^\d+\.\d$/.test(r.Seconds) && / — v\d+ /.test(r.Build) && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(r.Time), 'the reply, seconds, build, and a PHT timestamp', [r.Reply, r.Seconds, r.Build, r.Time]);
r = tl('16682', { ok: true, message: { text: 'Booked.' } });
ok(r.Path === 'book direct' && /Book Direct -> CREATED/.test(r.Tools) && r.Reply === 'Booked.', 'a yes booked in code: path book direct, its result', r);
r = tl('16739', { _dup: true });
ok(r.Path === 'duplicate dropped' && /nothing sent/.test(r.Reply), 'a dropped late copy is logged too');
r = new Function('$', '$input', '$execution', '$workflow', code(M, 'Turn Log Row'))(() => { throw new Error('boom'); }, wrap([{ json: {} }]), {}, {})[0].json;
ok(Object.keys(r).join() === 'Time,Exec,User,Message,Path,Tools,Reply,Claim,Seconds,Build' && /^\d{4}-\d{2}-\d{2} /.test(r.Time), 'never throws: every read failing still gives a row with the same ten columns');
const to = (n, b = 0) => ((((M.connections[n] || {}).main || [])[b]) || []).map(t => t.node);
ok(JSON.stringify(to('Send Reply')) === '["Clear Ack","Turn Log Row"]' && JSON.stringify(to('Duplicate?', 0)) === '["Clear Ack","Turn Log Row"]' && JSON.stringify(to('Turn Log Row')) === '["Log Turn"]', 'wiring: Send Reply and the dropped-duplicate branch -> Turn Log Row -> Log Turn; Clear Ack unchanged');
const lt = M.nodes.find(n => n.name === 'Log Turn');
ok(lt.parameters.sheetName.value === 'Turn Log' && lt.onError === 'continueRegularOutput' && lt.parameters.documentId.value === '1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo', 'Log Turn appends to the Jessie Log sheet, tab Turn Log, and cannot fail a turn');
ok(!/\$\('(?:Book Session|Prepare Booking|Cancel Booking|Move Booking|Find Booking|Room Availability|Prepare Cancel|Book Series|Expand Series)'\)/.test(code(M, 'Turn Log Row')), 'never reads a tool node (gotcha 11)');
ok(!/\$\('Jessie AI Agent'\)/.test(code(M, 'Turn Log Row')) && !/\$\((?!['"])/.test(code(M, 'Turn Log Row')), 'v194: never reads the AI Agent, never looks a node up by a variable name (v193 failed on both: "Unknown error")');

console.log('Booked For - PENDING 61, a "no" to a move card');
{ const rec = R('16685'), ME = 'U08V3CKDGJF', T = 1790690000;
  const SUM = '*ORANGE / Sasa Abella / AEG*\n*Date:* Thursday, September 30, 2027\n*Time:* 10:00 AM – 11:00 AM\n*Room:* Studio 7\n\n_check 1c7b1094_\n\nBook it? Reply yes or no.';
  const CARD = '*ORANGE / Sasa Abella / AEG*\n*Now:* Thursday, September 30, 2027, 10:00 AM – 11:00 AM, Studio 7\n*Moving to:* Thursday, September 30, 2027, 3:00 PM – 6:00 PM, Studio 7\n\nMove it? Reply yes or no.';
  const hist = newer => newer.map((x, i) => ({ json: { ts: String(T + 90 - i * 10), ...x } })).concat([{ json: { ts: String(T + 40), text: 'Booked.', bot_id: 'B1' } }, { json: { ts: String(T + 30), text: 'yes', user: ME } }, { json: { ts: String(T + 20), text: SUM, bot_id: 'B1' } }]);
  const bf = (w, newer) => { const h = hist(newer); return new Function('$', '$input', code(w, 'Booked For'))(n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([{ json: h[0].json }]) : wrap(rec(n) || [{ json: {} }]), wrap([{ json: {} }]))[0].json; };
  const seq = [{ text: 'no', user: ME }, { text: CARD, bot_id: 'B1' }, { text: '3-6pm not 6-7', user: ME }, { text: CARD, bot_id: 'B1' }, { text: 'move it to 3-6pm', user: ME }];
  let b = bf(M, seq);
  ok(!b.changeJustBooked && !b.moveStart && /THEY SAID NO TO THE MOVE/.test(b.notice), '"no" to the move card -> no move, the model is told nothing is moved', [b.changeJustBooked, b.moveStart]);
  ok(bf(OM, seq).changeJustBooked === true, '  (v192: the change still counted - the corrected move offered again)');
  b = bf(M, [{ text: 'make it 5pm instead', user: ME }, { text: 'Got it, move cancelled! What would you like to do instead?', bot_id: 'B1' }].concat(seq));
  ok(b.changeJustBooked === true && b.moveStart === '17:00', 'a new change after that -> read as usual (5 PM)', [b.changeJustBooked, b.moveStart, b.moveEnd]);
  b = bf(M, [{ text: 'no', user: ME }, { text: 'Which room would you like instead?', bot_id: 'B1' }, { text: 'move it to 3-6pm', user: ME }]);
  ok(!/THEY SAID NO TO THE MOVE/.test(b.notice || ''), 'a "no" to anything other than a move card is not treated as this'); }

console.log('Guard Probe - series labels (PENDING 59) and "this week" dates (bug 10)');
{ const rec = R('16739');
  const gp = (w, output, steps, said) => new Function('$input', '$', code(w, 'Guard Probe'))(wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
    n => n === 'Slack Trigger' && said ? wrap([{ json: { text: said, user: 'U08V3CKDGJF' } }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
  const SER = '*QASERIES / Jem Lim / DR*\n*Dates (3):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027\n- Tuesday, 16 November 2027\n Time: 10:00 AM – 12:00 PM\n Room: Studio 8\n Session Type: VO Recording\n Client: Jem Lim\n Engineer: Daryl Reyes\n Department: Audio Post\n*Booked by:* Howard Luistro\n\nBook it? Reply yes or no.';
  let o = gp(M, SER, []);
  ok(/\n\*Time:\* 10:00 AM – 12:00 PM\n\*Room:\* Studio 8\n\*Session Type:\* VO Recording\n\*Client:\* Jem Lim\n\*Engineer:\* Daryl Reyes\n\*Department:\* Audio Post\n/.test(o), 'series summary: " Time: ..." -> "*Time:* ..." on every detail line', o);
  ok(/\n Time: /.test(gp(OM, SER, [])), '  (v192: the leading space, no bold label)');
  ok(gp(M, 'The Time: 3pm slot is taken.', []) === 'The Time: 3pm slot is taken.', 'not a series summary -> untouched');
  const RA = d => ({ action: { tool: 'Room_Availability', toolInput: { window_start: d + 'T10:00:00+08:00', window_end: d + 'T12:00:00+08:00', window_room: 'Studio 7' } }, observation: '[{"status":"OK"}]' });
  const wk = ['2027-10-04', '2027-10-05', '2027-10-06', '2027-10-07', '2027-10-08'].map(RA);
  o = gp(M, 'Studio 7 is free every morning, 10 AM to 12 PM.', wk, 'is studio 7 free this week in the morning?');
  ok(/\n\nDates checked: Monday, October 4 to Friday, October 8, 2027\.$/.test(o), '"this week", no date in the reply -> "Dates checked: Monday, October 4 to Friday, October 8, 2027."', o);
  ok(!/Dates checked/.test(gp(M, 'Studio 7 is free on Monday and Tuesday mornings.', wk, 'is studio 7 free this week?')), 'the reply names days -> nothing added');
  ok(!/Dates checked/.test(gp(M, 'Studio 7 is free then.', wk, 'is studio 7 free tomorrow at 10am?')), 'not a week question -> nothing added');
  o = gp(M, 'Studio 7 is free both days.', [RA('2027-10-12'), RA('2027-10-14')], 'is studio 7 free next week?');
  ok(/Dates checked: Tuesday, October 12; Thursday, October 14, 2027\./.test(o), 'days that are not a run are listed', o); }

console.log('Book Session v67 - each date of a series gets its booking type');
{ const run = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
  const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
  const REQ0 = rec('When Executed by Another Workflow')[0].json;
  const cc = (w, req) => { const Rq = [{ json: { ...REQ0, ...req } }];
    const $c = n => { const it = n === 'When Executed by Another Workflow' ? Rq : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
    return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json; };
  const SERIES = { mode: '', series: true, confirmed: true, bookingType: '' };
  let c = cc(B, SERIES);
  ok(/\| Type: External \|/.test(c.final_description || ''), 'a series date with no booking type from the model -> "Type: External" from the client record', c.final_description || c.reason);
  ok(!/Type:/.test(cc(OB, SERIES).final_description || ''), '  (v66: no Type on series events)');
  c = cc(B, { ...SERIES, bookingType: 'Personal' });
  ok(/\| Type: Personal \|/.test(c.final_description || ''), 'a booking type that was sent is kept');
  c = cc(B, { mode: '', series: false, confirmed: true, bookingType: '' });
  ok(!/Type:/.test(c.final_description || ''), 'not a series (a single confirmed booking) -> unchanged: its type comes from the checked summary'); }

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
