#!/usr/bin/env node
// Book Session v129 + Slack Interactions v76 (9 Nov, Howard): "Check your booking in Google Calendar" with the event's link on the
// Booked card (form and DM). Usage: node scripts/sim-calendar-link.js [book-session] [slack-interactions]
const fs = require('fs');
const bs = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/book-session-v129.json', 'utf8'));
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v76.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const CAL = 'c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com';
(async () => {
  console.log('Book Session v129: Verify passes the link on');
  const REQ = { start_iso: '2026-11-12T14:00:00+08:00', end_iso: '2026-11-12T16:00:00+08:00' };
  const CC = { final_start: REQ.start_iso, final_end: REQ.end_iso, duration_note: '' };
  const ev = { id: 'abc123def', summary: 'SONG / Jem Lim / MV', start: { dateTime: REQ.start_iso }, end: { dateTime: REQ.end_iso }, attendees: [],
    htmlLink: 'https://www.google.com/calendar/event?eid=YWJjMTIzZGVmIGNfcmU1bWNyZzlvbTBtYWNwOWRvcWhsc2k4M2dAZw' };
  const outs = { 'When Executed by Another Workflow': [{ json: REQ }], 'Check Conflicts': [{ json: CC }], 'Create Event': [{ json: ev }] };
  let v = await j1(bs, 'Verify', [{ json: ev }], outs);
  ok(v.status === 'CREATED' && v.html_link === ev.htmlLink && v.event_id === 'abc123def' && v.human === 'Booked.', 'CREATED carries Google\'s htmlLink as html_link (the rest as before)', v);
  const ev2 = Object.assign({}, ev); delete ev2.htmlLink;
  v = await j1(bs, 'Verify', [{ json: ev2 }], Object.assign({}, outs, { 'Create Event': [{ json: ev2 }] }));
  const want = 'https://www.google.com/calendar/event?eid=' + Buffer.from('abc123def ' + CAL).toString('base64').replace(/=+$/, '');
  ok(v.status === 'CREATED' && v.html_link === want, 'no htmlLink from Google -> the link built from the id and the KDC Bookings calendar', v.html_link);
  ok(Buffer.from(v.html_link.split('eid=')[1], 'base64').toString() === 'abc123def ' + CAL, '… which decodes to "<event id> <calendar>" (Google\'s eid)');
  v = await j1(bs, 'Verify', [{ json: Object.assign({}, ev, { attendees: [{ email: 'x@resource.calendar.google.com', displayName: 'Studio 7', responseStatus: 'declined' }] }) }], outs);
  ok(v.status === 'ROOM_DECLINED' && !v.html_link, 'a declined room -> no link (nothing is booked)');

  console.log('Slack Interactions v76: the Booked card');
  const ctx = { 'Read Step 2': [{ json: { s: { date: '2026-11-12', t0: '14:00', t1: '16:00', when: 'Thursday, November 12, 2026 · 2:00 PM – 4:00 PM', purpose: 'Music Recording', kind: 'studio' }, room: 'Studio 7', viewId: 'V1', channel: 'D1' } }],
    'After Prepare': [{ json: { F: { Room: 'Studio 7' }, book: { start_iso: REQ.start_iso, end_iso: REQ.end_iso } } }] };
  const ab = await j1(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'abc123def', title: 'SONG / Jem Lim / MV', html_link: ev.htmlLink } }], ctx);
  const V78 = Number((si.name.match(/v(\d+)/) || [])[1]) >= 78;   // v78: "🔗 Check your booking in GCal"
  const line = V78 ? '🔗 <' + ev.htmlLink + '|Check your booking in GCal>' : '<' + ev.htmlLink + '|Check your booking in Google Calendar>';
  const dmCard = ab.blocks.find(b => b.block_id === 'bk_abc123def'), formCard = ab.view.blocks[0];
  ok(dmCard && dmCard.text.text.endsWith('\n\n' + line) && /^✅ \*Booked\.\*\n\n\*SONG \/ Jem Lim \/ MV\*/.test(dmCard.text.text), 'the DM card ends with ' + (V78 ? '"🔗 Check your booking in GCal"' : '"Check your booking in Google Calendar"') + ' (the link), after the details', dmCard && dmCard.text.text);
  ok(formCard.text.text === dmCard.text.text, 'the form\'s Booked screen shows the same');
  ok(!/google\.com/.test(ab.text) && /^✅ \*Booked\.\*/.test(ab.text), 'the message\'s plain text (notifications, Booked Notices, what Jessie reads back) has no link', ab.text);
  ok(ab.blocks.map(b => b.block_id || b.type).join() === 'bk_abc123def,bka_abc123def,nav', 'the rest of the DM as before: Change / Cancel, Book another / My bookings');
  const ab0 = await j1(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'abc123def', title: 'SONG / Jem Lim / MV' } }], ctx);
  ok(!/Google Calendar|GCal/.test(JSON.stringify(ab0.blocks)) && ab0.blocks[0].text.text === ab0.text, 'no link from Book Session (v128) -> the card exactly as before');
  const ab1 = await j1(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'abc123def', title: 'X', html_link: 'https://evil.example/x|Click' } }], ctx);
  ok(!/evil|Google Calendar|GCal/.test(JSON.stringify(ab1.blocks)), 'anything not a Google Calendar event link is left out');
  if (/v7[7-9]|v[89]\d/.test(si.name.match(/v\d+/)[0])) {   // v77: no link preview under the Booked DM
    const jb = si.nodes.find(n => n.name === 'DM Booked').parameters.jsonBody.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
    const body = JSON.parse(new Function('$', 'return (' + jb + ');')(n => ({ first: () => ({ json: n === 'After Book' ? ab : {} }) })));
    ok(body.unfurl_links === false && body.unfurl_media === false && (body.blocks || []).length === ab.blocks.length && body.channel === 'D1',
      'v77: the Booked DM is posted with unfurl_links / unfurl_media false (no Google Workspace preview), the card as built', body);
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
