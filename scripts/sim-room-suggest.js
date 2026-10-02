#!/usr/bin/env node
// Offline tests for Book Session v63 (QA bugs 11/13): no room named -> the highest-ranked free room, as a suggestion.
//
//   node scripts/sim-room-suggest.js <book-session-prepare-execution.json>
//
// The execution is a real Book Session prepare run (29 Sep exec 16681: "Book Studio 8 on Thursday, November 18 from
// 2pm to 4pm, VO recording, project QANEW ..."). Check Conflicts and Render Summary run on its recorded inputs with
// only the requester's words, the model's room and the calendar replaced - on v63 and on v62.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = WF(process.env.BOOK || 'book-session-v63.json'), OLD = WF('book-session-v62.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const REF = JSON.parse(REQ0.reference_data);
const nm = id => (REF.rooms.find(r => r.id === id) || {}).name;
const vo = REF.types.find(t => t.type === 'VO Recording');
const PRI = vo.priority.map(nm), LAST = vo.last.map(nm);
const email = n => { const m = code(NEW, 'Check Conflicts').match(new RegExp("'" + n + "': '([^']+)'")); return m ? m[1] : ''; };
const D = REQ0.start_iso.slice(0, 10);
const busy = (id, room, s = '14:00', e = '16:00', title = 'OTHER / X / TL') => ({ id, status: 'confirmed', summary: title,
  start: { dateTime: D + 'T' + s + ':00+08:00' }, end: { dateTime: D + 'T' + e + ':00+08:00' }, attendees: [{ email: email(room), resource: true }], description: 'ref: U999' });
const TXT = 'Book on Thursday, November 18 from 2pm to 4pm, VO recording, project QANEW, client Jem Lim, engineer Drey';

const cc = (w, items, req = {}) => {
  const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const inp = [{ json: { kind: 'calendar#events', items } }];
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap(inp), () => ({}))[0].json;
};
const rs = (w, ccOut, req = {}) => {
  const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: ccOut }])
    : n === 'Decide Preempt' ? (() => { throw new Error('unexecuted'); })() : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Render Summary'))($, wrap([{ json: ccOut }]))[0].json;
};
console.log('VO Recording ranking from the recording: priority ' + PRI.join(', ') + ' | last resort ' + LAST.join(', '));
ok(PRI.length >= 2, 'the recording carries a VO Recording ranking');

console.log('No room named - the top free room is suggested');
let r = cc(NEW, [], { requester_text: TXT, rooms: 'Studio 3' });
ok(r.verdict === 'CLEAR' && r.final_rooms === PRI[0] && r.room_suggested === PRI[0], 'the model chose Studio 3 -> replaced by ' + PRI[0] + ' (first in the ranking)', r);
let s = rs(NEW, r, { requester_text: TXT, rooms: 'Studio 3' }).summary_text;
ok(new RegExp('\\*Room:\\* ' + PRI[0] + '\\n').test(s), 'the summary shows ' + PRI[0], s);
const SHORT = !/_check /.test(s);   // v73+: the short card (no code; one-line note)
ok(SHORT ? new RegExp("I picked " + PRI[0] + "\\. Tell me if you’d like another room\\.").test(s) : new RegExp("I picked " + PRI[0] + " - the first choice for VO Recording that is free then\\. OK with that room\\? If not, tell me which one you'd like\\.").test(s), 'and says it was picked, and asks if it is OK', s);
ok(SHORT ? /Confirm to book\.$/.test(s.trim()) : /_check [0-9a-f]{8}_\n\nReply only with "yes" to book/.test(s), 'the confirmation is still last');
r = cc(NEW, [busy('b1', PRI[0])], { requester_text: TXT, rooms: '' });
ok(r.verdict === 'CLEAR' && r.room_suggested === PRI[1], 'no room at all, ' + PRI[0] + ' taken -> ' + PRI[1], r);
r = cc(NEW, PRI.map((p, i) => busy('p' + i, p)), { requester_text: TXT, rooms: '' });
ok(r.verdict === 'CLEAR' && r.room_suggested === LAST[0], 'every usual room taken -> the first free last-resort room (' + LAST[0] + ')', r);
r = cc(NEW, PRI.concat(LAST).map((p, i) => busy('x' + i, p)), { requester_text: TXT, rooms: '' });
ok(r.verdict === 'REJECTED' && r.reason === 'NO_ROOM' && /is free then, so nothing was prepared\. Offer 2-3 other times/.test(r.human), 'every ranked room taken -> nothing prepared, offer other times', r);
r = cc(NEW, [busy('b1', PRI[0], '10:00', '12:00')], { requester_text: TXT, rooms: '' });
ok(r.room_suggested === PRI[0], 'a booking outside the window does not count');
r = cc(NEW, [], { requester_text: TXT, rooms: PRI[0] + ', Studio A' });
ok(r.final_rooms === PRI[0] + ', Studio A', 'a free booth the model paired is kept', r.final_rooms);
r = cc(NEW, [busy('a1', 'Studio A')], { requester_text: TXT, rooms: PRI[1] + ', Studio A' });
ok(r.final_rooms === PRI[0], 'a taken booth is dropped', r.final_rooms);

