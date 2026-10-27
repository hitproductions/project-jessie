#!/usr/bin/env node
// The launch-fix round of 27 Oct (PENDING 125, 127, 128, 129): Slack Interactions v46, Move v39, Cancel v33, Reminders v7, main v284.
//   125 - a failed sub-workflow call reaches the person in words (form or DM) and Howard (Ops Alert)
//   127 - who is on a booking is read from the description's first line only, never the note
//   128 - the Change form's question, step 2 and a cancel reach the DM when the window / message is gone
//   129 - notices: "booked these dates for you" in a series, who it is for kept on a change, "changed" vs "moved", "taken off"
// Usage: node scripts/sim-launch-fixes.js [si v46] [move v39] [cancel v33] [reminders v7] [main v284]
const fs = require('fs');
const L = (i, d) => JSON.parse(fs.readFileSync(process.argv[i] || d, 'utf8'));
const si = L(2, 'workflows/slack-interactions-v46.json'), mv = L(3, 'workflows/move-booking-v39.json'), cx = L(4, 'workflows/cancel-booking-v33.json'),
  RM = L(5, 'workflows/reminders-v7.json'), main = L(6, 'workflows/project-jessie-v284.json');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (!si.nodes.some(n => n.name === 'Ops Alert')) { console.log('0 ok, 0 failed (an older build: the launch fixes not in it)'); process.exit(0); }
