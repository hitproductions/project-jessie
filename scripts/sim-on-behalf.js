#!/usr/bin/env node
// Offline tests for Book Session v80 (on-behalf + session type). Live 1 Oct 16:29 ("book studio 7 for
// joaquin, he's recording himself for jem lim's project YELLOW" -> YELLOW / Jem Lim / HL, VO Recording) and 16:40
// ("book studio 3 for anj's project DASHING" -> DASHING / HL, Localization Editing, no "which Anj?").
//
//   node scripts/sim-on-behalf.js <book-session-prepare-execution.json> <main-execution.json>
// Offline tests for Book Session v73 (types + short summary) - PENDING 69, 70, 71. Real prepare inputs: 29 Sep exec 16681.
//   node scripts/sim-types-short.js <book-session-prepare-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const B = WF(process.env.BOOK || 'book-session-v80.json'), OB = WF('imported/book-session-v72-imported.json');
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


const OLDB = WF('book-session-v79.json');
const OM = WF(process.env.MAIN || 'project-jessie-v208.json');
const ME = 'Howard Luistro', REF = 'U08V3CKDGJF';
const relay = h => { const m = String(h || '').match(/(?:Ask exactly this|naming both)[^"]*"((?:[^"\\]|\\.)+)"/); return m ? m[1].replace(/\\"/g, '"') : null; };
const forD = (who, eng = 'Howard Luistro') => 'Engineer: ' + eng + ' | Booked by: ' + ME + ' (for ' + who + ') | ref: ' + REF;
const JEMC = client('Jem Lim', ['Advertising'], 'Advertising Producer');
const Y = "book studio 7 for joaquin, he's recording himself for jem lim's project YELLOW. later at 9-11pm";
const yel = (extra = {}, over = {}) => go(B, { ...BASE, summary: 'YELLOW / Jem Lim / HL', client: 'Jem Lim', engineer: 'Joaquin Santos', session_type: 'VO Recording', rooms: 'Studio 7', description: forD('Joaquin Santos', 'Joaquin Santos'), requester_text: Y, ...extra }, { 'Get Client': JEMC, ...over });

console.log('Live 16:29 - YELLOW for Joaquin');
let r = yel();
ok(r.c.reason === 'NEED_SESSION_TYPE' && relay(r.c.human) === 'What kind of session is this?', 'no session type said -> "What kind of session is this?" (was VO Recording)', [r.c.reason, relay(r.c.human)]);
r = go(OLDB, { ...BASE, summary: 'YELLOW / Jem Lim / HL', client: 'Jem Lim', engineer: 'Joaquin Santos', session_type: 'VO Recording', rooms: 'Studio 7', description: forD('Joaquin Santos', 'Joaquin Santos'), requester_text: Y }, { 'Get Client': JEMC });
ok(r.c.verdict === 'CLEAR' && /Engineer: Howard Luistro/.test(r.c.final_description || ''), '  (v79: prepared, engineer Howard)', [r.c.verdict, r.c.final_description]);
r = yel({ requester_text: Y + '\nvo recording' });
ok(r.c.verdict === 'CLEAR' && /Engineer: Joaquin Santos/.test(r.c.final_description || '') && /\/ JS$/.test(r.c.final_summary || ''), '"he\'s recording himself" -> the engineer is Joaquin (title ... / JS)', [r.c.final_description, r.c.final_summary]);
ok(/\n\*For:\* Joaquin Santos\n/.test(r.o.summary_text || ''), 'the card says "For: Joaquin Santos"', r.o.summary_text);
r = yel({ engineer: 'Howard Luistro', description: forD('Joaquin Santos'), requester_text: 'book studio 7 for joaquin tomorrow 9-11pm, vo recording, client jem lim, project YELLOW' });
ok(r.c.reason === 'NEED_ENGINEER' && relay(r.c.human) === 'Who’s the engineer?', 'for a colleague, no engineer named -> "Who’s the engineer?" (not the requester)', [r.c.reason, relay(r.c.human)]);
r = yel({ engineer: 'Howard Luistro', description: forD('Joaquin Santos'), requester_text: 'book studio 7 for joaquin tomorrow 9-11pm, vo recording, client jem lim, project YELLOW, engineer howard' });
ok(r.c.verdict === 'CLEAR' && /Engineer: Howard Luistro/.test(r.c.final_description || ''), '... unless they named themselves ("engineer howard")', [r.c.reason, r.c.final_description]);
r = go(B, { ...BASE, summary: 'QAMINE / Jem Lim / HL', client: 'Jem Lim', engineer: 'Howard Luistro', description: 'Engineer: Howard Luistro | Booked by: ' + ME + ' | ref: ' + REF, requester_text: 'book studio 8 tomorrow 2-4pm vo recording, client jem lim' }, { 'Get Client': JEMC });
ok(r.c.verdict === 'CLEAR' && /Engineer: Howard Luistro/.test(r.c.final_description || '') && !/\*For:\*/.test(r.o.summary_text || ''), 'booking for themselves -> the engineer default stays, no "For:" line', [r.c.reason, r.o.summary_text]);

console.log('An arranger colleague, no other client - on behalf, or their own project?');
const J = (txt, extra = {}) => go(B, { ...BASE, summary: 'QAJOAQ / HL', client: '', engineer: '', session_type: 'Music Vocal Recording', rooms: 'Studio F', description: 'Booked by: ' + ME + ' (for Joaquin Santos) | ref: ' + REF, requester_text: txt, ...extra });
r = J('book studio f for joaquin tomorrow 2-4pm, music vocal recording');
ok(r.c.reason === 'ON_BEHALF_OR_OWN' && relay(r.c.human) === 'Booking this on behalf of Joaquin Santos, or is it Joaquin’s own project?', 'asked once', relay(r.c.human));
r = J('book studio f for joaquin tomorrow 2-4pm, music vocal recording\nhis own project');
ok(r.c.reason !== 'ON_BEHALF_OR_OWN' && /Joaquin Santos/.test(r.c.final_summary || r.c.human || '') , '"his own project" -> Joaquin is the client', [r.c.reason, r.c.final_summary, r.c.human]);
r = J('book studio f for joaquin tomorrow 2-4pm, music vocal recording\non his behalf');
ok(r.c.reason !== 'ON_BEHALF_OR_OWN' && !/Joaquin Santos \//.test(r.c.final_summary || ''), '"on his behalf" -> not the client (the client is asked as usual)', [r.c.reason, r.c.final_summary, relay(r.c.human)]);
r = J('book studio f for joaquin tomorrow 2-4pm, music vocal recording, client jem lim', { client: 'Jem Lim', summary: 'QAJOAQ / Jem Lim / HL' });
ok(r.c.reason !== 'ON_BEHALF_OR_OWN', 'another client named -> not asked');

console.log('Session type - named or asked');
const ST = (st, txt) => go(B, { ...BASE, session_type: st, requester_text: txt + ', no client' }, {}).c;
for (const [st, txt, want] of [['Post Mixing', 'book studio 3 tomorrow 2-4pm for a mix', false], ['Post Mixing', 'book studio 3 tomorrow 2-4pm post mix', true],
    ['VO Recording', 'book studio 8 tomorrow 2-4pm vo', true], ['VO Recording', 'book studio 8 tomorrow 2-4pm voice over', true], ['VO Recording', 'book isr studio 8 tomorrow 2-4pm', true],
    ['Music Vocal Recording', 'book studio f tomorrow 2-4pm vocals', true], ['Localization Dubbing', 'book studio 3 tomorrow 2-4pm dubbing', true],
    ['Localization Editing', "book studio 3 for anj's project DASHING 4-6pm later", false], ['VO Recording', 'book studio 8 tomorrow 2-4pm recording', false],
    ['Music Mixing', 'book studio 3 tomorrow 2-4pm music mixing', true], ['Band Recording', 'book studio f tomorrow 2-4pm band', true]]) {
  const c = ST(st, txt);
  ok(want ? c.reason !== 'NEED_SESSION_TYPE' : c.reason === 'NEED_SESSION_TYPE', JSON.stringify(txt) + ' as ' + st + ' -> ' + (want ? 'named' : 'asked'), [c.reason, c.human]);
}

if (/v81 \(live 1 Oct 17:03\)/.test(code(B, 'Check Conflicts'))) {
  console.log('v81 - partial words, typos, choices (live 17:03: "mixing" asked again)');
  const S = (st, txt, asked = '', desc) => go(B, { ...BASE, session_type: st, requester_text: txt, asked_text: asked, __keep80: true, ...(desc ? { description: desc } : {}) }, {}).c;
  const Q = c => relay(c.human);
  let c = S('Post Mixing', 'mixing\nbook studio 8 tonight for project CATS 3-6pm, no client', 'What kind of session is this?');
  ok(c.reason === 'NEED_SESSION_TYPE' && /^Which one - /.test(Q(c) || '') && /Post Mixing/.test(Q(c)) && /Music Mixing/.test(Q(c)) && /Localization Mixing/.test(Q(c)), 'live 17:03: "mixing" -> "Which one - ...?" (the mixing types)', Q(c));
  c = S('Post Mixing', 'post\nmixing\nbook studio 8 tonight for project CATS 3-6pm, no client', 'Which one - Post Mixing, Music Mixing, Localization Mixing or Localization Atmos Mixing?');
  ok(c.reason !== 'NEED_SESSION_TYPE' && c.reason !== 'SESSION_TYPE_IS', 'then "post" -> Post Mixing (with "mixing" already said)', [c.reason, Q(c)]);
  c = S('Music Mixing', 'post mixing\nbook studio 8 tonight for project CATS 3-6pm, no client', 'Which one - Post Mixing, Music Mixing, Localization Mixing or Localization Atmos Mixing?');
  ok(c.reason === 'SESSION_TYPE_IS' && c.session_type === 'Post Mixing', 'the model passed Music Mixing after "post mixing" -> told Post Mixing', [c.reason, c.session_type]);
  for (const [st, txt] of [['Celebrity Recording', 'celeb recording'], ['Celebrity Recording', 'celebirty recording'], ['Post Mixing', 'post mixng'], ['Localization Dubbing', 'dubing'], ['Localization Dubbing', 'loc dubbing'], ['Music Vocal Recording', 'vocal recordng']])
    ok(S(st, 'book studio 8 tomorrow 2-4pm ' + txt + ', no client').reason !== 'NEED_SESSION_TYPE', JSON.stringify(txt) + ' -> ' + st);
  c = S('VO Recording', 'book studio 8 tomorrow 2-4pm, no client', 'What kind of session is this?');
  ok(Q(c) === 'What kind of session is this? (e.g. VO Recording, Post Mixing, Post Processing)', 'asked again with nothing matched -> examples from the department (Audio Post)', Q(c));
  c = S('VO Recording', 'book studio 8 tomorrow 2-4pm, no client');
  ok(Q(c) === 'What kind of session is this?', 'first ask: short');
  ok(S('Meeting', "book studio 8 tomorrow 2-4pm, let's meet the client, vo recording").reason === 'SESSION_TYPE_IS' && true, '"meet" is not taken over a full "vo recording"');
  ok(S('VO Recording', 'book studio 8 tomorrow 2-4pm even if late, vo').reason !== 'NEED_SESSION_TYPE', '"even" is not "event"');
}
console.log('Live 16:40 - "for anj\'s project": which Anj?');
const ANGELA = [{ json: { id: 'recA', fields: { Name: 'Angela Dela Calzada', Notes: 'Goes by Anj', 'Booker Type': 'Advertising Producer', 'Client Type': ['Advertising'] } } }];
r = go(B, { ...BASE, summary: 'DASHING / HL', client: '', engineer: 'Howard Luistro', session_type: 'Localization Editing', rooms: 'Studio 3', description: 'Engineer: Howard Luistro | Booked by: ' + ME + ' (for Angelo Villegas) | ref: ' + REF, requester_text: "book studio 3 for anj's project DASHING 4-6pm later" }, { 'Client Aliases': ANGELA });
ok(r.c.reason === 'AMBIGUOUS_PERSON' && /do you mean Angelo Villegas \(Music Arranger\) or Angela Dela Calzada/.test(relay(r.c.human) || ''), 'Book Session: "anj\'s" -> "by Anj, do you mean Angelo ... or Angela ...?"', [r.c.reason, relay(r.c.human)]);
const run2 = JSON.parse(fs.readFileSync(process.argv[3])).data.resultData.runData;
const rec2 = n => run2[n] ? (((run2[n][0].data || {}).main || [[]])[0] || []) : null;
const bfm = (w, txt) => { const h = [{ json: { user: REF, text: txt, ts: '1790841600.000100' } }];
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap(h) : n === 'Get Booker' ? wrap([{ json: { fields: { Name: ME } } }]) : n === 'Gate Context' ? wrap([{ json: { epoch: '0' } }]) : wrap(rec2(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const b8 = bfm(OM, "book studio 3 for anj's project DASHING 4-6pm later");
ok(b8.bookedFor === 'Angelo Villegas', 'main v208 Booked For already reads "for anj\'s" as Angelo Villegas - the gap was Book Session\'s "which Anj?" check', b8.bookedFor);
ok(bfm(OM, 'book studio 3 for jem lim tomorrow 2-4pm').bookedFor === '' , '"for jem lim" (a client) -> not on behalf, as before');

console.log('Heads-up line');
r = go(B, { ...BASE, session_type: 'VO Recording', requester_text: 'book studio 8 nov 18 2-4pm vo recording, no client' });
const RS = code(B, 'Render Summary');
ok(/\(\+_ty3\.max && _len > \+_ty3\.max\) \? 'longer' : 'shorter'/.test(RS) && /'at least ' \+ _durTxt/.test(RS), 'the line says "shorter" for a short session and "at least N" with no maximum');

console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
