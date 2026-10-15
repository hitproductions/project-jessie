#!/usr/bin/env node
// main v273 (v272 fixed) offline: the Slack exchange of 15 Oct 16:56-16:57. Book a room under an answer carries the message's
// date / time / room since v272, and Form Offer took that answer for its own offer - so the next question was "more details".
// Usage: node scripts/sim-v273.js [main v273]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v273.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = n => main.nodes.find(x => x.name === n).parameters.jsCode;
async function run(name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

// Jessie's messages as Slack returns them (newest first in history)
const answer = { bot_id: 'B1', ts: '100', text: 'x', blocks: [
  { type: 'section', text: { type: 'mrkdwn', text: '🗓️ October 16 (Saturday), 3:00 PM – 5:00 PM\n\n⚠️ Studio 8 is booked 4:00 PM – 5:00 PM (LEMON ADE / Harold Orozco / HL) - free 3:00 PM – 4:00 PM.' } },
  { type: 'actions', elements: [{ type: 'button', action_id: 'open_book', value: JSON.stringify({ d: '2027-10-16', s: '15:00', e: '17:00', r: 'Studio 8' }) },
    { type: 'button', action_id: 'my_bookings', value: 'menu' }] }] };
const offerMsg = { bot_id: 'B1', ts: '101', text: 'x', blocks: [
  { type: 'section', text: { type: 'mrkdwn', text: 'Here’s what I have so far:\n🗓️ *Studio 8 · Saturday, October 16 · 3:00 PM – 5:00 PM*' } },
  { type: 'actions', elements: [{ type: 'button', action_id: 'open_book', value: JSON.stringify({ r: 'Studio 8', d: '2027-10-16', s: '15:00', e: '17:00' }) },
    { type: 'button', action_id: 'my_bookings', value: 'menu' }] },
  { type: 'context', elements: [{ type: 'mrkdwn', text: 'Opens the form with these filled in - only free rooms are offered.' }] }] };

const offer = async (text, last, dates, bf) => (await j1('Form Offer', [{ json: {} }], {
  'All Rooms': ['Studio 4', 'Studio 7', 'Studio 8'].map(r => ({ json: { fields: { 'Room Name': r } } })), 'All Session Types': ['VO Recording'].map(t => ({ json: { fields: { Type: t } } })), 'All Bookers': [],
  'Slack Trigger': [{ json: { text, channel: 'D1', ts: '200' } }], 'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-15', gate: {} } }],
  'Booked For': [{ json: Object.assign({ requesterText: text }, bf || {}) }], 'Get Recent Messages': [{ json: { ts: '200', text, user: 'U1' } }, { json: last }] })).formOffer;

(async () => {
  // the 16:57 replies
  let F = await offer('what do I have this week?', answer, '2027-10-15,2027-10-16,2027-10-17,2027-10-18,2027-10-19,2027-10-20,2027-10-21');
  ok(!F.offer, '16:57 "what do I have this week?" after the Studio 8 answer -> no offer (was "Here’s what I have so far: Studio 8 · 3-5 PM") - ' + F.why);
  F = await offer('what\'s in studio 4 on thursday?', offerMsg, '2027-10-21');
  ok(!F.offer && F.why === 'a question after an offer', '16:57 "what\'s in studio 4 on thursday?" after an offer -> no offer (was Studio 4 · Thursday · 3-5 PM) - ' + F.why);
  F = await offer('what\'s in studio 4 on thursday?', answer, '2027-10-21');
  ok(!F.offer, '"what\'s in studio 4 on thursday?" after an answer -> no offer - ' + F.why);
  // an answer's button is not an offer: details after it are a new request, not added to its date / room
  F = await offer('studio 7 tomorrow 2-4pm', answer, '2027-10-16', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(F.offer && F.why === 'a booking request' && F.prefill.r === 'Studio 7' && F.prefill.s === '14:00', 'booking details after an answer -> their own offer');
  // a real offer still builds
  F = await offer('project orange', offerMsg, '', { project: 'orange' });
  ok(F.offer && F.why === 'more details after an offer' && F.prefill.r === 'Studio 8' && F.prefill.pj && /orange/i.test(F.prefill.pj), 'details after an offer still add to it - ' + JSON.stringify(F.prefill));
  F = await offer('book studio 7 friday 1-2pm instead', offerMsg, '2027-10-22', { timeInNewest: true, timeStart: '13:00', timeEnd: '14:00' });
  ok(F.offer && F.prefill.r === 'Studio 7', '"book … instead" after an offer -> a new offer');
  F = await offer('ok', offerMsg, '');
  ok(!F.offer && F.why === 'nothing new after an offer', '"ok" after an offer -> nothing new (the late menu)');

  // Menu Check: only an offer waits for an answer
  const menuFor = async (text, last) => (await j1('Menu Check', [], { 'Slack Trigger': [{ json: { text, channel: 'D1', ts: '200' } }], 'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }],
    'Gate Context': [{ json: { datesInMessage: '', gate: {} } }], 'Get Recent Messages': [{ json: { ts: '200', text } }, { json: last }] })).menu;
  ok(await menuFor('thanks', answer) === true, '"thanks" after an answer -> the menu');
  ok(await menuFor('thanks', offerMsg) === false, '"thanks" after an offer -> not here (the late menu answers it)');

  // then Mine Check takes "what do I have this week?"
  const mc = (await j1('Mine Check', [{ json: {} }], { 'Slack Trigger': [{ json: { text: 'what do I have this week?', channel: 'D1', user: 'U1' } }],
    'Gate Context': [{ json: { datesInMessage: '', todayIso: '2027-10-15', gate: {} } }] })).mineCheck;
  ok(mc.go && mc.week, '"what do I have this week?" -> My bookings in code');

  // Change Offer: everyday words are not a title (16:58 "cancel a booking i have next friday" -> searched for "have")
  const words = async (text, dates) => (await j1('Change Offer', [{ json: { formOffer: { why: 'a cancel or move' } } }], { 'Slack Trigger': [{ json: { text, channel: 'D1', user: 'U1', ts: '200' } }],
    'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-15', gate: {} } }], 'Booked For': [{ json: {} }], 'Get Recent Messages': [] })).changeOffer;
  let co = await words('cancel a booking i have next friday', '2027-10-22');
  ok(co.go && co.kind === 'cancel' && co.words.length === 0 && co.fDates.join() === '2027-10-22', '16:58 "cancel a booking i have next friday" -> every booking that day, no title word - ' + JSON.stringify(co.words));
  for (const t of ['cancel the one i booked for friday', 'cancel what i have scheduled on friday', 'pa-cancel naman yung booking ko sa friday'])
    ok((await words(t, '2027-10-22')).words.length === 0, 'no title word - ' + t + ' ' + JSON.stringify((await words(t, '2027-10-22')).words));
  co = await words('cancel ORANGE friday', '2027-10-22');
  ok(co.words.join() === 'orange', 'a real title word still counts');
  co = await words('move DINOS to 4pm', '');
  ok(co.kind === 'change' && co.words.join() === 'dinos', 'a change keeps its title word');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
