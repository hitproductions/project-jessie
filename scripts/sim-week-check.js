#!/usr/bin/env node
// Offline tests for Room Availability v12 (multi-day check fix) + main v197 (this-week range fix) - PENDING 62. 29 Sep 23:17 PHT: "this week" was
// checked as one Monday-to-Sunday block, starting on a day already past.
//   node scripts/sim-week-check.js
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const RA = WF(process.env.RA || 'room-availability-v12.json'), ORA = WF('room-availability-v11.json');
const M = WF(process.env.MAIN || 'project-jessie-v197.json'), OM = WF('imported/project-jessie-v196-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', S8 = 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com';
const REF = JSON.stringify({ rooms: [{ id: 'r7', name: 'Studio 7' }, { id: 'r8', name: 'Studio 8' }, { id: 'rF', name: 'Studio F' }, { id: 'rK', name: 'Katha', common: true }],
  types: [{ type: 'VO Recording', priority: ['r7', 'r8', 'rF'], last: [] }] });
const EV = [
  { id: 'e1', summary: 'SPORT / Alex Gorne / AEG', start: { dateTime: '2027-10-01T12:00:00+08:00' }, end: { dateTime: '2027-10-01T13:00:00+08:00' }, attendees: [{ email: S7 }] },
  { id: 'e2', summary: 'HOLD / DR', start: { date: '2027-10-02' }, end: { date: '2027-10-03' }, attendees: [{ email: S8 }] },
  { id: 'e3', summary: 'LATE / EG', start: { dateTime: '2027-09-30T15:00:00+08:00' }, end: { dateTime: '2027-09-30T17:00:00+08:00' }, attendees: [{ email: S7 }] }];
Date.now = () => Date.parse('2026-09-30T08:00:00Z');
const ra = (w, req, evs = EV) => new Function('$', '$input', code(w, 'Compute Availability'))(
  n => wrap([{ json: { reference_data: REF, scope: 'all', ...req } }]), wrap([{ json: { items: evs } }]))[0].json;
const WEEK = { start_iso: '2027-09-30T09:00:00+08:00', end_iso: '2027-10-03T18:00:00+08:00' };

console.log('Room Availability - a named room over several days');
let r = ra(RA, { ...WEEK, room: 'Studio 7' });
ok(r.multi_day && r.days.length === 4 && r.asked.status === 'MULTI_DAY', 'Thu 30 Sep to Sun 3 Oct, 9 AM - 6 PM -> four days, MULTI_DAY', r);
ok(/- Thursday, September 30: taken 3:00 PM – 5:00 PM by "LATE \/ EG"/.test(r.human) && /- Friday, October 1: taken 12:00 PM – 1:00 PM by "SPORT \/ Alex Gorne \/ AEG"/.test(r.human)
   && /- Saturday, October 2: free/.test(r.human) && /- Sunday, October 3: free/.test(r.human), 'each day: free, or taken - by what and when', r.human);
ok(/^Studio 7, 9:00 AM – 6:00 PM, day by day:/.test(r.human), 'says which hours were checked each day', r.human.split('\n')[0]);
ok(ra(ORA, { ...WEEK, room: 'Studio 7' }).asked.status === 'BUSY', '  (v11: one block - "Studio 7 is taken in that window", all week)');
r = ra(RA, { start_iso: '2027-09-30T14:00:00+08:00', end_iso: '2027-10-03T16:00:00+08:00', room: 'Studio 7' });
ok(/Thursday, September 30: taken 3:00 PM/.test(r.human) && /Friday, October 1: free/.test(r.human), '2-4 PM each day: SPORT (12-1) does not count on Friday; LATE (3-5) does on Thursday', r.human);
r = ra(RA, { start_iso: '2027-09-30T00:00:00+08:00', end_iso: '2027-10-04T00:00:00+08:00', room: 'Studio 8' });
ok(/^Studio 8, all day, day by day:/.test(r.human) && /Saturday, October 2: taken all day by "HOLD \/ DR"/.test(r.human) && r.days.length === 4, 'midnight to midnight -> whole days; an all-day hold shown as all day', r.human);

console.log('Room Availability - which rooms are free, several days');
r = ra(RA, { ...WEEK, session_type: 'VO Recording' });
ok(/^Free for VO Recording, 9:00 AM – 6:00 PM, day by day:/.test(r.human) && /Thursday, September 30: Studio 8, Studio F/.test(r.human) && /Saturday, October 2: Studio 7, Studio F/.test(r.human),
   'with a session type -> the usual rooms free each day', r.human);
ok(!('free_rooms' in r) && !('free_priority' in r), 'no top-level free list, so Guard Probe does not read a week as one answer');
r = ra(RA, { ...WEEK, scope: 'studios' });
ok(/Friday, October 1: Studio 8, Studio F$/m.test(r.human) && !/Katha/.test(r.human), 'no session type, studios only -> each day, conference rooms left out', r.human);

console.log('Unchanged');
const DAY = { start_iso: '2027-10-01T09:00:00+08:00', end_iso: '2027-10-01T18:00:00+08:00', room: 'Studio 7' };
ok(JSON.stringify(ra(RA, DAY)) === JSON.stringify(ra(ORA, DAY)), 'a one-day window -> exactly as v11');
ok(ra(RA, { ...WEEK, room: 'Studio Z' }).asked.status === 'UNKNOWN_ROOM', 'a room that does not exist -> answered once');
ok(ra(RA, { ...WEEK, room: 'Katha', session_type: 'VO Recording' }).asked.status === 'NOT_RUN_HERE', 'not run for that session type -> answered once');
ok(ra(RA, { start_iso: '2027-09-30T09:00:00+08:00', end_iso: '2027-11-30T18:00:00+08:00', room: 'Studio 7' }).multi_day !== true, 'more than 14 days -> not split (answered as one window, as before)');
ok(ra(RA, { ...WEEK, room: 'Studio 7' }, []).days.every(d => d.rooms[0].status === 'FREE'), 'an empty calendar -> free every day');

console.log('main v197');
const gate = w => { const src = code(w, 'Gate Context'); Date.now = () => Date.parse('2026-09-30T06:00:00Z');   // Thu 30 Sep (QA year 2027)
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text: 'what is free this week', user: 'U1', ts: '1790745000.1' } : n === 'Get Booker' ? { fields: { Name: 'Howard Luistro' } } : {} }), all: () => [] });
  return new Function('$', '$getWorkflowStaticData', src)($, () => ({}))[0].json; };
