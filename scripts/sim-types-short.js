#!/usr/bin/env node
// Offline tests for Book Session v73 (types + short summary) - PENDING 69, 70, 71. Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-types-short.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v74.json'), OB = WF('imported/book-session-v72-imported.json');
const NOTE74 = !/self_engineer\) notes\.push/.test(code(B, 'Render Summary'));   // v74: the engineer note was removed
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const JEM = rec('Get Client');   // Jem Lim: Client Type External (not recoded yet), Booker Type Advertising Producer
const client = (name, types, bt) => [{ json: { id: 'recX', fields: { Name: name, 'Client Type': types, 'Booker Type': bt || '' } } }];
const go = (w, req, over = {}) => { const R = [{ json: { ...REQ0, ...req } }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], ...over };
  const $c = n => { if (n === 'When Executed by Another Workflow') return wrap(R); if (O[n]) return wrap(O[n]); const it = rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  if (c.verdict === 'REJECTED') return { c, s: '', o: {} };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(rec(n) || [{ json: {} }]);
  const o = new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json;
  return { c, s: o.summary_text || '', o, F: (() => { try { return JSON.parse(o.prep_payload).F; } catch (e) { return {}; } })() }; };
const by = (name, ref = 'U08V3CKDGJF', eng = 'Drey') => 'Engineer: ' + eng + ' | Booked by: ' + name + ' | ref: ' + ref;
const BASE = { summary: 'QATYPE / DR', client: '', engineer: 'Drey', session_type: 'VO Recording', rooms: 'Studio 8', bookingType: '',
  description: by('Howard Luistro'), requester_text: 'book qatype studio 8 nov 18 2-4pm vo recording, engineer drey', asked_text: '' };

