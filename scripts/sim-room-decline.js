#!/usr/bin/env node
// sim-room-decline (Book Session v106, PENDING 44): Verify reads the event back after the room has answered.
//   node scripts/sim-room-decline.js [workflows/book-session-vN.json]
const fs = require('fs'), path = require('path');
const B = JSON.parse(fs.readFileSync(process.argv[2] || path.join(__dirname, '..', 'workflows', 'book-session-v106.json')));
const code = n => B.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
const S7 = { email: 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio 7 (7)', resource: true };
const made = { id: 'e1', summary: 'X / HL', start: { dateTime: '2027-10-13T15:00:00+08:00' }, end: { dateTime: '2027-10-13T17:00:00+08:00' }, attendees: [{ ...S7, responseStatus: 'needsAction' }] };
const verify = reread => new Function('$', '$input', code('Verify'))(n => wrap([{ json: n === 'Create Event' ? made : n === 'Check Conflicts' ? { final_start: made.start.dateTime, final_end: made.end.dateTime } : { all_day: false } }]), wrap([{ json: reread }]))[0].json;
let r = verify({ ...made, attendees: [{ ...S7, responseStatus: 'declined' }] });
ok(r.status === 'ROOM_DECLINED' && r.human === '❌ Studio 7 turned this booking down - its own calendar shows it is taken then. Nothing is booked. Want another time or studio?', 'read back declined -> ROOM_DECLINED, a reply for the requester', r);
r = verify({ ...made, attendees: [{ ...S7, responseStatus: 'accepted' }] });
ok(r.status === 'CREATED' && r.human === 'Booked.', 'accepted -> Booked.', r.status);
r = verify({ error: { message: 'boom' } });
ok(r.status === 'CREATED', 'the read back failed -> the create response stands (still needsAction -> Booked.)', r.status);
const con = B.connections;
ok(con['Create Event'].main[0][0].node === 'Wait for Room' && con['Wait for Room'].main[0][0].node === 'Reread Event' && con['Reread Event'].main[0][0].node === 'Verify', 'Create Event -> Wait for Room -> Reread Event -> Verify');
const w = B.nodes.find(x => x.name === 'Wait for Room'), rr = B.nodes.find(x => x.name === 'Reread Event');
ok(w.parameters.amount === 6 && (w.parameters.unit || 'seconds') === 'seconds' && rr.onError === 'continueRegularOutput', '6 seconds; a failed read never stops the booking');
const cc = code('Check Conflicts');
ok(/v106 \(12 Oct/.test(cc), 'internal rooms: no Engineer line (Check Conflicts)');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