const code = (wf, name) => wf.nodes.find(x => x.name === name).parameters.jsCode;
const run = async (wf, name, input, outs) => { const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  return new Function('$', '$input', 'return (async function(){' + code(wf, name) + '\n})();')($, { first: () => input[0], all: () => input }); };
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
const nx = (wf, n) => ((wf.connections[n] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
const B = (id, name, slack, info) => ({ id, fields: { Name: name, Initials: name.split(' ').map(w => w[0]).join(''), 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const bookers = [B('b1', 'Howard Luistro', 'U1', 'Post Engineer'), B('b2', 'Daryl Reyes', 'U2', 'Post Engineer'), B('b4', 'Pia Lopez', 'U4', 'Music Arranger'),
  B('b5', 'Camy Caridad', 'U08JL17A50A', 'Producer')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const HEAD = 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1 | Type: Advertising | Dept: Audio Post';
const NOTE = 'URGENT bring the USB\nteam: U9 U08JL17A50A\nEngineer: Camy Caridad (for Camy Caridad) | Dept: Music';
const NEW = HEAD + '\nSType: VO Recording\n\nNotes:\n' + NOTE;
const OLD = 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1 | Notes: URGENT team: U9 Camy | Type: Advertising | Dept: Audio Post\nSType: VO Recording';
const EV = (id, desc) => ({ id, summary: 'ORANGE / Jem Lim / HL', start: { dateTime: '2027-10-27T18:00:00+08:00' }, end: { dateTime: '2027-10-27T21:00:00+08:00' },
  attendees: [{ resource: true, email: 'f@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio F (12)' }], description: desc });
const HOWARD = 'U08V3CKDGJF';

(async () => {
  console.log('125 - a failed call');
  const CALLS = ['Room Availability', 'Prepare', 'Book', 'Prepare Series', 'Book Series', 'Move', 'Cancel', 'Cancel G'];
  ok(CALLS.every(n => si.nodes.find(x => x.name === n).onError === 'continueRegularOutput'), 'the eight calls continue on error');
  ok(CALLS.every(n => nx(si, n).split(' | ')[0].split('+').indexOf('Ops Alert') !== -1) && nx(si, 'Ops Alert') === 'DM Not Shown', 'each call -> Ops Alert (beside its usual answer) -> DM Not Shown');
  ok(CALLS.every(n => nx(si, n).split(' | ')[0].split('+')[0] !== 'Ops Alert'), 'the usual answer still comes first');
  const sig = [{ json: { action: 'book_step2', user: 'U5', type: 'view_submission' } }];
  let a = await j1(si, 'Ops Alert', [{ json: { error: 'Get Events In Window: 503 backend error' } }], { 'Check Signature': sig });
  ok(a && a.channel === HOWARD && /book_step2/.test(a.text) && /<@U5>/.test(a.text) && /503 backend error/.test(a.text), 'an error -> Howard, with the step, the person and the error', a);
  ok((await run(si, 'Ops Alert', [{ json: { status: 'CREATED' } }], { 'Check Signature': sig })).length === 0
     && (await run(si, 'Ops Alert', [{ json: { status: 'CALENDAR_ERROR', error: 'x' } }], { 'Check Signature': sig })).length === 0
     && (await run(si, 'Ops Alert', [{ json: { booked: [], skipped: [], failed: [] } }], { 'Check Signature': sig })).length === 0, 'an answer (even a refusal) -> nothing');
  const R2 = { viewId: 'V1', channel: 'U1', calTitle: 'ORANGE / Jem Lim / HL', rooms: 'Studio F', again: { d: '2027-10-27', s: '18:00', e: '21:00', p: 'VO Recording' },
    s: { date: '2027-10-27', t0: '18:00', t1: '21:00', kind: 'studio', purpose: 'VO Recording', requester: 'U1', when: 'x' } };
  const outs2 = { 'Read Step 2': [{ json: R2 }], 'To Prepare': [{ json: {} }], 'Read Cache 2': cache, 'Read Step 1': [{ json: { s: R2.s } }],
    'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(R2.s), blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Step 2' } }], state: { values: {} } } } } }] };
  let p = await j1(si, 'After Prepare', [{ json: { error: 'boom' } }], outs2);
  ok(p.go === false && /^Something went wrong on our side – nothing was booked\./.test(p.warn) && /Something went wrong/.test(JSON.stringify(p.view)), 'Prepare failed -> "nothing was booked", on the form', p.warn);
  p = await j1(si, 'After Book', [{ json: { error: 'boom' } }], Object.assign({}, outs2, { 'After Prepare': [{ json: { F: {} } }] }));
  ok(p.ok === false && /may or may not have gone through\. Check \*My bookings\*/.test(p.warn), 'Book failed -> "may or may not have gone through - check My bookings"', p.warn);
  const rd = await j1(si, 'Result DM', [{ json: { ok: false } }], { 'Read Step 2': [{ json: R2 }], 'After Book': [{ json: p }] });
  ok(/^⚠️ Something went wrong/.test(rd.blocks[0].text.text) && !/Not booked\./.test(rd.blocks[0].text.text), 'the DM (window gone) does not say "Not booked." in front of it', rd.blocks[0].text.text);
  const rd2 = await j1(si, 'Result DM', [{ json: { ok: false } }], { 'Read Step 2': [{ json: R2 }], 'After Book': [{ json: { ok: false, warn: 'Studio F is taken then.' } }] });
  ok(/^⚠️ \*Not booked\.\* Studio F/.test(rd2.blocks[0].text.text), 'any other answer as before');
  p = await j1(si, 'After Prepare Series', [{ json: { error: 'boom' } }], outs2);
  ok(/nothing was booked/.test(JSON.stringify(p)), 'a series\' Prepare failed -> "nothing was booked"');
  const bs = await j1(si, 'After Book Series', [{ json: { error: 'boom' } }], { 'Read Series Confirm': [{ json: { user: 'U1', meta: { n: 3, title: 'SER / DR', time: '10:00-12:00' } } }], 'To Book Series': [{ json: { go: true, rooms: 'Studio F' } }] });
  ok(/^⚠️ \*Something went wrong on our side\* while booking \*SER \/ DR\*\. Some dates may have gone in – check \*My bookings\*/.test(bs.text), 'Book Series failed -> "some dates may have gone in"', bs.text);
  const RC = { viewId: 'V1', user: 'U1', meta: { ch: 'D1', ts: '5.5' }, b: { id: 'e1', d: '2027-10-27', s: '18:00', e: '21:00', r: 'Studio F', t: 'ORANGE / Jem Lim / HL' },
    n: { d: '2027-10-28', s: '10:00', e: '12:00', r: 'Studio F' } };
  const am = await j1(si, 'After Move', [{ json: { error: 'boom' } }], { 'Read Change': [{ json: RC }], 'To Move': [{ json: {} }], 'Read Cache 7': cache });
  ok(am.ok === false && /may or may not have changed\. Check \*My bookings\*/.test(JSON.stringify(am)), 'Move failed -> "may or may not have changed"', am);
  const BK = { id: 'e1', d: '2027-10-27', s: '18:00', e: '21:00', r: 'Studio F', t: 'ORANGE / Jem Lim / HL' };
  const pay = { actions: [{ action_id: 'bk_cancel_go', value: JSON.stringify(BK) }], container: { channel_id: 'D1', message_ts: '9.9' } };
  const rows = [{ type: 'section', block_id: 'bk_e1', text: { type: 'mrkdwn', text: '*ORANGE / Jem Lim / HL*' } }, { type: 'actions', block_id: 'bka_e1', elements: [] }];
  const ac = await j1(si, 'After Cancel', [{ json: { ok: true, messages: [{ ts: '9.9', text: 'x', blocks: rows }] } }], { 'Cancel': [{ json: { error: 'boom' } }], 'Read Request': [{ json: { payload: pay } }] });
  ok(ac.ok === false && /Something went wrong on our side\. Check \*My bookings\* to see if it’s still there\./.test(JSON.stringify(ac.blocks)), 'Cancel failed -> "check My bookings to see if it\'s still there"', ac.blocks);

  console.log('127 - people from the first line only');
  for (const [wf, nm, label] of [[RM, 'Build Reminders', 'Reminders'], [si, 'Render My Bookings', 'My bookings (form)'], [main, 'Mine Reply', 'My bookings (typed)'],
                                 [main, 'Change Reply', 'Change / cancel (typed)'], [si, 'Series Notices', 'Series Notices'], [cx, 'Check Ownership', 'Cancel'], [mv, 'Resolve Booking', 'Move']]) {
    const js = code(wf, nm), line = js.split('\n').find(l => /PENDING 127/.test(l) && /split\(\/\\n\|<br/.test(l));
    let headOk = false, d = null;
    if (line) { const m = line.match(/=>?\s*(String\((\w+(?:\.\w+)?) \|\| ''\)[^;]*);/);   // Move: const _hd = x => String(x || '')…
      if (m) { const f = new Function('v', 'return ' + m[1].replace(m[2], 'v'));
        d = [f(NEW), f(OLD), f(HEAD.replace(' | team: U1', '') + '<br><br>Notes:<br>team: U9')];
        headOk = d[0] === HEAD && !/U9|URGENT/.test(d[1]) && /^Engineer: Howard Luistro \| Booked by/.test(d[1]) && !/U9/.test(d[2]); } }
    ok(headOk, label + ' (' + nm + '): the first line, without the note block, an older inline note or a <br> note', d);
  }
  const rmOut = (await run(RM, 'Build Reminders', [], { 'Window': [{ json: { kind: 'daily', start: '2027-10-27', end: '2027-10-28' } }], 'List Events R': [{ json: { items: [EV('e1', NEW), EV('e2', OLD)] } }], 'Read Cache R': cache })).map(i => i.json);
  ok(rmOut.length === 1 && !/URGENT|USB|U9|Camy/.test(JSON.stringify(rmOut.map(x => [x.channel, (x.blocks || []).filter(b => b.type === 'context')]))), 'Reminders: one reminder (the booker) - not URGENT, USB, U9 or Camy from the note', rmOut.map(x => x.channel));
  const W = { user: 'U9', start: '2027-10-26', end: '2027-11-02', ch: 'D1', ts: '5.5' };
  const mb = await j1(si, 'Render My Bookings', [{ json: { items: [EV('e1', NEW), EV('e2', OLD)] } }], { 'My Window': [{ json: W }], 'Read Cache 4': cache });
  ok(!(mb.blocks || []).some(b => /^bk_/.test(b.block_id || '')), 'My bookings: "team: U9" in a note does not put the booking in U9\'s list');
  const mr = await j1(main, 'Mine Reply', [{ json: { items: [EV('e1', NEW)] } }], { 'Mine Check': [{ json: { mineCheck: { go: true, user: 'U9', channel: 'D1', start: '2027-10-26', end: '2027-11-02', week: true, room: '' } } }] });
  ok(!/bk_e1/.test(JSON.stringify(mr)), 'typed "what do I have": the same');
  const me = await j1(main, 'Mine Reply', [{ json: { items: [EV('e1', NEW)] } }], { 'Mine Check': [{ json: { mineCheck: { go: true, user: 'U1', channel: 'D1', start: '2027-10-26', end: '2027-11-02', week: true, room: '' } } }] });
  ok(/bk_e1/.test(JSON.stringify(me)), 'the booker still sees it');

  console.log('128 - the DM when the window or message is gone');
  ok(nx(si, 'Ask Again') === 'Get Message RA+Ask DM' && nx(si, 'Ask DM') === 'DM Not Shown' && nx(si, 'Show Step 2') === 'Timing Sample+Step 2 DM' && nx(si, 'Step 2 DM') === 'DM Not Shown'
     && nx(si, 'Update Cancelled') === 'Cancel DM' && nx(si, 'Cancel DM') === 'DM Not Shown', 'wiring: Ask Again -> Ask DM, Show Step 2 -> Step 2 DM, Update Cancelled -> Cancel DM, each -> DM Not Shown');
  ok(/warn, askedClient: t \} \}\];/.test(code(si, 'To Move')), 'To Move hands on the question and the client it asked about');
  const WARN = 'Did you mean *Jem Lim*? Or press *Change* again to keep "Jem Lin" as a new client.';
  const RCd = Object.assign({}, RC, { b: Object.assign({}, BK, { st: 'VO Recording' }), d: { project: 'ORANGE', client: 'Jem Lin', code: '', title: '', forname: '', en: 'U2', ar: 'none', st: '', notes: 'bring cans', teamShown: true } });
  const askOuts = { 'To Move': [{ json: { go: false, warn: WARN, askedClient: 'Jem Lin' } }], 'Read Change': [{ json: RCd }] };
  ok((await run(si, 'Ask DM', [{ json: { ok: true } }], askOuts)).length === 0, 'the question shown on the form -> no DM');
  const ad = await j1(si, 'Ask DM', [{ json: { ok: false, error: 'not_found' } }], askOuts);
  const btn = ad.blocks[2].elements[0], bv = JSON.parse(btn.value);
  ok(ad.channel === 'U1' && ad.blocks[0].block_id === 'bk_e1' && ad.blocks[1].block_id === 'bkn_e1' && /Not changed yet\.\* Did you mean \*Jem Lim\*/.test(ad.blocks[1].elements[0].text)
     && ad.blocks[2].block_id === 'bka_e1' && btn.action_id === 'bk_change' && btn.text.text === 'Continue changing' && ad.blocks[2].elements[1].action_id === 'my_bookings', 'window closed -> the DM: the booking, the question, Continue changing + My bookings', ad.blocks);
  ok(bv.id === 'e1' && bv.n.d === '2027-10-28' && bv.v.client === 'Jem Lin' && bv.v.en === 'U2' && bv.v.notes === 'bring cans' && !('teamShown' in bv.v) && bv.ac === 'Jem Lin' && bv.w === WARN && btn.value.length <= 2000,
     'the button carries the new date / time, what was filled in, the question and the client', bv);
  const big = await j1(si, 'Ask DM', [{ json: { ok: false } }], Object.assign({}, askOuts, { 'Read Change': [{ json: Object.assign({}, RCd, { d: Object.assign({}, RCd.d, { notes: 'x'.repeat(2500) }) }) }] }));
  const bigV = JSON.parse(big.blocks[2].elements[0].value);
  ok(big.blocks[2].elements[0].value.length <= 2000 && bigV.v.client === 'Jem Lin' && !bigV.v.notes, 'a long note is left off the button (Slack\'s 2,000), the rest kept');
  const bc = await j1(si, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'bk_change', value: btn.value }], container: { channel_id: 'D1', message_ts: '8.8' } } } }] });
  const vs = JSON.stringify(bc.view), meta = JSON.parse(bc.view.private_metadata);
  ok(/Did you mean \*Jem Lim\*/.test(vs) && meta.askedClient === 'Jem Lin' && /"initial_value":"Jem Lin"/.test(vs) && /"initial_date":"2027-10-28"/.test(vs) && meta.ts === '8.8' && !('v' in meta.b) && !('w' in meta.b),
     'Continue changing -> the Change form: the new date, "Jem Lin" filled in, the question on it; Change again keeps the client', { meta, q: /Did you mean/.test(vs) });
  const bc0 = await j1(si, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'bk_change', value: JSON.stringify(BK) }], container: { channel_id: 'D1', message_ts: '8.8' } } } }] });
  ok(!/⚠️/.test(JSON.stringify(bc0.view)) && !JSON.parse(bc0.view.private_metadata).askedClient, 'a plain Change press as before (no question)');
  const S1 = { s: { requester: 'U1', date: '2027-10-27', t0: '18:00', t1: '21:00', kind: 'studio', purpose: 'VO Recording' } };
  ok((await run(si, 'Step 2 DM', [{ json: { ok: true } }], { 'Read Step 1': [{ json: S1 }] })).length === 0, 'step 2 shown -> no DM');
  let sd = await j1(si, 'Step 2 DM', [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 1': [{ json: S1 }] });
  const sb = sd.blocks[1].elements[0], sv = JSON.parse(sb.value);
  ok(sd.channel === 'U1' && /Not booked yet/.test(sd.blocks[0].text.text) && sb.action_id === 'book_continue' && sb.text.text === 'Continue booking' && sv.d === '2027-10-27' && sv.s === '18:00' && sv.e === '21:00' && sv.p === 'VO Recording',
     'step 2 could not be shown -> the DM with Continue booking (date, time, type)', sd);
  sd = await j1(si, 'Step 2 DM', [{ json: { ok: false } }], { 'Read Step 1': [{ json: { s: Object.assign({}, S1.s, { kind: 'booth', purpose: '__booth', series: { dates: ['2027-10-27', '2027-11-03'] } }) } }] });
  ok(sd.blocks[1].elements[0].action_id === 'open_book' && sd.blocks[1].elements[0].value === 'menu', 'a repeating booking -> Book a room');
  const cdOuts = A => ({ 'After Cancel': [{ json: A }], 'Check Signature': [{ json: { user: 'U1' } }], 'Read Request': [{ json: { payload: pay } }] });
  ok((await run(si, 'Cancel DM', [{ json: { ok: true } }], cdOuts({ ok: true, blocks: [] }))).length === 0, 'the message updated -> no DM');
  let cd = await j1(si, 'Cancel DM', [{ json: { ok: false, error: 'message_not_found' } }], cdOuts({ ok: true, blocks: [{ type: 'section', block_id: 'bk_e1', text: { type: 'mrkdwn', text: '❌ *Cancelled.*\n\n*ORANGE / Jem Lim / HL*\n*Date:* x' } }] }));
  ok(cd.channel === 'U1' && /^❌ \*Cancelled\.\*/.test(cd.blocks[0].text.text) && cd.blocks[1].elements.map(e => e.action_id).join() === 'open_book,my_bookings', 'cancelled, message gone -> the Cancelled card in the DM', cd);
  cd = await j1(si, 'Cancel DM', [{ json: { ok: false } }], cdOuts({ ok: false, blocks: [{ type: 'context', block_id: 'bkw_e1', elements: [{ type: 'mrkdwn', text: '⚠️ Only the booker, engineer or arranger can cancel this.' }] }] }));
  ok(/^⚠️ \*ORANGE \/ Jem Lim \/ HL\* was not cancelled\. Only the booker/.test(cd.blocks[0].text.text), 'not cancelled -> why, in the DM', cd.blocks[0].text.text);

  console.log('129 - notices');
  const bl = code(si, 'Booked Notices').split('\n').find(l => l.startsWith('    const text = (to !== x.id'));
  ok(['Series Notices', 'Change Notices'].every(n => code(si, n).split('\n').find(l => l.startsWith('    const text = (to !== x.id')) === bl) && /x\.line \|\|/.test(bl), 'one notices(): Series / Change Notices take x.line like Booked Notices');
  const sn = (await run(si, 'Series Notices', [], { 'Read Series Confirm': [{ json: { user: 'U1' } }],
    'To Book Series': [{ json: { go: true, description: 'Engineer: Daryl Reyes | Arranger: Pia Lopez | Booked by: Howard Luistro (for Camy Caridad) | ref: U1 | team: U2 U4 U08JL17A50A | Notes: x\nSType: VO\n\nNotes:\nteam: U9' } }],
    'After Book Series': [{ json: { text: '✅ *Booked 3 dates.*\n\n*SER / DR x PL*\n*Dates:*\n- Tue, Oct 19' } }], 'Read Cache 8': cache })).map(i => i.json.text);
  ok(sn.length === 3 && /booked you as the engineer for 3 dates/.test(sn[0]) && /booked you as the arranger for 3 dates/.test(sn[1]) && /Howard Luistro booked 3 dates for you\./.test(sn[2]) && !sn.some(t => /U9/.test(t.split('\n')[0])),
     'a series: the engineer, the arranger, and who it is for ("booked 3 dates for you", not "as the arranger")', sn.map(t => t.split('\n').slice(0, 2).join(' / ')));
  ok(/teamWas: \[O\.en, O\.ar\]/.test(code(si, 'Read Change')), 'Read Change sends who was engineer / arranger (teamWas)');
  const rb = code(mv, 'Resolve Booking');
  const k1 = rb.indexOf('let __title = title, __desc = desc'), k2 = rb.indexOf('} catch (e) { __title = title; __desc = desc;', k1);
  const rewrite = (desc, nd, team) => new Function('desc', 'title', 'REQ', 'team', rb.slice(k1, k2) + '} catch (e) { __title = title; __desc = desc; }\nreturn [__desc, __teamChanged];')(desc, 'T', { new_details: JSON.stringify(nd) }, team);
  const D0 = 'Engineer: Daryl Reyes | Booked by: Howard Luistro (for Camy Caridad) | ref: U1 | team: U2 U08JL17A50A | Type: Advertising\nSType: VO Recording';
  let rw = rewrite(D0, { Engineer: 'Pia Lopez', Arranger: '', team: 'U4', teamWas: ['U2'] }, ['U2', 'U08JL17A50A']);
  ok(/team: U4 U08JL17A50A/.test(rw[0]) && rw[1] === true, 'a new engineer: who it is for stays on team:', rw[0]);
  rw = rewrite(D0, { Engineer: 'Pia Lopez', Arranger: '', team: 'U4' }, ['U2', 'U08JL17A50A']);
  ok(/team: U4(?: |$|\n)/.test(rw[0]) && !/U08JL17A50A/.test(rw[0].split('\n')[0].split('team:')[1]), 'an older Slack Interactions (no teamWas): as before', rw[0]);
  rw = rewrite(D0, { Notes: 'n' }, ['U2', 'U08JL17A50A']);
  ok(/team: U2 U08JL17A50A/.test(rw[0]) && rw[1] === false, 'no team change -> team: untouched');
  const notice = (co) => new Function('$', code(mv, 'Build Recipients'))(n => ({ first: () => ({ json: n === 'Resolve Booking' ? co
    : n === 'When Executed by Another Workflow' ? { requester: 'U9', requester_name: 'Camy', booking_date: '2027-10-27' } : {} }) })).map(i => i.json);
  const CO = { title: 'T / HL', bookerRef: 'U1', bookerName: 'Howard', team: ['U2', 'U5'], old_start: '2027-10-27T18:00:00+08:00', old_end: '2027-10-27T21:00:00+08:00',
    new_start: '2027-10-27T18:00:00+08:00', new_end: '2027-10-27T21:00:00+08:00', old_location: 'KDC Plaza-Top Level-Studio F (12)', location: 'Studio F', description: D0, new_team: ['U2', 'U5'], team_changed: false };
  const lead = o => o.blocks[0].text.text.split('\n')[0];
  let ns = notice(CO);
  ok(ns.length === 3 && lead(ns[0]) === 'Your booking was changed by Camy:' && lead(ns[1]) === 'A session you are on was changed by Camy:', 'only the details changed -> "changed"', ns.map(lead));
  ns = notice(Object.assign({}, CO, { new_start: '2027-10-28T18:00:00+08:00', new_end: '2027-10-28T21:00:00+08:00' }));
  ok(lead(ns[0]) === 'Your booking was moved by Camy:', 'a new date -> "moved"');
  ns = notice(Object.assign({}, CO, { location: 'Studio 7' }));
  ok(lead(ns[0]) === 'Your booking was moved by Camy:', 'a new room -> "moved"');
  ns = notice(Object.assign({}, CO, { old_location: 'KDC Plaza-Top Level-Likha (Big Room) (12)', location: 'Likha' }));
  ok(lead(ns[0]) === 'Your booking was changed by Camy:', 'the same room written two ways ("Likha (Big Room) (12)" / "Likha") -> "changed"');
  const older = Object.assign({}, CO); delete older.old_end; delete older.old_location; delete older.new_team; delete older.team_changed;
  ok(lead(notice(older)[0]) === 'Your booking was moved by Camy:', 'an older Resolve Booking (no old_end) -> "moved", as before');
  ns = notice(Object.assign({}, CO, { team_changed: true, new_team: ['U4', 'U5'] }));
  ok(ns.length === 3 && lead(ns[1]) === 'You were taken off this session by Camy:' && lead(ns[2]) === 'A session you are on was changed by Camy:', 'an engineer taken off -> "You were taken off this session"', ns.map(lead));
  ok(/old_end: .*old_location: ev\.location/.test(rb) && /new_team: \(\(_hd\(__desc\)/.test(rb) && /team_changed: __teamChanged/.test(rb), 'Resolve Booking returns old_end, old_location, new_team, team_changed');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
