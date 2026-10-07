#!/usr/bin/env node
// Offline tests for main v229 (vocals in-room; QA A3, 7 Oct): the prompt's room block lists the rooms with Airtable's
// `Records Vocals In-Room` checkbox (7, 8, C, D, F), and the Rooms and Studios tool can filter on it.
//   node scripts/sim-vocals-in-room.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const M = WF(process.env.MAIN || 'project-jessie-v229.json'), OM = WF('project-jessie-v228.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData; const rec = n => run[n] ? run[n][0].data.main[0] : [{ json: {} }];
const node = (W, n) => W.nodes.find(x => x.name === n);
const rt = W => new Function('$', '$input', node(W, 'Room Table').parameters.jsCode)(n => wrap(rec(n)), wrap([{ json: {} }]))[0].json.roomTable;
const t = rt(M);
const line = (t.split('\n').find(l => /Record vocals in the room itself/.test(l)) || '');
ok(/: Studio 7 · Studio 8 · Studio C · Studio D · Studio F\./.test(line), 'the room block lists exactly 7, 8, C, D, F (from the checkbox)', line);
ok(!/Studio [1-6]\b/.test(line.split('.')[0]), 'no Studio 1-6 in the list');
ok(/Vocal booths - normally: Studio A · Studio B · Studio D/.test(t), 'the vocal-booth line is unchanged (A, B, D)');
ok(!/Record vocals in the room itself/.test(rt(OM)), '  (v228: no in-room line)');
const f = node(M, 'Rooms and Studios').parameters.filterByFormula.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
const q = a => new Function('$fromAI', 'return (' + f + ');')((k, d, ty, def) => k in a ? a[k] : def);
ok(q({ records_vocals_in_room: true }) === 'AND({Active / Bookable}, {Records Vocals In-Room})', 'tool: records_vocals_in_room -> the checkbox', q({ records_vocals_in_room: true }));
ok(q({ vocal_booth: true }) === 'AND({Active / Bookable}, {Vocal Booth})', 'tool: vocal_booth unchanged');
ok(q({ vocal_booth: true, records_vocals_in_room: true }) === 'AND({Active / Bookable}, OR({Vocal Booth}, {Records Vocals In-Room}))', 'tool: both asked -> either, not only D');
let threw = ''; try { q({}); } catch (e) { threw = e.message; } ok(/record vocals in-room/.test(threw), 'tool: nothing asked -> says what it can look up');
ok(/records_vocals_in_room true returns/.test(node(M, 'Rooms and Studios').parameters.toolDescription), 'tool description names it');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
