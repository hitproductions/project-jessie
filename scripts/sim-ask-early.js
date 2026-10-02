#!/usr/bin/env node
// Offline tests for main v212 + Book Session v85 (live 2 Oct 12:29, PENDING 77: the model asked the session type itself,
// with examples, and the time was not asked with it). Decided 2 Oct: date / time asked early; no type examples; shorthand
// still registers.
//   node scripts/sim-ask-early.js <book-session-prepare-execution.json> <main-execution.json>
// Offline tests for Book Session v73 (types + short summary) - PENDING 69, 70, 71. Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-types-short.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v85.json'), OB = WF('imported/book-session-v72-imported.json');
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


const M = WF(process.env.MAIN || 'project-jessie-v212.json'), OM = WF('project-jessie-v211.json');
const run2 = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
const rec2 = n => run2[n] ? (((run2[n][0].data || {}).main || [[]])[0] || []) : null;
const gp = (W, output, said, dates = '', steps = []) => new Function('$input', '$', code(W, 'Guard Probe'))(
  wrap([{ json: { ...((rec2('Guard Probe') || [{ json: {} }])[0].json), output, intermediateSteps: steps } }]),
  n => n === 'Booked For' ? wrap([{ json: { requesterText: said, bookedFor: '' } }]) : n === 'Gate Context' ? wrap([{ json: { ...(((rec2('Gate Context') || [{ json: {} }])[0] || {}).json || {}), datesUnderDiscussion: dates } }])
     : n === 'Get Booker' ? wrap([{ json: { fields: { Name: 'Howard Luistro' } } }]) : wrap(rec2(n) || [{ json: {} }]))[0].json.output;
console.log('Guard Probe - the model\'s question asks for the day / time too, and has no examples');
const LIVE = 'What session type is this? (e.g. Celebrity Recording, Post Mixing, VO Recording, etc.)';
let o = gp(M, LIVE, 'book studio 7 in 2 days, project thank you, client sir vic', '2027-10-04');
ok(o === 'What kind of session is this?\nAnd what time?', 'live 12:29 -> "What kind of session is this?\\nAnd what time?"', o);
ok(/e\.g\./.test(gp(OM, LIVE, 'book studio 7 in 2 days, project thank you, client sir vic', '2027-10-04')), '  (v211: examples, no time)');
o = gp(M, 'What kind of session is this?', 'book studio 7 for project cats');
ok(o === 'What kind of session is this?\nAnd which day and time?', 'no day, no time -> "And which day and time?"', o);
o = gp(M, 'Who’s the client? (or "none")', 'book studio 7 for project cats 2-4pm');
ok(o === 'Who’s the client? (or "none")\nAnd which day?', 'a time, no day -> "And which day?"', o);
o = gp(M, 'What kind of session is this?', 'book studio 7 tomorrow 2-4pm', '2027-10-03');
ok(o === 'What kind of session is this?', 'day and time given -> nothing added', o);
o = gp(M, 'What time works for you?', 'book studio 7 for project cats', '2027-10-03');
ok(o === 'What time works for you?', 'already asks the time -> nothing added', o);
o = gp(M, 'What type of session is it for?', 'book m3 tomorrow', '2027-10-03');
ok(!/what time/i.test(o), 'an M booth hold -> no time asked', o);
o = gp(M, 'x', 'book studio 7 for project cats', '', [{ action: { tool: 'Prepare_Booking' }, observation: JSON.stringify([{ verdict: 'REJECTED', reason: 'NEED_SESSION_TYPE', human: 'Nothing was prepared. Ask exactly this, in one message: "What kind of session is this? And which day and time?" Then prepare it again.' }]) }]);
ok(o === 'What kind of session is this? And which day and time?', 'Book Session\'s own question is sent as written (not doubled)', o);
o = gp(M, 'Hi Howard! What do you need?', 'hello');
ok(o === 'Hi Howard! What do you need?', 'a greeting gets nothing');
console.log('Book Session v85 - second ask without examples; shorthand registers');
const S = (st, txt, asked = '') => go(B, { ...BASE, session_type: st, requester_text: txt, asked_text: asked, __keep80: true }).c;
const relay = h => { const m = String(h || '').match(/Ask exactly this[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
ok(relay(S('VO Recording', 'book studio 8 nov 18 2-4pm, no client', 'What kind of session is this?').human) === 'What kind of session is this?', 'asked again -> same question, no "(e.g. ...)"');
for (const [st, word] of [['Localization Dubbing', 'dubbing'], ['Localization Dubbing', 'dub'], ['VO Recording', 'vo'], ['VO Recording', 'voice over'], ['VO Recording', 'isr'], ['Celebrity Recording', 'celeb'],
    ['Localization Atmos Mixing', 'atmos'], ['Localization Mixing', 'loc mixing'], ['Localization Editing', 'editing'], ['Post Processing', 'processing'], ['Band Recording', 'band'], ['QC', 'qc'], ['Music Vocal Recording', 'vocals'], ['Post Mixing', 'post mix']])
  ok(S(st, 'book studio 8 nov 18 2-4pm ' + word + ', no client').reason !== 'NEED_SESSION_TYPE', JSON.stringify(word) + ' -> ' + st);
ok(/^Which one - /.test(relay(S('Post Mixing', 'book studio 8 nov 18 2-4pm mixing, no client').human) || ''), '"mixing" alone -> still asks which one');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