console.log('The short summary (PENDING 69)');
let r = go(B, { ...BASE, summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim' }, { 'Get Client': JEM });
ok(r.s === '*QATYPE / Jem Lim / DR*\n*Date:* Thursday, November 18, 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8\n\nConfirm to book.', 'title, Date, Time, Room and the confirmation - nothing else, no check code', r.s);
ok(r.F.Client === 'Jem Lim' && /Daryl Reyes/.test(r.F.Engineer) && r.F['Session Type'] === 'VO Recording' && r.F['Booking Type'] === 'Advertising' && r.F.Department === 'Audio Post' && /^Howard Luistro/.test(r.F['Booked by']),
   'every other detail is stored with it (client, engineer, session type, type, department, booked by)', r.F);
ok(/^prep-[0-9a-f]{8}$/.test(r.o.prep_key) && JSON.parse(r.o.prep_payload).ref === 'U08V3CKDGJF', 'stored under prep-<fingerprint of the requester + the four lines>', r.o.prep_key);
ok(/_check /.test(go(OB, { ...BASE, summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim' }, { 'Get Client': JEM }).s), '  (v72: every line and a printed check code)');
const r2 = go(B, { ...BASE, summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim', requester_text: BASE.requester_text + ', client jem lim, tvc' }, { 'Get Client': JEM });
ok(r2.o.prep_key === r.o.prep_key, 'the key is over the requester and the visible lines (the same booking prepared again -> the same key; the latest wins)');
ok(go(B, { ...BASE, summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim', description: by('Ana Cadelina', 'U0BGQABJY11') }, { 'Get Client': JEM }).o.prep_key !== r.o.prep_key, '... and another requester\'s identical summary has another key');

console.log('Booking type (PENDING 70)');
ok(r.c.final_booking_type === 'Advertising', 'a producer client (Jem Lim) -> Advertising - her record still says External, which is not used');
const T = (txt, extra = {}, over = {}) => go(B, { ...BASE, requester_text: txt + ', no client', ...extra }, over).c.final_booking_type;
ok(T('book qatype studio 8 nov 18 2-4pm, my own project') === 'Personal', '"my own project" -> Personal');
ok(T('book qatype studio 8 nov 18 2-4pm, for the digicon') === 'Internal', '"digicon" -> Internal');
ok(T('book qatype studio 8 nov 18 2-4pm, tvc') === 'Advertising', '"tvc" -> Advertising');
ok(T('book qatype studio 8 nov 18 2-4pm, film dubbing') === 'Entertainment', '"film dubbing" -> Entertainment');
ok(T('book qatype studio 8 nov 18 2-4pm, external') === 'Advertising', '"external" (the old word) -> the department\'s client type (Audio Post: Advertising)');
ok(T('book qatype studio 8 nov 18 2-4pm') === 'Advertising', 'nothing said, a Post engineer booking -> Advertising (department default)');
ok(T('book qatype studio 1', { session_type: 'Localization Dubbing', summary: 'NET-QA / DR', rooms: 'Studio 1' }) === 'Entertainment', 'a Localization session -> Entertainment, whoever books it');
ok(T('book', { description: by('Ana Cadelina', 'U0BGQABJY11') }) === 'Internal', 'a Business Development booker -> Internal');
ok(T('book', { description: by('Cristel Cube', 'U0XXX') }) === 'Entertainment', 'a Localization booker -> Entertainment');
ok(go(B, { ...BASE, summary: 'QATYPE / Acme / DR', client: 'Acme' }, { 'Get Client': client('Acme', ['Entertainment']) }).c.final_booking_type === 'Entertainment', 'the client\'s record wins over the department (Entertainment)');
r = go(B, { ...BASE, summary: 'QATYPE / Acme / DR', client: 'Acme' }, { 'Get Client': client('Acme', ['Advertising', 'Personal']) });
ok(r.c.reason === 'NEED_BOOKING_TYPE' && /"Advertising or personal\?"/.test(r.c.human), 'a record with two types -> "Advertising or personal?"', r.c.human);
ok(go(B, { ...BASE, bookingType: 'Personal', requester_text: BASE.requester_text + ', no client' }).c.final_booking_type === 'Advertising', 'a type the model sent but nobody said is not used');
r = go(B, { ...BASE, description: by('BP Valenzuela', 'U0BP'), engineer: 'Drey', session_type: 'Music Vocal Recording', rooms: 'Studio F', requester_text: 'book studio f nov 18 2-4pm, music vocal recording, engineer drey, arranger me' });
ok(r.c.reason === 'NEED_BOOKING_TYPE' && /"Client work or your own project\?"/.test(r.c.human), 'an arranger with no client -> "Client work or your own project?"', r.c.human);
ok(go(B, { ...BASE, description: by('BP Valenzuela', 'U0BP'), session_type: 'Music Vocal Recording', rooms: 'Studio F', requester_text: 'book studio f nov 18 2-4pm, engineer drey\nmy own project' }).c.final_booking_type === 'Personal', '... "my own project" -> Personal');
r = go(B, { ...BASE, description: by('BP Valenzuela', 'U0BP'), session_type: 'Music Vocal Recording', rooms: 'Studio F', requester_text: 'book studio f nov 18 2-4pm, engineer drey\nclient work' });
ok(r.c.final_booking_type === 'Advertising' || r.c.reason === 'NEED_CLIENT', '... "client work" -> Advertising (and then the client is asked)', [r.c.final_booking_type, r.c.reason]);
r = go(B, { summary: 'LIKHA - Post', client: '', session_type: '', rooms: 'Likha', description: 'Booked by: Howard Luistro | ref: U08V3CKDGJF', requester_text: 'book likha for a meeting nov 18 2-4pm', engineer: '' });
ok(r.c.final_booking_type === 'Internal' && /^\*LIKHA - Post\*\n\*Date:\*/.test(r.s), 'a conference room, no client -> Internal, the short card', [r.c.final_booking_type, r.s]);
ok(go(B, { ...BASE, session_type: 'Meeting', rooms: 'Likha', summary: 'QAMEET / DR', requester_text: 'book likha nov 18 2-4pm meeting' }).c.final_booking_type === 'Internal', 'a Meeting session -> Internal (not the Post default)');
ok(/Type: Advertising/.test(go(B, { ...BASE, summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim' }, { 'Get Client': JEM }).c.final_description), 'the calendar event carries "Type: Advertising"');

console.log('The client question');
r = go(B, { ...BASE });
ok(r.c.reason === 'NEED_CLIENT' && /"Who’s the client\? \(or \\"none\\"\)"/.test(r.c.human), 'client work, no client named -> "Who’s the client? (or "none")"', r.c.human);
ok(go(B, { ...BASE, requester_text: BASE.requester_text + '\nnone' }).c.verdict === 'CLEAR', '"none" -> no client, booked as is');
ok(go(B, { ...BASE, asked_text: 'Who’s the client? (or "none")' }).c.reason !== 'NEED_CLIENT', 'asked once already -> not asked again');
ok(go(B, { ...BASE, description: by('Ana Cadelina', 'U0BGQABJY11') }).c.reason !== 'NEED_CLIENT', 'Internal -> no client question');

console.log('Series dates (never asked)');
r = go(B, { ...BASE, mode: '', series: true, confirmed: true, bookingType: 'External', summary: 'QATYPE / Jem Lim / DR', client: 'Jem Lim' }, { 'Get Client': JEM });
ok(r.c.final_booking_type === 'Advertising' && /Type: Advertising/.test(r.c.final_description || ''), 'a series date with the old "External" -> Advertising', [r.c.final_booking_type, r.c.reason]);

console.log('"me" as the engineer (PENDING 71)');
r = go(B, { ...BASE, engineer: 'me', description: by('Howard Luistro', 'U08V3CKDGJF', 'me'), requester_text: BASE.requester_text + ', no client' });
ok(/Howard Luistro/.test(r.F.Engineer) && !/down as the engineer/.test(r.s), '"me" -> Howard Luistro, and no "you\'re down as the engineer" note', [r.F.Engineer, r.s]);
r = go(B, { ...BASE, engineer: 'Howard Luistro', description: by('Howard Luistro', 'U08V3CKDGJF', 'Howard Luistro'), requester_text: 'book studio 8 nov 18 2-4pm vo, no client\nme' });
ok(!/down as the engineer/.test(r.s), 'a bare "me" answer -> no note');
r = go(B, { ...BASE, engineer: '', description: 'Booked by: Howard Luistro | ref: U08V3CKDGJF', requester_text: 'book studio 8 nov 18 2-4pm vo, no client' });
ok(/Howard Luistro/.test(r.F.Engineer) && /\/ HL\*/.test(r.s) && (NOTE74 ? !/down as the engineer/.test(r.s) : /You’re down as the engineer\./.test(r.s)), 'nobody named -> Howard Luistro engineers (v74: no note - the title\'s initials say who)', [r.F.Engineer, r.s]);
{ const ANG = { json: { id: 'recA', fields: { Name: 'Angela Dela Calzada', Notes: ' Goes by Anj', 'Client Type': ['Advertising'], 'Booker Type': 'Advertising Producer' } } };
  r = go(B, { summary: 'DASHING / Angelo Villegas / AV', client: 'Angelo Villegas', engineer: 'Angelo Villegas', session_type: 'VO Recording', rooms: 'Studio 8', bookingType: '',
    description: 'Engineer: Angelo Villegas | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF', requester_text: 'book studio 8 for me nov 18 3-6pm, project dashing for anj\nangela', asked_text: 'Just to check - by Anj, do you mean Angelo Villegas (Music Arranger) or Angela Dela Calzada (Advertising Producer, a client)?' }, { 'Client Aliases': [ANG] });
  ok(r.c.verdict === 'CLEAR' && /Howard Luistro/.test(r.F.Engineer) && r.F.Client === 'Angela Dela Calzada', 'the live DASHING case: "angela" -> you engineer, not "Who is the engineer?"', [r.c.reason, r.F.Engineer, r.s]); }

console.log('Notes and questions, short');
r = go(B, { ...BASE, start_iso: '2027-11-18T09:00:00+08:00', end_iso: '2027-11-18T18:00:00+08:00', requester_text: 'book qatype studio 8 nov 18 9am-6pm vo recording, engineer drey, no client' });
ok(/Heads up: 9 hours is longer than VO Recording usually runs \(1 hour – 3 hours\)\./.test(r.s), 'the length heads-up', r.s);
const arr = code(B, 'Check Conflicts');
ok(/Who\\u2019s the arranger\?/.test(arr) && /Ask exactly this: "Which day\?"/.test(arr) && /"Who\\u2019s engineering\?"/.test(arr), 'shorter arranger / date / engineer questions');

console.log('Wiring');
const to = n => ((((B.connections[n] || {}).main || [])[0]) || []).map(t => t.node);
ok(JSON.stringify(to('Render Summary')) === '["Store Prepared"]' && JSON.stringify(to('Store Prepared')) === '["Prepared Out"]', 'Render Summary -> Store Prepared -> Prepared Out');
const SP = B.nodes.find(n => n.name === 'Store Prepared');
ok(SP.parameters.operation === 'upsert' && SP.parameters.dataTableId.value === 'CsdJhgDxCsqq9K9j' && SP.onError === 'continueRegularOutput' && SP.alwaysOutputData && SP.executeOnce, 'Store Prepared: upsert into the reference-cache table, never fails the turn');
{ const po = new Function('$', '$input', code(B, 'Prepared Out'))(n => n === 'Render Summary' ? wrap([{ json: { status: 'PREPARED', summary_text: 'x' } }]) : wrap([{ json: { cache_key: 'prep-1' } }]), wrap([]));
  ok(po[0].json.status === 'PREPARED' && po[0].json.summary_text === 'x' && po[0].json.prep_stored === true, 'Prepared Out hands Render Summary\'s result back to main'); }

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
