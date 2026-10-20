#!/usr/bin/env node
// Round 6 offline (Slack Interactions v23 + Book Session v111): the session-length note under the Booked card is a small
// line (bkn_<id>), not part of the card, and in hours; a change or cancel that goes through removes it.
// Usage: node scripts/sim-round-6.js [slack-interactions v23] [book-session v111]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v23.json', 'utf8'));
const bs = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/book-session-v111.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(name, input, outs) {
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(si, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

(async () => {
  // ---- Book Session: the note in hours (the block that builds it, run on its own)
  const cc = jsOf(bs, 'Check Conflicts');
  const a = cc.indexOf('const hasMin = Number.isFinite(minD) && minD > 0;'), b = cc.indexOf('// --- what actually goes on the calendar entry');
  const noteFor = (minD, maxD, mins, type) => new Function('minD', 'maxD', 'mins', 'allDay', 'ST', 'let durationNote = "";' + cc.slice(a, b) + '; return durationNote;')(minD, maxD, mins, false, { Type: type });
  const V114 = /a usual ' \+ kind/.test(cc);   // round 12: "That's a bit longer than a usual X session (1–3 hours)."
  const N = (w, type, range) => V114 ? 'That’s a bit ' + w + ' than a usual ' + type + ' session (' + range + ').' : 'That is a bit ' + w + ' than ' + type + ' sessions usually run (' + range + ' is typical).';
  ok(noteFor(240, 600, 120, 'Localization Dubbing') === N('shorter', 'Localization Dubbing', '4–10 hours'),
     'hours: "(4–10 hours is typical)" - Slack 15 Oct said "(240-600 minutes is typical)" - ' + noteFor(240, 600, 120, 'Localization Dubbing'));
  ok(noteFor(60, 180, 300, 'VO Recording') === N('longer', 'VO Recording', '1–3 hours'), 'VO Recording 1–3 hours');
  ok(noteFor(90, 150, 30, 'X') === N('shorter', 'X', '1 hour 30 minutes – 2 hours 30 minutes'), 'not whole hours - ' + noteFor(90, 150, 30, 'X'));
  ok(noteFor(0, 180, 300, 'X') === N('longer', 'X', 'up to 3 hours') && noteFor(45, 0, 30, 'X') === N('shorter', 'X', 'at least 45 minutes'), 'up to / at least');
  ok(noteFor(60, 180, 120, 'X') === '', 'inside the range -> no note');

  // ---- After Book: the note as a small line, on the form and in the DM
  const note = 'That is a bit shorter than Localization Dubbing sessions usually run (4–10 hours is typical).';
  const ab = await j1('After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: 'LOCTEST / HL', duration_note: note } }], {
    'Read Step 2': [{ json: { s: { date: '2027-10-16', t0: '09:00', t1: '11:00', when: 'Saturday, Oct 16 · 9:00 AM–11:00 AM' }, room: 'Studio 2', rooms: 'Studio 2, Studio B', viewId: 'V1', channel: 'D1' } }],
    'After Prepare': [{ json: { F: { Room: 'Studio 2, Studio B', Date: 'Saturday, October 16, 2027', Time: '9:00 AM – 11:00 AM' }, book: { start_iso: '2027-10-16T09:00:00+08:00', end_iso: '2027-10-16T11:00:00+08:00' } } }] });
  const ids = ab.blocks.map(x => x.block_id || x.type);
  ok(ids.join() === 'bk_ev1,bkn_ev1,bka_ev1' && ab.blocks[1].type === 'context' && ab.blocks[1].elements[0].text === note, 'DM: card, then the note as a small line, then Change / Cancel - ' + ids.join());
  ok(ab.blocks[0].text.text.indexOf('That is a bit') === -1 && ab.blocks[0].text.text.endsWith('*Room:* Studio 2 + Studio B'), 'the card itself ends at Room');
  ok(ab.view.blocks.length === 2 && ab.view.blocks[1].type === 'context' && ab.view.blocks[1].elements[0].text === note, 'the form\'s result: the same small line');
  const ab2 = await j1('After Book', [{ json: { status: 'CREATED', event_id: 'ev2', title: 'X / HL' } }], {
    'Read Step 2': [{ json: { s: { date: '2027-10-16', t0: '09:00', t1: '11:00', when: 'x · y' }, room: 'Studio 7', viewId: 'V1', channel: 'D1' } }], 'After Prepare': [{ json: { F: { Room: 'Studio 7' }, book: {} } }] });
  ok(ab2.blocks.map(x => x.block_id).join() === 'bk_ev2,bka_ev2' && ab2.view.blocks.length === 1, 'no note -> nothing added');

  // ---- Cancel / Change that go through remove the old note
  const msgBlocks = ab.blocks;
  const bval = JSON.stringify({ id: 'ev1', d: '2027-10-16', s: '09:00', e: '11:00', r: 'Studio 2, Studio B', t: 'LOCTEST / HL' });
  const ac = await j1('After Cancel', [{ json: { status: 'CANCELLED' } }], { 'Read Request': [{ json: { payload: { actions: [{ value: bval }], message: { blocks: msgBlocks, ts: '1' }, container: { channel_id: 'D1', message_ts: '1' } } } }] });
  ok(!JSON.stringify(ac.blocks || ac).includes('bkn_ev1') && /Cancelled/.test(JSON.stringify(ac)), 'Cancelled -> the note goes');
  const acf = await j1('After Cancel', [{ json: { status: 'REJECTED', reason: 'LOOKUP_FAILED' } }], { 'Read Request': [{ json: { payload: { actions: [{ value: bval }], message: { blocks: msgBlocks, ts: '1' }, container: { channel_id: 'D1', message_ts: '1' } } } }] });
  ok(JSON.stringify(acf.blocks || acf).includes('bkn_ev1'), 'a failed cancel keeps it');
  const fm = await run('Fix Message', [{ json: { messages: [{ ts: '1', blocks: msgBlocks, text: 'x' }] } }], {
    'After Move': [{ json: { ts: '1', ch: 'D1', oldId: 'ev1', nb: { id: 'ev9', d: '2027-10-16', s: '10:00', e: '12:00', r: 'Studio 2, Studio B', t: 'LOCTEST / HL' }, card: '✅ *Changed.*' } }] });
  const fb = fm[0].json.blocks.map(x => x.block_id);
  ok(fb.indexOf('bkn_ev1') === -1 && fb.indexOf('bk_ev9') !== -1 && fb.indexOf('bka_ev9') === fb.indexOf('bk_ev9') + 1, 'Changed -> the old note goes, the buttons follow the card - ' + fb.join());

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
