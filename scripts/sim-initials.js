#!/usr/bin/env node
// PENDING 161 (24 Nov): a booking made by hand is also the person's whose initials end its title (option b: listed, changeable,
// cancellable, reminded). Jessie's own bookings (ref: / team:) are read exactly as before. Initials two people share go to the one
// with Client Booking authority. Runs the real nodes; made-up people.
//   node scripts/sim-initials.js [si v88] [cancel v37] [move v49] [reminders v12] [main v301] [si v87] [reminders v11]
const fs = require('fs');
const L = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const SI = L(process.argv[2], 'workflows/slack-interactions-v88.json'), CX = L(process.argv[3], 'workflows/cancel-booking-v37.json');
const MV = L(process.argv[4], 'workflows/move-booking-v49.json'), RM = L(process.argv[5], 'workflows/reminders-v12.json');
const MAIN = L(process.argv[6], 'workflows/project-jessie-v301.json'), SI0 = L(process.argv[7], 'workflows/slack-interactions-v87.json');
const RM0 = L(process.argv[8], 'workflows/reminders-v11.json');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const wrap = a => ({ first: () => a[0] || { json: {} }, all: () => a });
const run = (w, name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(w, name).parameters.jsCode + '\n})();')(
  n => { if (!(n in outs)) throw new Error('not run: ' + n); return wrap(outs[n]); }, wrap(input));

// People: a coordinator who makes bookings by hand; an engineer; two people sharing the initials QZ (the one who books studios has
// Client Booking); someone else
const P = (name, ini, id, email, extra) => Object.assign({ Name: name, Initials: ini, 'Slack User ID': id, Email: email, Info: 'Engineer', Department: ['Music'], Authority: ['Standard'] }, extra || {});
const COORD = P('Coord Person', 'CP', 'UCOORD01', 'coord@example.com', { 'Alt email': 'coord.alt@example.com', Authority: ['Standard', 'Client Booking'] });
const ENG = P('Eng Person', 'EP', 'UENG0001', 'eng@example.com');
const ENG2 = P('Mix Person', 'MX', 'UMIX0001', 'mix@example.com');
const QZ1 = P('Quin Zed', 'QZ', 'UQZBOOK1', 'quin@example.com', { Authority: ['Standard', 'Client Booking'] });
const QZ2 = P('Quella Zed', 'QZ', 'UQZFIN01', 'quella@example.com', { Department: ['Finance'], Authority: ['Standard', 'Dept Head'] });
const OTHER = P('Other Person', 'OP', 'UOTHER01', 'other@example.com');
const ALL = [COORD, ENG, ENG2, QZ1, QZ2, OTHER];
const bookers = ALL.map((f, i) => ({ id: 'rec' + i, fields: f }));
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
const ev = (id, title, creator, desc, day) => ({ id, summary: title, start: { dateTime: (day || '2026-11-25') + 'T09:00:00+08:00' }, end: { dateTime: (day || '2026-11-25') + 'T17:00:00+08:00' },
  creator: { email: creator }, description: desc || '', location: 'KDC Plaza-Top Level-Studio 7 (7)', attendees: [{ email: S7, displayName: 'KDC Plaza-Top Level-Studio 7 (7)', resource: true, responseStatus: 'accepted' }] });
const HAND = ev('h1', 'ATE / Client Name / EP', 'coord@example.com');                        // by hand, for the engineer
const HAND2 = ev('h2', 'NET | PANDA ANI | EP x MX', 'coord.alt@example.com');               // by hand, two people
const HANDQZ = ev('h3', 'PROJ / QZ', 'coord@example.com');                                  // shared initials
const HANDM1 = ev('h4', 'M1 - Eng', 'coord@example.com');                                   // no initials part
const JESSIE = ev('j1', 'PROJ / Client / EP', 'jessie@example.com', 'Booked by: Other Person | ref: UOTHER01 | Dept: Music');   // Jessie's, EP in the title, no team:
const HANDTEAM = ev('h5', 'PROJ / EP', 'coord@example.com', 'team: UMIX0001');              // hand-made but someone is listed

