#!/usr/bin/env node
// Round 12 offline (Slack Interactions v30, 20 Oct): the Change form offers a Vocal booth / Holding rooms whenever the booking type
// does (and follows a type change); the project code without Enter; Post Processing's Booker as a dropdown set to the person
// booking; Repeats "How often?" with Weekly / Weekdays / Daily.
// Usage: node scripts/sim-round-12.js [slack-interactions v30]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v30.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
if (!/function pairBlocksC\(/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (round 12 is v30 on; this build is older)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
async function run(name, input, outs) {
  const js = si.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const ST = (t, req, pri, role) => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': req, Priority: pri, 'Last Resort': [], 'Engineer Role Required': role } });
const sessionTypes = FX.sessionTypes.concat([ST('Band Recording', 'Large', ['rf'], ['Music Engineer', 'Music Arranger']), ST('Van Recording', '', ['sm'], ['Post Engineer', 'Music Arranger']),
  ST('Atmos Mixing', 'Large', ['rc'], ['Post Engineer']), ST('Post Mixing', 'Stereo Mixing', ['r7'], ['Post Engineer'])]);
const rooms = FX.rooms.concat([{ id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'] } }]);
const B = (id, name, ini, slack, info) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.'), B('b4', 'BP Valenzuela', 'BPV', 'U9', 'Music Arranger'),
  B('b5', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer'), B('b7', 'Dylan Diaz', 'DD', 'U0BQ77XKWA3', 'Multimedia Specialist'), B('b8', 'Camy Caridad', 'CC', 'U5', 'Coordinator')];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const chk = u => ({ json: { user: u || 'U1', triggerId: 'T1', channel: 'D1' } });
const tv = v => ({ selected_option: { value: v } });
const blk = (v, id) => v.blocks.find(b => b.block_id === id);
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const buildChange = async (b) => (await j1('Build Change', [], { 'Check Signature': [chk()], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
const rcv = async (cv, vals) => j1('Read Change', [], { 'Check Signature': [chk()], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata, state: { values: vals } } } } }], 'Read Cache 10': cacheRow });
const toggle = async (view, action, extra, state) => run('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
  actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow, 'Loc Projects 9': [] });
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-21', t0: '13:00', t1: '16:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
const read2 = async (vv, meta, u) => j1('Read Step 2', [], { 'Check Signature': [chk(u)], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const BK = (st, r, t) => ({ id: 'e1', d: '2027-10-21', s: '13:00', e: '16:00', r, t, st });

(async () => {
  console.log('2: the Change form - Vocal booth / Holding rooms when the type offers them');
  let cv = await buildChange(BK('Band Recording', 'Studio F', 'BAND REC TEST / Sasa Abella / HL x BPV'));   // Howard's screenshot
  let bc = blk(cv, 'booth_c');
  ok(bc && bc.optional && !bc.element.initial_option && bc.element.placeholder.text === 'No booth' && bc.element.options.map(o => o.value).join() === 'Studio A,Studio B,Studio D' + (V39 ? ',none' : ''),
     'Band Recording in Studio F, no booth -> Vocal booth offered, empty ("No booth")', bc);
  ok(blk(cv, 'room').label.text === 'Studio' && ids(cv).indexOf('booth_c') === ids(cv).indexOf('room') + 1 && !blk(cv, 'holding_c'), 'right under Studio; no Holding rooms for Band Recording');
  cv = await buildChange(BK('Celebrity Recording', 'Studio F', 'CELEB / Jem Lim / HL'));
  ok(blk(cv, 'booth_c') && blk(cv, 'holding_c') && !blk(cv, 'holding_c').element.initial_options && blk(cv, 'holding_c').element.options.map(o => o.value).join() === 'Katha,Likha,Salin',
     'Celebrity Recording, no booth / holding rooms -> both offered, empty', blk(cv, 'holding_c'));
  cv = await buildChange(BK('Celebrity Recording', 'Studio F, Studio A, Likha', 'CELEB / Jem Lim / HL'));
  ok(blk(cv, 'booth_c').element.initial_option.value === 'Studio A' && blk(cv, 'holding_c').element.initial_options.map(o => o.value).join() === 'Likha', 'a booking with a booth and Likha -> both set as now (unchanged)');
  for (const [st, r, t] of [['Meeting', 'Likha', 'LIKHA - Weekly sync'], ['Van Recording', 'Studio M', 'VAN / HL'], ['Atmos Mixing', 'Studio C', 'ATMOS / HL'], ['Post Mixing', 'Studio 7', 'MIX / HL'], ['Post Processing', 'Studio E', 'TRAILER / DD']]) {
    cv = await buildChange(BK(st, r, t));
    ok(!blk(cv, 'booth_c') && !blk(cv, 'holding_c') && blk(cv, 'room').label.text === 'Room', st + ' -> neither (Room)');
  }
  cv = await buildChange(BK('Localization Dubbing', 'Studio 1', 'NET-MALAS / JT'));
  ok(blk(cv, 'booth_c') && !blk(cv, 'holding_c'), 'Localization Dubbing (needs a separate vocal booth) -> Vocal booth offered');
  // the band booking: a booth added
  cv = await buildChange(BK('Band Recording', 'Studio F', 'BAND REC TEST / HL'));
  const base = { date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio F') },
    purpose_c: { purpose_c: tv('Band Recording') }, det_project: { det_project_in: { value: 'BAND REC TEST' } }, det_client: { det_client_in: { value: '' } }, det_engineer: { det_engineer_pick: tv('U1') } };
  let rc = await rcv(cv, Object.assign({}, base, { booth_c: { booth_c_pick: tv('Studio A') } }));
  ok(rc.valid && rc.roomChanged && rc.newRooms === 'Studio F, Studio A', 'Studio A picked -> Move gets "Studio F, Studio A"', { v: rc.valid, r: rc.newRooms, e: rc.answer });
  rc = await rcv(cv, Object.assign({}, base, { booth_c: { booth_c_pick: {} } }));
  ok(!rc.valid && rc.answer.errors.date === 'Nothing changed.', 'left empty -> "Nothing changed." (an empty booth is no change)', rc.answer);
  // the type changed on the form
  const md = cv.private_metadata;
  let t = await toggle({ blocks: cv.blocks, private_metadata: md, callback_id: 'change_booking' }, 'purpose_c', { selected_option: { value: 'Celebrity Recording' } }, { booth_c: { booth_c_pick: tv('Studio B') } });
  let nv = t[0].json.view;
  ok(blk(nv, 'booth_c') && blk(nv, 'booth_c').element.initial_option.value === 'Studio B' && blk(nv, 'holding_c') && ids(nv).filter(x => x === 'booth_c').length === 1,
     'Band -> Celebrity Recording: Holding rooms added, the booth pick kept (Studio B)', ids(nv));
  t = await toggle({ blocks: nv.blocks, private_metadata: md, callback_id: 'change_booking' }, 'purpose_c', { selected_option: { value: 'Post Mixing' } }, {});
  nv = t[0].json.view;
  ok(!blk(nv, 'booth_c') && !blk(nv, 'holding_c'), 'Celebrity -> Post Mixing: both taken off (the booking has none)', ids(nv));
  cv = await buildChange(BK('VO Recording', 'Studio 7, Studio A', 'VO / HL'));
  t = await toggle({ blocks: cv.blocks, private_metadata: cv.private_metadata, callback_id: 'change_booking' }, 'purpose_c', { selected_option: { value: 'Post Mixing' } }, {});
  nv = t[0].json.view;
  ok(blk(nv, 'booth_c') && blk(nv, 'booth_c').element.initial_option.value === 'Studio A', 'a booking that has a booth keeps showing it, whatever the type');

  console.log('3: the project code - no Enter');
  let v = await step2(S('QC', 'loc'), { free_priority: ['Studio 3', 'Studio 5'] });
  let cb = blk(v, 'code');
  ok(cb && cb.element.type === 'plain_text_input' && !cb.dispatch_action && !cb.element.dispatch_action_config, 'QC step 2: Project code is a plain text box (no "Press \'enter\' to submit")');
  cv = await buildChange(BK('Localization Dubbing', 'Studio 1', 'NET-MALAS / HL'));
  cb = blk(cv, 'det_code');
  ok(cb && cb.element.initial_value === 'NET-MALAS' && !cb.dispatch_action && !cb.element.dispatch_action_config, 'Change: Project code - the code, no Enter');
  const enterBoxes = []; const walk = (x, n) => { if (!x || typeof x !== 'object') return; if (x.type === 'plain_text_input' && x.dispatch_action_config) enterBoxes.push(n); Object.values(x).forEach(y => walk(y, n)); };
  for (const n of si.nodes) { const js = (n.parameters || {}).jsCode || ''; if (/plain_text_input[^\n]*dispatch_action/.test(js) || /dispatch_action_config/.test(js)) enterBoxes.push(n.name); }
  ok(enterBoxes.length === 0, 'no text box anywhere reacts to Enter', enterBoxes);
  const r0 = await read2({ room: { room_radio: tv('Studio 3') }, code: { code_in: { value: 'net-malas' } }, engineer: { engineer_pick: tv('U1') } }, Object.assign(S('QC', 'loc'), { label: 'QC' }));
  ok(r0.valid && /^NET-MALAS \//.test(r0.calTitle), 'the code typed still books (NET-MALAS / …)', r0.calTitle);

  const V33P = /v33 \(Howard, 20 Oct\): "Who is it for\?"/.test(si.nodes.find(n => n.name === 'Build Step 2').parameters.jsCode);
  if (!V33P) {   // v33: Post Processing asks "Who is it for?" (sim-round-13)
  console.log('4: Post Processing - Booker is a dropdown');
  v = await step2(S('Post Processing', 'post'), { free_priority: ['Studio E'] });
  let bk = blk(v, 'booker');
  ok(bk && bk.type === 'input' && bk.element.action_id === 'booker_pick' && bk.element.initial_option.value === 'U1' && bk.element.options.length === 5 && bk.element.options[0].text.text === 'BP Valenzuela',
     'Booker: everyone in Bookers A-Z, set to the person booking (Howard)', bk && bk.element);
  ok(ids(v).indexOf('booker') < ids(v).indexOf('project'), 'above Project title (as before)');
  v = await step2(S('Post Processing', 'post', { requester: 'UNOBODY' }), { free_priority: ['Studio E'] });
  ok(!blk(v, 'booker').element.initial_option && blk(v, 'booker').element.placeholder.text === 'Select a booker', 'someone not in Bookers -> empty, "Select a booker"');
  v = await step2(S('Post Processing', 'post', { pre: { en: 'U0BQ77XKWA3' } }), { free_priority: ['Studio E'] });
  ok(blk(v, 'booker').element.initial_option.value === 'U0BQ77XKWA3', '"Book a room" again (filled in) -> the booker it had (Dylan)');
  const PM = Object.assign(S('Post Processing', 'post'), { label: 'Post Processing' });
  let r = await read2({ room: { room_radio: tv('Studio E') }, booker: { booker_pick: tv('U1') }, project: { project_in: { value: 'trailer cut' } } }, PM);
  ok(r.valid && r.calTitle === 'TRAILER CUT / HL' && r.team === '', 'Howard picked -> TRAILER CUT / HL, no engineer notice', { t: r.calTitle, team: r.team });
  r = await read2({ room: { room_radio: tv('Studio E') }, booker: { booker_pick: tv('U0BQ77XKWA3') }, project: { project_in: { value: 'trailer cut' } } }, PM);
  ok(r.valid && r.calTitle === 'TRAILER CUT / DD', 'Dylan picked -> TRAILER CUT / DD');
  r = await read2({ room: { room_radio: tv('Studio E') }, project: { project_in: { value: 'trailer cut' } } }, PM);
  ok(r.valid && r.calTitle === 'TRAILER CUT / DD', 'a form opened before v30 (no Booker field) -> Dylan, as before');
  cv = await buildChange(BK('Post Processing', 'Studio E', 'TRAILER / DD'));
  const db = blk(cv, 'det_engineer');
  ok(db && db.label.text === 'Booker' && !db.optional && db.element.initial_option.value === 'U0BQ77XKWA3' && !blk(cv, 'det_booker'), 'Change: Booker dropdown, set to the booking\'s booker (DD -> Dylan)', db);
  const pbase = { date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio E') },
    purpose_c: { purpose_c: tv('Post Processing') }, det_project: { det_project_in: { value: 'TRAILER' } } };
  rc = await rcv(cv, Object.assign({}, pbase, { det_engineer: { det_engineer_pick: tv('U1') } }));
  ok(rc.valid && rc.newTitle === 'TRAILER / HL' && rc.newDetails && rc.newDetails.team === '' && rc.newDetails.Engineer === 'Howard Luistro', 'Change: Dylan -> Howard -> TRAILER / HL, no engineer notice', { t: rc.newTitle, d: rc.newDetails, e: rc.answer });
  rc = await rcv(cv, Object.assign({}, pbase, { det_engineer: { det_engineer_pick: tv('U0BQ77XKWA3') } }));
  ok(!rc.valid && rc.answer.errors.date === 'Nothing changed.', 'Change: Dylan kept -> "Nothing changed."', rc.answer);
  // other kinds keep their engineer notice
  cv = await buildChange(BK('VO Recording', 'Studio 7', 'VO / HL'));
  rc = await rcv(cv, { date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') },
    purpose_c: { purpose_c: tv('VO Recording') }, det_project: { det_project_in: { value: 'VO' } }, det_client: { det_client_in: { value: '' } }, det_engineer: { det_engineer_pick: tv('U2') } });
  ok(rc.valid && rc.newDetails && rc.newDetails.team === 'U2', 'VO Recording: a new engineer is still told (unchanged)', rc.newDetails);

  }
  console.log('5: Repeats wording');
  const s1 = (await j1('Build Step 1', [], { 'Check Signature': [chk()], 'Read Cache': cacheRow, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: JSON.stringify({ d: '2027-10-20', rep: { f: 'weekly', days: ['WE'] } }) }], container: { channel_id: 'D1', message_ts: '9.9' } } } }] })).view;
  const fq = s1.blocks.find(b => b.block_id === 'rep_freq');
  ok(fq && fq.label.text === 'How often?' && fq.element.options.map(o => o.text.text + '=' + o.value).join() === 'Weekly=weekly,Weekdays=weekdays,Daily=daily', 'Book step 1: "How often?" - Weekly / Weekdays / Daily (values unchanged)', fq);
  t = await toggle({ blocks: [{ type: 'actions', block_id: 'repeat_toggle', elements: [] }, { type: 'input', block_id: 'date', element: { type: 'datepicker', initial_date: '2027-10-20' } }], private_metadata: '{}', callback_id: 'book_step1' },
    'repeat_toggle', { selected_options: [{ value: 'on' }] }, { date: { date_pick: { selected_date: '2027-10-20' } } });
  const fq2 = t[0].json.view.blocks.find(b => b.block_id === 'rep_freq');
  ok(fq2 && fq2.label.text === 'How often?' && fq2.element.options[0].text.text === 'Weekly', 'Repeats ticked -> the same labels');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
