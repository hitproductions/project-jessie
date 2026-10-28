#!/usr/bin/env node
// Slice 2 - room requests (21 Oct; docs/design/slice-2-approvals.md), offline, through the real nodes:
//   Jessie — Request Messages v1 (the messages, open and end), Open Consent Request v12 (the row: real ids, engineer as Approver 2,
//   names, the same request twice), Finalize Consent v11 (the row read again, WITHDRAWN, messages), Consent Sweep v3 (no answer),
//   Room Availability v23 (busy_detail), Book Session v120 (request_ok), Slack Interactions v37 (Booked – ask to use, Send request,
//   the request buttons, I've cleared it with them).
// Usage: node scripts/sim-approvals.js [request-messages] [open-consent] [finalize] [sweep] [room-availability] [book-session] [si]
const fs = require('fs');
const A = process.argv.slice(2);
const load = (i, f) => JSON.parse(fs.readFileSync((A[i] && A[i].length) ? A[i] : f, 'utf8'));
const RM = load(0, 'workflows/request-messages-v1.json'), OCR = load(1, 'workflows/open-consent-request-v12.json'), FIN = load(2, 'workflows/finalize-consent-v11.json');
const SW = load(3, 'workflows/consent-sweep-v3.json'), RA = load(4, 'workflows/room-availability-v23.json'), BS = load(5, 'workflows/book-session-v120.json');
const SI = load(6, 'workflows/slack-interactions-v37.json');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const run = async (wf, name, input, outs) => {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(wf, name).parameters.jsCode + '\n}).call(this);').call({ helpers: {} }, $, $input); };
const nx = (wf, k) => ((wf.connections[k] || {}).main || []).map(o => (o || []).map(c => c.node).filter(x => !/^(?:Ops Alert|Ask DM|Step 2 DM|Cancel DM)$/.test(x)).join('+'));   // v46: the side branches left out
const J = x => { try { return JSON.parse(x); } catch (e) { return null; } };
const HOWARD = 'U08V3CKDGJF';
const B = (name, slack, info, auth, dept) => ({ id: 'b' + slack, fields: { Name: name, 'Slack User ID': slack, Info: info, Authority: auth ? [auth] : [], Department: [dept || 'Music'], Initials: 'X' } });
const bookers = [B('Howard Luistro', HOWARD, 'Post Engineer', 'HAIST Dev', 'Audio Post'), B('Camy Caridad', 'U08JL17A50A', 'Voice Caster', 'Standard'),
  B('Celeste Cruz', 'U7', 'Producer', 'Dept Head'), B('Daryl Reyes', 'U2', 'Music Engineer'), B('Angelo Villegas', 'U3', 'Music Arranger, Goes by Anj.'), B('Jem Santos', 'U9', 'Voice Talent')];
const ST = (t, pri, last, rank) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': last, 'Preemption Rank': rank, 'Engineer Role Required': ['Music Engineer'] } });
const sessionTypes = [ST('Celebrity Recording', ['rf', 'rc'], ['r7'], 3), ST('VO Recording', ['r7', 'rf'], ['r8'], 1), ST('Music Mixing', ['r3'], [], 2)];
const rooms = FX.rooms.concat([{ id: 'm4', fields: { 'Room Name': 'M4', 'Room Type': ['M Booth'] } }]);
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const PAY = JSON.stringify({ summary: 'SONG 2 / Netflix / HL', session_type: 'Celebrity Recording', rooms: 'Studio F' });
const baseRow = (o) => Object.assign({ 'Request ID': '20271021-U7', 'Status': 'PENDING', 'Kind': 'PREEMPT', 'Requester': 'U7', 'Requester Name': 'Celeste Cruz',
  'Approver': 'U2', 'Approver Name': 'Daryl Reyes', 'Approver 2': 'U3', 'Approver 2 Name': 'Angelo Villegas', 'Room/Booth': 'Studio F',
  'Req Start': '2027-10-22T14:00:00+08:00', 'Req End': '2027-10-22T16:00:00+08:00', 'Incumbent Event Id': 'e1', 'Incumbent Title': 'SONG / Jem Lim / DR',
  'Deadline': '2027-10-22T13:00:00+08:00', 'Req Payload': PAY,
  'Messages': JSON.stringify({ m: [], inc: { id: 'e1', d: '2027-10-22', s: '14:00', e: '16:00', r: 'Studio F', t: 'SONG / Jem Lim / DR', st: 'VO Recording' } }) }, o || {});
const ids = bl => bl.map(b => b.block_id || b.type);
const btns = bl => bl.filter(b => b.type === 'actions').flatMap(b => b.elements.map(e => e.action_id + ':' + e.text.text));
const uniq = bl => bl.every(b => { const a = (b.elements || []).map(e => e.action_id).filter(Boolean); return new Set(a).size === a.length; });