(async () => {
  console.log('The rule: which titles carry initials');
  const H = node(SI, 'Render My Bookings').parameters.jsCode;
  const inits = new Function(H.slice(0, H.indexOf('const _p161Id')) + '\nreturn _p161Inits;')();
  const cases = [['ATE / Leslie Perez / HL', 'HL'], ['VSI-TRES | MT', 'MT'], ['NET | PANDA ANI | JL', 'JL'], ['NET-BONJOUR 6 / VGA', 'VGA'], ['X / HL x MV', 'HL,MV'],
    ['X / HL AEG x MV', 'HL,AEG,MV'], ['NET - S. I. Mixing / TC', 'TC'], ['M1 - Rico', ''], ['SALIN - MUSIC DEPT', ''], ['KDC DAY', ''], ['NET | PANDA ANI', ''],
    ['ATE / Leslie Perez', ''], ['PROJ / Client / hl', ''], ['M2 - RICHARD', '']];
  for (const [t, want] of cases) ok(inits(t).join() === want, JSON.stringify(t) + ' -> ' + (want || 'none'), inits(t));

  console.log('Slack Interactions v88: My bookings');
  const rmb = async (w, user, items) => (await run(w, 'Render My Bookings', [{ json: { items } }],
    { 'My Window': [{ json: { user, start: '2026-11-22', end: '2026-11-29', channel: 'D1' } }], 'Read Cache 4': cache }))[0].json;
  const ids = b => b.blocks.filter(x => /^bk_/.test(x.block_id || '')).map(x => x.block_id.slice(3)).sort().join();
  const ITEMS = [HAND, HAND2, HANDQZ, HANDM1, JESSIE, HANDTEAM];
  let r = await rmb(SI, 'UENG0001', ITEMS);
  ok(ids(r) === 'h1,h2', 'the engineer: the two hand-made bookings ending in EP; not Jessie\'s booking (ref:, no team:) nor one that lists someone (team:)', ids(r));
  ok(/You’re on the team/.test(JSON.stringify(r.blocks.find(x => x.block_id === 'bk_h1'))), 'the note under it: "You’re on the team"');
  ok(/bk_cancel/.test(JSON.stringify(r.blocks.filter(x => x.block_id === 'bka_h1'))), 'with Change / Cancel (option b)');
  ok(ids(await rmb(SI, 'UMIX0001', ITEMS)) === 'h2,h5', 'the second person: "EP x MX" by initials, and the one listing them on team:', ids(await rmb(SI, 'UMIX0001', ITEMS)));
  ok(ids(await rmb(SI, 'UCOORD01', ITEMS)) === 'h1,h2,h3,h4,h5', 'the coordinator: everything they made by hand, as before');
  ok(ids(await rmb(SI, 'UQZBOOK1', ITEMS)) === 'h3', 'shared initials QZ: the one with Client Booking');
  ok(ids(await rmb(SI, 'UQZFIN01', ITEMS)) === '', 'shared initials QZ: not the other one');
  ok(ids(await rmb(SI, 'UOTHER01', ITEMS)) === 'j1', 'someone else: only their Jessie booking, as before');
  const v87 = ids(await rmb(SI0, 'UENG0001', ITEMS));
  ok(v87 === '', 'v87 (live): the engineer saw none of them', v87);
  for (const u of ['UCOORD01', 'UOTHER01']) ok(JSON.stringify((await rmb(SI, u, ITEMS)).blocks) === JSON.stringify((await rmb(SI0, u, ITEMS)).blocks), u + ': My bookings exactly v87\'s');

  console.log('Slack Interactions v88: To Cancel / To Move send people');
  const tc = (await run(SI, 'To Cancel', [], { 'Check Signature': [{ json: { user: 'UENG0001' } }], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify({ id: 'h1', d: '2026-11-25', t: HAND.summary, s: '09:00' }) }] } } }], 'Read Cache 5': cache }))[0].json;
  const PM = JSON.parse(tc.people);
  ok(PM.i.EP === 'UENG0001' && PM.i.QZ === 'UQZBOOK1' && PM.e['coord.alt@example.com'][0] === 'UCOORD01' && PM.e['coord@example.com'][1] === 'Coord Person', 'people: initials -> one owner (QZ -> Client Booking), emails -> [id, name]', PM);
  ok(tc.people.length < 4000, 'people stays small (' + tc.people.length + ' characters for ' + ALL.length + ' people)');
  ok(/people: peopleMap\(data\)/.test(node(SI, 'To Move').parameters.jsCode), 'To Move: people on the call');
  for (const [w, nm] of [[CX, 'Cancel v37'], [MV, 'Move v49']])
    ok(node(w, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'people'), nm + ': people is an input of the trigger');

  console.log('Slack Interactions v88: the Change form reads shared initials the same way');
  const bc = node(SI, 'Build Change').parameters.jsCode;
  const staffOf = new Function(bc.slice(bc.indexOf('function staffOf'), bc.indexOf('function detOrig')) + '\nreturn { staffOf, byIni };')();
  const st = staffOf.staffOf({ bookers });
  ok((staffOf.byIni(st, 'QZ') || {}).slack === 'UQZBOOK1' && (staffOf.byIni(st, 'EP') || {}).slack === 'UENG0001', 'byIni: QZ -> the one with Client Booking; EP -> the engineer');

  console.log('Cancel v37 (Check Ownership)');
  const people = tc.people;
  const req = o => Object.assign({ confirmed: true, mode: '', booking_date: '2026-11-25', event_id: 'h1', title: HAND.summary, requester: 'UENG0001', requester_name: 'Eng Person', authority: 'Standard', department: 'Music', my_emails: 'eng@example.com', people }, o);
  const co = (w, r, day) => new Function('$', '$input', node(w, 'Check Ownership').parameters.jsCode)(n => n === 'Find By Title' ? wrap([{ json: { items: [] } }]) : wrap([{ json: r }]), wrap([{ json: { items: day } }]))[0].json;
  let c = co(CX, req({}), [HAND]);
  ok(c.verdict === 'CLEAR' && c.bookerRef === 'UCOORD01' && c.bookerName === 'Coord Person' && c.notify === true, 'the engineer cancels the hand-made booking: allowed; the coordinator who made it is told', c);
  c = co(CX, req({ people: '' }), [HAND]);
  ok(c.verdict === 'REJECTED' && c.reason === 'NO_REFERENCE', 'no people (main\'s older path) -> NO_REFERENCE, as before', c.reason);
  c = co(CX, req({ requester: 'UOTHER01', my_emails: 'other@example.com' }), [HAND]);
  ok(c.verdict === 'REJECTED' && c.reason === 'NO_REFERENCE', 'someone not on it -> NO_REFERENCE, as before', c.reason);
  c = co(CX, req({ event_id: 'j1', title: JESSIE.summary }), [JESSIE]);
  ok(c.verdict === 'REJECTED' && c.reason === 'NOT_YOURS', 'Jessie\'s booking with EP in its title (no team:) -> NOT_YOURS, as before: Jessie\'s own fields decide', c.reason);
  c = co(CX, req({ requester: 'UQZFIN01', event_id: 'h3', title: HANDQZ.summary }), [HANDQZ]);
  ok(c.verdict === 'REJECTED', 'shared QZ, the one without Client Booking -> refused', c.reason);
  c = co(CX, req({ requester: 'UCOORD01', my_emails: 'coord@example.com,coord.alt@example.com', event_id: 'h2', title: HAND2.summary }), [HAND2]);
  ok(c.verdict === 'CLEAR' && c.bookerRef === 'UCOORD01' && JSON.stringify(c.team) === '["UENG0001","UMIX0001"]' && c.notify === true, 'the coordinator cancels "EP x MX": both are told (team by initials)', c);
  const br = new Function('$', '$input', node(CX, 'Build Recipients').parameters.jsCode)(n => wrap(n === 'Check Ownership' ? [{ json: c }] : n === 'When Executed by Another Workflow' ? [{ json: { requester: 'UCOORD01', requester_name: 'Coord Person', booking_date: '2026-11-25' } }] : n === 'Lookup Engineer' ? [{ json: {} }] : []), wrap([]));
  ok(br.map(i => i.json.to).sort().join() === 'UENG0001,UMIX0001', 'Build Recipients: the two by initials, not the coordinator who did it', br.map(i => i.json.to));

  console.log('Move v49 (Resolve Booking)');
  const mreq = o => [{ json: Object.assign({ event_id: 'h1', booking_date: '2026-11-25', title: HAND.summary, new_start_iso: '2026-11-25T10:00:00+08:00', new_end_iso: '2026-11-25T18:00:00+08:00',
    confirmed: true, requester: 'UENG0001', authority: 'Standard', department: 'Music', requester_name: 'Eng Person', new_summary: '', new_details: '', my_emails: 'eng@example.com', people }, o) }];
  const rv = (o, e) => new Function('$', '$input', node(MV, 'Resolve Booking').parameters.jsCode)(n => wrap(n === 'When Executed by Another Workflow' ? mreq(o) : []), wrap([{ json: { items: [e || HAND] } }]))[0].json;
  let m = rv({});
  ok(m.verdict === 'CLEAR' && m.description === 'Booked by: Coord Person | ref: UCOORD01 | team: UENG0001', 'the engineer changes it: the coordinator stays the booker, the engineer goes on team:', m.description);
  ok(m.bookerRef === 'UCOORD01' && m.notify === true, 'the coordinator is told', m);
  m = rv({ requester: 'UCOORD01', requester_name: 'Coord Person', my_emails: 'coord@example.com,coord.alt@example.com' });
  ok(m.verdict === 'CLEAR' && m.description === 'Booked by: Coord Person | ref: UCOORD01 | Dept: Music | team: UENG0001', 'the coordinator changes it: "Booked by | ref | Dept" (v44) + team: the engineer', m.description);
  ok(JSON.stringify(m.team) === '["UENG0001"]' && m.notify === true, 'the engineer is told', m);
  m = rv({}, Object.assign({}, HAND, { description: 'call time 8am' }));
  ok(m.description === 'Booked by: Coord Person | ref: UCOORD01 | team: UENG0001\n\nNotes: call time 8am', 'its own text kept under Notes:', m.description);
  m = rv({ requester: 'UCOORD01', requester_name: 'Coord Person', my_emails: 'coord@example.com', event_id: 'h4', title: HANDM1.summary }, HANDM1);
  ok(m.description === 'Booked by: Coord Person | ref: UCOORD01 | Dept: Music', 'no initials part ("M1 - Eng"): exactly v48\'s replacement', m.description);
  m = rv({ event_id: 'j1', title: JESSIE.summary }, JESSIE);
  ok(m.verdict === 'REJECTED' && m.reason === 'NOT_YOURS', 'Jessie\'s booking with EP in its title -> NOT_YOURS, as before', m.reason);
  m = rv({ people: '' });
  ok(m.verdict === 'REJECTED' && m.reason === 'NO_REFERENCE', 'no people -> NO_REFERENCE, as before', m.reason);
  m = rv({ requester: 'UCOORD01', requester_name: 'Coord Person', my_emails: 'coord@example.com', new_details: JSON.stringify({ Engineer: 'Mix Person', team: 'UMIX0001', teamWas: ['UENG0001'] }) });
  ok(m.verdict === 'CLEAR' && /\| team: UMIX0001$/.test(m.description.split('\n')[0]) && !/team:.*\n\nNotes:.*team:/.test(m.description), 'the Change form picked another engineer: its team: wins, on the first line', m.description);

  console.log('Reminders v12');
  const runR = async (w, items) => (await new Function('$', '$input', 'return (async function(){' + node(w, 'Build Reminders').parameters.jsCode + '\n})();')(
    n => wrap(n === 'Window' ? [{ json: { kind: 'weekly', start: '2026-11-23', end: '2026-11-30' } }] : n === 'List Events R' ? [{ json: { items } }] : n === 'Read Cache R' ? cache : []), wrap([]))).map(i => i.json);
  const RITEMS = [HAND, HAND2, HANDQZ, JESSIE, HANDTEAM, ev('h6', 'PROJ / EP', 'outsider@example.com'), ev('h7', 'PROJ / EP', 'coord@example.com', 'Engineer: Mix Person')];
  const out = await runR(RM, RITEMS), to = id => out.find(j => j.person === id);
  const rids = j => j ? j.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id.slice(3)).sort().join() : '';
  ok(rids(to('UENG0001')) === 'h1,h2,h6', 'the engineer: the hand-made ones ending in EP (even one made by someone not in Bookers); not Jessie\'s, not one naming someone', rids(to('UENG0001')));
  ok(rids(to('UMIX0001')) === 'h2,h5,h7', 'the second person: by initials, by team:, by Engineer: (as before)', rids(to('UMIX0001')));
  ok(rids(to('UQZBOOK1')) === 'h3' && !to('UQZFIN01'), 'shared QZ: only the one with Client Booking');
  const old = await runR(RM0, RITEMS);
  for (const u of ['UCOORD01', 'UOTHER01']) ok(JSON.stringify((old.find(j => j.person === u) || {}).blocks) === JSON.stringify((to(u) || {}).blocks), u + ': reminder exactly v11\'s');

  console.log('main v301: typed "my bookings" and typed changes');
  const mineOf = async (fields, items) => (await run(MAIN, 'Mine Reply', [{ json: { items } }], { 'Mine Check': [{ json: { mineCheck: { user: fields['Slack User ID'], start: '2026-11-22', end: '2026-11-29', channel: 'D1' } } }],
    'Get Booker': [{ json: { id: 'r', fields } }], 'All Bookers': bookers.map(b => ({ json: b })) }))[0].json;
  const mids = j => (j.blocks || []).filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id.slice(3)).sort().join();
  ok(mids(await mineOf(ENG, ITEMS)) === 'h1,h2', 'Mine Reply: the engineer\'s hand-made ones, as My bookings', mids(await mineOf(ENG, ITEMS)));
  ok(mids(await mineOf(QZ2, ITEMS)) === '', 'Mine Reply: shared QZ without Client Booking - none');
  const chg = (await run(MAIN, 'Change Reply', [{ json: { items: ITEMS } }], { 'Change Offer': [{ json: { changeOffer: { kind: 'change', user: 'UENG0001', channel: 'D1', words: ['ate'], fDates: [], fRooms: [], n: {}, today: '2026-11-24' } } }],
    'Get Booker': [{ json: { id: 'r', fields: ENG } }], 'All Bookers': bookers.map(b => ({ json: b })) }))[0].json;
  ok(chg.count === 1 && chg.blocks[1].block_id === 'bk_h1', 'Change Reply: "change the ATE booking" finds it for the engineer', (chg.blocks || []).map(b => b.block_id));

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
