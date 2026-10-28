#!/usr/bin/env node
// main v286 (Howard, 28 Oct: "what rooms have symphony?" got only the button pointer): Facts Check answers questions about
// what the rooms have from the cached Rooms & Studios fields; Room Table hands every room's details to the prompt; Build Reply
// drops only a booking question, not the answer before it. Rooms below are copied from Airtable (28 Oct).
// Usage: node scripts/sim-room-facts.js [main v286]
const fs = require('fs');
const M = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v286.json', 'utf8'));
if (!M.nodes.some(n => n.name === 'Facts Check')) { console.log('0 ok, 0 failed (an older build: v286 not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const node = n => M.nodes.find(x => x.name === n);
const run = (name, input, outs) => {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', node(name).parameters.jsCode).call({}, $, $input); };
const R = (name, f) => ({ json: { id: 'r' + name, fields: Object.assign({ 'Room Name': name }, f) } });
const rooms = [
  R('Studio F', { Equipment: 'Can record bands/strings. Preferred for celebrity/VIP recordings. Pair of Genelec speakers.',
    'Equipment (additional)': '**AUDIO INTERFACES **\n- 2 Focusrite RED 8Pre\n- Symphony\n- Hear System\n**PREAMPS**\n- Portico 5012\n- Portico II\n- Manley SLAM!\n- NPNG DMP-2NW\n- Seventh Circle Audio (A12, N72, C84, J99)\n\n\n',
    'Prioritized For': ['Celebrity-VIP'], 'Room Type': ['Recording Control Room', 'Editing', 'Stereo Mixing'], Capacity: 12, 'Recording Format': ['Stereo'],
    'Records Vocals In-Room': true, Workstation: ['Mac Studio', 'Laptop Ready'], 'Size Category': 'Large' }),
  R('Studio 8', { Equipment: 'Symphony (laptop connection) only, no Mac Studio. Stereo only. Pair of Amie Speakers, w Sub', 'Prioritized For': ['Audio Post'],
    'Room Type': ['Recording Control Room', 'Editing', 'Stereo Mixing'], Capacity: 7, 'Recording Format': ['Stereo with Sub'], 'Records Vocals In-Room': true,
    Workstation: ['Laptop Ready'], 'Size Category': 'Medium' }),
  R('Studio C', { Equipment: 'Atmos room. Preferred for Atmos mixing; secondary choice for celebrity/VIP recordings.',
    'Equipment (additional)': '**AUDIO INTERFACES **\n- AVID Pro Tools MTRX Studio\n- Symphony\n- Hear system\n**PREAMPS**\n- Focusrite ff ISA 428\n- Symetrix 528E Voice Processor\n- 6 Brent Averill preamps\n- Manly SLAM! Compressor\n\n\n',
    'Room Type': ['Recording Control Room', 'Editing', '5.1 Mixing', 'Atmos Suite'], Capacity: 12, 'Recording Format': ['Stereo', '5.1', 'Atmos'], Workstation: ['Mac Studio'], 'Size Category': 'Large' }),
  R('Studio 7', { Equipment: 'Mac Studio + Symphony (laptop connection). Stereo only. Pair of Amie Speakers', 'Paired with': 'Studio A, B, or D, Can change using Dante',
    'Room Type': ['Recording Control Room', 'Editing', 'Stereo Mixing'], Capacity: 7, 'Recording Format': ['Stereo'], 'Records Vocals In-Room': true,
    Workstation: ['Mac Studio', 'Laptop Ready'], 'Size Category': 'Medium' }),
  R('Studio 3', { Equipment: 'Amie Speakers Surround Set', 'Paired with': 'Studio A, B, or D, Can change using Dante', 'Room Type': ['Recording Control Room', 'Editing', 'Stereo Mixing', '5.1 Mixing'],
    Capacity: 7, 'Recording Format': ['5.1', 'Stereo'], Workstation: ['Mac Studio'], 'Size Category': 'Medium' }),
  R('Studio A', { Equipment: 'Vocal booth room. No computer. Effort Stand.\n', 'Vocal Booth': true, 'Room Type': ['Recording Booth'], Capacity: 5, 'Recording Format': ['None'], Workstation: ['None'], 'Size Category': 'Small ' }),
  R('M4', { Equipment: 'Pair of Genelec speakers\nFocusrite Scarlett 4i4 interface\nDisplay monitor', 'Room Type': ['M Booth'], Capacity: 1, 'Recording Format': ['Stereo'], Workstation: ['Laptop Ready'], 'Size Category': 'Small ' }),
  R('Likha', { Equipment: 'Display TV\nPair of Genelec Speakers', 'Room Type': ['Conference Room'], Capacity: 10, 'Recording Format': ['None'], Workstation: ['None'], 'Size Category': 'Large' }),
  R('Studio M', { 'Equipment (additional)': '\n', 'Paired with': 'N/A\n', 'Room Type': ['Van'], Capacity: 5, 'Recording Format': ['Stereo'], Workstation: ['Mac Mini'], 'Size Category': 'Medium' }),
];
const types = ['VO Recording', 'Music Recording', 'Atmos Mixing', 'Post Mixing', 'Celebrity Recording'].map(t => ({ json: { fields: { Type: t } } }));
const facts = (text, dates) => run('Facts Check', [{ json: { keep: 1 } }], {
  'Slack Trigger': [{ json: { text, channel: 'D1', ts: '1' } }], 'Gate Context': [{ json: { datesInMessage: dates || '' } }],
  'All Rooms': rooms, 'All Session Types': types })[0].json;

console.log('Facts Check - which rooms have <thing>');
let f = facts('what rooms have symphony?');
ok(f.factsCheck.go && f.keep === 1, 'answered in code, the item passed on', f.factsCheck);
ok(/^\*Rooms with Symphony:\*/.test(f.factsCheck.text) && JSON.stringify(f.factsCheck.rooms) === JSON.stringify(['Studio 7', 'Studio 8', 'Studio C', 'Studio F']),
  'Howard\'s question: Studio 7, 8, C and F, in order', f.factsCheck);
ok(/• \*Studio C\* – Audio interfaces: Symphony/.test(f.factsCheck.text) && /• \*Studio 8\* – Symphony \(laptop connection\) only, no Mac Studio/.test(f.factsCheck.text),
  'each with the line that says so (the heading for a listed item)', f.factsCheck.text);
ok(f.factsCheck.blocks[1].elements.map(e => e.action_id).join() === 'open_book,my_bookings' && f.factsCheck.blocks[1].elements[0].value === 'menu', 'Book a room / My bookings under it');
f = facts('which studios have a mac studio');
ok(f.factsCheck.go && f.factsCheck.rooms.indexOf('Studio 8') === -1 && f.factsCheck.rooms.indexOf('Studio 7') !== -1 && f.factsCheck.rooms.indexOf('Studio 3') !== -1,
  '"no Mac Studio" (Studio 8) is not a match', f.factsCheck.rooms);
f = facts('rooms with genelec speakers?');
ok(f.factsCheck.go && ['Studio F', 'M4', 'Likha'].every(r => f.factsCheck.rooms.includes(r)), 'plural / no question word: "rooms with genelec speakers"', f.factsCheck.rooms);
f = facts('which rooms have a manley slam');
ok(f.factsCheck.go && JSON.stringify(f.factsCheck.rooms) === '["Studio F"]', 'Manley SLAM! (Studio C\'s is spelled "Manly")', f.factsCheck.rooms);
f = facts('which rooms are laptop ready?');
ok(f.factsCheck.go && f.factsCheck.rooms.includes('Studio 8') && f.factsCheck.rooms.includes('M4') && !f.factsCheck.rooms.includes('Studio C'), 'which rooms are laptop ready (Workstation)', f.factsCheck.rooms);
f = facts('where is the hear system?');
ok(f.factsCheck.go && f.factsCheck.rooms.includes('Studio F') && f.factsCheck.rooms.includes('Studio C'), 'where is the Hear system', f.factsCheck.rooms);
f = facts('which rooms have a theremin?');
ok(!f.factsCheck.go, 'nothing lists it -> the AI says so from the details (no code guess on a stray term)', f.factsCheck);
f = facts('what rooms have symphony setup?');
ok(f.factsCheck.go && f.factsCheck.rooms.length === 4, '"symphony setup" -> Symphony', f.factsCheck);

console.log('Facts Check - one room');
f = facts('tell me about studio f');
ok(f.factsCheck.go && /^\*Studio F\*\n/.test(f.factsCheck.text) && /\*Audio interfaces:\* 2 Focusrite RED 8Pre, Symphony, Hear System/.test(f.factsCheck.text)
  && /\*Preamps:\* Portico 5012/.test(f.factsCheck.text) && /\*Size:\* Large · up to 12 people/.test(f.factsCheck.text) && /\*Workstation:\* Mac Studio, Laptop Ready/.test(f.factsCheck.text),
  'tell me about Studio F -> its details', f.factsCheck.text);
f = facts('does studio 8 have a mac studio?');
ok(f.factsCheck.go && /^Airtable doesn’t list \*mac studio\* for \*Studio 8\*\./.test(f.factsCheck.text) && /\*Studio 8\*\n/.test(f.factsCheck.text), 'Studio 8 + Mac Studio -> not listed, then its details', f.factsCheck.text);
f = facts('does studio 7 have a mac studio?');
ok(f.factsCheck.go && /^\*Studio 7\* has mac studio:\n• Workstation: Mac Studio, Laptop Ready\n• Mac Studio \+ Symphony/.test(f.factsCheck.text), 'Studio 7 + Mac Studio -> yes, the lines', f.factsCheck.text);
f = facts('how many people fit in likha?');
ok(f.factsCheck.go && /\*Size:\* Large · up to 10 people/.test(f.factsCheck.text), 'how many fit in Likha -> its size', f.factsCheck.text);
f = facts('does studio 3 have 5.1?');
ok(f.factsCheck.go && /^\*Studio 3\* has 5\.1:\n• Formats: 5\.1, Stereo/.test(f.factsCheck.text), 'a format on one room: from Formats only', f.factsCheck.text);
f = facts('does studio 7 have 5.1?');
ok(f.factsCheck.go && /^Airtable doesn’t list \*5\.1\* for \*Studio 7\*/.test(f.factsCheck.text), 'Studio 7 is stereo: not listed');
f = facts('what does the m4 booth have?');
ok(f.factsCheck.go && /^\*M4\*/.test(f.factsCheck.text) && /Focusrite Scarlett 4i4 interface/.test(f.factsCheck.text), 'an M booth by name', f.factsCheck.text);
f = facts('what equipment does studio m have?');
ok(f.factsCheck.go && /^\*Studio M\*/.test(f.factsCheck.text) && !/Paired with/.test(f.factsCheck.text) && /Mac Mini/.test(f.factsCheck.text), 'Studio M: "N/A" pairing left out', f.factsCheck.text);

console.log('Facts Check - left to the AI');
for (const [q, d, why] of [['is studio 7 free tomorrow?', '2027-10-29', 'availability'], ['which rooms have atmos?', '', 'a format across rooms (the tool)'],
  ['which rooms are used for vo recording?', '', 'session type ranking'], ['book studio f tomorrow 2-4pm', '2027-10-29', 'a booking'], ['what do i have this week', '', 'my bookings'],
  ['which rooms have vocal booths?', '', 'vocal booths (the tool)'], ['who is the engineer for loc?', '', 'people'], ['studio 7 and studio 8 - which has more speakers?', '', 'two rooms'],
  ['thanks', '', 'not a question'], ['what time does studio c open?', '', 'a time'],
  ['what about studio f?', '', 'a follow-up about a room (could be its schedule)'], ['whats in studio 4?', '', '"whats in" can mean its schedule'],
  ['does studio 7 have a session at 3?', '', 'a booking question with no am/pm'], ['which rooms have space for 10 people?', '', 'capacity across rooms (the AI, with the details)'],
  ['which studios have engineers?', '', 'people'], ['which rooms are taken?', '', 'taken = a booking question'], ['does studio 8 have anyone in it?', '', 'someone in it']]) {
  f = facts(q, d);
  ok(!f.factsCheck.go, why + ': "' + q + '" -> the AI', f.factsCheck);
}
const bad = run('Facts Check', [{ json: {} }], { 'Slack Trigger': [{ json: { text: 'what rooms have symphony?' } }], 'Gate Context': [{ json: {} }] })[0].json;
ok(bad.factsCheck.go === false, 'no rooms read -> never throws, the AI answers', bad.factsCheck);

console.log('Facts Check - safe output');
const evil = rooms.concat([R('Studio Z', { Equipment: 'Symphony <!channel> <https://x.example|click> & <@U123>' })]);
const fz = run('Facts Check', [{ json: {} }], { 'Slack Trigger': [{ json: { text: 'what rooms have symphony?', channel: 'D1' } }], 'Gate Context': [{ json: {} }], 'All Rooms': evil, 'All Session Types': types })[0].json.factsCheck;
ok(fz.go && !/<!channel>|<https|<@U/.test(fz.text) && /&lt;!channel&gt;/.test(fz.text) && /&amp;/.test(fz.text), 'Airtable text is escaped: no @channel, link or mention can be posted', fz.text);
for (const q of ['does studio 8 have <!channel>?', 'does studio 8 have @here?', 'which rooms have <@U08V3CKDGJF>?'])
  { const x = facts(q).factsCheck; ok(!/<|@/.test(x.text), 'a typed mention is never echoed: ' + q, x.text); }
ok(facts('what rooms have symphony?').factsCheck.channel === 'D1', 'answers only in the DM it came from');
let t0 = Date.now(); const long = facts('which rooms have ' + 'a'.repeat(39000) + '?'); ok(Date.now() - t0 < 200 && !long.factsCheck.go, 'a 39,000-character message: read capped, fast, no answer', Date.now() - t0);
t0 = Date.now(); facts('which rooms have ' + 'symphony '.repeat(4000)); ok(Date.now() - t0 < 200, 'a repeated term: no slow regex', Date.now() - t0);

console.log('Room Table - the details in the prompt');
const rt = node('Room Table').parameters.jsCode;
const i = rt.indexOf('// v286 (28 Oct): what each room has'), j = rt.indexOf('const preemptionRanks = {};');
const piece = new Function('$', rt.slice(i, j) + '\nreturn roomDetails;');
const detFor = q => piece(n => ({ all: () => n === 'All Rooms' ? rooms : [], first: () => ({ json: n === 'Slack Trigger' ? { text: q } : {} }) }));
const det = detFor('which rooms have symphony?');
for (const q of ['thanks', 'who is the engineer for loc?', 'is studio 7 free tomorrow?', 'book studio 8 friday 2-4pm', 'what do i have in studio c this week'])
  ok(detFor(q) === '(not needed for this message)', 'no details in the prompt: "' + q + '"');
for (const q of ['is there a good mic in salin', 'which rooms have a theremin?', 'does likha have a tv?', 'how many people fit in katha'])
  ok(detFor(q) !== '(not needed for this message)', 'the details in the prompt: "' + q + '"');
ok(/^- Likha - /.test(det) && /\n- Studio F - Room type: Recording Control Room, Editing, Stereo Mixing; Size: Large · up to 12 people;[^\n]*Audio interfaces: 2 Focusrite RED 8Pre, Symphony, Hear System; Preamps: Portico 5012/.test(det),
  'one line per room, every field, in order', det.split('\n').slice(0, 3));
ok(det.split('\n').length === rooms.length && !/\*\*/.test(det), 'every room, no Airtable bold marks');
ok(/roomDetails: roomDetails \}/.test(rt), 'Room Table returns roomDetails');
const sm = node('Jessie AI Agent').parameters.options.systemMessage;
ok(/\*What each room has\*[\s\S]*\{\{ \$\('Room Table'\)\.first\(\)\.json\.roomDetails \}\}/.test(sm), 'the prompt carries the details under *What each room has*');

console.log('Build Reply - an answer kept');
const br = t => run('Build Reply', [{ json: { output: t } }], { 'Guard Probe': [{ json: {} }], 'Gate Context': [{ json: {} }], 'Booked For': [{ json: {} }], 'Slack Trigger': [{ json: { text: 'x' } }] })[0].json.output;
ok(br('Studio 7, Studio 8, Studio C and Studio F have Symphony. Which room would you like to book?') === 'Studio 7, Studio 8, Studio C and Studio F have Symphony.', 'the closing booking question dropped, the answer kept');
ok(br('Which session type is it?') === 'Use *Book a room* or *My bookings* below.', 'only a booking question -> the pointer, as before');
ok(br('*Studio F*\nGenelec speakers.\nWhich studio do you want?') === '*Studio F*\nGenelec speakers.', 'lines kept, the question line dropped');
ok(br('Studio F is a large room.') === 'Studio F is a large room.', 'no booking question -> unchanged');
for (const t of ['I’ve noted the project as ORANGE. Who’s the client?', 'Got it, Studio 7 on Friday. Which session type is it?', '*Project:* ORANGE\n*Client:* Jem Lim\nConfirm to book. (yes/no)', 'What would you like to do? What’s the project?', 'Who’s the arranger? (or "none")', 'Cancel it? Reply yes or no.', 'Which room?'])
  ok(br(t) === 'Use *Book a room* or *My bookings* below.', 'nothing but questions -> the pointer: ' + t, br(t));

console.log('Wiring');
const C = M.connections, to = (a, k) => ((C[a] || {}).main || [])[k || 0].map(x => x.node);
ok(to('Mine?', 1).join() === 'Facts Check' && to('Facts Check').join() === 'Facts?' && to('Facts?', 0).join() === 'Send Facts' && to('Facts?', 1).join() === 'Early Room Plan',
  'Mine? (no) -> Facts Check -> Facts? -> Send Facts / Early Room Plan');
ok(JSON.stringify(to('Send Facts').sort()) === JSON.stringify(to('Send Mine').sort()), 'Send Facts -> the same as Send Mine (Turn Log Row, Clear Ack)', to('Send Facts'));
ok(/fa \? 'room details'/.test(node('Turn Log Row').parameters.jsCode), 'Turn Log: path "room details"');
ok(/factsCheck\.blocks/.test(node('Send Facts').parameters.jsonBody) && node('Send Facts').onError === 'continueRegularOutput', 'Send Facts posts the blocks, continues on error');
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
