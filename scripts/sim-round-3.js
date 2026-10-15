#!/usr/bin/env node
// Round 3 offline (main v272): Room Availability's times only from this message (1); Book a room under an answer filled in
// from this message (2); "what do I have …" answered in code as My bookings (3); the question rules back in the prompt (4).
// Usage: node scripts/sim-round-3.js [main v272]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v272.json', 'utf8'));
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
  // ---- 1: Room Availability's window - the AI's times stand unless times are typed in this message
  const ra = main.nodes.find(n => n.name === 'Room Availability').parameters.workflowInputs.value;
  const evalWin = (expr, bf, g, aiStart, aiEnd) => {
    let e = expr.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
    const $fromAI = k => (k === 'window_start' ? aiStart : aiEnd);
    const $ = n => ({ first: () => ({ json: n === 'Booked For' ? bf : g }) });
    return new Function('$', '$fromAI', 'return (' + e + ');')($, $fromAI);
  };
  const spill = { timeStart: '14:00', timeEnd: '16:00', timeInNewest: false, timesMentioned: ['14:00', '16:00'] };
  const g = { datesInMessage: '2027-10-15' };
  ok(evalWin(ra.start_iso, spill, g, '2027-10-15T12:00:00+08:00', '2027-10-15T18:00:00+08:00') === '2027-10-15T12:00:00+08:00'
     && evalWin(ra.end_iso, spill, g, '2027-10-15T12:00:00+08:00', '2027-10-15T18:00:00+08:00') === '2027-10-15T18:00:00+08:00',
     '1: "what\'s free friday afternoon?" after an earlier "2-4pm" -> the AI\'s 12-6 PM stands (live 16:44: 2-4 PM)');
  const typed = { timeStart: '15:00', timeEnd: '17:00', timeInNewest: true, timesMentioned: [] };
  ok(evalWin(ra.start_iso, typed, { datesInMessage: '2027-10-16' }, '2027-10-16T15:30:00+08:00', '2027-10-16T17:00:00+08:00') === '2027-10-16T15:00:00+08:00', '1: times typed in this message still correct the AI\'s');
  ok(!/cancel or move/.test(main.nodes.find(n => n.name === 'List Events').parameters.toolDescription), '1: List Events no longer mentions cancel / move');

  // ---- 2: Book a room under an answer, filled in from this message
  const reply = async (text, g, bf) => (await j1('Build Reply', [{ json: { output: 'Studio 8 is booked 4-5 PM - free 3-4 PM.' } }],
    { 'Guard Probe': [{ json: {} }], 'Gate Context': [{ json: g }], 'Booked For': [{ json: bf || {} }], 'Slack Trigger': [{ json: { text } }] })).reply;
  let r = await reply('is studio 8 free tomorrow 3-5?', { datesInMessage: '2027-10-16' }, { timeInNewest: true, timeStart: '15:00', timeEnd: '17:00' });
  const btn = r.blocks[r.blocks.length - 1].elements[0];
  ok(btn.action_id === 'open_book' && btn.value === JSON.stringify({ d: '2027-10-16', s: '15:00', e: '17:00', r: 'Studio 8' }), '2: "is studio 8 free tomorrow 3-5?" -> Book a room carries Oct 16, 3-5 PM, Studio 8 - ' + btn.value);
  r = await reply('what\'s free friday afternoon?', { datesInMessage: '2027-10-15' }, spill);
  ok(r.blocks[r.blocks.length - 1].elements[0].value === JSON.stringify({ d: '2027-10-15' }), '2: an earlier message\'s times are not carried - only Friday');
  r = await reply('which rooms can do 5.1?', { datesInMessage: '' }, {});
  ok(r.blocks[r.blocks.length - 1].elements[0].value === 'menu', '2: nothing named -> an empty form');
  r = (await j1('Build Reply', [{ json: { output: 'x' } }], {})).reply;
  ok(r.blocks[r.blocks.length - 1].elements[0].value === 'menu', '2: an old-card reply (nothing read) -> an empty form');

  // ---- 3: "what do I have …" in code
  const check = async (text, dates) => (await j1('Mine Check', [{ json: { keep: 1 } }], { 'Slack Trigger': [{ json: { text, channel: 'D1', user: 'U1' } }],
    'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-15', gate: {} } }] })).mineCheck;
  let mc = await check('what do I have this week?');
  ok(mc.go && mc.start === '2027-10-15' && mc.end === '2027-10-22' && mc.week, '3: "what do I have this week?" -> the next 7 days (live 16:47: written by the AI)');
  mc = await check('what do i have tomorrow?', '2027-10-16');
  ok(mc.go && mc.start === '2027-10-16' && mc.end === '2027-10-17' && !mc.week, '3: tomorrow -> that day');
  mc = await check('what do I have in November?');
  ok(mc.go && mc.start === '2027-11-01' && mc.end === '2027-12-01' && !mc.week, '3: in November -> the month');
  mc = await check('what do I have next week');
  ok(mc.start === '2027-10-22' && mc.end === '2027-10-29' && mc.week, '3: next week');
  ok((await check('my bookings')).go && (await check("what's on my schedule?")).go && (await check('am I engineering anything friday?', '2027-10-22')).go, '3: "my bookings", "what\'s on my schedule", "am I engineering …"');
  for (const t of ['cancel my booking tomorrow', 'is studio 7 free friday?', 'what can you do', 'book studio 7 tomorrow'])
    ok(!(await check(t)).go, '3: not this - ' + JSON.stringify(t));
  const ev = (id, title, s, e, desc) => ({ id, summary: title, start: { dateTime: s }, end: { dateTime: e }, description: desc,
    attendees: [{ resource: true, email: 'x@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio F (6)' }] });
  const items = [ev('a', 'MUSICTEST / Jem Lim / HL x MV', '2027-10-15T13:00:00+08:00', '2027-10-15T15:00:00+08:00', 'Engineer: Howard Luistro | Arranger: Mike Villegas | ref: U9 | team: U1 U5'),
    ev('b', 'MAKINA / Sasa Abella / AEG', '2027-10-15T20:00:00+08:00', '2027-10-15T22:00:00+08:00', 'Engineer: Alec Elijah Gan | ref: U1 | team: U3'),
    ev('c', 'THEIRS / X / DR', '2027-10-16T10:00:00+08:00', '2027-10-16T11:00:00+08:00', 'ref: U9')];
  mc = await check('what do I have this week?');
  const mr = await j1('Mine Reply', [{ json: { items } }], { 'Mine Check': [{ json: { mineCheck: mc } }] });
  const rows = mr.blocks.filter(b => /^bk_/.test(b.block_id || ''));
  ok(mr.blocks[0].text.text === '*Your bookings* · Fri, Oct 15 – Thu, Oct 21' && rows.length === 2 && rows[0].text.text === '*MUSICTEST / Jem Lim / HL x MV*\nFri, Oct 15 · 1:00 PM – 3:00 PM · Studio F',
     '3: title, date, time, room - no engineer / arranger, no "Filtering for" - ' + JSON.stringify(rows.map(r => r.text.text)));
  ok(mr.blocks.some(b => b.block_id === 'bka_a') && mr.blocks.find(b => b.block_id === 'my_nav').elements.map(e => e.action_id).join() === 'my_page_prev,my_page_next'
     && mr.blocks.find(b => b.block_id === 'menu_nav').elements[0].action_id === 'open_book', '3: each with Change / Cancel; Previous / Next 7 days; Book a room');
  ok(mr.blocks.every(b => !b.elements || new Set(b.elements.map(e => e.action_id).filter(Boolean)).size === b.elements.filter(e => e.action_id).length), '3: no block repeats an action id');
  const mr2 = await j1('Mine Reply', [{ json: { items: [] } }], { 'Mine Check': [{ json: { mineCheck: await check('what do i have tomorrow?', '2027-10-16') } }] });
  ok(mr2.blocks[0].text.text === '*Your bookings* · Sat, Oct 16' && mr2.blocks[1].text.text === 'Nothing booked for you then.' && !mr2.blocks.some(b => b.block_id === 'my_nav'), '3: one day, nothing -> said, no paging');
  ok(nx('Late Menu?') === 'Send Late Menu | Mine Check' && nx('Mine?') === 'List My Window | Early Room Plan' && nx('Mine Reply') === 'Send Mine' && nx('Send Mine') === 'Turn Log Row+Clear Ack', '3 wiring');
  ok((await j1('Turn Log Row', [{ json: {} }], { 'Slack Trigger': [{ json: { text: 'x', ts: '1' } }], 'Send Mine': [{ json: { ok: true } }] })).Path === 'my bookings', '3: Turn Log "my bookings"');

  // ---- 4: the prompt
  const sm = main.nodes.find(n => n.name === 'Jessie AI Agent').parameters.options.systemMessage;
  ok(/\*Each question stands alone\.\*/.test(sm) && /Never invent a reason or a detail a tool did not give/.test(sm) && /Never add who booked it, the engineer, the arranger, the client or notes/.test(sm)
     && /Small chunks, line breaks between ideas/.test(sm), '4: the question rules are back');
  ok(!/Filtering for/.test(sm), '4: the prompt never shows the habit it stops (gotcha 6)');
  ok(!/Prepare Booking|Book Session|Prepare Cancel|Move Booking|Prepare Series|Book Series|Cancel Booking/.test(sm) && /plus\(\{ years: 1 \}\)/.test(sm), '4: still no booking tools; the year shift kept');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