let g = gate(M);
ok(g.datesUnderDiscussion.split(',')[0] === '2027-09-30' && g.datesUnderDiscussion.split(',').pop() === '2027-10-03' && /Thursday, 30 September 2027/.test(g.dateNotice), '"this week" on Thursday -> Thu 30 Sep to Sun 3 Oct', [g.datesUnderDiscussion, g.dateNotice]);
ok(gate(OM).datesUnderDiscussion.split(',')[0] === '2027-09-27', '  (v196: from Monday 27 Sep, already past)');
const gp = (w, steps, said = 'is studio 7 free this week', output = 'Studio 7 is free on some days.') => new Function('$input', '$', code(w, 'Guard Probe'))(
  wrap([{ json: { output, intermediateSteps: steps } }]),
  n => wrap([{ json: n === 'Slack Trigger' ? { text: said } : n === 'Gate Context' ? { datesUnderDiscussion: '' } : {} }]))[0].json.output;
const step = { action: { tool: 'Room_Availability', toolInput: { window_start: '2027-09-30T09:00:00+08:00', window_end: '2027-10-03T18:00:00+08:00', window_room: 'Studio 7' } }, observation: '[]' };
let o = gp(M, [step]);
ok(/Dates checked: Thursday, September 30 to Sunday, October 3, 2027\./.test(o), '"Dates checked" covers the whole window', o);
ok(/Dates checked: Thursday, September 30, 2027\./.test(gp(OM, [step])), '  (v196: only the first day)');
ok(gp(M, [step], 'is studio 7 free this week', 'Studio 7:\n- Thursday: free Give this day by day as it is; do not merge the days or add rooms.').indexOf('Give this day by day') === -1, 'the relay instruction never reaches the requester');
ok(/answers day by day/.test(M.nodes.find(n => n.name === 'Room Availability').parameters.description), 'the tool description says to pass a range as one window');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