(async () => {
  console.log('Jessie — Request Messages: open');
  const render = async (mode, row, extra) => (await run(RM, 'Render', [], { 'When Executed by Another Workflow': [{ json: { mode, row: JSON.stringify(row), extra: JSON.stringify(extra || {}) } }] })).map(i => i.json);
  let o = await render('open', baseRow());
  ok(o.length === 3 && o.map(x => x.r).join() === 'r,a1,a2' && o.every(x => x.op === 'post' && x.channel === HOWARD), 'priority: the requester, the booker and the engineer - all to Howard while testing', o.map(x => x.r + '>' + x.channel));
  const req = o[0], a1 = o[1], a2 = o[2];
  ok(/⏳ \*Requested – Studio F\*/.test(req.blocks[0].text.text) && /Daryl Reyes \(booker\), Angelo Villegas \(engineer\)/.test(req.blocks[0].text.text) && /Fri, Oct 22, 1:00 PM/.test(req.blocks[0].text.text),
     'the requester\'s card: who was asked, by when', req.blocks[0].text.text);
  ok(btns(req.blocks).join() === 'cr_cleared:I’ve cleared it with them,cr_withdraw:Withdraw request,cr_pick:Pick another room' && uniq(req.blocks), 'the requester\'s buttons');
  const cv = J(req.blocks[1].elements[0].value), pv = J(req.blocks[1].elements[2].value);
  ok(cv.id === '20271021-U7' && cv.as === 'U2' && cv.inc.id === 'e1' && pv.d === '2027-10-22' && pv.s === '14:00' && pv.p === 'Celebrity Recording', 'values: the request, their booking, and the form at the same date and time', [cv, pv]);
  ok(/Test: this is for Celeste Cruz/.test(JSON.stringify(req.blocks)) && /Test: this is for Daryl Reyes/.test(JSON.stringify(a1.blocks)) && /Test: this is for Angelo Villegas/.test(JSON.stringify(a2.blocks)), 'each marked who it is really for');
  const RM4 = /v4 \(Howard, 26 Oct\)/.test(JSON.stringify(RM.nodes));   // Request Messages v4: both bookings as cards
  ok((RM4 ? /^🙋 Celeste Cruz is requesting a new booking to take over your existing one\. Their Celebrity Recording session takes priority over your VO Recording session in that room\.\n\n\*Their requested booking:\*\n\*SONG 2 \/ Netflix \/ HL\*\n\*Date:\* Friday, October 22, 2027\n\*Time:\* 2:00 PM – 4:00 PM\n\*Room:\* Studio F\n\n\*Your existing booking:\*\n\*SONG \/ Jem Lim \/ DR\*\n\*Date:\* Friday, October 22, 2027/.test(a1.blocks[0].text.text)
        && /Please answer by/.test(JSON.stringify(a1.blocks[a1.blocks.length - 2]))
     : /Celeste Cruz asks for Studio F/.test(a1.blocks[0].text.text) && /takes priority over VO Recording/.test(a1.blocks[0].text.text) && /Your booking: \*SONG \/ Jem Lim \/ DR\* · Fri, Oct 22 · 2:00 PM – 4:00 PM/.test(a1.blocks[0].text.text))
     && btns(a1.blocks).join() === 'cr_move:Move my booking,cr_giveup:Give it up,cr_keep:Keep my booking' && uniq(a1.blocks), 'the booker: who asks, why, their booking, Move / Give it up / Keep', a1.blocks[0].text.text);
  const mv = J(a1.blocks[1].elements[0].value);
  ok(mv.id === 'e1' && mv.d === '2027-10-22' && mv.s === '14:00' && mv.st === 'VO Recording' && mv.rid === '20271021-U7' && mv.w === 'a1' && J(a2.blocks[1].elements[2].value).w === 'a2',
     'Move my booking carries the booking (the Change form) and who pressed it', mv);
  ok(a1.blocks[1].elements[1].confirm && a1.blocks[1].elements[2].confirm && !a1.blocks[1].elements[0].confirm, 'Give it up and Keep ask "are you sure?" first');
  o = await render('open', baseRow({ 'Kind': 'MBOOTH', 'Room/Booth': 'M4', 'Approver': 'U9', 'Approver Name': 'Jem Santos', 'Approver 2': '', 'Approver 2 Name': '', 'Incumbent Title': 'M4 - Jem',
    'Deadline': '2027-10-22T10:00:00+08:00', 'Req Payload': JSON.stringify({ summary: 'M4 - Celeste', session_type: '', rooms: 'M4' }) }));
  ok(o.length === 2 && /asks to use M4/.test(o[1].blocks[0].text.text) && /No answer by Fri, Oct 22, 10:00 AM: it’s booked for them/.test(o[1].blocks[0].text.text)
     && btns(o[1].blocks).join() === 'cr_allow:Let them use it,cr_keep:Keep it', 'shared booth: the holder - Let them use it / Keep it, the timeout said up front', o[1].blocks[0].text.text);
  ok(btns(o[0].blocks)[0] === 'cr_attest:I’ve cleared it with them' && o[0].blocks[1].elements[0].confirm && J(o[0].blocks[1].elements[2].value).p === '__booth', 'shared booth: I\'ve cleared it with them books at once (after a confirm); Pick another room opens an M booth form');

  console.log('Jessie — Request Messages: end');
  const msgs = { m: [{ r: 'r', u: 'U7', c: 'D1', t: '1.1' }, { r: 'a1', u: 'U2', c: 'D1', t: '1.2' }, { r: 'a2', u: 'U3', c: 'D1', t: '1.3' }], inc: J(baseRow()['Messages']).inc };
  const ended = async (st, extra, more) => render('end', baseRow(Object.assign({ 'Status': st, 'Messages': JSON.stringify(msgs) }, more || {})), extra);
  o = await ended('DONE', { how: 'move-hook', event: { id: 'n9', title: 'SONG 2 / Netflix / HL' } });
  ok(o.length === 3 && o.every(x => x.op === 'update' && x.channel === 'D1') && o.map(x => x.ts).join() === '1.1,1.2,1.3', 'every message updated in place (channel + ts kept on the row)');
  ok(/✅ \*Booked\.\* Daryl Reyes moved their booking/.test(o[0].blocks[0].text.text) && ids(o[0].blocks).join().indexOf('bk_n9,bka_n9,actions') === 0 && btns(o[0].blocks).join().indexOf('bk_change:Change,bk_cancel:Cancel,open_book:Book another') === 0,
     'booked: the requester\'s card becomes the Booked card with Change / Cancel and Book another', o[0].blocks[0].text.text);
  ok(/✓ Done – Studio F is Celeste’s from 2:00 PM\. Your booking was moved\./.test(JSON.stringify(o[1].blocks)) && (/v4 \(Howard, 26 Oct\)/.test(JSON.stringify(RM.nodes)) ? btns(o[1].blocks).join() === 'my_bookings:My bookings'
     && /^Celeste Cruz asks for the following booking:\n\n\*Date:\* Friday, October 22, 2027\n\*Time:\* 2:00 PM – 4:00 PM\n\*Room:\* Studio F$/.test(o[1].blocks[0].text.text) : !btns(o[1].blocks).length),
     'the booker: done - who asked for which booking, how it ended, My bookings only (v4; no buttons before)');
  o = await ended('REJECTED', { how: 'kept', by: 'Daryl Reyes' });
  ok(/❌ \*Daryl Reyes is keeping Studio F\.\*/.test(o[0].blocks[0].text.text) && btns(o[0].blocks).join() === 'cr_pick:Pick another room,my_bookings:My bookings'
     && /You kept it/.test(JSON.stringify(o[1].blocks)) && /Daryl Reyes kept it/.test(JSON.stringify(o[2].blocks)), 'kept: said to the requester (Pick another room); "You kept it" / "Daryl Reyes kept it"');
  o = await ended('EXPIRED', { how: 'sweep-expired' });
  ok(/⌛ \*No answer by Fri, Oct 22, 1:00 PM – Studio F stays booked\.\*/.test(o[0].blocks[0].text.text) && /your booking stays/.test(JSON.stringify(o[1].blocks)), 'no answer: said on both sides');
  o = await ended('WITHDRAWN', { how: 'withdrawn' });
  ok(/Request withdrawn/.test(o[0].blocks[0].text.text) && /Withdrawn – nothing to do/.test(JSON.stringify(o[2].blocks)), 'withdrawn');
  o = await ended('FAILED', { how: 'move-hook', why: 'it’s still taken then' });
  ok(/Couldn’t book Studio F after all\* – it’s still taken then/.test(o[0].blocks[0].text.text), 'could not be placed', o[0].blocks[0].text.text);
  o = await render('end', baseRow({ 'Status': 'DONE', 'Kind': 'MBOOTH', 'Room/Booth': 'M4', 'Approver': 'U9', 'Approver Name': 'Jem Santos', 'Approver 2': '' }), { how: 'sweep-timeout', event: { id: 'n8' } });
  ok(o.length === 2 && o.every(x => x.op === 'post') && /No answer by/.test(JSON.stringify(o[1].blocks)), 'a request with no stored messages (before slice 2): new messages instead');
  ok(/✅ \*Booked\.\* No answer by .*, so it’s yours\./.test(o[0].blocks[0].text.text) && !/let you use it/.test(o[0].blocks[0].text.text), 'shared booth, no answer: "No answer by …, so it’s yours." (not "let you use it")', o[0].blocks[0].text.text);
  o = await render('end', baseRow({ 'Status': 'DONE', 'Kind': 'MBOOTH', 'Room/Booth': 'M4', 'Approver': 'U9', 'Approver Name': 'Jem Santos', 'Approver 2': '' }), { how: 'holder', event: { id: 'n8' } });
  ok(/Jem Santos let you use it/.test(o[0].blocks[0].text.text), 'shared booth, let use: "Jem Santos let you use it."');
  const col = (await run(RM, 'Collect', [{ json: { ok: true, channel: 'D1', ts: '5.1' } }, { json: { ok: false, error: 'channel_not_found' } }], { 'Render': [{ json: { r: 'r', u: 'U7', channel: HOWARD } }, { json: { r: 'a1', u: 'U2', channel: HOWARD } }] }))[0].json;
  ok(col.messages.length === 1 && col.messages[0].t === '5.1' && col.failed[0] === 'a1: channel_not_found', 'Collect: where each went; a failed one said');
  ok(/const DEV_REDIRECT = 'U08V3CKDGJF';/.test(node(RM, 'Render').parameters.jsCode) && /const ALL_TO_DEV = (true|false);/.test(node(RM, 'Render').parameters.jsCode), 'launch switch: DEV_REDIRECT + ALL_TO_DEV in Render');
  if (/const ALL_TO_DEV = false;/.test(node(RM, 'Render').parameters.jsCode)) {   // v2 (21 Oct, QA): the QA roster gets its own
    const q = await render('open', baseRow({ 'Requester': 'U08JL17A50A', 'Requester Name': 'Camy Caridad', 'Approver': HOWARD, 'Approver Name': 'Howard Luistro', 'Approver 2': 'U2' }));
    ok(q.map(x => x.r + '>' + x.channel).join() === 'r>U08JL17A50A,a1>' + HOWARD + ',a2>' + HOWARD && !/Test:/.test(JSON.stringify(q[0].blocks)) && !/Test:/.test(JSON.stringify(q[1].blocks))
       && /Test: this is for Angelo Villegas/.test(JSON.stringify(q[2].blocks)), 'v2 (QA): Camy gets her own card, Howard his request; the engineer (not on the QA list) comes to Howard, marked - one each, no copies', q.map(x => x.r + '>' + x.channel));
  }

  console.log('Open Consent Request v12');
  const trig = { requester: 'U7', requesterName: 'Celeste Cruz', approver: 'U2', approverName: '', room: 'Studio F', reqStart: '2027-10-22T14:00:00+08:00', reqEnd: '2027-10-22T16:00:00+08:00',
    incumbentEventId: 'e1', incumbentTitle: 'SONG / Jem Lim / DR', reqType: 'Celebrity Recording', reqPriority: 3, incPriority: 1, reqPayload: PAY, kind: 'PREEMPT' };
  const incEv = { id: 'e1', summary: 'SONG / Jem Lim / DR', start: { dateTime: '2027-10-22T14:00:00+08:00' }, end: { dateTime: '2027-10-22T16:00:00+08:00' },
    attendees: [{ resource: true, displayName: 'KDC Plaza-Top Level-Studio F (8)' }], description: 'Engineer: Daryl Reyes | Arranger: Angelo Villegas | Booked by: Daryl Reyes | ref: U2 | team: U3\nSType: VO Recording' };
  const bReq = async (t, rows, ev) => (await run(OCR, 'Build Request', [], { 'When Executed by Another Workflow': [{ json: t }], 'Read Requests': rows || [{ json: {} }], 'Get Incumbent': [{ json: ev || incEv }], 'Read Cache': cache }))[0].json;
  let br = await bReq(trig);
  ok(br.row['Requester'] === 'U7' && br.row['Approver'] === 'U2' && br.row['Approver Name'] === 'Daryl Reyes' && br.row['Requester Name'] === 'Celeste Cruz', 'real ids and names from Bookers (78) - no Howard id in the row', br.row);
  ok(br.row['Approver 2'] === '' && br.asked === 'Daryl Reyes (booker)', 'the booker is the engineer here -> nobody twice');
  br = await bReq(Object.assign({}, trig), null, Object.assign({}, incEv, { description: 'Engineer: Angelo Villegas | Booked by: Daryl Reyes | ref: U2 | team: U3\nSType: VO Recording' }));
  ok(br.row['Approver 2'] === 'U3' && br.row['Approver 2 Name'] === 'Angelo Villegas' && br.asked === 'Daryl Reyes (booker) and Angelo Villegas (engineer)', 'the booking\'s engineer is asked too (80)', br.row);
  const inc = J(br.row['Messages']).inc;
  ok(inc.id === 'e1' && inc.d === '2027-10-22' && inc.s === '14:00' && inc.e === '16:00' && inc.r === 'Studio F' && inc.st === 'VO Recording', 'their booking read from the calendar (for Move my booking)', inc);
  ok(Date.parse(br.row['Deadline']) <= Date.parse('2027-10-22T13:00:00+08:00') && br.row['Kind'] === 'PREEMPT', 'deadline: no later than an hour before');
  const cols = ['Request ID', 'Status', 'Kind', 'Requester', 'Requester Name', 'Approver', 'Approver Name', 'Room/Booth', 'Req Start', 'Req End', 'Incumbent Event Id', 'Incumbent Title',
    'Incumbent New Start', 'Incumbent New End', 'Req Priority', 'Inc Priority', 'Deadline', 'Requester DM', 'Approver DM', 'Log Thread TS', 'Resolved Via', 'Attested By', 'Decided At', 'Req Payload',
    'Approver 2', 'Approver 2 Name', 'Messages', 'Withdrawn At'];
  ok(Object.keys(br.row).join() === cols.join(), 'the row: the 24 columns + the 4 new ones, nothing else (Write Pending Row maps them by name)');
  br = await bReq(trig, [{ json: baseRow({ 'Requester': 'U7', 'Req Start': '2027-10-22T14:00:00+08:00' }) }]);
  ok(br.dup === true && br.existing['Request ID'] === '20271021-U7', 'the same request again -> the open one (27)');
  const rex = (await run(OCR, 'Return Existing', [], { 'Build Request': [{ json: br }] }))[0].json;
  ok(rex.status === 'PENDING' && rex.existing === true && rex.request_id === '20271021-U7', 'Return Existing');
  br = await bReq(Object.assign({}, trig, { kind: 'MBOOTH', room: 'M4', approver: 'U9', incumbentTitle: 'M4 - Jem', reqStart: '2027-10-22T10:00:00+08:00' }), null, {});
  ok(br.row['Kind'] === 'MBOOTH' && br.row['Approver 2'] === '' && br.row['Approver Name'] === 'Jem Santos', 'shared booth: the holder only');
  ok(nx(OCR, 'When Executed by Another Workflow')[0] === 'Read Requests' && nx(OCR, 'Again?').join('|') === 'Return Existing|Row Only' && nx(OCR, 'Write Pending Row')[0] === 'Post Messages'
     && nx(OCR, 'Post Messages')[0] === 'Save Messages' && nx(OCR, 'Save Messages')[0] === 'Update Row' && !node(OCR, 'DM Incumbent'), 'wiring: read, build, write, post the messages, save where they went; no "reply yes" DM');
  ok(node(OCR, 'Post Messages').parameters.workflowInputs.value.mode === 'open' && node(OCR, 'Get Incumbent').executeOnce && node(OCR, 'Read Cache').executeOnce, 'Post Messages (open); reads once');
  const sv = (await run(OCR, 'Save Messages', [{ json: { messages: [{ r: 'r', u: 'U7', c: 'D1', t: '1' }] } }], { 'Build Request': [{ json: Object.assign({}, br, { row: { 'Request ID': 'X' } }) }] }))[0].json;
  ok(Object.keys(sv).join() === 'Request ID,Messages' && J(sv.Messages).m.length === 1 && J(sv.Messages).inc, 'Save Messages: the row\'s Messages, and nothing else');

  console.log('Finalize Consent v11');
  const plan = async (row, fresh) => (await run(FIN, 'Plan', [], { 'When Executed by Another Workflow': [{ json: { row: JSON.stringify(row), resolvedVia: 'holder', attestedBy: '' } }], 'Read Row': fresh || [{ json: {} }] }))[0].json;
  let pl = await plan(baseRow());
  ok(pl.ok === true && pl.placeTarget === 'book', 'a PENDING request is placed');
  pl = await plan(baseRow(), [{ json: baseRow({ 'Status': 'WITHDRAWN' }) }]);
  ok(pl.ok === false && pl.reason === 'ALREADY_WITHDRAWN', 'withdrawn since the caller read it (the row read again) -> not placed');
  ok(nx(FIN, 'When Executed by Another Workflow')[0] === 'Read Row' && nx(FIN, 'Mark Done')[0] === 'Done Info' && nx(FIN, 'Done Info')[0] === 'Done Messages' && nx(FIN, 'Mark Failed Place')[0] === 'Fail Info'
     && !node(FIN, 'Notify Incumbent') && !node(FIN, 'Notify Requester OK') && !node(FIN, 'Notify Place Fail'), 'wiring: the plain DMs replaced by the request\'s messages');
  const di = (await run(FIN, 'Done Info', [], { 'Plan': [{ json: { rowDone: { 'Request ID': '20271021-U7', 'Status': 'DONE', 'Resolved Via': 'move-hook' } } }],
    'When Executed by Another Workflow': [{ json: { row: JSON.stringify(baseRow()), resolvedVia: 'move-hook', attestedBy: '' } }], 'Read Row': [], 'Book Requester': [{ json: { status: 'CREATED', event_id: 'n9', title: 'SONG 2 / Netflix / HL' } }] }))[0].json;
  ok(J(di.row).Status === 'DONE' && J(di.extra).event.id === 'n9' && J(di.extra).how === 'move-hook', 'Done Info: DONE, the new booking, how');

  console.log('Consent Sweep v3');
  const due = baseRow({ 'Deadline': '2020-01-01T00:00:00Z' });
  const sd = (await run(SW, 'Sweep Decide', [{ json: due }, { json: baseRow({ 'Request ID': 'M', 'Kind': 'MBOOTH', 'Deadline': '2020-01-01T00:00:00Z' }) }], {})).map(i => i.json);
  ok(sd[0]._sweepAction === 'expire' && sd[0]._row['Request ID'] === '20271021-U7' && sd[1]._sweepAction === 'book', 'priority past its deadline -> expire (with its row); M booth -> book');
  const er = (await run(SW, 'Expire Row', [{ json: sd[0] }], {}))[0].json;
  ok(Object.keys(er).join() === 'Request ID,Status,Resolved Via,Decided At', 'Expire Row: the sheet\'s columns only');
  const ei = (await run(SW, 'Expire Info', [], { 'Sweep Decide': sd.map(j => ({ json: j })) })).map(i => i.json);
  ok(ei.length === 1 && J(ei[0].row).Status === 'EXPIRED', 'Expire Info: its messages, as EXPIRED');
  ok(node(SW, 'Sweep Book').parameters.mode === 'each' && node(SW, 'Expire Messages').parameters.mode === 'each' && nx(SW, 'Sweep Route?')[1] === 'Expire Row', 'one Finalize per request (was: only the first)');

  console.log('Book Session v120');
  const tv = node(BS, 'When Executed by Another Workflow').parameters.workflowInputs.values.map(v => v.name);
  ok(tv.indexOf('request_ok') !== -1, 'input request_ok');
  const cc = { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ id: 'e1', summary: 'SONG / Jem Lim / DR', room: 'Studio F', description: 'ref: U2\nSType: VO Recording' }] };
  const REQ = o => Object.assign({ session_type: 'Celebrity Recording', rooms: 'Studio F', description: 'Booked by: Celeste Cruz | ref: U7', authority: 'Dept Head', start_iso: 'a', end_iso: 'b',
    reference_data: JSON.stringify({ preemptionRanks: { 'Celebrity Recording': 3, 'VO Recording': 1 } }) }, o || {});
  const dp = async o => (await run(BS, 'Decide Preempt', [{ json: cc }], { 'When Executed by Another Workflow': [{ json: REQ(o) }] }))[0].json;
  ok((await dp()).offer === false && (await dp()).preemptReason === 'NOT_ASKED', 'not asked -> refused as before (ROOM_OCCUPIED), no request');
  const d2 = await dp({ request_ok: 'true' });
  ok(d2.offer === true && d2.open.approver === 'U2', 'asked (the form) and outranks -> a request', d2);
  const d3 = await dp({ request_ok: true, rooms: 'Studio F, Likha' });
  ok(d3.offer && d3.open.room === 'Studio F' && JSON.parse(d3.open.reqPayload).rooms === 'Studio F, Likha', 'a request with a holding room: Studio F is asked for, both are placed', d3.open);
  ok((await run(BS, 'Return Offer', [{ json: { status: 'PENDING', request_id: 'R1', deadline: 'D', asked: 'Daryl Reyes (booker)', existing: true } }], {}))[0].json.asked === 'Daryl Reyes (booker)', 'Return Offer passes on who was asked');

  console.log('Room Availability v23');
  ok(/out\.busy_detail = /.test(node(RA, 'Compute Availability').parameters.jsCode), 'busy_detail on a single window');

  console.log('Slack Interactions v37: Booked – ask to use');
  const s = { date: '2027-10-22', t0: '14:00', t1: '16:00', purpose: 'Celebrity Recording', kind: 'studio', requester: 'U7', channel: 'D1', ext: 'x' };
  const det = (room, evs) => ({ room, events: evs });
  const RAres = (free, detail) => ({ status: 'OK', free_priority: free, free_last_resort: [], busy: detail.map(d => d.room + ' (x)'), busy_detail: detail });
  const vo = det('Studio F', [{ id: 'e1', title: 'SONG / Jem Lim / DR', start: '2027-10-22T14:00:00+08:00', end: '2027-10-22T16:00:00+08:00', stype: 'VO Recording', ref: 'U2', team: ['U3'], recurring: false }]);
  const mix = det('Studio C', [{ id: 'e2', title: 'MIX / DR', start: '2027-10-22T13:00:00+08:00', end: '2027-10-22T17:00:00+08:00', stype: 'Music Mixing', ref: 'U2', recurring: false }]);
  const step2 = async (ss, ra) => (await run(SI, 'Build Step 2', [{ json: ra }], { 'Read Step 1': [{ json: { s: ss } }], 'Read Cache 2': cache, 'Loc Projects 2': [] }))[0].json.view;
  let v = await step2(s, RAres(['Studio 7'], [vo, mix]));
  const ro = v.blocks.find(b => b.block_id === 'room_other');
  const groups = ro && ro.element.option_groups;
  ok(groups && groups.length === 2 && groups[1].label.text === 'Booked – ask to use' && groups[1].options.map(o => o.value).join() === 'ask:P|Studio F,ask:P|Studio C'
     && groups[1].options[0].text.text === 'Studio F · VO Recording, 2:00 PM–4:00 PM', 'a Dept Head: Studio F (VO Recording) and Studio C (Music Mixing) can be asked for - both lower', groups);
  ok(v.submit.text === 'Book' && JSON.parse(v.private_metadata).sub === 'Book', 'a free room too -> Book (sub kept for when a request is unpicked)');
  v = await step2(Object.assign({}, s, { requester: 'U08JL17A50A' }), RAres(['Studio 7'], [vo]));
  ok(!JSON.stringify(v).includes('ask:'), 'a Standard user: no priority requests');
  v = await step2(Object.assign({}, s, { requester: 'U2' }), RAres(['Studio 7'], [vo]));
  ok(!JSON.stringify(v).includes('ask:'), 'your own booking is never offered');
  v = await step2(Object.assign({}, s, { purpose: 'VO Recording' }), RAres(['Studio 8'], [det('Studio F', [Object.assign({}, vo.events[0], { stype: 'Celebrity Recording' })])]));
  ok(!JSON.stringify(v).includes('ask:'), 'a higher-priority booking in the way: not offered');
  v = await step2(s, RAres(['Studio 7'], [det('Studio 3', [Object.assign({}, vo.events[0])])]));
  ok(!JSON.stringify(v).includes('ask:'), 'a room that does not normally do this type: not offered (never room_override)');
  v = await step2(Object.assign({}, s, { series: { dates: ['2027-10-22', '2027-10-29'] } }), RAres(['Studio 7'], [vo]));
  ok(!JSON.stringify(v).includes('ask:'), 'a series: no requests (decided 21 Oct)');
  const allBusy = n => ['Studio 1','Studio 2','Studio 3','Studio 5','Studio 6','Studio 7','Studio 8','Studio C','Studio E','Studio M'].map(r => r + ' (x)');
  v = await step2(s, Object.assign(RAres([], [vo]), { busy: ['Studio F (x)'].concat(allBusy()) }));
  ok(!v.blocks.some(b => b.block_id === 'room') && /you can ask for a booked room below/.test(JSON.stringify(v.blocks)) && v.submit.text === 'Send request'
     && v.blocks.find(b => b.block_id === 'room_other').element.option_groups.length === 1 && v.blocks.some(b => b.block_id === 'project'),
     'nothing free, one to ask for -> no dead end: the request group, the details, Send request', v.blocks.map(b => b.block_id || b.type));
  const sB = { date: '2027-10-22', t0: '10:00', t1: '12:00', purpose: '__booth', kind: 'booth', requester: 'U08JL17A50A', channel: 'D1', ext: 'x' };
  v = await step2(sB, Object.assign(RAres([], [det('M4', [{ id: 'h1_x', title: 'M4 - Jem', start: '2027-10-22T09:00:00+08:00', end: '2027-10-22T18:00:00+08:00', ref: 'U9', recurring: true }])]), { free_rooms: ['M1'] }));
  const bg = (v.blocks.find(b => b.block_id === 'room_other') || { element: {} }).element.option_groups || [];
  ok(bg.length && bg[bg.length - 1].options[0].value === 'ask:M|M4' && /^M4 · Jem(’s standing hold)?$/.test(bg[bg.length - 1].options[0].text.text), 'an M booth during a standing hold - anyone can ask', bg);

  console.log('Slack Interactions v37: picking one');
  const view = await step2(s, RAres(['Studio 7'], [vo]));
  const nt = async (aid, sel) => (await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', state: { values: {} } }, view), actions: [Object.assign({ action_id: aid }, sel)] } } }] }))[0];
  let r = await nt('room_other_pick', { selected_option: { value: 'ask:P|Studio F', text: { text: 'Studio F · VO Recording, 2:00 PM–4:00 PM' } } });
  const an = r.json.view.blocks.find(b => b.block_id === 'ask_note');
  ok(an && /🔒 \*Studio F is booked then\* \(VO Recording, 2:00 PM–4:00 PM\)\. Jessie will ask its booker and engineer – they have until \*[A-Z][a-z]{2}, [A-Z][a-z]{2} \d+, \d+:\d{2} [AP]M\* to answer/.test(an.elements[0].text) && r.json.view.submit.text === 'Send request',
     'a request picked: what happens under it, the button says Send request', an && an.elements[0].text);
  const v2 = r.json.view;
  r = (await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', state: { values: { room_other: { room_other_pick: { selected_option: { value: 'ask:P|Studio F' } } } } } }, v2),
    actions: [{ action_id: 'room_radio', selected_option: { value: 'Studio 7' } }] } } }] }))[0];
  ok(!r.json.view.blocks.some(b => b.block_id === 'ask_note') && r.json.view.submit.text === 'Book', 'a free room picked again -> the line goes, Book is back');

  console.log('Slack Interactions v37: Send request');
  const rs2 = async (pickVal) => (await run(SI, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U7' } }], 'Read Cache 3': cache, 'Timings 2': [],
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', blocks: view.blocks, private_metadata: view.private_metadata,
      state: { values: { room_other: { room_other_pick: { selected_option: { value: pickVal } } }, project: { project_in: { value: 'song 2' } }, client: { client_in: { value: 'Netflix' } },
        engineer: { engineer_pick: { selected_option: { value: 'U2' } } } } } } } } }] }))[0].json;
  let R2 = await rs2('ask:P|Studio F');
  ok(R2.valid && R2.ask === 'P' && R2.rooms === 'Studio F' && R2.prep.request_ok === true && R2.prep.room_override === false && /Sending a request for Studio F/.test(JSON.stringify(R2.answer || R2)),
     'the request: the room, request_ok, never room_override, "Sending a request…"', { valid: R2.valid, ask: R2.ask, rooms: R2.rooms, ok: R2.prep && R2.prep.request_ok, ov: R2.prep && R2.prep.room_override });
  R2 = await rs2('Studio 7');
  ok(R2.prep.request_ok === false, 'a free room: request_ok false');
  const ab = (await run(SI, 'After Book', [{ json: { status: 'PREEMPT_PENDING', request_id: 'R1', asked: 'Daryl Reyes (booker) and Angelo Villegas (engineer)' } }],
    { 'Read Step 2': [{ json: { viewId: 'V1', channel: 'D1', rooms: 'Studio F', s } }], 'After Prepare': [{ json: { F: {}, book: {} } }], 'Read Request': [{ json: { payload: {} } }] }))[0].json;
  ok(ab.req === true && ab.ok === false && /📨 \*Request sent – Studio F\.\*\nJessie asked Daryl Reyes \(booker\) and Angelo Villegas \(engineer\)\./.test(ab.view.blocks[0].text.text), 'After Book: "Request sent" on the form', ab.view);
  ok((await run(SI, 'Result DM', [{ json: { ok: false } }], { 'After Book': [{ json: ab }], 'Read Step 2': [{ json: {} }] })).length === 0, 'no "Not booked" DM - the card is in the DM already');

  console.log('Slack Interactions v37: the request buttons');
  const sig = async (type, action, cb) => (await run(SI, 'Check Signature', [{ json: { computed: 'a' } }], { 'Read Request': [{ json: { sig: 'v0=a', ts: String(Math.floor(Date.now() / 1000)),
    payload: { type, actions: action ? [{ action_id: action }] : [], view: cb ? { callback_id: cb } : undefined } } }] }))[0].json.route;
  ok((await sig('block_actions', 'cr_keep')) === 16 && (await sig('block_actions', 'cr_giveup')) === 16 && (await sig('block_actions', 'cr_allow')) === 16 && (await sig('block_actions', 'cr_withdraw')) === 16
     && (await sig('block_actions', 'cr_attest')) === 16 && (await sig('block_actions', 'cr_cleared')) === 17 && (await sig('view_submission', '', 'cr_cleared')) === 18
     && (await sig('block_actions', 'cr_move')) === 10 && (await sig('block_actions', 'cr_pick')) === 4, 'routes: buttons 16, cleared 17 / 18, Move my booking -> Change, Pick another room -> Book a room');
  ok(nx(SI, 'Route')[16] === 'Ack Request' && nx(SI, 'Route')[17] === 'Ack Cleared' && nx(SI, 'Route')[18] === 'Read Cleared' && node(SI, 'Route').parameters.numberOutputs === 19, 'Route has 19 outputs');
  const act = async (user, action_id, w, row) => (await run(SI, 'Request Act', [{ json: row || baseRow() }], { 'Check Signature': [{ json: { user } }],
    'Read Request': [{ json: { payload: { actions: [{ action_id, value: JSON.stringify({ id: '20271021-U7', w }) }] } } }] }))[0].json;
  let x = await act('U2', 'cr_keep', 'a1');
  ok(x.go === 0 && x.upd.Status === 'REJECTED' && x.extra.by === 'Daryl Reyes', 'the booker keeps it -> REJECTED');
  x = await act(HOWARD, 'cr_keep', 'a2');
  ok(x.go === 0 && x.extra.by === 'Angelo Villegas', 'Howard answers for the engineer while testing (by = the engineer)');
  x = await act('U08JL17A50A', 'cr_keep', 'a1');
  ok(x.go === 3, 'someone else pressing it -> nothing');
  x = await act('U7', 'cr_keep', 'r');
  ok(x.go === 3, 'the requester cannot "keep"');
  x = await act('U7', 'cr_withdraw', 'r');
  ok(x.go === 0 && x.upd.Status === 'WITHDRAWN' && x.upd['Withdrawn At'], 'the requester withdraws -> WITHDRAWN');
  x = await act('U2', 'cr_giveup', 'a1');
  ok(x.go === 2 && x.how === 'gave-up', 'Give it up -> cancel, then Finalize');
  x = await act('U9', 'cr_allow', 'a1', baseRow({ 'Kind': 'MBOOTH', 'Approver': 'U9' }));
  ok(x.go === 1 && x.how === 'holder', 'Let them use it -> Finalize');
  x = await act('U7', 'cr_attest', 'r', baseRow({ 'Kind': 'MBOOTH', 'Approver': 'U9' }));
  ok(x.go === 1 && x.how === 'attestation', 'M booth: I\'ve cleared it with them -> Finalize');
  x = await act('U2', 'cr_keep', 'a1', baseRow({ 'Status': 'DONE' }));
  ok(x.go === 4, 'already ended -> its messages redrawn, nothing changed');
  ok(nx(SI, 'Act Route').join('|') === 'Row Update|Finalize Request|Give Up Plan||End Messages' && nx(SI, 'Row Update')[0] === 'Update Request' && nx(SI, 'Update Request')[0] === 'End Messages', 'wiring: the endings');
  const gp = (await run(SI, 'Give Up Plan', [{ json: {} }], { 'Check Signature': [{ json: { user: 'U2', channel: 'D1' } }], 'Request Act': [{ json: { row: baseRow(), by: 'Daryl Reyes' } }] }))[0].json;
  ok(gp.ok && gp.cancel.event_id === 'e1' && gp.cancel.requester === 'U2' && gp.cancel.confirmed === true && gp.cancel.booking_date === '2027-10-22', 'Give it up: cancelled as its booker (the request\'s authority)', gp.cancel);
  ok(nx(SI, 'Can Free?').join('|') === 'To Cancel G|Freed Note' && nx(SI, 'Cancel G')[0] === 'Freed?' && nx(SI, 'Freed?').join('|') === 'Finalize Given Up|Freed Note', 'wiring: cancel, then Finalize; a failure said in the DM');

  console.log('Slack Interactions v37: I\'ve cleared it with them');
  const cm = (await run(SI, 'Cleared Modal', [], { 'Check Signature': [{ json: { triggerId: 'T1' } }], 'Read Request': [{ json: { payload: { actions: [{ value: req.blocks[1].elements[0].value }] } } }] }))[0].json;
  ok(cm.view.callback_id === 'cr_cleared' && JSON.parse(cm.view.private_metadata).as === 'U2' && /SONG \/ Jem Lim \/ DR/.test(cm.view.blocks[0].text.text), 'the small form: move it / they gave it up');
  const rc = async choice => (await run(SI, 'Read Cleared', [], { 'Check Signature': [{ json: { viewId: 'V9' } }], 'Read Request': [{ json: { payload: { view: { private_metadata: cm.view.private_metadata,
    state: { values: { cleared: { cleared_pick: { selected_option: { value: choice } } } } } } } } }] }))[0].json;
  const rcm = await rc('move');
  ok(rcm.move && rcm.answer.response_action === 'update' && rcm.as === 'U2' && rcm.inc.id === 'e1', 'move -> "Opening their booking…"');
  const V38 = /const _row = \$\('Read Requests C'\)/.test(node(SI, 'Build Change C').parameters.jsCode);   // v38: the request checked first
  const bcc = (await run(SI, 'Build Change C', [], { 'Check Signature': [{ json: { user: 'U7', viewId: 'V9' } }], 'Read Cleared': [{ json: rcm }], 'Read Cache C': cache, 'Read Requests C': [{ json: baseRow() }] }))[0].json;
  if (V38) {
    const kept = (await run(SI, 'Build Change C', [], { 'Check Signature': [{ json: { user: 'U7', viewId: 'V9' } }], 'Read Cleared': [{ json: rcm }], 'Read Cache C': cache, 'Read Requests C': [{ json: baseRow({ 'Status': 'REJECTED' }) }] }))[0].json;
    const other = (await run(SI, 'Build Change C', [], { 'Check Signature': [{ json: { user: 'U08JL17A50A', viewId: 'V9' } }], 'Read Cleared': [{ json: rcm }], 'Read Cache C': cache, 'Read Requests C': [{ json: baseRow() }] }))[0].json;
    ok(/isn’t open any more/.test(JSON.stringify(kept.view)) && /isn’t open any more/.test(JSON.stringify(other.view)) && kept.view.callback_id === undefined,
       'v38: the booker kept it (REJECTED), or not the requester -> no Change form, "That request isn’t open any more"');
    ok(nx(SI, 'Answer Cleared')[0] === 'Read Requests C' && nx(SI, 'Read Requests C')[0] === 'Cleared Move?' && ['Read Cache C|Give Up Plan', 'Read Cache C|Claim Row'].indexOf(nx(SI, 'Cleared Move?').join('|')) !== -1 /* v49: the claim first */, 'v38 wiring: the sheet read before either choice');
  }
  const meta = JSON.parse(bcc.view.private_metadata);
  ok(bcc.view_id === 'V9' && bcc.view.callback_id === 'change_booking' && meta.as === 'U2' && meta.b.id === 'e1' && meta.ch === '' && meta.ts === '', 'their booking\'s Change form, changed as its booker', meta);
  ok(/requester: \(R\.meta && R\.meta\.as\) \|\| R\.user/.test(node(SI, 'To Move').parameters.jsCode), 'To Move: as its booker when the request says so');
  const rcg = await rc('gaveup');
  ok(!rcg.move && rcg.answer.response_action === 'clear', 'gave up -> the form closes');
  const gp2 = (await run(SI, 'Give Up Plan', [{ json: baseRow() }], { 'Check Signature': [{ json: { user: 'U7', channel: 'D1' } }], 'Read Cleared': [{ json: rcg }], 'Read Requests C': [{ json: baseRow() }] }))[0].json;
  ok(gp2.ok && gp2.how === 'cleared-gave-up' && gp2.by === 'Celeste Cruz' && gp2.cancel.requester === 'U2', '… cancelled as its booker, then Finalize');
  const gp3 = (await run(SI, 'Give Up Plan', [{ json: baseRow() }], { 'Check Signature': [{ json: { user: 'U08JL17A50A', channel: 'D1' } }], 'Read Cleared': [{ json: rcg }], 'Read Requests C': [{ json: baseRow() }] }))[0].json;
  ok(gp3.ok === false, 'not the requester -> nothing changed');
  const bch = (await run(SI, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U2', triggerId: 'T' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { actions: [{ action_id: 'cr_move', value: a1.blocks[1].elements[0].value }], container: { channel_id: 'D1', message_ts: '1.2' } } } }] }))[0].json;
  ok(JSON.parse(bch.view.private_metadata).ts === '' && JSON.parse(bch.view.private_metadata).b.id === 'e1', 'Move my booking: the Change form, the request message left to Finalize');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
