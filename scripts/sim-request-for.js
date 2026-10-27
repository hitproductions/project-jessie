#!/usr/bin/env node
// Jessie — Request Messages v5 (27 Oct, Howard): who a room request's booking is for ("Who is it for?" = Kristine, matched to a
// Booker) is told when the request opens and how it ended; the engineer / arranger once a request is booked (PENDING 126).
// Usage: node scripts/sim-request-for.js [request-messages v5]
const fs = require('fs');
const RM = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/request-messages-v5.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const js = RM.nodes.find(n => n.name === 'Render').parameters.jsCode;
if (!/function forOpen/.test(js)) { console.log('0 ok, 0 failed (an older build: v5 not in it)'); process.exit(0); }
const render = (mode, row, extra) => new Function('$', js)(n => ({ first: () => ({ json: { mode, row: JSON.stringify(row), extra: JSON.stringify(extra || {}) } }) })).map(i => i.json);
const HOWARD = 'U08V3CKDGJF', CAMY = 'U08JL17A50A', KRISTINE = 'U0KRIST1';
const pay = desc => JSON.stringify({ summary: 'M7 - Kristine', session_type: '', description: desc });
const MB = (o) => Object.assign({ 'Request ID': 'R7', 'Status': 'PENDING', 'Kind': 'MBOOTH', 'Requester': HOWARD, 'Requester Name': 'Howard Luistro',
  'Approver': 'U0ANA', 'Approver Name': 'Ana Cadelina', 'Room/Booth': 'M7', 'Req Start': '2027-10-28', 'Req End': '2027-10-29',
  'Incumbent Event Id': 'h1', 'Incumbent Title': 'M7 - Ana', 'Deadline': '2027-10-28T16:48:00+08:00',
  'Req Payload': pay('Booked by: Howard Luistro (for Kristine Trocino) | ref: ' + HOWARD + ' | team: ' + KRISTINE + ' | Type: Internal\nSType: M Booth'),
  'Messages': JSON.stringify({ m: [], inc: { id: 'h1', d: '2027-10-28', r: 'M7', t: 'M7 - Ana' } }) }, o || {});
const txt = o => JSON.stringify(o.blocks).replace(/\\n/g, '\n');

console.log('The request opens');
let out = render('open', MB());
const f = out.find(x => x.r === 'f');
ok(out.length === 3 && f && f.u === KRISTINE && f.op === 'post', 'requester, holder, and who it is for (Kristine) - three messages', out.map(x => x.r));
ok(f.channel === HOWARD && /Test: this is for Kristine Trocino/.test(txt(f)), 'while testing: to Howard, marked "Test: this is for Kristine Trocino"');
ok(/👋 \*Howard Luistro asked to use M7 for you\.\*/.test(txt(f)) && /\*Date:\* Thursday, October 28, 2027/.test(txt(f)) && /Ana Cadelina is being asked \(their standing hold\)\. You’ll hear here when it’s settled\./.test(txt(f))
   && !/cr_/.test(JSON.stringify(f.blocks)), 'the message: asked for you, the card, who is being asked - no request buttons', txt(f));
out = render('open', MB({ 'Req Payload': pay('Booked by: Howard Luistro (for Camy Caridad) | ref: ' + HOWARD + ' | team: ' + CAMY) }));
ok(out.find(x => x.r === 'f').channel === CAMY, 'someone on the QA roster (Camy) gets her own');
ok(!render('open', MB({ 'Req Payload': pay('Booked by: Howard Luistro | ref: ' + HOWARD + '\nSType: M Booth\n\nNotes:\nteam: U0X9 (for Someone)') })).some(x => x.r === 'f'),
   'no "for" on the first line (only in the note) -> nobody extra');
ok(!render('open', MB({ 'Req Payload': pay('Booked by: Howard Luistro (for Ana Cadelina) | ref: ' + HOWARD + ' | team: U0ANA') })).some(x => x.r === 'f'), 'the holder is never told twice');
ok(!render('open', MB({ 'Req Payload': pay('Booked by: Howard Luistro (for Kristine Trocino) | ref: ' + HOWARD + ' | team: U0A U0B') })).some(x => x.r === 'f'),
   'team: and the names do not match up -> nobody extra (never a guess)');

