#!/usr/bin/env node
// Offline tests for main v214 + Book Session v86 (project asked; live 2 Oct 13:02 'VO RECORDING / Vic Icasas / HL'). Was: (live 2 Oct 12:29, PENDING 77: the model asked the session type itself,
// with examples, and the time was not asked with it). Decided 2 Oct: date / time asked early; no type examples; shorthand
// still registers.
//   node scripts/sim-ask-early.js <book-session-prepare-execution.json> <main-execution.json>
// Offline tests for Book Session v73 (types + short summary) - PENDING 69, 70, 71. Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-types-short.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v86.json'), OB = WF('imported/book-session-v72-imported.json');
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
  // v84: a missing time is asked - these older cases name one so they test what they were written for
  if (/v84 \(decided 2 Oct\)/.test(code(w, 'Check Conflicts')) && String(_r80.requester_text || '').trim() && !req.__keep80
      && !/\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b|\b\d{1,2}\s*(?:-|to)\s*\d{1,2}\b|\ball day\b/i.test(_r80.requester_text)) _r80.requester_text += '\n2-4pm';
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


const M = WF(process.env.MAIN || 'project-jessie-v214.json'), OM = WF('project-jessie-v213.json');
const run2 = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
const rec2 = n => run2[n] ? (((run2[n][0].data || {}).main || [[]])[0] || []) : null;
const gp = (W, output, said, dates = '', steps = []) => new Function('$input', '$', code(W, 'Guard Probe'))(
  wrap([{ json: { ...((rec2('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { ...(((rec2('Gate Context') || [{ json: {} }])[0] || {}).json || {}), datesUnderDiscussion: dates } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec2(n) || [{ json: {} }]))[0].json.output;

const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const VIC = [{ json: { id: 'recV', fields: { Name: 'Vic Icasas', 'Client Type': ['Personal'] } } }];
const P = (summary, txt, extra = {}) => go(B, { ...BASE, summary, client: 'Vic Icasas', requester_text: txt, __keep80: true, __keep86: true, ...extra }, { 'Get Client': VIC }).c;
console.log('Book Session v86 - the project is required');
let c = P('VO RECORDING / Vic Icasas / DR', 'vo recording, 12-3pm\ncan you book studio 7 for me nov 18 - client is vic icasas');
ok(c.reason === 'NEED_PROJECT' && relay(c.human) === 'What’s the project?', 'live 13:02: title "VO RECORDING" (the session type) -> "What’s the project?"', [c.reason, relay(c.human)]);
c = P('DIGICON / Vic Icasas / DR', 'vo recording, 12-3pm\ncan you book studio 7 for me nov 18 - client is vic icasas, project digicon');
ok(c.verdict === 'CLEAR', 'project typed -> the card', [c.reason, c.human]);
c = P('VIC ICASAS / Vic Icasas / DR', 'vo recording 12-3pm nov 18, client is vic icasas');
ok(c.reason === 'NEED_PROJECT', 'the client as the project -> asked');
c = P('STUDIO 7 / Vic Icasas / DR', 'book studio 7 nov 18 vo recording 12-3pm, client vic icasas');
ok(c.reason === 'NEED_PROJECT', 'the room as the project -> asked');
c = P('CATS / Vic Icasas / DR', 'book studio 7 for me - client is vic icasas', { session_type: 'VO Recording', expected_date: '' });
ok(c.reason === 'NEED_SESSION_TYPE' && relay(c.human) === 'What kind of session is this? What’s the project? And which day and time?', 'several missing -> one message', relay(c.human));
c = P('VO RECORDING / Vic Icasas / DR', 'vo recording\ncan you book studio 7 for me nov 18 - client is vic icasas');
ok(c.reason === 'NEED_PROJECT' && relay(c.human) === 'What’s the project? And what time?', 'no project, no time -> "What’s the project? And what time?"', relay(c.human));
console.log('Guard Probe v214 - the model\'s question asks for the project too, on one line');
let o = gp(M, 'What kind of session is this?', 'can you book studio 7 for me - client is vic icasas', '2027-10-07');
ok(o === 'What kind of session is this? What’s the project? And what time?', 'live 13:02 -> one line with the project and time', o);
ok(/\nAnd what time\?/.test(gp(OM, 'What kind of session is this?', 'can you book studio 7 for me - client is vic icasas', '2027-10-07')), '  (v213: "And what time?" on a new line, no project)');
o = gp(M, 'What kind of session is this?', 'book studio 7 for DIGICON tomorrow 2-4pm', '2027-10-07');
ok(o === 'What kind of session is this?', 'a name in capitals counts as the project');
o = gp(M, 'Who’s the client? (or "none")', 'book studio 7 tomorrow 2-4pm, project cats', '2027-10-07');
ok(o === 'Who’s the client? (or "none")', '"project cats" counts');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
