#!/usr/bin/env node
// Offline test for Book Session v64 (QA bug 9): the summary shows the booking type Check Conflicts settled on.
//
//   node scripts/sim-booking-type-line.js <book-session-prepare-execution.json>
//
// The execution is the real QAROOM prepare run (29 Sep, main exec 16795): the model sent no bookingType, the
// client's Client Type made it External, and v63's summary had no Booking Type line. Replayed on v64 and v63, then
// read back through main's Prepared Booking the way the yes does.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const NEW = WF(process.env.BOOK || 'book-session-v64.json'), OLD = WF('book-session-v63.json'), M = WF(process.env.MAIN || 'project-jessie-v187.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const summary = (w, req = {}) => {
  const R = [{ json: { ...REQ0, ...req } }];
  const $c = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const cc = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: cc }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: cc }]))[0].json.summary_text;
};
ok(!String(REQ0.bookingType || '').trim(), 'the recording: the model sent no booking type', REQ0.bookingType);
const s = summary(NEW);
ok(/\n\*Booking Type:\* External\n/.test(s), 'v64: the summary shows Booking Type: External (from the client record)', s);
ok(!/Booking Type/.test(summary(OLD)), '  (v63: no Booking Type line)');
// the summary line and the event description always agree (both from Check Conflicts)
{ const R = [{ json: REQ0 }], $c = n => { const it = n === 'When Executed by Another Workflow' ? R : rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const cc = new Function('$', '$input', '$getWorkflowStaticData', code(NEW, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  ok(/\| Type: External \|/.test(cc.final_description) && cc.final_booking_type === 'External', 'the event description says Type: External - the same value the summary shows', cc.final_description); }
ok(/\*Booking Type:\* External/.test(summary(NEW, { bookingType: 'External' })), 'a booking type the model did send is shown as before');
const shown = s.replace(/\n\nReply only with[^\n]*\nConfirm to book\.$/, '\n\nBook it? Reply yes or no.');
const pb = new Function('$', '$input', code(M, 'Prepared Booking'))(n => n === 'Gate Context' ? wrap([{ json: { confirmed: true, gate: { saidYes: true } } }])
  : n === 'Get Recent Messages' ? wrap([{ json: { user: 'U08V3CKDGJF', text: 'yes', ts: String(Date.now() / 1000) } }, { json: { bot_id: 'B1', text: shown, ts: String(Date.now() / 1000 - 30) } }]) : wrap([{ json: {} }]), wrap([{ json: {} }]))[0].json;
ok(pb.use === true && pb.ok === true && pb.p.bookingType === 'External', 'at the yes, main verifies the code and books it as External', pb);
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
