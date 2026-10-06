#!/usr/bin/env node
// Offline tests for main v223 (availability times from the requester; PENDING 88, live 6 Oct 14:46 PHT): Room
// Availability's window takes Booked For's time range, like Book Session's inputs, so "10-12pm" is never checked as 10 PM.
//   node scripts/sim-ra-time.js
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v223.json'), OM = WF('project-jessie-v222.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d))); } };
const ev = (W, k, ws, we, bf, gc = {}) => { const e = W.nodes.find(x => x.name === 'Room Availability').parameters.workflowInputs.value[k].replace(/^=\{\{ /, '').replace(/ \}\}$/, '');
  const $fromAI = n => n === 'window_start' ? ws : we;
  const $ = n => ({ first: () => ({ json: n === 'Booked For' ? bf : n === 'Gate Context' ? gc : {} }) });
  return new Function('$fromAI', '$', 'return (' + e + ');')($fromAI, $); };
const BF = { timeStart: '10:00', timeEnd: '12:00', timePhrase: '10-12pm', timesMentioned: ['10:00', '12:00'] };
const W = (k, s, e, bf = BF, gc) => ev(M, k, s, e, bf, gc);
console.log('main v223 - Room Availability window');
let s = W('start_iso', '2027-10-08T22:00:00+08:00', '2027-10-08T12:00:00+08:00'), e = W('end_iso', '2027-10-08T22:00:00+08:00', '2027-10-08T12:00:00+08:00');
ok(s === '2027-10-08T10:00:00+08:00' && e === '2027-10-08T12:00:00+08:00', 'live 14:46: the model\'s 10 PM - 12 PM -> 10:00 AM - 12:00 PM', [s, e]);
ok(ev(OM, 'start_iso', '2027-10-08T22:00:00+08:00', '2027-10-08T12:00:00+08:00', BF) === '2027-10-08T22:00:00+08:00', '  (v222: 22:00 sent as is)');
s = W('start_iso', '2027-10-08T10:00:00+08:00', '2027-10-08T12:00:00+08:00');
ok(s === '2027-10-08T10:00:00+08:00', 'already right -> unchanged', s);
s = W('start_iso', '2027-10-08T00:00:00+08:00', '2027-10-08T23:59:00+08:00'); e = W('end_iso', '2027-10-08T00:00:00+08:00', '2027-10-08T23:59:00+08:00');
ok(s === '2027-10-08T00:00:00+08:00' && e === '2027-10-08T23:59:00+08:00', 'a whole-day check is not narrowed', [s, e]);
s = W('start_iso', '2027-10-08T14:00:00+08:00', '2027-10-08T16:00:00+08:00', {});
ok(s === '2027-10-08T14:00:00+08:00', 'no range typed -> the model\'s window stands', s);
s = W('start_iso', '2027-10-08T15:00:00+08:00', '2027-10-08T17:00:00+08:00', { ...BF, timesMentioned: ['10:00', '12:00', '15:00'] });
ok(s === '2027-10-08T15:00:00+08:00', 'a time the requester also typed (e.g. an alternative) -> kept', s);
s = W('start_iso', '2027-10-09T22:00:00+08:00', '2027-10-09T12:00:00+08:00', BF, { datesInMessage: '2027-10-08' });
ok(s === '2027-10-08T10:00:00+08:00', 'the date pin (v213) still runs, then the time', s);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
