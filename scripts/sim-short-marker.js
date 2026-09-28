#!/usr/bin/env node
// The one-line confirmation ("Book it? Reply yes or no."), offline, on main v177.
//
//   node scripts/sim-short-marker.js <main-v177.json> <main-execution-with-a-prepared-summary.json>
//
// Guard Probe runs on real recorded inputs; the prepared summary is the one Book Session really rendered. The
// summary then goes through Prepared Booking exactly as Slack would hand it back.
const fs = require('fs');
const [mf, ef] = process.argv.slice(2);
const M = JSON.parse(fs.readFileSync(mf)), run = JSON.parse(fs.readFileSync(ef)).data.resultData.runData;
const code = n => M.nodes.find(x => x.name === n).parameters.jsCode;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const gin = rec('Jessie AI Agent')[0].json;   // Guard Probe's input is the agent's output
const steps0 = gin.intermediateSteps || [];
const prepObs = steps0.map(s => { try { return [].concat(JSON.parse(String(s.observation || '')))[0]; } catch (e) { return null; } }).find(o => o && o.summary_text);
const gp = (output, steps = []) => new Function('$input', '$', code('Guard Probe'))(wrap([{ json: { ...gin, output, intermediateSteps: steps } }]), n => wrap(rec(n) || [{ json: {} }]))[0].json.output;
const ends = (t, v) => new RegExp('\\n\\n' + v + ' it\\? Reply yes or no\\.$').test(t) && !/Reply only with|Confirm to (book|cancel|move)/i.test(t);

console.log('Guard Probe');
ok(prepObs && /Confirm to book\.$/.test(prepObs.summary_text), 'the recorded Prepare Booking summary is in the old two-line form (as Book Session renders it)');
const sent = gp('ignored', steps0);
ok(ends(sent, 'Book'), 'a prepared summary goes out ending in one line: "Book it? Reply yes or no."', sent.slice(-160));
const body = s => s.replace(/\n\n(?:Reply only with[^\n]*\n)?(?:Confirm to book\.|Book it\? Reply yes or no\.)$/, '');
ok(body(sent) === body(prepObs.summary_text), 'every booking line and the check code are unchanged');
ok(ends(gp('Studio 7 is booked for you?\n\nConfirm to cancel. (yes/no)'), 'Cancel'), 'a model-written "Confirm to cancel. (yes/no)" -> "Cancel it? Reply yes or no."');
ok(ends(gp('Move QATEST to 3pm?\nConfirm to move both.'), 'Move'), 'a rephrased marker ("Confirm to move both.") is still normalised');
const copied = gp('Here it is.\n\nBook it? Reply yes or no.');
ok((copied.match(/Reply yes or no/g) || []).length === 1, 'the model copying the short line back -> still exactly one line', copied);
ok(gp('Which room would you like?') === 'Which room would you like?', 'a reply with no confirmation is untouched');

console.log('Prepared Booking reads the new line');
const pb = (text, gate) => new Function('$', '$input', code('Prepared Booking'))(n => n === 'Gate Context' ? wrap([{ json: gate }]) :
  n === 'Get Recent Messages' ? wrap([{ json: { user: 'U026N6E1R', text: 'yes' } }, { json: { bot_id: 'B1', text } }]) : wrap(rec(n) || [{ json: {} }]), wrap([{ json: {} }]))[0].json;
const g = rec('Gate Context')[0].json;
const r1 = pb(sent, { ...g, confirmed: true });
ok(r1.ok === true && r1.use === true, 'a yes to the one-line summary is booked directly (Book Direct)', r1);
const r0 = pb(prepObs.summary_text, { ...g, confirmed: true });
ok(r0.ok === true && r0.use === true, 'a summary still in the old form (sent before the change) also still works', r0);
ok(pb(sent.replace('Book it? Reply yes or no.', 'Book it? Reply yes or no. Or pick another room.'), { ...g, confirmed: true }).use !== true, 'text after the line -> not a summary, not booked');

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
