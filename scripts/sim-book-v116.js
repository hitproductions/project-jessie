#!/usr/bin/env node
// Book Session v116 offline (20 Oct): no Airtable client lookups when there is no client - Localization / QC, Post Processing,
// Meeting, Event, M booths, and any booking with no client named that is not booked for someone. Found on 20 Oct 20:36: Client
// Aliases hung 2 min 9 s on a Localization Dubbing booking with no client.
// Usage: node scripts/sim-book-v116.js [book-session v116]
const fs = require('fs');
const B = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/book-session-v116.json', 'utf8'));
if (!/v116 \(20 Oct\): nothing to look up/.test(JSON.stringify(B.nodes))) { console.log('0 ok, 0 failed (v116 on; this build is older)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const code = n => B.nodes.find(x => x.name === n).parameters.jsCode;
const wrap = rows => ({ first: () => rows[0], all: () => rows });
const cache = REQ => new Function('$', code('Client Cache'))(n => wrap([{ json: REQ }]))[0].json;
const D = ' | Booked by: Howard Luistro | ref: U1';
const skip = [
  ['Localization Dubbing', { summary: 'NET-CMA / JL', rooms: 'Studio 6, Studio A' }],
  ['Localization Dubbing, even with a client passed', { summary: 'NET-CMA / JL', client: 'Netflix' }],
  ['QC', { summary: 'ABC-01 / JL', rooms: 'Studio 3' }],
  ['Post Processing', { summary: 'TRAILER / DD', rooms: 'Studio E' }],
  ['Meeting', { summary: 'LIKHA - Weekly sync', rooms: 'Likha' }],
  ['Event', { summary: 'LOBBY - Launch', rooms: 'Lobby' }],
  ['Meeting booked for someone', { summary: 'SALIN - Sync', rooms: 'Salin', description: 'Booked by: Howard Luistro (for Japs Concepcion) | ref: U1' }],
];
for (const [label, extra] of skip) {
  const st = label.split(',')[0].replace(' booked for someone', '');
  const r = cache(Object.assign({ mode: 'prepare', session_type: st, description: 'x' + D }, extra));
  ok(r.use === true && Array.isArray(r.gc) && !r.gc.length && Array.isArray(r.an) && r.none, label + ' -> no client lookups', r);
}
let r = cache({ mode: 'prepare', session_type: '', rooms: 'M4', summary: 'M4 - Howard', description: 'x' + D });
ok(r.use && r.none, 'an M booth (no type, room M4) -> no client lookups');
r = cache({ mode: 'prepare', session_type: 'VO Recording', rooms: 'Studio 7', summary: 'ORANGE / HL', description: 'x' + D });
ok(r.use && r.none, 'VO Recording with no client named -> no client lookups');
r = cache({ mode: 'prepare', session_type: 'VO Recording', client: 'Jem Lim', summary: 'ORANGE / Jem Lim / HL', description: 'x' + D });
ok(r.use === false, 'VO Recording for Jem Lim -> the lookups run, as before', r);
r = cache({ mode: 'prepare', session_type: 'VO Recording', summary: 'ORANGE / Jem Lim / HL', description: 'x' + D });
ok(r.use === false, 'a client only in the title -> the lookups run');
r = cache({ mode: 'prepare', session_type: 'VO Recording', summary: 'ORANGE / HL', description: 'Booked by: Howard Luistro (for Anj) | ref: U1' });
ok(r.use === false, 'no client but booked for someone (a nickname may be a client\'s) -> the lookups run');
r = cache({ mode: 'prepare', session_type: '', rooms: 'Studio 7', summary: 'ORANGE / Acme / HL', description: 'x' + D });
ok(r.use === false, 'no type but a client (an old chat booking) -> the lookups run');
const gc = [{ id: 'rec1', fields: { Name: 'Jem Lim' } }];
r = cache({ mode: '', session_type: 'VO Recording', client: 'Jem Lim', summary: 'O / Jem Lim / HL', client_cache: JSON.stringify({ v: 1, at: new Date().toISOString(), client: 'Jem Lim', gc }) });
ok(r.use && r.gc.length === 1 && !r.none, 'a booking run with a fresh cache -> the cached rows (v112, unchanged)');
r = cache({ mode: '', session_type: 'Localization Dubbing', summary: 'NET-CMA / JL', client_cache: '' });
ok(r.use && r.none, 'the Localization booking run (no cache: the prepare run skipped) -> no lookups either');

console.log('every reader copes with the skip');
const CC = code('Check Conflicts');
const re = /\(\(\(\) => \{ try \{ const c = \$\('Client Cache'\)\.first\(\)\.json; if \(c && c\.use && Array\.isArray\(c\.(gc|al|an)\)\) return c\.\1\.map\(j => \(\{ json: j \}\)\); \} catch \(e\) \{\} return \$\('(Get Client|Client Aliases|All Client Names)'\)\.all\(\); \}\)\(\)\)/g;
const reads = [...CC.matchAll(re)];
ok(reads.length >= 5 && ['gc', 'al', 'an'].every(k => reads.some(m => m[1] === k)), 'Check Conflicts reads Get Client / Client Aliases / All Client Names only through the cache switch (' + reads.length + ')');
const notRun = n => n === 'Client Cache' ? wrap([{ json: { use: true, gc: [], al: [], an: [], none: true } }]) : { first: () => { throw new Error(n + ' not executed'); }, all: () => { throw new Error(n + ' not executed'); } };
for (const m of reads.slice(0, 6)) { let rows = null, err = ''; try { rows = new Function('$', 'return ' + m[0])(notRun); } catch (e) { err = e.message; } ok(Array.isArray(rows) && rows.length === 0, 'cache "none": ' + m[2] + ' -> no rows, no error', err); }
const one = CC.match(/\(\(\(\) => \{ try \{ const c = \$\('Client Cache'\)\.first\(\)\.json; if \(c && c\.use && Array\.isArray\(c\.gc\)\) return \{ json: c\.gc\[0\] \|\| \{\} \}; \} catch \(e\) \{\} return \$\('Get Client'\)\.first\(\); \}\)\(\)\)/);
ok(!one || JSON.stringify(new Function('$', 'return ' + one[0])(notRun)) === '{"json":{}}', 'the single-row read -> an empty row');
for (const n of ['Render Summary', 'Prepared Out', 'Build Log Row']) {
  const t = code(n); const plain = (t.match(/\$\('(Get Client|Client Aliases|All Client Names)'\)/g) || []).length;
  ok(plain === 0 || /try \{[^}]*\$\('(Get Client|Client Aliases|All Client Names)'\)/.test(t) || /Array\.isArray\(c\.gc\)\) return c\.gc\.map/.test(t), n + ': its reads of the lookups are inside try or through the cache switch');
}
const C = B.connections, nx = k => ((C[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
ok(nx('Client Cache') === 'Cached?' && nx('Cached?') === 'Get Events In Window | Get Client', 'Cached? (yes) goes straight to the calendar read');
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
