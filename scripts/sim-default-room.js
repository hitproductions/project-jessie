#!/usr/bin/env node
// Offline tests for Book Session v77 + main v208 (default room): Bookers "Default Type" is a person's default room,
// used when no room is named, if it is free and one of the session type's usual rooms (decided 1 Oct).
//
//   node scripts/sim-default-room.js <book-session-prepare-execution.json>     (29 Sep exec 16681)
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = WF(process.env.BOOK || 'book-session-v77.json'), OLD = WF('book-session-v76.json'), M = WF(process.env.MAIN || 'project-jessie-v208.json');
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
const busy = (id, room) => ({ id, status: 'confirmed', summary: 'OTHER / X / TL', start: { dateTime: D + 'T14:00:00+08:00' }, end: { dateTime: D + 'T16:00:00+08:00' }, attendees: [{ email: email(room), resource: true }], description: 'ref: U999' });
const TXT = 'Book on Thursday, November 18 from 2pm to 4pm, VO recording, project QANEW, client Jem Lim, engineer Drey';
const ME = (String(REQ0.description || '').match(/booked by\s*:\s*([^|(]+)/i) || [])[1].trim();
const staffRows = (mine, extra = []) => {
  const base = (rec('All Bookers') || []).map(i => i.json.fields || {}).filter(f => f.Name);
  return base.map(f => ({ json: { fields: f.Name === ME ? { ...f, 'Default Type': mine } : f } })).concat(extra.map(f => ({ json: { fields: f } })));
};
const cc = (w, items, req = {}, staff) => {
  const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => { if (n === 'All Bookers' && staff) return wrap(staff); const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  return new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($, wrap([{ json: { kind: 'calendar#events', items } }]), () => ({}))[0].json;
};
const rs = (w, ccOut, req = {}) => {
  const R = [{ json: { ...REQ0, ...req } }];
  const $ = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: ccOut }]) : n === 'Decide Preempt' ? (() => { throw new Error('unexecuted'); })() : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Render Summary'))($, wrap([{ json: ccOut }]))[0].json;
};
console.log('requester ' + ME + ' | VO Recording usual rooms: ' + PRI.join(', ') + ' | last resort: ' + LAST.join(', '));
const DEF = PRI[PRI.length - 1];   // a usual room that is not the first choice

console.log('No room named - the default room when free and usual');
let r = cc(NEW, [], { requester_text: TXT, rooms: '' }, staffRows([DEF]));
ok(r.verdict === 'CLEAR' && r.final_rooms === DEF && r.room_default === DEF, 'default ' + DEF + ' (free, usual) -> ' + DEF + ' (not ' + PRI[0] + ')', r);
const s = rs(NEW, r, { requester_text: TXT, rooms: '' }).summary_text || '';
ok(new RegExp('\\*Room:\\* ' + DEF).test(s) && /Your usual room\. Tell me if you’d like another\./.test(s), 'the card shows it, "Your usual room."', s);
ok(cc(OLD, [], { requester_text: TXT, rooms: '' }, staffRows([DEF])).final_rooms === PRI[0], '  (v76: ' + PRI[0] + ', the default ignored)');
r = cc(NEW, [busy('b1', DEF)], { requester_text: TXT, rooms: '' }, staffRows([DEF]));
ok(r.verdict === 'CLEAR' && r.final_rooms === PRI[0] && !r.room_default, 'default busy -> the usual first free room (' + PRI[0] + ')', r);
if (LAST.length) { r = cc(NEW, [], { requester_text: TXT, rooms: '' }, staffRows([LAST[0]]));
  ok(r.final_rooms === PRI[0] && !r.room_default, 'default only a last-resort room for VO -> not used (' + PRI[0] + ')', r); }
r = cc(NEW, [], { requester_text: TXT, rooms: '' }, staffRows(['Likha']));
ok(r.final_rooms === PRI[0] && !r.room_default, 'default not a VO room (Likha) -> not used', r);
r = cc(NEW, [], { requester_text: TXT, rooms: '' }, staffRows([]));
ok(r.final_rooms === PRI[0] && !r.room_default, 'no default -> as before', r);
r = cc(NEW, [], { requester_text: TXT, rooms: '' }, staffRows([{ name: DEF }]));
ok(r.final_rooms === DEF, 'Airtable object form {name} read too');
r = cc(NEW, [], { requester_text: 'Book ' + PRI[0] + ' on Thursday, November 18 from 2pm to 4pm, VO recording', rooms: PRI[0] }, staffRows([DEF]));
ok(r.final_rooms === PRI[0] && !r.room_default, 'a named room always wins', r);

console.log('Booked for a colleague - their default');
const COL = { Name: 'Test Colleague', Initials: 'TC2', Info: 'Post Engineer', Department: ['Audio Post'], 'Default Type': [PRI[1]] };
r = cc(NEW, [], { requester_text: TXT, rooms: '', description: String(REQ0.description).replace(/Booked by:\s*([^|]+)/i, 'Booked by: ' + ME + ' (for Test Colleague) ') }, staffRows([DEF], [COL]));
ok(r.final_rooms === PRI[1] && r.room_default === PRI[1], 'for a colleague with default ' + PRI[1] + ' -> ' + PRI[1], r);

console.log('main v208 - the staff list carries the default room');
for (const t of ['Prepare Booking', 'Book Session', 'Book Direct']) {
  const e = M.nodes.find(x => x.name === t).parameters.workflowInputs.value.staff_data;
  const out = new Function('$', 'return ' + e.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''))(n => wrap([{ json: { fields: { Name: 'Dylan Diaz', Initials: 'DD', Info: 'x', Department: ['Marketing'], 'Default Type': ['Studio E'] } } }]));
  ok(JSON.parse(out)[0]['Default Type'][0] === 'Studio E', t + ': staff_data includes "Default Type"');
}
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
