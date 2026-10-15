#!/usr/bin/env node
// main v271 offline - every message leads to the buttons: every reply carries Book a room / My bookings (Build Reply), an
// agent reply asking for booking details is replaced; "what can you do" -> the menu with what Jessie does; booking details
// without "book" -> the booking reply; the booking tools are off the agent and its prompt answers questions only.
// Usage: node scripts/sim-every-message.js [main v271]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v271.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = n => main.nodes.find(x => x.name === n).parameters.jsCode;
async function run(name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const C = main.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');

(async () => {
  // ---- 1: every reply carries the buttons
  let r = await j1('Build Reply', [{ json: { output: 'Studio 7 is free 2:00 – 6:00 PM.' } }], { 'Guard Probe': [{ json: {} }] });
  const acts = r.reply.blocks[r.reply.blocks.length - 1];
  ok(r.reply.blocks[0].text.text === 'Studio 7 is free 2:00 – 6:00 PM.' && acts.elements.map(e => e.action_id + ':' + e.value).join() === 'open_book:menu,my_bookings:menu' && acts.elements[0].style === 'primary',
     '1: an answer -> the text, then Book a room / My bookings');
  r = await j1('Build Reply', [{ json: { output: 'What would you like to do? What’s the project?' } }], { 'Guard Probe': [{ json: {} }] });
  ok(r.reply.blocks[0].text.text === 'Tap *Book a room* below - the form asks for everything it needs. To change or cancel, open *My bookings*.', '1: the agent asking for booking details (live 16:27) -> a pointer to the buttons');
  for (const t of ['Who’s the arranger? (or "none")', "Who's the client?", 'Which room?', 'Confirm to book. (yes/no)', 'Cancel it? Reply yes or no.'])
    ok((await j1('Build Reply', [{ json: { output: t } }], { 'Guard Probe': [{ json: {} }] })).output.indexOf('Book a room') !== -1, '1: replaced - ' + t);
  r = await j1('Build Reply', [{ json: { output: 'Booked "X" - Confirm to book. (yes/no)' } }], {});
  ok(r.output === 'Booked "X" - Confirm to book. (yes/no)' && r.reply.blocks.length === 2, '1: a reply from the old card paths (no agent) is sent as it is, with the buttons');
  r = await j1('Build Reply', [{ json: { output: 'x'.repeat(6000) } }], { 'Guard Probe': [{ json: {} }] });
  ok(r.reply.blocks.length === 4 && r.reply.blocks.slice(0, 3).every(b => b.text.text.length <= 2900), '1: a long answer -> split into sections, buttons last');
  const sr = main.nodes.find(n => n.name === 'Send Reply');
  ok(sr.type === 'n8n-nodes-base.httpRequest' && /chat\.postMessage/.test(sr.parameters.url) && /reply\.blocks/.test(sr.parameters.jsonBody) && sr.credentials.slackApi.id === 'EcX8szEJrOLYLUfl', '1: Send Reply posts the blocks');
  const into = Object.keys(C).filter(k => (C[k].main || []).some(o => o.some(c => c.node === 'Build Reply')));
  ok(into.sort().join() === ['Already Done Reply', 'Book Direct Reply', 'Cancel Direct Reply', 'Error filter', 'Move Direct Reply', 'Reference Lookup Failed', 'Series Busy Reply', 'Series Direct Reply'].sort().join()
     && nx('Build Reply') === 'Send Reply' && nx('Send Reply') === 'Turn Log Row+Clear Ack' && !Object.keys(C).some(k => k !== 'Build Reply' && (C[k].main || []).some(o => o.some(c => c.node === 'Send Reply'))),
     '1 wiring: every reply goes through Build Reply - ' + into.join(', '));
  const tl = await j1('Turn Log Row', [{ json: { ok: true, message: { text: 'Studio 7 is free.' } } }], { 'Slack Trigger': [{ json: { text: 'x', ts: '1' } }], 'Guard Probe': [{ json: {} }] });
  ok(tl.Reply === 'Studio 7 is free.', '1: Turn Log still reads the reply');

  // ---- 2: "what can you do"
  const menuFor = async (text, o) => j1('Menu Check', [], { 'Slack Trigger': [{ json: { text, channel: 'D1', ts: '9' } }], 'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }],
    'Gate Context': [{ json: Object.assign({ datesInMessage: '', gate: {} }, (o || {}).g || {}) }], 'Get Recent Messages': [] });
  for (const t of ['what can you do for me', 'What can you do?', 'how does this work', 'what are your features', 'who are you', 'help me'])
    ok((await menuFor(t)).menu === true && /^I book studios and rooms at Hit Productions/.test((await menuFor(t)).blocks[0].text.text), '2: ' + JSON.stringify(t) + ' -> what Jessie does, with the menu (live: "What’s the project?")');
  ok((await menuFor('what studios do we have?')).menu === false, '2: a real question still goes to the agent');

  // ---- 3: booking details without "book"
  const offer = async (text, dates, bf) => (await j1('Form Offer', [{ json: {} }], {
    'All Rooms': [{ json: { fields: { 'Room Name': 'Studio 7' } } }], 'All Session Types': ['VO Recording', 'Music Mixing'].map(t => ({ json: { fields: { Type: t } } })), 'All Bookers': [],
    'Slack Trigger': [{ json: { text, channel: 'D1', ts: '1' } }], 'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-15', gate: {} } }],
    'Booked For': [{ json: Object.assign({ requesterText: text }, bf || {}) }], 'Get Recent Messages': [] })).formOffer;
  let F = await offer('project orange', '', { project: 'orange' });
  ok(F.offer && F.prefill.pj === 'orange' && /Project: orange/.test(F.text), '3: "project orange" (live 16:27) -> the booking reply with the project');
  F = await offer('studio 7 tomorrow 2-4pm', '2027-10-16', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(F.offer && F.prefill.r === 'Studio 7' && F.prefill.d === '2027-10-16' && F.prefill.s === '14:00', '3: "studio 7 tomorrow 2-4pm" -> the booking reply');
  F = await offer('i need studio 7 every monday 2-4pm', '2027-10-18', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(F.offer && F.prefill.rep && F.prefill.rep.days.join() === 'MO', '3: "i need studio 7 every monday" -> the form with Repeats (PENDING 116)');
  for (const [t, d] of [['is studio 7 free tomorrow?', '2027-10-16'], ['what session types are there', ''], ['make it 3pm', ''], ['cancel orange', ''], ['thanks', ''], ['lhkjf;kj', '']])
    ok(!(await offer(t, d)).offer, '3: not a booking request - ' + JSON.stringify(t));

  // ---- 4: the agent answers questions only
  const tools = Object.keys(C).filter(k => C[k].ai_tool).sort();
  ok(tools.join() === ['Bookers', 'Clients', 'Find Booking', 'List Events', 'Localization Projects', 'Room Availability', 'Rooms and Studios', 'Session Types'].sort().join(), '4: the agent keeps only the question tools - ' + tools.join(', '));
  ok(!main.nodes.some(n => ['Prepare Booking', 'Book Session', 'Prepare Series', 'Book Series', 'Prepare Cancel', 'Cancel Booking', 'Move Booking'].indexOf(n.name) !== -1), '4: the booking tools are gone');
  const sm = main.nodes.find(n => n.name === 'Jessie AI Agent').parameters.options.systemMessage;
  ok(!/Prepare Booking|Book Session|Prepare Cancel|Move Booking|Prepare Series|Book Series|Cancel Booking/.test(sm) && /Never ask for booking details/.test(sm) && /Book a room/.test(sm), '4: the prompt names no booking tool and sends booking to the buttons');
  ok(/plus\(\{ years: 1 \}\)/.test(sm), '4: the QA year shift is still in the prompt (a launch switch)');
  ok(sm.length < 9000, '4: the prompt is short (' + sm.length + ' characters; was 33,450)');
  ok(/never judge a room busy from the busy list/i.test(sm) && /"My bookings" means involvement/.test(sm) && /number the options and accept a number back/.test(sm) && /Never pick the closest or the first/.test(sm),
     '4: the three question sections kept - Showing bookings, the busy-list rule, Who is who');
  ok(!/cancel or move/.test(main.nodes.find(n => n.name === 'Find Booking').parameters.description), '4: Find Booking no longer offers cancelling or moving');
  ok(['Book Direct', 'Cancel Direct', 'Move Direct', 'Series Direct'].every(n => main.nodes.some(x => x.name === n)), '4: an old chat card on screen can still be answered (the Direct paths stay)');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