console.log('How it ended (her message updated)');
const stored = { m: [{ r: 'r', u: HOWARD, c: 'D1', t: '1.1' }, { r: 'a1', u: 'U0ANA', c: 'D1', t: '1.2' }, { r: 'f', u: KRISTINE, c: 'D1', t: '1.3' }], inc: { id: 'h1', d: '2027-10-28', r: 'M7', t: 'M7 - Ana' } };
const end = (status, extra) => render('end', MB({ Status: status, Messages: JSON.stringify(stored) }), extra).find(x => x.r === 'f');
let e = end('DONE', { how: 'holder', event: { id: 'ev9', title: 'M7 - Kristine' } });
ok(e.op === 'update' && e.ts === '1.3' && /✅ \*M7 is booked for you\* – Howard booked it\./.test(txt(e)) && /bk_change/.test(JSON.stringify(e.blocks)) && /"block_id":"bk_ev9"/.test(JSON.stringify(e.blocks)),
   'booked -> "M7 is booked for you – Howard booked it." with Change / Cancel', txt(e));
ok(/❌ \*Not booked\* – Ana Cadelina is keeping M7\./.test(txt(end('REJECTED', { how: 'kept' }))), 'kept -> "Not booked – Ana Cadelina is keeping M7."');
ok(/\*Not booked\* – Howard withdrew the request\./.test(txt(end('WITHDRAWN', { how: 'withdrawn' }))), 'withdrawn -> "Howard withdrew the request."');
ok(/⌛ \*Not booked\* – no answer by/.test(txt(end('EXPIRED', { how: 'sweep-expired' }))), 'no answer -> "Not booked – no answer by …"');

console.log('PENDING 126 - engineer / arranger of a booking placed by a request');
const PRE = (o) => MB(Object.assign({ Kind: 'PREEMPT', 'Room/Booth': 'Studio F', 'Req Start': '2027-10-28T10:00:00+08:00', 'Req End': '2027-10-28T12:00:00+08:00',
  'Approver': 'U0BK', 'Approver Name': 'Rico Gonzales', 'Approver 2': 'U0EN', 'Approver 2 Name': 'Daryl Reyes',
  'Req Payload': JSON.stringify({ summary: 'SONG / Jem Lim / DR x PL', session_type: 'Music Recording',
    description: 'Engineer: Daryl Reyes | Arranger: Pia Lopez | Booked by: Howard Luistro (for Camy Caridad) | ref: ' + HOWARD + ' | team: U0DR U0PL ' + CAMY + ' | Type: Advertising' }) }, o || {}));
const pre = (status, extra) => render('end', PRE({ Status: status, Messages: JSON.stringify({ m: [{ r: 'r', u: HOWARD, c: 'D1', t: '2.1' }], inc: {} }) }), extra);
let p = pre('DONE', { how: 'gave-up', event: { id: 'ev5', title: 'SONG / Jem Lim / DR x PL' } });
const t = p.filter(x => x.r === 't');
ok(t.length === 2 && t[0].u === 'U0DR' && /👋 \*Howard Luistro booked you as the engineer\.\*/.test(txt(t[0])) && t[1].u === 'U0PL' && /booked you as the arranger/.test(txt(t[1])) && t.every(x => x.op === 'post'),
   'booked through a request -> the engineer and the arranger told (posted once)', p.map(x => x.r + ':' + x.u));
ok(!pre('DONE', { how: 'gave-up' }).some(x => x.r === 't'), 'a redraw of a done request (no event handed over) -> not posted again');
ok(!pre('REJECTED', { how: 'kept' }).some(x => x.r === 't'), 'not booked -> the engineer / arranger are not told');
ok(render('open', PRE()).filter(x => x.r === 't').length === 0 && render('open', PRE()).find(x => x.r === 'f').u === CAMY, 'when it opens: only who it is for (Camy), not the engineer / arranger');

console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
