#!/usr/bin/env node
// Offline tests for Book Session v84 + main v211 (live 2 Oct: "THANK / ruff lopez / HL x BPV", "DIGICON / Sir Vic / HL",
// "M3 - Howard Luistro", "Engineer: ... (Post Engineer)", and a time picked instead of asked).
//   node scripts/sim-names-asks.js <book-session-prepare-execution.json> <main-execution.json>
// Offline tests for Book Session v73 (types + short summary) - PENDING 69, 70, 71. Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-types-short.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v84.json'), OB = WF('imported/book-session-v72-imported.json');
const NOTE74 = !/self_engineer\) notes\.push/.test(code(B, 'Render Summary'));   // v74: the engineer note was removed
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const JEM = rec('Get Client');   // Jem Lim: Client Type External (not recoded yet), Booker Type Advertising Producer
const client = (name, types, bt) => [{ json: { id: 'recX', fields: { Name: name, 'Client Type': types, 'Booker Type': bt || '' } } }];
const go = (w, req, over = {}) => { const _r80 = { ...REQ0, ...req };
  // v80: a session type the requester did not name is asked, and an arranger colleague is asked "on behalf or own?" -
  // these older cases name the type (and, for an arranger colleague, "on his behalf") so they test what they were for.
  if (/NEED_SESSION_TYPE/.test(code(w, 'Check Conflicts')) && _r80.session_type && String(_r80.requester_text || '').trim() && !req.__keep80) {
    _r80.requester_text = String(_r80.requester_text) + '\n' + _r80.session_type;
    if (/\(for\s+(?:Angelo|Joaquin|Brian|BP|Robbie|Peter|Arnold)\b/i.test(String(_r80.description || '')) && !/\b(own|behalf)\b/i.test(_r80.requester_text)) _r80.requester_text += '\non his behalf';
  }
  // v86: the project is required - older cases name the title's project so they test what they were written for
  if (/v86 \(live 2 Oct 13:02/.test(code(w, 'Check Conflicts')) && !req.__keep86 && String(_r80.requester_text || '').trim() && String(_r80.summary || '').indexOf(' / ') !== -1) {
    const _p0 = String(_r80.summary).split(' / ')[0].trim();
    if (_p0 && (' ' + String(_r80.requester_text).toLowerCase().replace(/[^a-z0-9]+/g, ' ') + ' ').indexOf(' ' + _p0.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() + ' ') === -1) _r80.requester_text += '\nproject ' + _p0.toLowerCase();
  }
  const R = [{ json: _r80 }];
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


const OLD = WF('book-session-v83.json'), M = WF(process.env.MAIN || 'project-jessie-v211.json'), OM = WF('project-jessie-v210.json');
const relay = h => { const m = String(h || '').match(/(?:Ask exactly this|naming both)[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const VIC = [{ json: { id: 'recV', fields: { Name: 'Vic Icasas', 'Client Type': ['Personal'] } } }];
const TXT = BASE.requester_text;

console.log('Client names');
let r = go(B, { ...BASE, summary: 'DIGICON / Sir Vic / DR', client: 'Sir Vic', requester_text: TXT + ', client sir vic, digicon' }, { 'Get Client': VIC });
ok(/^DIGICON \/ Vic Icasas \//.test(r.c.final_summary || '') && r.c.final_client === 'Vic Icasas', '"Sir Vic" -> Vic Icasas (on record)', [r.c.reason, r.c.final_summary, r.c.final_client]);
r = go(B, { ...BASE, summary: 'THANK YOU / ruff lopez / DR', client: 'ruff lopez', requester_text: TXT + ', client ruff lopez' }, { 'Get Client': [{ json: {} }] });
ok(/^THANK YOU \/ Ruff Lopez \//.test(r.c.final_summary || '') && r.c.final_client === 'Ruff Lopez', 'new client "ruff lopez" -> Ruff Lopez', [r.c.reason, r.c.final_summary]);
ok(/^THANK YOU \/ ruff lopez/.test(go(OLD, { ...BASE, summary: 'THANK YOU / ruff lopez / DR', client: 'ruff lopez', requester_text: TXT + ', client ruff lopez' }, { 'Get Client': [{ json: {} }] }).c.final_summary || ''), '  (v83: as typed)');
r = go(B, { ...BASE, summary: 'QAX / DCVI / DR', client: 'DCVI', requester_text: TXT + ', client DCVI' }, { 'Get Client': [{ json: {} }] });
ok(/\/ DCVI \//.test(r.c.final_summary || ''), 'a name typed with capitals is left as typed (DCVI)', r.c.final_summary);
r = go(B, { ...BASE, summary: 'QAX / ms. jem / DR', client: 'ms. jem', requester_text: TXT + ', client ms. jem' }, { 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim', 'Client Type': ['Advertising'] } } }] });
ok(/\/ Jem Lim \//.test(r.c.final_summary || ''), '"ms. jem" -> Jem Lim (one client with that first name)', r.c.final_summary);
const GC = W => W.nodes.find(x => x.name === 'Get Client').parameters.filterByFormula;
const gcv = (W, client) => new Function('$', 'return ' + GC(W).replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''))(n => wrap([{ json: { client, summary: '' } }]));
ok(/LOWER\('vic'\)/.test(gcv(B, 'Sir Vic')) && /LOWER\('sir vic'\)/.test(gcv(OLD, 'Sir Vic')), 'Get Client searches "vic" (was "sir vic")', gcv(B, 'Sir Vic'));

console.log('Event description and M booth title');
r = go(B, { ...BASE, client: 'Jem Lim', summary: 'QAX / Jem Lim / DR', requester_text: TXT + ', client jem lim' }, { 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim', 'Client Type': ['Advertising'] } } }] });
ok(/Engineer: Daryl Reyes( \||$)/.test(r.c.final_description || '') && !/\(\w+ Engineer\)/.test(r.c.final_description || ''), '"Engineer: Daryl Reyes" - no "(Music Engineer)"', r.c.final_description);
r = go(B, { ...BASE, summary: 'M3 - Howard Luistro', rooms: 'M3', session_type: '', engineer: '', client: '', all_day: true, start_iso: '2027-11-18', end_iso: '2027-11-19', requester_text: 'book m3 nov 18', description: 'Booked by: Howard Luistro | ref: U08V3CKDGJF' });
ok((r.c.final_summary || '') === 'M3 - Howard', 'M booth -> "M3 - Howard"', [r.c.reason, r.c.final_summary, r.c.human]);

console.log('Ask for what is missing in one message');
const ASK = (txt, extra = {}) => go(B, { ...BASE, requester_text: txt, __keep80: true, ...extra }).c;
let c = ASK('book studio 8 for project CATS, no client', { session_type: 'VO Recording', expected_date: '' });
ok(c.reason === 'NEED_SESSION_TYPE' && relay(c.human) === 'What kind of session is this? And which day and time?', 'no type, day or time -> "What kind of session is this? And which day and time?"', [c.reason, relay(c.human)]);
c = ASK('book studio 8 for project CATS, vo recording, no client', { expected_date: '' });
ok(c.reason === 'MISSING_DATE' && relay(c.human) === 'Which day and time?', 'type named, no day or time -> "Which day and time?"', [c.reason, relay(c.human)]);
c = ASK('book studio 8 nov 18 for project CATS, vo recording, no client');
ok(c.reason === 'NEED_TIME' && relay(c.human) === 'What time?', 'day named, no time -> "What time?" (no time picked)', [c.reason, relay(c.human)]);
c = ASK('book studio 8 nov 18 2-4pm for project CATS, no client', { session_type: 'VO Recording' });
ok(c.reason === 'NEED_SESSION_TYPE' && relay(c.human) === 'What kind of session is this?', 'day and time named -> only the type asked', relay(c.human));
c = ASK('book studio 8 nov 18 2-4pm for project CATS, vo recording, no client');
ok(c.verdict === 'CLEAR', 'all given -> the card', [c.reason, c.human]);
ok(go(B, { ...BASE, rooms: 'M3', session_type: '', all_day: true, summary: 'M3 - Howard Luistro', requester_text: 'book m3 nov 18', description: 'Booked by: Howard Luistro | ref: U08V3CKDGJF' }).c.reason !== 'NEED_TIME', 'an M booth hold needs no time');

console.log('main v211 - multi-word project');
const run2 = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
const rec2 = n => run2[n] ? (((run2[n][0].data || {}).main || [[]])[0] || []) : null;
const bfm = (w, txt) => { const h = [{ json: { user: 'U08V3CKDGJF', text: txt, ts: '1790841600.000100' } }];
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap(h) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(rec2(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
for (const [txt, want] of [['book project thank you for ruff lopez tomorrow 8-10pm', 'thank you'], ['book project thank you tomorrow 8-10pm', 'thank you'],
    ['book studio c project thank you studio c 8pm', 'thank you'], ['project thank you vo recording tomorrow', 'thank you'], ['project blue sky client jem lim', 'blue sky'],
    ['book project cats please', 'cats'], ['book project CATS tomorrow', 'CATS'], ['project ORANGE soda tomorrow', 'ORANGE'], ['project dashing with drey at 3pm', 'dashing']])
  ok(bfm(M, txt).project === want, JSON.stringify(txt) + ' -> project "' + want + '"', bfm(M, txt).project);
ok(bfm(OM, 'book project thank you for ruff lopez tomorrow 8-10pm').project === 'thank', '  (v210: "thank")');
const sumX = (W, b, model) => { const e = W.nodes.find(x => x.name === 'Prepare Booking').parameters.workflowInputs.value.summary;
  return new Function('$', '$fromAI', 'return ' + e.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, ''))(n => wrap([{ json: b }]), () => model); };
const B1 = { project: 'thank you', client: 'ruff lopez', saidWords: 'book project thank you for ruff lopez tomorrow 8 10pm', offeredWords: '' };
ok(sumX(M, B1, 'THANK / ruff lopez / HL x BPV') === 'THANK YOU / ruff lopez / HL x BPV', 'model title "THANK" -> "THANK YOU"', sumX(M, B1, 'THANK / ruff lopez / HL x BPV'));
ok(sumX(OM, B1, 'THANK / ruff lopez / HL x BPV') === 'THANK / ruff lopez / HL x BPV', '  (v210: "THANK" kept)');
ok(sumX(M, { ...B1, project: 'cats' }, 'CATS / HL') === 'CATS / HL', 'a whole project stays as it is');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
