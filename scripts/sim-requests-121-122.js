#!/usr/bin/env node
// PENDING 121 + 122 (27 Oct), room requests: Move Booking v40 (the request follows a changed booking that still overlaps; placed
// only when it no longer does), Slack Interactions v49 (one answer at a time - the Claim column; the requester's "they'll move it"
// opens the booking the row names now; a request card that ended is not written back), Consent Sweep v4 (waits on a fresh claim).
// Usage: node scripts/sim-requests-121-122.js [move v40] [si v49] [sweep v4]
const fs = require('fs');
const L = (i, d) => JSON.parse(fs.readFileSync(process.argv[i] || d, 'utf8'));
const mv = L(2, 'workflows/move-booking-v40.json'), si = L(3, 'workflows/slack-interactions-v49.json'), sw = L(4, 'workflows/consent-sweep-v4.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (!si.nodes.some(n => n.name === 'Claim Check')) { console.log('0 ok, 0 failed (an older build: PENDING 121/122 not in it)'); process.exit(0); }
const node = (wf, n) => wf.nodes.find(x => x.name === n), code = (wf, n) => node(wf, n).parameters.jsCode;
const wrap = it => ({ first: () => it[0], all: () => it });
const nx = (wf, n) => ((wf.connections[n] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
const run = (wf, name, input, outs, exec) => new Function('$', '$input', '$execution', code(wf, name))(
  n => { if (!(n in outs)) throw new Error('not run: ' + n); return wrap(outs[n]); }, wrap(input || []), exec || { id: 'ex1' }).map(i => i.json);

const INC = { id: 'old1', d: '2027-10-28', s: '10:00', e: '12:00', r: 'Studio F', t: 'ORANGE / Jem Lim / DR', st: 'VO Recording' };
const ROW = { 'Request ID': 'R1', 'Status': 'PENDING', 'Kind': 'PREEMPT', 'Room/Booth': 'Studio F', 'Req Start': '2027-10-28T10:00:00+08:00', 'Req End': '2027-10-28T12:00:00+08:00',
  'Incumbent Event Id': 'old1', 'Incumbent Title': INC.t, 'Requester': 'U1', 'Requester Name': 'Howard Luistro', 'Approver': 'U2', 'Approver Name': 'Daryl Reyes',
  'Messages': JSON.stringify({ m: [{ ch: 'D1', ts: '1.1' }], inc: INC }), 'Claim': '' };

console.log('121 - Move Booking v40: the Consent Hook');
const hook = (RB, rows, newId) => run(mv, 'Consent Hook', (rows || [ROW]).map(json => ({ json })), { 'Resolve Booking': [{ json: Object.assign({ original_id: 'old1', title: INC.t }, RB) }],
  'Create Replacement': [{ json: { id: newId === undefined ? 'new9' : newId } }] })[0];
let h = hook({ original_id: 'other' , new_start: '2027-10-28T14:00:00+08:00', new_end: '2027-10-28T16:00:00+08:00', location: 'Studio F' });
ok(!h.hasMatch && !h.retarget, 'a booking no request names -> nothing');
h = hook({ new_start: '2027-10-28T14:00:00+08:00', new_end: '2027-10-28T16:00:00+08:00', location: 'KDC Plaza-Top Level-Studio F (12)' });
ok(h.hasMatch && !h.retarget && h.matched['Request ID'] === 'R1', 'moved out of the requested time -> placed (Finalize)');
h = hook({ new_start: '2027-10-28T10:00:00+08:00', new_end: '2027-10-28T12:00:00+08:00', location: 'Studio 7' });
ok(h.hasMatch, 'moved to another room at the same time -> placed');
h = hook({ new_start: '2027-10-28T12:00:00+08:00', new_end: '2027-10-28T14:00:00+08:00', location: 'Studio F' });
ok(h.hasMatch, 'moved to start right when the request ends (12:00) -> no overlap -> placed');
h = hook({ new_start: '2027-10-28T11:00:00+08:00', new_end: '2027-10-28T13:00:00+08:00', location: 'Studio F', title: 'ORANGE / Jem Lim / DR' });
const M = JSON.parse((h.row || {}).Messages || '{}');
ok(!h.hasMatch && h.retarget && h.row['Request ID'] === 'R1' && h.row['Incumbent Event Id'] === 'new9' && M.inc.id === 'new9' && M.inc.s === '11:00' && M.inc.e === '13:00' && M.inc.d === '2027-10-28'
   && M.inc.st === 'VO Recording' && M.m.length === 1, 'moved within the slot -> the request stays open and follows the booking (new id, times kept in Messages)', h);
h = hook({ new_start: '2027-10-28T10:00:00+08:00', new_end: '2027-10-28T12:00:00+08:00', location: 'Studio F', title: 'ORANGE / Jem Lim / PL' });
ok(!h.hasMatch && h.retarget && h.row['Incumbent Title'] === 'ORANGE / Jem Lim / PL', 'only the engineer / title changed -> stays open, follows the booking (the old result: FAILED "still taken")');
h = hook({ new_start: 'x', new_end: 'y', location: 'Studio F' });
ok(!h.hasMatch && h.retarget, 'a time that cannot be read -> treated as overlapping (never placed into a taken room)');
h = hook({ new_start: '2027-10-28T11:00:00+08:00', new_end: '2027-10-28T13:00:00+08:00', location: 'Studio F' }, undefined, '');
ok(!h.hasMatch && !h.retarget, 'no new event id -> nothing written (as before, minus the failed placement)');
h = hook({ new_start: '2027-10-28T11:00:00+08:00', new_end: '2027-10-28T13:00:00+08:00', location: 'Studio F' }, [Object.assign({}, ROW, { Status: 'REJECTED' })]);
ok(!h.hasMatch && !h.retarget, 'an ended request -> nothing');
ok(nx(mv, 'Place If Consent?') === 'Call Finalize | Retarget?' && nx(mv, 'Retarget?') === 'Retarget Data | Notify?' && nx(mv, 'Retarget Data') === 'Retarget Row' && nx(mv, 'Retarget Row') === 'Notify?'
   && node(mv, 'Retarget Row').parameters.operation === 'update' && node(mv, 'Retarget Row').parameters.columns.matchingColumns.join() === 'Request ID' && node(mv, 'Retarget Row').onError === 'continueRegularOutput',
   'wiring: not placed -> Retarget? -> Retarget Data -> Retarget Row (Consent Requests, by Request ID, never fails the move) -> Notify?');
ok(/_M\.inc && _M\.inc\.id\) b = Object\.assign\(\{\}, b, _M\.inc\)/.test(code(si, 'Build Change C')), 'Slack Interactions: "they\'ll move it" opens the booking the row names now');

console.log('122 - one answer at a time (Slack Interactions v49)');
const CS = [{ json: { user: 'U2', channel: 'D2' } }];
const act = (row, action, w) => run(si, 'Request Act', [{ json: row }], { 'Check Signature': CS, 'Read Request': [{ json: { payload: { actions: [{ action_id: action, value: JSON.stringify({ id: 'R1', w }) }] } } }] })[0];
const now = new Date().toISOString(), old = new Date(Date.now() - 5 * 60000).toISOString();
ok(act(ROW, 'cr_keep', 'a1').go === 0, 'Keep, no claim -> acts (go 0)');
ok(act(Object.assign({}, ROW, { Claim: 'ex7@' + now }), 'cr_giveup', 'a1').go === 3, 'Give it up while another answer holds a fresh claim -> nothing (go 3)');
ok(act(Object.assign({}, ROW, { Claim: 'ex7@' + old }), 'cr_keep', 'a1').go === 0, 'a claim older than 2 minutes (a run that stopped) -> acts');
ok(nx(si, 'Request Act') === 'Claim?' && nx(si, 'Claim?') === 'Claim Row | Act Route' && nx(si, 'Claim Row') === 'Write Claim?' && nx(si, 'Write Claim?') === 'Claim Data | Claim Check'
   && nx(si, 'Claim Data') === 'Write Claim' && nx(si, 'Write Claim') === 'Wait Claim' && nx(si, 'Wait Claim') === 'Read Claim' && nx(si, 'Read Claim') === 'Claim Check' && nx(si, 'Claim Check') === 'Act Route'
   && nx(si, 'Cleared Move?') === 'Read Cache C | Claim Row', 'wiring: Request Act -> Claim? -> Claim Row -> Write Claim -> Wait Claim (2 s) -> Read Claim -> Claim Check -> Act Route; "They gave it up" too');
ok(node(si, 'Wait Claim').parameters.amount === 2 && node(si, 'Write Claim').parameters.columns.matchingColumns.join() === 'Request ID' && node(si, 'Read Claim').alwaysOutputData === true, 'Wait 2 s; Write Claim by Request ID; Read Claim always answers');
// two answers at once: both read PENDING, both claim; the later write wins, the earlier finds someone else's claim
const sheet = Object.assign({}, ROW);
const claim = (ex, A) => run(si, 'Claim Row', [{ json: A }], {}, { id: ex })[0];
const A1 = act(ROW, 'cr_keep', 'a1'), A2 = act(ROW, 'cr_giveup', 'a1');
const c1 = claim('ex1', A1), c2 = claim('ex2', A2);
ok(!c1.skip && !c2.skip && /^ex1@/.test(c1.Claim) && /^ex2@/.test(c2.Claim), 'both claim (ex1 Keep, ex2 Give it up)');
sheet.Claim = c1.Claim; sheet.Claim = c2.Claim;   // ex2 wrote last
const check = (CR, A) => run(si, 'Claim Check', [], { 'Claim Row': [{ json: CR }], 'Read Claim': [{ json: sheet }], 'Request Act': [{ json: A }] })[0];
const k1 = check(c1, A1), k2 = check(c2, A2);
ok(k1.go === 3 && k1.mine === false && k2.go === 2 && k2.mine === true, 'read back: Keep finds Give it up\'s claim -> does nothing; Give it up acts - never both', { k1, k2 });
sheet.Status = 'REJECTED';
const k3 = check(c2, A2);
ok(k3.go === 4 && k3.mine === false, 'the request ended before the read-back -> its messages redrawn, nothing done');
ok(run(si, 'Claim Row', [{ json: Object.assign({}, A1, { row: Object.assign({}, ROW, { Claim: 'exZ@' + now }) }) }], {})[0].skip === true, 'a fresh claim already there -> no claim written');
// the requester's "They gave it up" (the Change C modal) - same claim, Give Up Plan says why when it may not act
const RC = [{ json: { rid: 'R1', move: false } }];
const cr = run(si, 'Claim Row', [], { 'Read Cleared': RC, 'Read Requests C': [{ json: ROW }] }, { id: 'ex3' })[0];
ok(!cr.skip && cr['Request ID'] === 'R1', '"They gave it up" claims too');
const sheet2 = Object.assign({}, ROW, { Claim: 'ex9@' + now });
const kb = run(si, 'Claim Check', [], { 'Claim Row': [{ json: cr }], 'Read Claim': [{ json: sheet2 }], 'Read Cleared': RC })[0];
ok(kb.go === 2 && kb.mine === false, '... and someone else\'s claim won -> Give Up Plan with mine: false');
const gp = run(si, 'Give Up Plan', [{ json: kb }], { 'Check Signature': [{ json: { user: 'U1', channel: 'D1' } }], 'Read Cleared': RC, 'Read Requests C': [{ json: ROW }], 'Claim Check': [{ json: kb }] })[0];
ok(gp.ok === false && /Someone answered this request at the same time – nothing was changed\./.test(gp.text), 'Give Up Plan: "Someone answered this request at the same time – nothing was changed."', gp);
const gp2 = run(si, 'Give Up Plan', [{ json: { go: 2, mine: true } }], { 'Check Signature': [{ json: { user: 'U1', channel: 'D1' } }], 'Read Cleared': RC, 'Read Requests C': [{ json: ROW }], 'Claim Check': [{ json: { go: 2, mine: true } }] })[0];
ok(gp2.ok === true && gp2.cancel.event_id === 'old1', 'its claim held -> the booking is given up as before');
const moved = Object.assign({}, ROW, { 'Incumbent Event Id': 'new9', Messages: JSON.stringify({ m: [], inc: Object.assign({}, INC, { id: 'new9' }) }) });
const gp3 = run(si, 'Give Up Plan', [{ json: { go: 2, mine: true } }], { 'Check Signature': [{ json: { user: 'U2', channel: 'D2' } }], 'Request Act': [{ json: { row: ROW, by: 'Daryl Reyes' } }],
  'Read Claim': [{ json: moved }], 'Claim Check': [{ json: { mine: true } }] })[0];
ok(gp3.ok === true && gp3.cancel.event_id === 'new9', 'Give it up after the booking moved within the slot (Move v40) -> the booking the row names now');

console.log('122 - Consent Sweep v4');
const sweep = rows => run(sw, 'Sweep Decide', rows.map(json => ({ json })), {});
const due = Object.assign({}, ROW, { Kind: 'MBOOTH', Deadline: new Date(Date.now() - 60000).toISOString() });
ok(sweep([due]).some(j => j._sweepAction === 'book'), 'past its deadline, no claim -> booked as before');
ok(!sweep([Object.assign({}, due, { Claim: 'ex1@' + now })]).some(j => j._sweepAction), 'past its deadline, an answer being acted on -> waits a round');

console.log('122 - a "Pick another room" booking does not write an ended request card back');
const D = { channel: 'D1', ts: '1.1', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'old card' } }, { type: 'actions', elements: [{ action_id: 'cr_withdraw' }] }], text: 'x' };
const sc = msg => run(si, 'Source Check', [{ json: { ok: true, messages: [msg] } }], { 'Source Done': [{ json: D }] });
ok(sc({ ts: '1.1', blocks: [{ type: 'section', block_id: 'src_head' }, { type: 'context', block_id: 'src_status' }] }).length === 1, 'the "⏳" line still there -> updated as before');
ok(sc({ ts: '1.1', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Request withdrawn.' } }] }).length === 0, 'the card was redrawn meanwhile (request ended) -> left as it is');
ok(nx(si, 'Source Done') === 'Get Source 2' && nx(si, 'Get Source 2') === 'Source Check' && nx(si, 'Source Check') === 'Update Source', 'wiring: Source Done -> Get Source 2 -> Source Check -> Update Source');

console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