console.log('A room named - theirs is used, as before');
r = cc(NEW, [], { requester_text: 'Book Studio 8 on Thursday, November 18 from 2pm to 4pm, VO recording, project QANEW', rooms: 'Studio 8' });
ok(r.verdict === 'CLEAR' && !r.room_suggested && r.final_rooms === 'Studio 8', '"Book Studio 8" -> Studio 8, no suggestion note', r);
ok(!/I picked/.test(rs(NEW, r).summary_text), '  and the summary has no "I picked" note');
r = cc(NEW, [], { requester_text: 'book studio8 thursday 2-4pm vo', rooms: 'Studio 8' });
ok(!r.room_suggested, '"studio8" (no space) counts as naming it');
r = cc(NEW, [], { requester_text: 'VO recording thursday 2pm to 4pm\nuse Studio 5 please', rooms: 'Studio 5' });
ok(!r.room_suggested && (r.final_rooms === 'Studio 5' || (r.reason === 'ROOM_NOT_PRIORITY' && JSON.stringify(r.requested) === '["Studio 5"]')), 'named in a later message -> theirs is kept (Studio 5 is last resort for VO, so the usual guard asks first)', r);
r = cc(NEW, [], { requester_text: TXT + ' in m3', rooms: 'M3' });
ok(!r.room_suggested, 'an M booth named ("m3") counts');

console.log('Not a suggestion case - unchanged');
r = cc(NEW, [], { requester_text: TXT, rooms: 'Studio 3', mode: '' });
ok(!r.room_suggested && (r.final_rooms === 'Studio 3' || r.reason), 'not prepare mode (the yes) -> the room on the summary is booked, never re-picked', r);
r = cc(NEW, [], { requester_text: '', rooms: 'Studio 3' });
ok(!r.room_suggested, 'no requester text (a consent placement, an older caller) -> unchanged');
r = cc(NEW, [], { requester_text: TXT, rooms: 'Studio 3', room_override: true });
ok(!r.room_suggested, 'room_override (they insisted) -> unchanged');
r = cc(NEW, [], { requester_text: TXT, rooms: '' , mode: '' });
ok(r.reason === 'MISSING_DETAILS', 'no room outside prepare mode -> still refused as missing', r.reason);
let o = cc(OLD, [], { requester_text: TXT, rooms: 'Studio 3' });
ok(!o.room_suggested, '  (v62: the model\'s Studio 3 kept - ' + (o.reason || o.verdict) + ')');
o = cc(OLD, [], { requester_text: TXT, rooms: '' });
ok(o.reason === 'MISSING_DETAILS', '  (v62: no room -> refused as missing)');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
