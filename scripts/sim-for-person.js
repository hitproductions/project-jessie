#!/usr/bin/env node
// Offline tests for Book Session v70 (for-person fix) and main v196 (client nickname search) - PENDING 65.
// Live QA 30 Sep 09:30 PHT: "book orange studio 7 for anj" -> engineer = client = Angelo Villegas; and "Anj" is also
// Angela Dela Calzada, a client. Check Conflicts + Render Summary run on a real prepare run's inputs (29 Sep exec 16681).
//   node scripts/sim-for-person.js <book-session-prepare-execution.json> [<main-execution.json>]   (29 Sep exec 16681, 16685)
const fs = require('fs'), path = require('path');
const FULL = require('./lib-full-summary.js');   // v73: the stored fields as the old summary lines
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v70.json'), OB = WF('imported/book-session-v69-imported.json');
const V73 = /__decideType/.test(code(B, 'Check Conflicts'));   // Book Session v73: an engineer requester engineers; client work asks for the client
const M = WF(process.env.MAIN || 'project-jessie-v196.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const REQ0 = rec('When Executed by Another Workflow')[0].json;
const ANGELA = { json: { id: 'recwol21IzBHIhuCE', fields: { Name: 'Angela Dela Calzada', Notes: ' Goes by Anj', 'Client Type': ['External'], 'Booker Type': 'Advertising Producer' } } };
const go = (w, req, over = {}) => { const _r80 = { ...REQ0, ...req };
  // v80: a session type the requester did not name is asked, and an arranger colleague is asked "on behalf or own?" -
  // these older cases name the type (and, for an arranger colleague, "on his behalf") so they test what they were for.
  if (/NEED_SESSION_TYPE/.test(code(w, 'Check Conflicts')) && _r80.session_type && String(_r80.requester_text || '').trim() && !req.__keep80) {
    _r80.requester_text = String(_r80.requester_text) + '\n' + _r80.session_type;
    if (/\(for\s+(?:Angelo|Joaquin|Brian|BP|Robbie|Peter|Arnold)\b/i.test(String(_r80.description || '')) && !/\b(own|behalf)\b/i.test(_r80.requester_text)) _r80.requester_text += '\non his behalf';
  }
  // v84: a missing time is asked - these older cases name one so they test what they were written for
  if (/v84 \(decided 2 Oct\)/.test(code(w, 'Check Conflicts')) && String(_r80.requester_text || '').trim() && !req.__keep80
      && !/\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b|\b\d{1,2}\s*(?:-|to)\s*\d{1,2}\b|\ball day\b/i.test(_r80.requester_text)) _r80.requester_text += '\n2-4pm';
  // v86: the project is required - older cases name the title's project so they test what they were written for
  if (/v86 \(live 2 Oct 13:02/.test(code(w, 'Check Conflicts')) && !req.__keep86 && String(_r80.requester_text || '').trim() && String(_r80.summary || '').indexOf(' / ') !== -1) {
    const _p0 = String(_r80.summary).split(' / ')[0].trim();
    if (_p0 && (' ' + String(_r80.requester_text).toLowerCase().replace(/[^a-z0-9]+/g, ' ') + ' ').indexOf(' ' + _p0.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() + ' ') === -1) _r80.requester_text += '\nproject ' + _p0.toLowerCase();
  }
  const R = [{ json: _r80 }];
  const O = { 'Get Client': [{ json: {} }], 'Client Aliases': [ANGELA], ...over };
  const $c = n => { if (n === 'When Executed by Another Workflow') return wrap(R); if (O[n]) return wrap(O[n]); const it = rec(n); if (!it) throw new Error('unexecuted ' + n); return wrap(it); };
  const c = new Function('$', '$input', '$getWorkflowStaticData', code(w, 'Check Conflicts'))($c, wrap([{ json: { items: [] } }]), () => ({}))[0].json;
  if (c.verdict === 'REJECTED') return { c, s: '' };
  const $r = n => n === 'When Executed by Another Workflow' ? wrap(R) : n === 'Check Conflicts' ? wrap([{ json: c }]) : n === 'Decide Preempt' ? (() => { throw 1; })() : O[n] ? wrap(O[n]) : wrap(rec(n) || [{ json: {} }]);
  return { c, s: FULL(new Function('$', '$input', code(w, 'Render Summary'))($r, wrap([{ json: c }]))[0].json, c) }; };
const ASK = 'Just to check - by Anj, do you mean Angelo Villegas (Music Arranger) or Angela Dela Calzada (Advertising Producer, a client)?';
const LIVE = { summary: 'ORANGE / Angelo Villegas / AV', client: 'Angelo Villegas', engineer: 'Angelo Villegas', bookingType: '', session_type: 'VO Recording', rooms: 'Studio 7',
  description: 'Engineer: Angelo Villegas | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF',
  requester_text: 'book orange studio 7 for anj', asked_text: '' };

console.log('The live case - "for anj", and Anj is two people');
let r = go(B, LIVE);
ok(r.c.reason === 'AMBIGUOUS_PERSON' && r.c.human.indexOf('"' + ASK + '"') !== -1, 'asks: "' + ASK + '"', r.c);
ok(go(OB, LIVE).c.reason !== 'AMBIGUOUS_PERSON', '  (v69: never asked - went on with Angelo Villegas as engineer and client)', go(OB, LIVE).c.reason);
r = go(B, { ...LIVE, requester_text: 'book orange studio 7 for anj, no client' });
ok(r.c.reason === 'AMBIGUOUS_PERSON', '"no client" is not an answer to which Anj', r.c.reason);

console.log('They meant the producer');
for (const ans of ['angela', 'the producer', 'Angela Dela Calzada', 'the client']) {
  r = go(B, { ...LIVE, requester_text: 'book orange studio 7 for anj\n' + ans, asked_text: ASK });
  ok(V73 ? (r.c.verdict === 'CLEAR' && /Howard Luistro/.test(r.s.match(/\*Engineer:\* ([^\n]+)/)[1]) && /\*Client:\* Angela Dela Calzada/.test(r.s)) : (r.c.reason === 'NEED_ENGINEER' && /The client is Angela Dela Calzada/.test(r.c.human) && /"Who is the engineer for this session\?"/.test(r.c.human)),
     '"' + ans + '" -> the client is Angela; Angelo taken out of the engineer slot, "Who is the engineer for this session?"', r.c); }
r = go(B, { ...LIVE, engineer: 'Drey', description: 'Engineer: Drey | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF',
  requester_text: 'book orange studio 7 for anj\nangela\ndrey', asked_text: 'Who is the engineer for this session?' });
ok(/^\*ORANGE \/ Angela Dela Calzada \/ DR\*/.test(r.s) && /\*Client:\* Angela Dela Calzada/.test(r.s) && (V73 ? /\*Booking Type:\* Advertising/ : /\*Booking Type:\* External/).test(r.s)
   && /\*Booked by:\* Howard Luistro\n/.test(r.s) && !/\(for /.test(r.s) && !/not in the client list/i.test(r.s),
   'then "drey" -> ORANGE / Angela Dela Calzada / DR, her Client Type (External), Booked by with no "(for ...)", not a new client', r.s || r.c);

const V80 = /NEED_SESSION_TYPE/.test(code(B, 'Check Conflicts'));   // v80: on behalf -> no engineer default, "Who’s the engineer?"
console.log('They meant the colleague');
for (const ans of ['angelo', 'the arranger', 'Angelo Villegas']) {
  r = go(B, { ...LIVE, requester_text: 'book orange studio 7 for anj\n' + ans, asked_text: ASK });
  ok(V80 ? (r.c.reason === 'NEED_ENGINEER' && /"Who’s the engineer\?"/.test(r.c.human)) : V73 ? (r.c.reason === 'NEED_CLIENT') : (r.c.reason === 'NEED_ENGINEER' && /"Who is the engineer for this session\? \(Angelo is who it is booked for, a Music Arranger\)"/.test(r.c.human)),
     '"' + ans + '" -> a Music Arranger is not the engineer: "Who is the engineer for this session? (Angelo is who it is booked for ...)"', r.c); }
r = go(B, { ...LIVE, engineer: 'Drey', client: '', summary: 'ORANGE / Angelo Villegas / DR', bookingType: 'External',
  description: 'Engineer: Drey | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF', requester_text: 'book orange studio 7 for anj\nangelo\ndrey', asked_text: '' });
ok(V73 ? r.c.reason === 'NEED_CLIENT' : (/^\*ORANGE \/ DR\*/.test(r.s) && /\*Client:\* None/.test(r.s) && /\*Engineer:\* Daryl Reyes/.test(r.s) && /\(for Angelo Villegas\)/.test(r.s)),
   'then "drey" -> ORANGE / DR, Client: None (Jessie asks), engineer Daryl Reyes, Booked by ... (for Angelo Villegas)', r.s || r.c);

console.log('No second Anj on record - the general case');
r = go(B, LIVE, { 'Client Aliases': [{ json: {} }] });
ok(V80 ? (r.c.reason === 'NEED_ENGINEER' && /"Who’s the engineer\?"/.test(r.c.human)) : V73 ? r.c.reason === 'NEED_CLIENT' : (r.c.reason === 'NEED_ENGINEER' && /Angelo is who it is booked for/.test(r.c.human)), 'the colleague in the engineer slot, never named as engineer -> taken out' + (V80 ? ' (v80: and the engineer asked, not the requester)' : V73 ? ' (v73: the requester, an engineer, engineers; then the client is asked)' : ' and asked'), r.c);
r = go(B, { ...LIVE, requester_text: 'book orange studio 7 for anj, engineer anj' }, { 'Client Aliases': [{ json: {} }] });
ok(r.c.reason !== 'NEED_ENGINEER', '"engineer anj" typed -> stays the engineer', r.c.reason);
r = go(B, { ...LIVE, requester_text: 'book orange studio 7 for anj with anj' }, { 'Client Aliases': [{ json: {} }] });
ok(r.c.reason !== 'NEED_ENGINEER', '"with anj" typed -> stays the engineer', r.c.reason);
r = go(B, { summary: 'ORANGE / DR', client: '', engineer: 'Daryl Reyes', bookingType: 'External', session_type: 'VO Recording', rooms: 'Studio 7',
  description: 'Engineer: Daryl Reyes | Booked by: Howard Luistro (for Daryl Reyes) | ref: U08V3CKDGJF', requester_text: 'book orange studio 7 for drey, no client', asked_text: '' });
ok(r.c.reason !== 'NEED_ENGINEER' && r.c.reason !== 'AMBIGUOUS_PERSON', 'booked for an engineer (their own session) -> they stay the engineer', r.c.reason);
r = go(B, { ...LIVE, engineer: 'Drey', bookingType: 'External', description: 'Engineer: Drey | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF', requester_text: 'book orange studio 7 for anj, engineer drey' }, { 'Client Aliases': [{ json: {} }] });
ok(V73 ? r.c.reason === 'NEED_CLIENT' : /\*Client:\* None/.test(r.s), 'the colleague in the client slot (not a client on record) -> ' + (V73 ? 'the client is asked' : 'Client: None'), r.s.split('\n').slice(0, 3));
r = go(B, { ...LIVE, engineer: 'Drey', bookingType: 'External', description: 'Engineer: Drey | Booked by: Howard Luistro (for Angelo Villegas) | ref: U08V3CKDGJF', requester_text: 'book orange studio 7 for anj, engineer drey' + (V80 ? '\nhis own project' : '') },
  { 'Client Aliases': [{ json: {} }], 'Get Client': [{ json: { id: 'recX', fields: { Name: 'Angelo Villegas', 'Client Type': ['Personal'] } } }] });
ok(/\*Client:\* Angelo Villegas/.test(r.s) || (V80 && /ORANGE \/ Angelo Villegas/.test(JSON.stringify(r.o || {}) + JSON.stringify(r.c))), '... unless they are a client on record too (the in-house arrangers, v54)', r.s.split('\n').slice(0, 3));
r = go(B, { ...LIVE, mode: '' });
ok(r.c.reason !== 'AMBIGUOUS_PERSON' && r.c.reason !== 'NEED_ENGINEER', 'not prepare mode (the yes, a series date, a consent placement) -> untouched', r.c.reason);

console.log('Wiring and the lookups');
const to = (w, n) => ((((w.connections[n] || {}).main || [])[0]) || []).map(t => t.node);
ok(JSON.stringify(to(B, 'Get Client')) === '["Client Aliases"]' && JSON.stringify(to(B, 'Client Aliases')) === '["Client Unmatched?"]', 'Get Client -> Client Aliases -> Client Unmatched?');
const CA = B.nodes.find(n => n.name === 'Client Aliases');
ok(CA.executeOnce && CA.alwaysOutputData && CA.onError === 'continueRegularOutput', 'Client Aliases runs once, always passes an item on, never fails the booking');
const fx = s => new Function('$', 'return `' + s.replace(/^=\{\{/, '${').replace(/\}\}$/, '}') + '`;');
const caf = req => fx(CA.parameters.filterByFormula)(n => ({ first: () => ({ json: req }) }));
ok(caf({ mode: 'prepare', description: 'Booked by: X (for Y)' }).indexOf("SEARCH('goes by'") !== -1 && caf({ mode: 'prepare', description: 'Booked by: X' }) === 'FALSE()' && caf({ mode: '', description: '(for Y)' }) === 'FALSE()',
   'it reads only for an on-behalf booking being prepared');
const clf = M.nodes.find(n => n.name === 'Clients').parameters.filterByFormula;
const cf = v => new Function('$fromAI', 'return `' + clf.replace(/^=\{\{/, '${').replace(/\}\}$/, '}') + '`;')(() => v);
ok(cf('anj') === "OR(SEARCH('anj', LOWER({Name})), AND(SEARCH('goes by', LOWER({Notes} & '')), REGEX_MATCH(LOWER({Notes} & ''), '(^|[^a-z])anj($|[^a-z])')))", 'main v196: the Clients tool also finds "Goes by Anj"', cf('anj'));
ok(/O\\'Brien|O\\\\'Brien/.test(cf("o'brien")) || cf("o'brien").indexOf("SEARCH('o\\'brien'") !== -1, "an apostrophe is still escaped", cf("o'brien"));
let threw = false; try { cf(''); } catch (e) { threw = true; } ok(threw, 'an empty name still looks nothing up (gotcha 7)');

if (process.argv[3]) {
  console.log('main Booked For - who "for <nickname>" is (an Info that ends in a line break)');
  const OM = WF('imported/project-jessie-v195-imported.json');
  const mrun = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
  const mrec = n => mrun[n] ? (((mrun[n][0].data || {}).main || [[]])[0] || []) : null;
  const bf = (w, text) => { const h = [{ json: { ts: '1790662300.1', text, user: 'U08V3CKDGJF' } }];
    const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : wrap(mrec(n) || [{ json: {} }]);
    return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json.bookedFor; };
  ok(bf(M, 'book orange studio 7 for anj') === 'Angelo Villegas', '"for anj" -> (for Angelo Villegas), which the checks above key on');
  ok(bf(M, 'book orange studio 7 for enrico') === 'Rico Gonzales' && bf(OM, 'book orange studio 7 for enrico') === '', '"for enrico" -> Rico Gonzales (v195: no one - the first "Goes by" name was lost)');
  ok(bf(M, 'book orange studio 7 for tel') === 'Cristel Cube', '"for tel" -> Cristel Cube, as before');
}

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
