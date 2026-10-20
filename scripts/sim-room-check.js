#!/usr/bin/env node
// "Booked." without the room wait (20 Oct): Book Session v117 returns right after creating the event and hands the rooms' answer
// to Jessie — Room Check v1 (not waited on); a decline deletes the event, DMs the person who booked and logs ROOM_DECLINED.
// Also Slack Interactions v32's Timing Sample order (it runs before the DMs).
// Usage: node scripts/sim-room-check.js [book-session v117] [room-check v1] [slack-interactions v32]
const fs = require('fs');
const B = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/book-session-v117.json', 'utf8'));
const RC = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/room-check-v1.json', 'utf8'));
const SI = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/slack-interactions-v32.json', 'utf8'));
if (!B.nodes.some(n => n.name === 'Room Check')) { console.log('0 ok, 0 failed (Book Session v117 on; this build is older)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const nx = (wf, k) => ((wf.connections[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
async function run(wf, name, input, outs) {
  const js = node(wf, name).parameters.jsCode;
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; } return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const expr = (e, outs) => { const body = String(e).replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); return new Function('$', 'return (' + body + ');')($); };
const T = 'When Executed by Another Workflow';

(async () => {
  console.log('Book Session v117: Booked as soon as the event is created');
  const gone = ['Wait for Room', 'Reread Event', 'Room Answered?', 'Wait for Room 2', 'Reread Event 2', 'Room Answered 2?', 'Wait for Room 3', 'Reread Event 3'];
  ok(gone.every(n => !node(B, n)) && !B.nodes.some(n => n.type === 'n8n-nodes-base.wait'), 'no room-wait steps left (1.5-6 s off every booking)');
  ok(nx(B, 'Create Event') === 'Verify | Return Rejection' && nx(B, 'Logged?') === 'Build Log Row | Declined?' && nx(B, 'Log Booking') === 'Room Check' && nx(B, 'Room Check') === 'Return Booked',
     'Create Event -> Verify -> … -> Log Booking -> Room Check -> Return Booked', [nx(B, 'Create Event'), nx(B, 'Log Booking'), nx(B, 'Room Check')]);
  const created = { id: 'ev1', summary: 'NET-CMA / JL', start: { dateTime: '2027-10-21T15:00:00+08:00' }, end: { dateTime: '2027-10-21T18:00:00+08:00' },
    attendees: [{ email: 's6@resource.calendar.google.com', resource: true, responseStatus: 'needsAction', displayName: 'Studio 6' }, { email: 'sa@resource.calendar.google.com', resource: true, responseStatus: 'needsAction', displayName: 'Studio A' }] };
  const REQ = { start_iso: '2027-10-21T15:00:00+08:00', end_iso: '2027-10-21T18:00:00+08:00', summary: 'NET-CMA / JL', rooms: 'Studio 6, Studio A', all_day: false,
    session_type: 'Localization Dubbing', description: 'Engineer: Josiah Lateo | Booked by: Howard Luistro | ref: U08V3CKDGJF | team: U044A89SGQY' };
  const CC = { final_start: REQ.start_iso, final_end: REQ.end_iso, final_rooms: 'Studio 6, Studio A', final_summary: 'NET-CMA / JL' };
  const v = (await run(B, 'Verify', [{ json: created }], { 'Create Event': [{ json: created }], [T]: [{ json: REQ }], 'Check Conflicts': [{ json: CC }] }))[0].json;
  ok(v.status === 'CREATED' && v.event_id === 'ev1' && v.title === 'NET-CMA / JL' && v.human === 'Booked.', 'Verify on the create response (rooms not answered yet) -> CREATED, "Booked."', v);
  const bad = (await run(B, 'Verify', [{ json: Object.assign({}, created, { start: { dateTime: '2027-10-21T16:00:00+08:00' } }) }], { [T]: [{ json: REQ }], 'Check Conflicts': [{ json: CC }] }))[0].json;
  ok(bad.status === 'MISMATCH', 'times not as asked -> still MISMATCH (unchanged)');
  const rcn = node(B, 'Room Check'), m = rcn.parameters.workflowInputs.value;
  const outs = { 'Verify': [{ json: v }], 'Check Conflicts': [{ json: CC }], [T]: [{ json: REQ }] };
  const got = Object.fromEntries(Object.entries(m).map(([k, e]) => [k, expr(e, outs)]));
  ok(got.event_id === 'ev1' && got.title === 'NET-CMA / JL' && got.rooms === 'Studio 6, Studio A' && got.requester === 'U08V3CKDGJF' && got.start_iso === REQ.start_iso
     && got.end_iso === REQ.end_iso && got.all_day === 'false' && got.session_type === 'Localization Dubbing', 'Room Check gets the event, the title, both rooms, the booker (ref:), the times', got);
  ok(rcn.parameters.options.waitForSubWorkflow === false && rcn.onError === 'continueRegularOutput' && rcn.type === 'n8n-nodes-base.executeWorkflow', 'called without waiting; a failed call never touches the booking');
  ok(['ROOM_CHECK_ID'].indexOf(rcn.parameters.workflowId.value) !== -1 || /^[A-Za-z0-9]{10,24}$/.test(rcn.parameters.workflowId.value), 'the Room Check id: the placeholder until set-room-check-id.py, then a real id - ' + rcn.parameters.workflowId.value);
  ok((() => { const tr = RC.nodes.find(n => n.name === T).parameters.workflowInputs.values.map(x => x.name); return Object.keys(m).every(k => tr.indexOf(k) !== -1) && tr.filter(k => Object.keys(m).indexOf(k) === -1).every(k => k === 'kind'); })(), 'the inputs match Room Check\'s trigger (v2 adds kind, which Book Session leaves empty)');

  console.log('Jessie — Room Check v1');
  ok(nx(RC, T) === 'Wait' && nx(RC, 'Wait') === 'Reread' && nx(RC, 'Reread') === 'Answered?' && nx(RC, 'Answered?') === 'Decide | Wait 2' && nx(RC, 'Answered 2?') === 'Decide | Wait 3'
     && nx(RC, 'Reread 3') === 'Decide' && (nx(RC, 'Decide') === 'Delete Declined' || (nx(RC, 'Decide') === 'Delete?' && nx(RC, 'Delete?') === 'Delete Declined | Build DM')) && nx(RC, 'Delete Declined') === 'Build DM' && nx(RC, 'Build DM') === 'Send DM'
     && nx(RC, 'Send DM') === 'Declined Row' && nx(RC, 'Declined Row') === 'Log Declined', 'read back at ~2 / 6 / 16 s, then decide, delete, DM, log');
  ok(['Wait', 'Wait 2', 'Wait 3'].map(n => node(RC, n).parameters.amount).join() === '2,4,10' && ['Wait', 'Wait 2', 'Wait 3'].every(n => node(RC, n).webhookId), 'waits 2 / 4 / 10 s (each with its own webhook id)');
  for (const n of ['Reread', 'Reread 2', 'Reread 3', 'Delete Declined']) ok(node(RC, n).credentials.googleCalendarOAuth2Api.id === '6D1r3kaq6KaFdL0a' && node(RC, n).onError === 'continueRegularOutput', n + ': the Google Calendar credential Book Session uses');
  ok(node(RC, 'Send DM').credentials.slackApi.id === 'EcX8szEJrOLYLUfl' && node(RC, 'Log Declined').credentials.googleApi.id === 'DU75rLW4KHlVhcK1' && node(RC, 'Log Declined').parameters.sheetName.value === 'gid=0',
     'Send DM: Jessie\'s Slack credential; Log Declined: the Log tab of the Jessie Log sheet');
  ok(!node(RC, 'Decide').onError, 'Decide stops the run on an error - never a delete on a guess');
  const tmpl = (t, outs) => { const $ = n => ({ first: () => (outs[n] || [])[0] }); return String(t).replace(/^=/, '').replace(/\{\{([\s\S]*?)\}\}/g, (m, e) => new Function('$', 'return (' + e + ');')($)); };
  const reread = tmpl(node(RC, 'Reread').parameters.url, { [T]: [{ json: { event_id: 'ev1' } }] });
  ok(/calendars\/c_re5mcrg9om0macp9doqhlsi83g%40group\.calendar\.google\.com\/events\/ev1$/.test(reread), 'Reread reads that one event on KDC Bookings', reread);
  const ans = ev => new Function('$json', 'return ' + node(RC, 'Answered?').parameters.conditions.conditions[0].leftValue.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''))(ev);
  ok(ans({ id: 'e', attendees: created.attendees }) === false && ans({ id: 'e', attendees: [{ resource: true, responseStatus: 'accepted' }, { resource: true, responseStatus: 'declined' }] }) === true,
     'Answered?: wait while a room has not answered; on once every room has');
  const TI = { event_id: 'ev1', title: 'NET-CMA / JL', rooms: 'Studio 6, Studio A', requester: 'U08V3CKDGJF', start_iso: REQ.start_iso, end_iso: REQ.end_iso, all_day: 'false', session_type: 'Localization Dubbing' };
  const decide = ev => run(RC, 'Decide', [{ json: ev }], { [T]: [{ json: TI }] });
  ok((await decide(Object.assign({}, created, { attendees: [{ resource: true, responseStatus: 'accepted' }, { resource: true, responseStatus: 'accepted' }] }))).length === 0, 'both rooms accepted -> nothing happens');
  ok((await decide(created)).length === 0, 'still no answer after 16 s -> nothing happens (the booking stands)');
  ok((await decide({ error: { message: 'Not Found' } })).length === 0 && (await decide({ id: 'ev1', status: 'cancelled' })).length === 0, 'the event gone (cancelled meanwhile) or unreadable -> nothing happens');
  const dec = await decide(Object.assign({}, created, { attendees: [{ resource: true, responseStatus: 'accepted', displayName: 'Studio 6' }, { resource: true, responseStatus: 'declined', displayName: 'Studio A (Vocal Booth)' }] }));
  ok(dec.length === 1 && dec[0].json.declined.join() === 'Studio A' && dec[0].json.event_id === 'ev1' && dec[0].json.requester === 'U08V3CKDGJF', 'Studio A declined -> delete ev1, tell U08V3CKDGJF', dec[0] && dec[0].json);
  ok((await decide(Object.assign({}, created, { attendees: [{ email: 'p@hitproductions.net', responseStatus: 'declined' }] }))).length === 0, 'a person (not a room) declining -> not a room decline');
  const dm = (await run(RC, 'Build DM', [{ json: {} }], { [T]: [{ json: TI }], 'Decide': dec }))[0].json;
  ok(dm.channel === 'U08V3CKDGJF' && /^❌ \*Studio A turned this booking down\* - its calendar shows it is taken then\. It was taken off the calendar, so nothing is booked\./.test(dm.blocks[0].text.text)
     && /\*NET-CMA \/ JL\*\nThursday, October 21, 2027 · 3:00 PM – 6:00 PM/.test(dm.blocks[0].text.text), 'the DM: which room, nothing booked, the booking and its date / time', dm.blocks[0].text.text);
  const btn = dm.blocks[1].elements[0], again = JSON.parse(btn.value);
  ok(btn.action_id === 'open_book' && again.d === '2027-10-21' && again.s === '15:00' && again.e === '18:00' && again.p === 'Localization Dubbing' && again.cd === 'NET-CMA' && dm.blocks[1].elements[1].action_id === 'my_bookings',
     'Book a room opens the form filled in (date, times, type, the code) + My bookings', again);
  const dmNot = (await run(RC, 'Build DM', [{ json: { error: { message: 'x' } } }], { [T]: [{ json: TI }], 'Decide': dec }))[0].json;
  ok(/could not be removed - delete it from the calendar/.test(dmNot.blocks[0].text.text) && dmNot.removed === false, 'the delete failed -> the DM says to delete it by hand');
  const booth = (await run(RC, 'Build DM', [{ json: {} }], { [T]: [{ json: Object.assign({}, TI, { title: 'M4 - Howard', rooms: 'M4', session_type: '', all_day: 'true' }) }], 'Decide': [{ json: { event_id: 'e', declined: ['M4'], title: 'M4 - Howard', requester: 'U1' } }] }))[0].json;
  ok(JSON.parse(booth.blocks[1].elements[0].value).p === '__booth' && /All day/.test(booth.blocks[0].text.text), 'an M booth all day -> Book a room opens booth time; "All day"');
  const lr = (await run(RC, 'Declined Row', [{ json: {} }], { [T]: [{ json: TI }], 'Decide': dec, 'Build DM': [{ json: dm }] }))[0].json;
  ok(lr.Action === 'ROOM_DECLINED' && lr.Title === 'NET-CMA / JL' && lr['Event ID'] === 'ev1' && /Studio A declined; removed/.test(lr.Note), 'a ROOM_DECLINED row for the Log sheet', lr);

  if (/v32: placed above the other steps/.test(JSON.stringify(SI.nodes))) {   // Slack Interactions v32 on
  console.log('Slack Interactions v32: the time taken when the answer is on screen');
  const by = Object.fromEntries(SI.nodes.map(n => [n.name, n]));
  for (const e of ['Show Step 2', 'Show Result', 'Show Series Step', 'Show Series Result', 'Show Change Result']) {
    const sib = SI.connections[e].main[0].map(c => c.node);
    const first = sib.slice().sort((a, b) => (by[a].position[1] - by[b].position[1]) || (by[a].position[0] - by[b].position[0]))[0];
    ok(first === 'Timing Sample', e + ': Timing Sample is the top branch, so it runs before ' + (sib.filter(x => x !== 'Timing Sample').join(', ') || 'nothing else'));
  }
  }

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
