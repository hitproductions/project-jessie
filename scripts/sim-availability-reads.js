#!/usr/bin/env node
// sim-availability-reads (Room Availability v20, 8 Oct): every answer about a room says exactly when it is booked and what
// is still free, written in code. Live 21:44 on v19: "what time is studio 7 free tom" -> "taken all day" for a 1-3 PM booking.
//   node scripts/sim-availability-reads.js [workflows/room-availability-vN.json]   (default: the newest)
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', 'workflows');
const file = process.argv[2] || path.join(dir, fs.readdirSync(dir).filter(f => /^room-availability-v\d+\.json$/.test(f))
  .sort((a, b) => +a.match(/\d+/)[0] - +b.match(/\d+/)[0]).pop());
const RA = JSON.parse(fs.readFileSync(file, 'utf8'));
const code = RA.nodes.find(x => x.name === 'Compute Availability').parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const ROOMS = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 7', 'Studio 8', 'Studio C', 'Studio F', 'Studio A', 'M2', 'M3', 'M5', 'Likha', 'Katha'];
const REF = JSON.stringify({ rooms: ROOMS.map((n, i) => ({ id: 'r' + i, name: n, vocalBooth: n === 'Studio A', common: /Likha|Katha/.test(n) })),
  types: [{ type: 'VO Recording', priority: ['r3', 'r4', 'r6'], last: ['r5'] }] });
Date.now = () => Date.parse('2026-10-08T13:00:00Z');
const ra = (req, evs = []) => new Function('$', '$input', code)(n => wrap([{ json: { reference_data: REF, scope: 'studios', ...req } }]), wrap([{ json: { items: evs } }]))[0].json;
const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const ev = (id, title, s, e, email = S7) => ({ id, summary: title, start: s.length === 10 ? { date: s } : { dateTime: s }, end: e.length === 10 ? { date: e } : { dateTime: e }, attendees: [{ email }] });
const DAY = { start_iso: '2027-10-09T00:00:00+08:00', end_iso: '2027-10-09T23:59:00+08:00' };
const CATTAIL = ev('c', 'CATTAIL / Sasa Abella / HL', '2027-10-09T13:00:00+08:00', '2027-10-09T15:00:00+08:00');

console.log('A day, Studio 7 asked about (the live 21:44 case)');
let r = ra({ ...DAY, room: 'Studio 7' }, [CATTAIL]);
ok(r.asked.status === 'BUSY' && r.asked.whole_window === false, 'BUSY, but not for the whole day', r.asked);
ok(/Studio 7 is booked 1:00 PM – 3:00 PM \(CATTAIL \/ Sasa Abella \/ HL\) - free the rest of the day\./.test(r.asked.human), 'the tool text says when, and that the rest is free', r.asked.human);
ok(!/all day|in that window/.test(r.asked.human), 'never "all day" or "in that window" for a part-day booking', r.asked.human);
ok(/^🗓️ October 9 \(Saturday\)\n\n⚠️ Studio 7 is booked 1:00 PM – 3:00 PM \(CATTAIL \/ Sasa Abella \/ HL\) - free the rest of the day\.\n\n✅ Free all day:\nStudios 1, 2, 3, 8, C, and F\.\nVocal booth A\.\nM2, M3, M5\.$/.test(r.reply_text || ''), 'reply: Studio 7 first, then the rooms free all day (Studio 7 not repeated)', r.reply_text);

console.log('A day: booked all day, free all day, two bookings');
r = ra({ ...DAY, room: 'Studio 7' }, [ev('h', 'HOLD / X / HL', '2027-10-09', '2027-10-10')]);
ok(r.asked.whole_window === true && /❌ Studio 7 is booked all day \(HOLD \/ X \/ HL\)\./.test(r.reply_text || ''), 'an all-day event -> booked all day', r.reply_text);
r = ra({ ...DAY, room: 'Studio 7' }, []);
ok(/✅ Studio 7 is free all day\./.test(r.reply_text || '') && r.asked.status === 'FREE', 'nothing booked -> free all day', r.reply_text);
r = ra({ ...DAY, room: 'Studio 7' }, [ev('a', 'AM / X / HL', '2027-10-09T10:00:00+08:00', '2027-10-09T12:00:00+08:00'), ev('b', 'PM / Y / HL', '2027-10-09T15:00:00+08:00', '2027-10-09T17:00:00+08:00')]);
ok(/⚠️ Studio 7 is booked 10:00 AM – 12:00 PM \(AM \/ X \/ HL\) and 3:00 PM – 5:00 PM \(PM \/ Y \/ HL\) - free the rest of the day\./.test(r.reply_text || ''), 'two bookings, each with its time', r.reply_text);

