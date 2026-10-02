#!/usr/bin/env node
// Offline tests for Room Availability v13 + main v211 (decided 2 Oct): free-room answers laid out by category, one line
// each - "Free studios:\nStudios 1, 2, 3, 7, 8, F, and C.\nM2, M3, M5." - and day by day for a range.
//   node scripts/sim-room-layout.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const RA = WF(process.env.RA || 'room-availability-v13.json'), M = WF(process.env.MAIN || 'project-jessie-v211.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const ROOMS = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 7', 'Studio 8', 'Studio C', 'Studio F', 'Studio A', 'M2', 'M3', 'M5', 'Likha', 'Katha'];
const REF = JSON.stringify({ rooms: ROOMS.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: n === 'Studio A', common: /Likha|Katha/.test(n) })), types: [] });
Date.now = () => Date.parse('2026-10-02T02:00:00Z');
const ra = (req, evs = []) => new Function('$', '$input', code(RA, 'Compute Availability'))(n => wrap([{ json: { reference_data: REF, scope: 'all', ...req } }]), wrap([{ json: { items: evs } }]))[0].json;
const DAY = { start_iso: '2027-10-02T09:00:00+08:00', end_iso: '2027-10-02T18:00:00+08:00' };

console.log('One window');
let r = ra({ ...DAY, scope: 'studios' });
ok(r.reply_text === 'Free studios:\nStudios 1, 2, 3, 7, 8, C, and F.\nVocal booth A.\nM2, M3, M5.', 'studios scope -> studios / booth / M booths on their own lines', r.reply_text);
r = ra(DAY);
ok(/^Free rooms:\nStudios 1, 2, 3, 7, 8, C, and F\.\nVocal booth A\.\nM2, M3, M5\.\nKatha, Likha\.$/.test(r.reply_text || ''), 'all rooms -> + conference rooms on a line', r.reply_text);
r = ra({ ...DAY, scope: 'studios' }, [{ id: 'e', summary: 'X', start: { dateTime: '2027-10-02T10:00:00+08:00' }, end: { dateTime: '2027-10-02T11:00:00+08:00' }, attendees: [{ email: 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com' }] }]);
ok(/Studios 1, 2, 3, 8, C, and F\./.test(r.reply_text || ''), 'a booked studio is left out (Studio 7)', r.reply_text);
console.log('A range - day by day');
r = ra({ start_iso: '2027-10-02T09:00:00+08:00', end_iso: '2027-10-03T18:00:00+08:00', scope: 'studios' });
ok(r.multi_day && /:\n\n.+:\nStudios 1, 2, 3, 7, 8, C, and F\.\nVocal booth A\.\nM2, M3, M5\.\n\n.+:\nStudios /.test(r.reply_text || ''), 'each day its own block, a blank line between days', r.reply_text);
console.log('Guard Probe sends the layout when the reply is just the list');
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const one = ra({ ...DAY, scope: 'studios' });
const gp = (output) => new Function('$input', '$', code(M, 'Guard Probe'))(
  wrap([{ json: { ...((rec('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: [{ action: { tool: 'Room_Availability', toolInput: {} }, observation: JSON.stringify([one]) }] } }]),
  n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
ok(gp('Free studios today: Studio 1, Studio 2, Studio 3, Studio 7, Studio 8, Studio A, Studio C, Studio F (Plus M2, M3, and M5).') === one.reply_text, 'live 17:20: the model\'s run-on list -> the laid-out list');
ok(/Who/.test(gp('Studio 8 is free. Who’s the client?')), 'a reply with a question keeps the model\'s text');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
