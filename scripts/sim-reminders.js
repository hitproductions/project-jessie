#!/usr/bin/env node
// Jessie — Reminders v1 + Slack Interactions v35 (20 Oct): 4:00 PM - tomorrow's studio sessions; Monday 9:00 AM - the week's
// bookings (studios, M booths, meeting rooms); one DM per person (booker, engineer / arranger, who it is for); Still on / Keep,
// Change, Free up the room; the QA redirect and year shift. SI v35: Keep marks the row; no free usual room -> other rooms offered.
// Usage: node scripts/sim-reminders.js [reminders v1] [slack-interactions v35]
const fs = require('fs');
const RM = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/reminders-v1.json', 'utf8'));
const SI = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v35.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
const ALL = JSON.stringify(RM.nodes).indexOf('const ALL_TO_DEV = true;') !== -1;
const V3 = JSON.stringify(RM.nodes).indexOf('REMINDER: You have') !== -1;   // v3: a reminder - cards with Change / Cancel, no Still on   // v2: every reminder to Howard during QA
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const run = async (wf, name, input, outs) => { const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
  return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(wf, name).parameters.jsCode + '\n})();')($, $input); };
const B = (id, name, slack, info) => ({ id, fields: { Name: name, Initials: 'X', 'Slack User ID': slack, Info: info, Department: ['Music'] } });
const bookers = [B('b1', 'Howard Luistro', 'U08V3CKDGJF', 'Post Engineer'), B('b2', 'Daryl Reyes', 'U2', 'Music Engineer'), B('b3', 'Angelo Villegas', 'U3', 'Music Arranger, Goes by Anj.'),
  B('b4', 'Dilan Diaz', 'U4', 'Multimedia Specialist, Goes by Dilan.'), B('b5', 'Japs Concepcion', 'U5', 'Accounts Lead, Goes by Japs.'), B('b6', 'Camy Caridad', 'U08JL17A50A', 'Voice Caster')];
const rooms = FX.rooms.concat([{ id: 'm4', fields: { 'Room Name': 'M4', 'Room Type': ['M Booth'] } }]);
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const res = id => ({ email: id + '@resource.calendar.google.com', resource: true, responseStatus: 'accepted' });
const EV = (id, title, d, s, e, room, desc, extra) => Object.assign({ id, summary: title, start: { dateTime: d + 'T' + s + ':00+08:00' }, end: { dateTime: d + 'T' + e + ':00+08:00' },
  attendees: [Object.assign(res(id), { displayName: room })], description: desc }, extra || {});
const items = [
  EV('ev1', 'SONG / Jem Lim / DR x AV', '2027-10-22', '14:00', '16:00', 'Studio F', 'Engineer: Daryl Reyes | Arranger: Angelo Villegas | Booked by: Camy Caridad | ref: U08JL17A50A | team: U2 U3\nSType: Music Recording'),
  EV('ev2', 'POST PROCESSING - TRAILER / Dilan', '2027-10-22', '09:00', '11:00', 'Studio E', 'Engineer: Dilan Diaz | Booked by: Howard Luistro | ref: U08V3CKDGJF\nSType: Post Processing'),
  EV('ev3', 'M4 - Japs', '2027-10-22', '10:00', '12:00', 'M4', 'Booked by: Howard Luistro (for Japs Concepcion) | ref: U08V3CKDGJF | team: U5'),
  EV('ev4', 'LIKHA - Weekly sync', '2027-10-22', '15:00', '16:00', 'Likha', 'Booked by: Camy Caridad | ref: U08JL17A50A\nSType: Meeting'),
  EV('ev5', 'TABLET BOOKING', '2027-10-22', '13:00', '14:00', 'Studio 7', 'Booked on the tablet'),   // no ref: not made through Jessie
  EV('ev6', 'VO / HL', '2027-10-23', '13:00', '14:00', 'Studio 7', 'Booked by: Howard Luistro | ref: U08V3CKDGJF'),   // the day after tomorrow
  EV('ev7', 'GONE / HL', '2027-10-22', '13:00', '14:00', 'Studio 8', 'ref: U08V3CKDGJF', { status: 'cancelled' })];