console.log('A set time');
const AT = { start_iso: '2027-10-09T14:00:00+08:00', end_iso: '2027-10-09T17:00:00+08:00' };
r = ra({ ...AT, room: 'Studio 7' }, [ev('m', 'MID / X / HL', '2027-10-09T15:00:00+08:00', '2027-10-09T16:00:00+08:00')]);
ok(/⚠️ Studio 7 is booked 3:00 PM – 4:00 PM \(MID \/ X \/ HL\) - free 2:00 PM – 3:00 PM and 4:00 PM – 5:00 PM\./.test(r.reply_text || ''), 'part of the time -> the free gaps', r.reply_text);
ok(/✅ Also free then:\nStudios 1, 2, 3, 8, C, and F\./.test(r.reply_text || ''), '...and the other rooms free then', r.reply_text);
r = ra({ start_iso: '2027-10-09T14:00:00+08:00', end_iso: '2027-10-09T15:00:00+08:00', room: 'Studio 7' }, [CATTAIL]);
ok(/❌ Studio 7 is booked 2:00 PM – 3:00 PM \(CATTAIL \/ Sasa Abella \/ HL\)\./.test(r.reply_text || ''), 'the whole time -> booked then', r.reply_text);
r = ra({ ...AT, room: 'Studio 7', session_type: 'VO Recording' }, [CATTAIL]);
ok(/✅ Usual rooms for VO Recording free then:\nStudios 8 and F\./.test(r.reply_text || ''), 'with a session type -> the usual rooms free then', r.reply_text);

console.log('Several days, Studio 7 asked about');
r = ra({ start_iso: '2027-10-09T00:00:00+08:00', end_iso: '2027-10-10T23:59:00+08:00', room: 'Studio 7' }, [CATTAIL]);
ok(r.multi_day && /🗓️ October 9 \(Saturday\)\n⚠️ Studio 7 is booked 1:00 PM – 3:00 PM \(CATTAIL \/ Sasa Abella \/ HL\) - free the rest of the day\.\n\n🗓️ October 10 \(Sunday\)\n✅ Studio 7 is free all day\./.test(r.reply_text || ''), 'day by day, each with times', r.reply_text);

console.log('No room asked about');
r = ra(DAY, [CATTAIL]);
ok(/⚠️ Studio 7: booked 1:00 PM – 3:00 PM, free the rest of the day\./.test(r.reply_text || '') && !/free except/.test(r.reply_text || ''), 'part-booked rooms say when, and that the rest is free', r.reply_text);

console.log('Not a usual room for the session type (RA v21)');
if (/v21 \(8 Oct 22:06\)/.test(code)) {
  const AT2 = { start_iso: '2027-10-14T14:00:00+08:00', end_iso: '2027-10-14T15:00:00+08:00' };
  r = ra({ ...AT2, room: 'Studio 3', session_type: 'VO Recording' }, []);
  ok(r.asked.status === 'NOT_RUN_HERE' && r.reply_text === "Studio 3 isn't a usual VO Recording room - Studio 7, Studio 8 and Studio F are free then. One of those, or still Studio 3?", 'a room not in the ranking (live 22:06) -> one short question, in code', r.reply_text);
  r = ra({ ...AT2, room: 'Studio C', session_type: 'VO Recording' }, []);
  ok(r.asked.status === 'FREE_BUT_LAST_RESORT' && /^Studio C isn't a usual VO Recording room - Studio 7, Studio 8 and Studio F are free then\. One of those, or still Studio C\?$/.test(r.reply_text || ''), 'a last-resort room -> the same question', r.reply_text);
}
console.log('Left to the model (unchanged)');
r = ra({ ...DAY, room: 'Studio 99' }, []);
ok(r.asked.status === 'UNKNOWN_ROOM' && !r.reply_text, 'an unknown room: no code reply', r);

console.log(`\n${pass} passing, ${fail} failing  (${path.basename(file)})`);
process.exit(fail ? 1 : 0);
