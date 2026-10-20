#!/usr/bin/env node
// Round 13 offline (main v277 + Slack Interactions v33, 20 Oct): "for <someone>" typed fills the form - an engineer -> Engineer,
// an arranger -> Arranger, Post Processing -> its Booker, an M booth -> "Who is it for?". Runs main's real Booked For, then Form
// Offer on what it read, then the form's step 2.
// Usage: node scripts/sim-round-13.js [main v277] [slack-interactions v33]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v277.json', 'utf8'));
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v33.json', 'utf8'));
if (!/v277 \(Howard, 20 Oct/.test(JSON.stringify(main.nodes))) { console.log('0 ok, 0 failed (round 13 is main v277 on; this build is older)'); process.exit(0); }
const SI33 = (si.nodes.find(n => n.name === 'Build Step 2').parameters.jsCode || '').indexOf('v33: "for <name>" typed') !== -1;
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const STAFF = [
  { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.', Department: ['Audio Post'] },
  { Name: 'Josiah Lateo', Initials: 'JL', 'Slack User ID': 'U044A89SGQY', Info: 'Loc Engineer, Goes by Josiah, JL.', Department: ['Localization'] },
  { Name: 'BP Valenzuela', Initials: 'BPV', 'Slack User ID': 'U9', Info: 'Music Arranger, Goes by BP.', Department: ['Music'] },
  { Name: 'Japs Concepcion', Initials: 'JPC', 'Slack User ID': 'U7', Info: 'Accounts Lead, Goes by Japs, JPC.', Department: ['Sales & Accounts'] },
  { Name: 'Dylan Diaz', Initials: 'DD', 'Slack User ID': 'U0BQ77XKWA3', Info: 'Multimedia Specialist, Goes by Dylan.', Department: ['Marketing'] }];
const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
const rooms = [R('r4', 'Studio 4'), R('r7', 'Studio 7'), R('re', 'Studio E'), R('rf', 'Studio F'), R('m4', 'M4', { 'Room Type': ['M Booth'] })];
const TYPES = ['VO Recording', 'Music Mixing', 'Band Recording', 'Localization Dubbing', 'Post Processing', 'Meeting', 'Event'];
const base = { 'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': TYPES.map(t => ({ json: { fields: { Type: t } } })), 'All Bookers': STAFF.map(f => ({ json: { fields: f } })) };

const bookedFor = text => new Function('$', jsOf(main, 'Booked For'))(n => {
  if (n === 'Get Booker') return { first: () => ({ json: { fields: { Name: 'Howard Luistro' } } }) };
  if (n === 'All Bookers') return { all: () => STAFF.map(f => ({ json: { fields: f } })) };
  if (n === 'Slack Trigger') return { first: () => ({ json: { text, user: 'U1', ts: '100.1', channel: 'D1' } }) };
  if (n === 'Gate Context') return { first: () => ({ json: { epoch: '' } }) };
  if (n === 'Get Recent Messages') return { all: () => [{ json: { ts: '100.1', text, user: 'U1' } }] };
  return { first: () => ({ json: {} }), all: () => [] };
})[0].json;
const offer = async (text, dates) => {
  const bf = bookedFor(text);
  const outs = Object.assign({}, base, { 'Slack Trigger': [{ json: { text, channel: 'D1', ts: '100.1' } }],
    'Gate Context': [{ json: { datesInMessage: dates || '2027-10-21', confirmed: false, gate: {} } }], 'Booked For': [{ json: bf }], 'Get Recent Messages': [] });
  return { bf, F: (await run(main, 'Form Offer', [{ json: { keep: 1 } }], outs))[0].json.formOffer };
};

(async () => {
  console.log('1: "for <someone>" fills the form');
  let { bf, F } = await offer('hello book dubbing session tomorrow studio 4 2-4pm for josiah');
  ok(bf.bookedFor === 'Josiah Lateo', 'Booked For reads "for josiah" = Josiah Lateo (as before)', bf.bookedFor);
  ok(F.offer && F.prefill.en === 'U044A89SGQY' && F.prefill.enN === 'Josiah Lateo' && F.prefill.r === 'Studio 4', 'Howard\'s message (21:18) -> Engineer: Josiah Lateo', F.prefill);
  ok(/Engineer: Josiah Lateo/.test(F.text) && JSON.parse(F.blocks[1].elements[0].value).en === 'U044A89SGQY', 'the reply says so, and Book a room carries it', F.text);
  ({ F } = await offer('book studio f tomorrow 2-4pm band recording for BP'));   // two-letter names are read in capitals (initials)
  ok(F.prefill.ar === 'U9' && !F.prefill.en && /Arranger: BP Valenzuela/.test(F.text), 'for an arranger ("for BP") -> Arranger', F.prefill);
  ({ F } = await offer('book studio 4 tomorrow 2-4pm dubbing for josiah, engineer howard'));
  ok(F.prefill.en === 'U1', '"engineer howard" typed as well -> the typed engineer wins');
  ({ F } = await offer('book studio 7 tomorrow 2-4pm vo recording for japs'));
  ok(!F.prefill.en && !F.prefill.ar && !F.prefill.c, 'for a colleague who is neither (Japs, Accounts) -> nothing filled (the form books as you), not the client', F.prefill);
  ({ F } = await offer('book studio e tomorrow 2-4pm post processing for dylan'));
  ok(F.prefill.en === 'U0BQ77XKWA3' && /Booker: Dylan Diaz/.test(F.text), 'Post Processing for Dylan -> Booker: Dylan Diaz', F.text);
  ({ F } = await offer('book m4 tomorrow for japs'));
  ok(F.prefill.p === '__booth' && F.prefill.fn === 'Japs' && !F.prefill.c && /For: Japs/.test(F.text), 'an M booth for Japs (staff) -> Who is it for? Japs', F.prefill);
  ({ F } = await offer('book m4 tomorrow 2-4pm for sasa'));
  ok(F.prefill.fn === 'Sasa' && !F.prefill.c && !/Client/.test(F.text), 'an M booth for Sasa (not staff) -> Who is it for? Sasa, not a client', F.prefill);
  ({ F } = await offer('book studio 7 tomorrow 2-4pm vo recording for Jem Lim'));   // a lowercase name after "for" is not read as a client (as before)
  ok(F.prefill.c === 'Jem Lim' && !F.prefill.en, 'for a client (not staff) -> the client, as before', F.prefill);
  ({ F } = await offer('book m4 tomorrow for sasa, all day'));
  ok(F.prefill.fn === 'Sasa', 'an M booth "for sasa, all day" -> Sasa (stops at the comma)', F.prefill);
  ({ F } = await offer('book m4 for tomorrow 2pm'));
  ok(!F.prefill.fn, 'an M booth "for tomorrow" -> no name (a date word)', F.prefill);
  ({ F } = await offer('book studio 7 tomorrow 2-4pm vo recording for Josiah'));
  ok(F.prefill.en === 'U044A89SGQY' && !F.prefill.c, 'a name that is staff is never the client - staff first (Howard, 20 Oct)', F.prefill);
  ({ F } = await offer('book studio f tomorrow 2-4pm band recording for bp'));
  ok(F.prefill.ar === 'U9' && !F.prefill.c, 'lowercase "for bp" -> Arranger BP Valenzuela too (a nickname, not initials - Howard)', F.prefill);
  ({ F } = await offer('book studio 7 tomorrow 2-4pm vo recording'));
  ok(!F.prefill.en && !F.prefill.fn, 'no "for" -> nothing new');

  console.log('two-letter names (Howard: "bp" too)');
  const ST2 = STAFF.concat([{ Name: 'Daryl Reyes', Initials: 'DR', 'Slack User ID': 'U2', Info: 'Music Engineer, Post Engineer. Goes by Daryl, Drei, Drey, DR.' },
    { Name: 'Kelly Dawa', Initials: 'KD', 'Slack User ID': 'U3', Info: 'Billing & Cost Assistant, Goes by Ate Kelly, Kelly, KD.' }]).map(f => f.Name === 'BP Valenzuela' ? Object.assign({}, f, { Initials: 'BP ' }) : f);
  const bf2 = text => new Function('$', jsOf(main, 'Booked For'))(n => {
    if (n === 'Get Booker') return { first: () => ({ json: { fields: { Name: 'Howard Luistro' } } }) };
    if (n === 'All Bookers') return { all: () => ST2.map(f => ({ json: { fields: f } })) };
    if (n === 'Slack Trigger') return { first: () => ({ json: { text, user: 'U1', ts: '1', channel: 'D1' } }) };
    if (n === 'Gate Context') return { first: () => ({ json: { epoch: '' } }) };
    if (n === 'Get Recent Messages') return { all: () => [{ json: { ts: '1', text, user: 'U1' } }] };
    return { first: () => ({ json: {} }), all: () => [] }; })[0].json;
  for (const [t, want] of [['book studio f for bp tomorrow', 'BP Valenzuela'], ['book studio f for BP tomorrow', 'BP Valenzuela'], ['book studio f for Bp', 'BP Valenzuela'],
    ['book studio 7 for DR tomorrow', 'Daryl Reyes'], ['book studio 7 for dr cruz tomorrow', ''], ['book studio 7 for KD', 'Kelly Dawa'], ['book studio 7 for kd', ''],
    ['book studio 7 for me tomorrow', ''], ['book studio 7 for am session', '']])
    ok(bf2(t).bookedFor === want, JSON.stringify(t) + ' -> ' + (want || 'no one'), bf2(t).bookedFor);
  console.log('2: the form starts on them');
  const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms.concat([{ id: 'm4', fields: { 'Room Name': 'M4', 'Room Type': ['M Booth'] } }]),
    sessionTypes: FX.sessionTypes, bookers: STAFF.map((f, i) => ({ id: 'b' + i, fields: f })) }) } }];
  const step2 = async (s, ra) => (await run(si, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] }))[0].json.view;
  const S = (purpose, kind, pre) => ({ date: '2027-10-21', t0: '14:00', t1: '16:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x', pre });
  let v = await step2(S('Localization Dubbing', 'loc', { en: 'U044A89SGQY' }), { free_priority: ['Studio 1', 'Studio 2'] });
  const eng = v.blocks.find(b => b.block_id === 'engineer');
  ok(eng && eng.element.initial_option && eng.element.initial_option.value === 'U044A89SGQY', 'Localization Dubbing: Engineer starts on Josiah', eng && eng.element.initial_option);
  v = await step2(S('', 'booth', { fn: 'Japs' }), { free_rooms: ['M4', 'M5'] });
  const fnb = v.blocks.find(b => b.block_id === 'forname');
  if (SI33) {
    ok(fnb && fnb.element.initial_value === 'Japs', 'SI v33: M booth - Who is it for? starts on Japs', fnb && fnb.element);
    v = await step2(S('', 'booth', {}), { free_rooms: ['M4', 'M5'] });
    ok(v.blocks.find(b => b.block_id === 'forname').element.initial_value === 'Howard', 'no name typed -> your first name, as before');
    const meta = Object.assign(S('', 'booth'), { label: 'M booth', when: 'x' });
    const r2 = (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Cache 3': cacheRow,
      'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: { room: { room_radio: { selected_option: { value: 'M4' } } }, forname: { forname_in: { value: 'japs' } } } } } } } }] }))[0].json;
    ok(r2.again && r2.again.fn === 'Japs', '"Book a room" again keeps the name (Japs)', r2.again);
    // Dylan Diaz is "Dilan Diaz" in Bookers (Howard, 20 Oct): the fallbacks find him by either spelling
    const ST3 = STAFF.map(f => f.Name === 'Dylan Diaz' ? Object.assign({}, f, { Name: 'Dilan Diaz', Info: 'Multimedia Specialist, Goes by Dilan, Dylan.' }) : f);
    const cache3 = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: ST3.map((f, i) => ({ id: 'b' + i, fields: f })) }) } }];
    const PM = Object.assign(S('Post Processing', 'post'), { label: 'Post Processing', when: 'x' });
    const vals3 = { room: { room_radio: { selected_option: { value: 'Studio E' } } }, project: { project_in: { value: 'trailer' } } };
    const view3 = { id: 'V1', private_metadata: JSON.stringify(PM), blocks: [], state: { values: vals3 } };
    const r3 = (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Cache 3': cache3, 'Read Request': [{ json: { payload: { type: 'view_submission', view: view3 } } }] }))[0].json;
    ok(r3.valid && r3.calTitle === 'TRAILER / DD', 'an old Post Processing form (no Booker field) -> Dilan Diaz, TRAILER / DD', { v: r3.valid, t: r3.calTitle, e: r3.answer && r3.answer.errors });
    const bc = async b => (await run(si, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cache3 }))[0].json.view;
    let cv = await bc({ id: 'e1', d: '2027-10-21', s: '13:00', e: '15:00', r: 'Studio E', t: 'TRAILER / DD', st: 'Post Processing' });
    ok(cv.blocks.find(b => b.block_id === 'det_engineer').element.initial_option.text.text === 'Dilan Diaz', 'Change: TRAILER / DD -> Booker: Dilan Diaz');
    cv = await bc({ id: 'e1', d: '2027-10-21', s: '13:00', e: '15:00', r: 'Studio E', t: 'TRAILER / ZZ', st: 'Post Processing' });
    ok(cv.blocks.find(b => b.block_id === 'det_engineer').element.initial_option.text.text === 'Dilan Diaz', 'Change: initials nobody has -> starts on Dilan Diaz (the usual booker)');
  } else ok(true, '(SI v33 not in this build - the booth name check skipped)');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