(async () => {
  console.log('Window and the year shift');
  const now = new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
  let w = (await run(RM, 'Window', [], { 'Daily 4 PM': [{ json: {} }] }))[0].json;
  const exp = (Number(now.slice(0, 4)) + 1) + now.slice(4);
  ok(w.kind === 'daily' && w.yearShift === 1 && w.start === new Date(Date.parse(exp + 'T12:00:00Z') + 86400000).toISOString().slice(0, 10), 'daily (QA): tomorrow, a year ahead', w);
  w = (await run(RM, 'Window', [], { 'Monday 9 AM': [{ json: {} }] }))[0].json;
  ok(w.kind === 'weekly' && new Date(w.start + 'T12:00:00Z').getUTCDay() === 1 && (Date.parse(w.end) - Date.parse(w.start)) === 7 * 86400000, 'Monday (QA): Monday to Sunday of this week, a year ahead', w);
  ok(node(RM, 'Daily 4 PM').parameters.rule.interval[0].expression === '0 16 * * *' && node(RM, 'Monday 9 AM').parameters.rule.interval[0].expression === '0 9 * * 1' && (RM.settings.timezone === 'Asia/Manila' || !RM.settings.timezone), '4:00 PM daily and 9:00 AM Mondays, Manila time (n8n drops the setting on import: the instance default is Manila - the pruner\'s hour 4 runs 04:00 PHT)');
  console.log('the day before (4:00 PM)');
  const W1 = { kind: 'daily', start: '2027-10-22', end: '2027-10-23' };
  let out = (await run(RM, 'Build Reminders', [], { 'Window': [{ json: W1 }], 'List Events R': [{ json: { items } }], 'Read Cache R': cache })).map(i => i.json);
  const by = {}; for (const o of out) (by[o.person] = by[o.person] || []).push(o);
  const ids = o => o.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id.slice(3));
  ok(by['U08JL17A50A'] && ids(by['U08JL17A50A'][0]).join() === 'ev1', 'the booker (Camy) - her studio session only (not the Likha meeting)', by['U08JL17A50A'] && ids(by['U08JL17A50A'][0]));
  ok(by['U2'] && ids(by['U2'][0]).join() === 'ev1' && by['U3'] && ids(by['U3'][0]).join() === 'ev1', 'the engineer (Daryl) and the arranger (Angelo) are reminded too');
  ok(by['U4'] && ids(by['U4'][0]).join() === 'ev2', 'who it is for: Dilan on POST PROCESSING - TRAILER / Dilan (the Engineer line)');
  ok(by['U08V3CKDGJF'] && ids(by['U08V3CKDGJF'][0]).join() === 'ev2', 'the booker of the Post Processing (Howard) - not the M4 booth (daily = studios), not the day after');
  ok(!out.some(o => ids(o).some(x => ['ev5', 'ev6', 'ev7', 'ev3', 'ev4'].indexOf(x) !== -1)), 'not: a tablet booking (no ref), tomorrow+1, a cancelled event, M booths, meetings');
  const m = by['U2'][0];
  ok(m.channel === 'U08V3CKDGJF' && /Test: this reminder is for Daryl Reyes/.test(JSON.stringify(m.blocks)), 'QA: Daryl is not on ALLOW -> to Howard, marked "Test: … for Daryl Reyes"');
  if (V3) {
    ok(m.blocks[0].text.text === '🔔 *REMINDER: You have a booking tomorrow*' && m.text === 'Reminder: you have a booking tomorrow', 'v3: one booking -> "You have a booking tomorrow"', m.blocks[0].text.text);
    const card = m.blocks.find(b => b.block_id === 'bk_ev1').text.text;
    ok(card === '*SONG / Jem Lim / DR x AV*\n*Date:* Friday, October 22, 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio F', 'v3: the booking as a card - title, Date, Time, Room', card);
    const a3 = m.blocks.find(b => b.block_id === 'bka_ev1').elements;
    ok(a3.map(x => x.action_id + ':' + x.text.text).join() === 'bk_change:Change,bk_cancel:Cancel' && a3[1].confirm && !m.blocks.some(b => b.block_id === 'rm_nav'), 'v3: Change / Cancel only (Cancel asks first), no Still on, no My bookings');
    ok(m.blocks[m.blocks.length - 1].type === 'context', 'v3: the test line at the bottom');
  }
  if (ALL) ok(out.every(o => o.channel === 'U08V3CKDGJF') && /Test: this reminder is for Camy Caridad/.test(JSON.stringify(by['U08JL17A50A'][0].blocks)) && !/Test:/.test(JSON.stringify(by['U08V3CKDGJF'][0].blocks)),
    'QA (v2): every reminder to Howard - Camy (on ALLOW) too, marked; Howard\'s own unmarked');
  else ok(by['U08JL17A50A'][0].channel === 'U08JL17A50A' && !/Test:/.test(JSON.stringify(by['U08JL17A50A'][0].blocks)), 'QA: Camy is on ALLOW -> to Camy herself');
  const acts = m.blocks.find(b => b.block_id === 'bka_ev1').elements;
  if (!V3) ok(acts.map(a => a.action_id + ':' + a.text.text).join() === 'rm_keep:Still on,bk_change:Change,bk_cancel:Free up the room' && acts[2].confirm.title.text === 'Free up this room?' && JSON.parse(acts[1].value).id === 'ev1',
     'Still on / Change / Free up the room (Slack\'s confirm), the row ids bk_ / bka_ as My bookings', acts.map(a => a.action_id));
  if (!V3) ok(/📅 \*Tomorrow\* · Friday, October 22, 2027/.test(m.blocks.find(b => b.type === 'section').text.text), 'the header: Tomorrow · Friday, October 22, 2027');
  ok((await run(RM, 'Build Reminders', [], { 'Window': [{ json: W1 }], 'List Events R': [{ json: { error: 'boom' } }], 'Read Cache R': cache })).length === 0, 'the calendar could not be read -> nothing sent');
  console.log('Monday 9:00 AM');
  out = (await run(RM, 'Build Reminders', [], { 'Window': [{ json: { kind: 'weekly', start: '2027-10-18', end: '2027-10-25' } }], 'List Events R': [{ json: { items } }], 'Read Cache R': cache })).map(i => i.json);
  const H = out.find(o => o.person === 'U08V3CKDGJF'), J = out.find(o => o.person === 'U5'), C = out.find(o => o.person === 'U08JL17A50A');
  ok(H && ids(H).join() === 'ev2,ev3,ev6', 'Howard\'s week: the Post Processing, the M4 booth, Saturday\'s VO - in time order', H && ids(H));
  ok(J && ids(J).join() === 'ev3', 'Japs (who the M4 booth is for) gets it too');
  ok(C && ids(C).join() === 'ev1,ev4', 'Camy: her studio session and her Likha meeting');
  if (V3) ok(/🔔 \*REMINDER: You have bookings this week\*\nMon, Oct 18 – Sun, Oct 24/.test(H.blocks[0].text.text) && H.blocks.filter(b => b.type === 'divider').length === 2 && /Reminder: you have 3 bookings this week/.test(H.text)
     && /You have a booking this week/.test(J.blocks[0].text.text), 'v3 Monday: "You have bookings this week" + the dates, a line between bookings; one -> "a booking"', H.blocks[0].text.text);
  else ok(H.blocks.find(b => b.block_id === 'bka_ev3').elements[0].text.text === 'Keep' && JSON.parse(H.blocks.find(b => b.block_id === 'bka_ev3').elements[0].value).w === 'weekly' && /Your week/.test(JSON.stringify(H.blocks)), 'Keep / Change / Free up; "Your week"');
  console.log('Slack Interactions v35: Still on / Keep');
  const cs = SI.nodes.find(n => n.name === 'Check Signature').parameters.jsCode;
  const route = (await run(SI, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload: { type: 'block_actions', actions: [{ action_id: 'rm_keep' }] } } }] }))[0].json.route;
  const nx = k => ((SI.connections[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+'));
  ok(route === 15 && nx('Route')[15] === 'Ack Keep' && nx('Ack Keep')[0] === 'Keep Row' && nx('Keep Row')[0] === 'Update Kept' && node(SI, 'Route').parameters.numberOutputs >= 16, 'rm_keep -> route 15 -> Ack Keep -> Keep Row -> Update Kept');
  const msg = { ts: '9.9', text: 'Tomorrow', blocks: m.blocks };
  const kr = (await run(SI, 'Keep Row', [], { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'rm_keep', value: JSON.stringify({ id: 'ev1', w: 'daily' }) }], message: msg, container: { channel_id: 'D1', message_ts: '9.9' } } } }] }))[0].json;
  ok(kr.channel === 'D1' && kr.ts === '9.9' && !kr.blocks.some(b => b.block_id === 'bka_ev1') && kr.blocks.some(b => b.block_id === 'bkd_ev1' && b.elements[0].text === '✓ Still on'), 'Still on: the row\'s buttons become "✓ Still on"', kr.blocks.map(b => b.block_id));
  console.log('Slack Interactions v35: no usual room free -> other rooms');
  const ST = (t, pri, last) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': last, 'Engineer Role Required': ['Music Engineer', 'Music Arranger'], 'Room Requirements': 'Large' } });
  const c2 = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: [ST('Band Recording', ['rf', 'rc'], ['lk', 'ka', 'sa'])], bookers }) } }];
  const s = { date: '2027-10-20', t0: '09:00', t1: '11:00', purpose: 'Band Recording', kind: 'studio', requester: 'U2', channel: 'D1', ext: 'x' };
  const v = (await run(SI, 'Build Step 2', [{ json: { status: 'OK', busy: ['Studio F', 'Studio C'], free_priority: [], free_last_resort: [] } }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': c2, 'Loc Projects 2': [] }))[0].json.view;
  const lbl = v.blocks.find(b => b.block_id === 'room_label'), radio = v.blocks.find(b => b.block_id === 'room');
  ok(lbl && /Available rooms:/.test(lbl.text.text) && v.blocks.some(b => b.block_id === 'room_why') && radio && radio.elements[0].options.length === 6 && !radio.elements[0].options.some(o => /Studio [FC]$/.test(o.value)),
     'Band Recording with F and C taken (20 Oct) -> "Available rooms:" + why, 6 free studios', v.blocks.map(b => b.block_id));
  ok(v.submit && JSON.parse(v.private_metadata).nu.length === 6 && v.blocks.some(b => b.block_id === 'project'), 'booked as asked (nu), with the details and a Book button');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
