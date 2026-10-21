#!/usr/bin/env node
// Slack Interactions v40 + main v280 (22 Oct): the date / time / type summaries on separate lines, not one " · " line (Howard, on
// a phone). Step 2's header (one booking, a series), the DM's "Your booking details:" (working, booked; one booking, a series)
// and a typed request's "Your booking details so far:". Booking rows in lists and cards keep one line (decided).
// Usage: node scripts/sim-v40-lines.js [slack-interactions v40] [main v280]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v40.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v280.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
async function runIn(wf, name, input, outs) {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (wf, ...a) => (await runIn(wf, ...a))[0].json;
if (JSON.stringify(si.nodes).indexOf('v40: ') === -1) { console.log('0 ok, 0 failed (an older build: v40 not in it)'); process.exit(0); }
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'] } }] }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const read2 = async (vv, meta) => j1(si, 'Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const step2 = async (s, ra) => (await j1(si, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-22', t0: '11:00', t1: '15:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const head = v => v.blocks[1].text.text;
const menuMsg = { ts: '50.5', text: 'Hi', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } }, { type: 'actions', elements: [{ action_id: 'open_book', value: 'menu' }] }] };

(async () => {
  console.log('Step 2');
  let v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] });
  ok(head(v) === '🗓️ *Friday, Oct 22, 2027*\n*11:00 AM–3:00 PM*\n*VO Recording*', 'one booking: date / time / type, each bold on its own line', head(v));
  v = await step2(S('', 'booth', { allDay: true, t0: '00:00', t1: '23:59' }), { free_rooms: ['M1', 'M2'] });
  ok(head(v) === '🗓️ *Friday, Oct 22, 2027*\n*All day*\n*M booth*', 'an M booth all day', head(v));
  const s2 = await step2(S('VO Recording', 'studio', { series: { dates: ['2027-10-22', '2027-10-29', '2027-11-05'] } }), { free_priority: ['Studio 7'] });
  ok(/^🗓️ \*\d+ dates\*\n\*11:00 AM–3:00 PM\*\n\*VO Recording\*$/.test(head(s2)), 'a series: N dates / time / type', head(s2));
  console.log('Your booking details: (the DM)');
  const r = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } },
    Object.assign(S('VO Recording', 'studio'), { when: 'Friday, Oct 22, 2027 · 11:00 AM–3:00 PM', label: 'VO Recording', msg: { ch: 'D1', ts: '50.5' } }));
  const MS = await j1(si, 'Mark Source', [{ json: { ok: true, messages: [menuMsg] } }], { 'Read Step 2': [{ json: r }] });
  ok(MS.blocks && MS.blocks[0].text.text === 'Your booking details:\n🗓️ *Studio 7*\n*Friday, October 22, 2027*\n*11:00 AM – 3:00 PM*', 'one booking: room / date / time', MS.blocks ? MS.blocks[0].text.text : MS);
  const offerMsg = { ts: '50.5', text: 'so far', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Your booking details so far:\n🗓️ *Studio 8*\n*Friday, October 22, 2027*\n*11:00 AM – 3:00 PM*' } },
    { type: 'actions', elements: [{ action_id: 'open_book', value: '{"r":"Studio 8"}' }, { action_id: 'my_bookings', value: 'menu' }] }] };
  const MO = await j1(si, 'Mark Source', [{ json: { ok: true, messages: [offerMsg] } }], { 'Read Step 2': [{ json: r }] });
  const SD = await runIn(si, 'Source Done', [], { 'Mark Source': [{ json: MO }], 'After Book': [{ json: { ok: true } }] });
  ok(MO.blocks[0].text.text === MS.blocks[0].text.text && SD[0].json.blocks[0].text.text === MS.blocks[0].text.text && SD[0].json.blocks[1].elements[0].text === '✅ Booked.',
     'a typed offer booked from the form (Studio 8 -> 7): the form\'s room / date / time, then "✅ Booked."', SD[0].json.blocks);
  const MSS = await j1(si, 'Mark Source Series', [{ json: { ok: true, messages: [menuMsg] } }], { 'Read Series Confirm': [{ json: { meta: { msg: { ch: 'D1', ts: '50.5' }, n: 3, time: '14:00-16:00', rooms: 'Studio 6, Studio A' } } }] });
  ok(MSS.blocks[0].text.text === 'Your booking details:\n🗓️ *Studio 6 + Studio A*\n*3 dates*\n*2:00 PM – 4:00 PM*', 'a series: rooms / N dates / time', MSS.blocks[0].text.text);
  console.log('A typed request (main)');
  const offer = async (text, dates, bf) => (await j1(main, 'Form Offer', [{ json: {} }], {
    'All Rooms': ['Studio 7', 'Studio 8'].map(x => ({ json: { fields: { 'Room Name': x } } })), 'All Session Types': ['VO Recording'].map(x => ({ json: { fields: { Type: x } } })), 'All Bookers': [],
    'Slack Trigger': [{ json: { text, channel: 'D1', ts: '200' } }], 'Gate Context': [{ json: { datesInMessage: dates, todayIso: '2027-10-21', gate: {} } }],
    'Booked For': [{ json: Object.assign({ requesterText: text }, bf) }], 'Get Recent Messages': [{ json: { ts: '200', text, user: 'U1' } }, { json: { bot_id: 'B1', ts: '100', text: 'Hi', blocks: [] } }] })).formOffer;
  let F = await offer('book studio 7 tomorrow 11am-3pm vo recording project orange', '2027-10-22', { timeInNewest: true, timeStart: '11:00', timeEnd: '15:00', project: 'orange' });
  ok(/^Your booking details so far:\n🗓️ \*Studio 7\*\n\*Friday, October 22, 2027\*\n\*11:00 AM – 3:00 PM\*\nVO Recording\nProject: /.test(F.text), 'room / date / time bold, then type and project on their own lines', F.text);
  F = await offer('book studio 7 every friday 2-4pm 4 times', '', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(/🔁 Every Friday · 4 times/.test(F.text) && !/🗓️ \*[^\n]* · /.test(F.text), 'a series: the pattern stays one line, the header has no dots', F.text);
  console.log('Booking rows keep one line (decided)');
  const rowFn = si.nodes.find(n => n.name === 'Render My Bookings').parameters.jsCode;
  ok(/function whenLine\(b\) \{ return dayShort\(b\.d\) \+ ' · '/.test(rowFn), 'My bookings rows: unchanged');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
