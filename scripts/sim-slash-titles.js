#!/usr/bin/env node
// Slack Interactions v50 (27 Oct): a slash typed inside a title part (project, client, code, meeting title, "Who is it for?")
// becomes " - ", so a title always has its " / " parts and nothing else - Book a room (Read Step 2) and Change (Read Change).
// Found in Howard's test: "Backyard Live // Test Session" -> "BACKYARD LIVE // TEST SESSION / SONY MUSIC / AEG x BPV".
// Usage: node scripts/sim-slash-titles.js [slack-interactions v50]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v50.json', 'utf8'));
if (!/noSlash|v50 \(27 Oct\): a slash typed/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (an older build: v50 not in it)'); process.exit(0); }
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
const B = (id, name, ini, slack, info) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.'), B('b4', 'BP Valenzuela', 'BPV', 'U9', 'Music Arranger'),
  B('b5', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer'), B('b7', 'Dylan Diaz', 'DD', 'U0BQ77XKWA3', 'Multimedia Specialist')];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const chk = () => ({ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } });
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind) => ({ date: '2027-10-21', t0: '13:00', t1: '16:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x', label: purpose });
const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [chk()], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const st = FX.sessionTypes.find(t => /vo recording/i.test(t.fields.Type)) || FX.sessionTypes[0];
const ST = st.fields.Type;

(async () => {
  console.log('Book a room');
  let r = await read2({ room: { room_radio: tv('Studio 3') }, project: { project_in: { value: 'Backyard Live // Test Session' } }, client: { client_in: { value: 'Sony Music' } },
    engineer: { engineer_pick: tv('U2') } }, S(ST, 'studio'));
  ok(r.valid && /^BACKYARD LIVE - TEST SESSION \/ Sony Music \/ DR$/.test(r.calTitle) && r.calTitle.split(' / ').length === 3, '"Backyard Live // Test Session" -> BACKYARD LIVE - TEST SESSION / Sony Music / DR (three parts)', { v: r.valid, t: r.calTitle, e: r.answer && r.answer.errors });
  r = await read2({ room: { room_radio: tv('Studio 3') }, project: { project_in: { value: 'Song/Remix' } }, client: { client_in: { value: 'Acme / Records' } }, engineer: { engineer_pick: tv('U2') } }, S(ST, 'studio'));
  ok(r.calTitle === 'SONG - REMIX / Acme - Records / DR' && r.prep.client === 'Acme - Records', 'one slash, with or without spaces, in project and client -> " - " (the client Book Session gets too)', { t: r.calTitle, c: r.prep && r.prep.client });
  r = await read2({ room: { room_radio: tv('Studio 3') }, project: { project_in: { value: '/Teaser/' } }, engineer: { engineer_pick: tv('U2') } }, S(ST, 'studio'));
  ok(r.calTitle === 'TEASER / DR', 'a slash at either end is dropped -> TEASER / DR', r.calTitle);
  r = await read2({ room: { room_radio: tv('Studio 3') }, project: { project_in: { value: 'Backyard Live - Test' } }, engineer: { engineer_pick: tv('U2') } }, S(ST, 'studio'));
  ok(r.calTitle === 'BACKYARD LIVE - TEST / DR', 'no slash -> unchanged');
  r = await read2({ room: { room_radio: tv('Studio 3') }, code: { code_in: { value: 'net/malas' } }, engineer: { engineer_pick: tv('U2') } }, S('QC', 'loc'));
  ok(r.calTitle === 'NET - MALAS / DR', 'a project code -> NET - MALAS / DR', r.calTitle);
  r = await read2({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'Plan / review' } } }, S('Meeting', 'meeting'));
  ok(r.calTitle === 'LIKHA - Plan - review' && !/\//.test(r.calTitle), 'a meeting title -> LIKHA - Plan - review', { t: r.calTitle, e: r.answer && r.answer.errors });
  r = await read2({ room: { room_radio: tv('Studio E') }, forname: { forname_in: { value: 'Sasa/Lyn' } }, project: { project_in: { value: 'trailer' } } }, S('Post Processing', 'post'));
  ok(/^POST PROCESSING - TRAILER \/ Sasa - Lyn$/.test(r.calTitle), 'Post Processing "Who is it for?" -> POST PROCESSING - TRAILER / Sasa - Lyn', { t: r.calTitle, e: r.answer && r.answer.errors });

  console.log('Change');
  const js = si.nodes.find(x => x.name === 'Read Change').parameters.jsCode;
  const line = (js.match(/\['project', 'client', 'code', 'title', 'forname'\]\.forEach\(k => \{ d\[k\] = (.+?); \}\);/) || [])[1];
  ok(!!line && js.indexOf(line) > js.indexOf("d.client = capWords(d.client);") && js.indexOf(line) < js.indexOf('d.st = sel('), 'Read Change: the typed details cleaned right after they are read, before anything uses them');
  const clean = new Function('d', 'k', 'return ' + line + ';');
  const t = (x) => clean({ v: x }, 'v');
  ok(t('Backyard Live // Test Session') === 'Backyard Live - Test Session' && t('Acme / Records') === 'Acme - Records' && t('/Teaser/') === 'Teaser' && t('') === '' && t(undefined) === '',
     'the same rule on Change: // and / -> " - ", ends dropped, empty stays empty');
  // the whole Change path: Build Change draws the form, Read Change reads it
  const bk = { id: 'e1', d: '2027-10-21', s: '13:00', e: '16:00', r: 'Studio 3', t: 'SONG / Acme / DR', st: ST };
  const cv = (await j1('Build Change', [], { 'Check Signature': [chk()], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(bk) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
  const rc = await j1('Read Change', [], { 'Check Signature': [chk()], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata, state: { values: {
    date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 3') }, purpose_c: { purpose_c: tv(ST) },
    det_project: { det_project_in: { value: 'Song // Remix' } }, det_client: { det_client_in: { value: 'Acme/Records' } }, det_engineer: { det_engineer_pick: tv('U2') } } } } } } }], 'Read Cache 10': cacheRow });
  ok(rc.valid && rc.newTitle === 'SONG - REMIX / Acme - Records / DR', 'Change: project "Song // Remix", client "Acme/Records" -> SONG - REMIX / Acme - Records / DR', { v: rc.valid, t: rc.newTitle, e: rc.answer });
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + e.stack); process.exit(1); });
