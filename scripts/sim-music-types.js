#!/usr/bin/env node
// Music types (Howard, 20 Oct): Music Arranging, Music Mixing, Music Presentation, Music Recording (was Music Vocal Recording), plus
// Band Recording. Slack Interactions v33: for a Music session the Arranger comes above the Engineer (Book and Change); an engineer
// OR an arranger when the type lists both (Airtable Engineer Role Required). main v277: typed types incl. "vocal recording".
// Book Session v118: its list of Music types. Session types as in Airtable on 20 Oct 21:43 PHT.
// Usage: node scripts/sim-music-types.js [slack-interactions v33] [main v277] [book-session v118]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v33.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v277.json', 'utf8'));
const bs = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/book-session-v118.json', 'utf8'));
if (!/function arrFirst\(/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (the music types are Slack Interactions v33 on; this build is older)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
async function run(wf, name, input, outs) {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const ST = (t, roles, pri) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri || ['rf', 'r7', 'r8', 'rc'], 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '' } });
const ME = 'Music Engineer', MA = 'Music Arranger';
const typesNow = [ST('Music Arranging', [MA]), ST('Music Presentation', [MA]), ST('Music Mixing', [ME, MA]), ST('Music Recording', [ME, MA], ['rf', 'rc']),
  ST('Band Recording', [ME, MA], ['rf', 'rc']), ST('Celebrity Recording', [ME, 'Post Engineer', MA], ['rf', 'rc']), ST('VO Recording', ['Post Engineer'], ['r7', 'r8'])];
const typesAfter = typesNow.map(t => /^Music (Arranging|Presentation)$/.test(t.fields.Type) ? ST(t.fields.Type, [ME, MA]) : t);   // once Music Engineer is added in Airtable
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: [dept] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer', 'Audio Post'), B('b2', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer, Goes by Daryl.', 'Music'),
  B('b3', 'BP Valenzuela', 'BPV', 'U9', 'Music Arranger, Goes by BP.', 'Music')];
const cache = types => [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: types, bookers }) } }];
const S = (purpose) => ({ date: '2027-10-22', t0: '14:00', t1: '16:00', purpose, kind: 'studio', requester: 'U2', channel: 'D1', ext: 'x' });
const step2 = async (types, purpose) => (await run(si, 'Build Step 2', [{ json: { status: 'OK', busy: [], free_priority: ['Studio F', 'Studio 7'] } }], { 'Read Step 1': [{ json: { s: S(purpose) } }], 'Read Cache 2': cache(types), 'Loc Projects 2': [] }))[0].json.view;
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const tv = v => ({ selected_option: { value: v } });

(async () => {
  console.log('the form: Arranger above Engineer for Music, either one');
  for (const t of ['Music Mixing', 'Music Recording', 'Band Recording']) {
    const v = await step2(typesNow, t), x = ids(v), a = v.blocks.find(b => b.block_id === 'arranger'), e = v.blocks.find(b => b.block_id === 'engineer');
    ok(x.indexOf('arranger') !== -1 && x.indexOf('arranger') < x.indexOf('engineer') && a.optional && e.optional, t + ': Arranger then Engineer, both optional (either one)', x);
  }
  let v = await step2(typesNow, 'Celebrity Recording');
  ok(ids(v).indexOf('engineer') < ids(v).indexOf('arranger'), 'Celebrity Recording (Music + Post): Engineer first, as before');
  v = await step2(typesNow, 'VO Recording');
  ok(!ids(v).includes('arranger') && ids(v).includes('engineer'), 'VO Recording: Engineer only, as before');
  for (const t of ['Music Arranging', 'Music Presentation']) {
    v = await step2(typesNow, t);
    const a = v.blocks.find(b => b.block_id === 'arranger');
    ok(a && !a.optional && !ids(v).includes('engineer'), t + ' (Airtable today: Music Arranger only) -> Arranger required, no Engineer', ids(v));
    v = await step2(typesAfter, t);
    ok(ids(v).indexOf('arranger') < ids(v).indexOf('engineer') && v.blocks.find(b => b.block_id === 'arranger').optional, t + ' (once Music Engineer is added in Airtable) -> either one, Arranger first', ids(v));
  }
  console.log('booking them');
  const read2 = async (types, purpose, vals) => (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U2' } }], 'Read Cache 3': cache(types),
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(Object.assign(S(purpose), { label: purpose, when: 'x' })), blocks: [], state: { values: vals } } } } }] }))[0].json;
  let r = await read2(typesNow, 'Music Presentation', { room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'pitch' } }, arranger: { arranger_pick: tv('U9') } });
  ok(r.valid && r.calTitle === 'PITCH / BPV' && r.prep.session_type === 'Music Presentation', 'Music Presentation with BP -> PITCH / BPV', { v: r.valid, t: r.calTitle, e: r.answer && r.answer.errors });
  r = await read2(typesAfter, 'Music Arranging', { room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'theme' } }, engineer: { engineer_pick: tv('U2') } });
  ok(r.valid && r.calTitle === 'THEME / DR', 'Music Arranging with only an engineer (after the Airtable change) -> THEME / DR', { v: r.valid, t: r.calTitle });
  r = await read2(typesNow, 'Music Recording', { room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'song' } } });
  ok(!r.valid && /Pick an engineer or an arranger/.test(JSON.stringify(r.answer.errors)), 'Music Recording with neither -> "Pick an engineer or an arranger."');
  r = await read2(typesNow, 'Music Arranging', { room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'theme' } } });
  ok(!r.valid && r.answer.errors.arranger === 'Pick the arranger.', 'Music Arranging (arranger only, today) with no arranger -> "Pick the arranger."', r.answer && r.answer.errors);
  console.log('the Change form');
  const bc = async (types, b) => (await run(si, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U2', triggerId: 'T1', channel: 'D1' } }], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cache(types) }))[0].json.view;
  let cv = await bc(typesNow, { id: 'e1', d: '2027-10-22', s: '14:00', e: '16:00', r: 'Studio F', t: 'SONG / DR x BPV', st: 'Music Recording' });
  ok(ids(cv).indexOf('det_arranger') < ids(cv).indexOf('det_engineer') && cv.blocks.find(b => b.block_id === 'det_arranger').element.initial_option.value === 'U9', 'Change a Music Recording: Arranger (BP) above Engineer', ids(cv));
  cv = await bc(typesNow, { id: 'e2', d: '2027-10-22', s: '14:00', e: '16:00', r: 'Studio F', t: 'CELEB / Jem Lim / DR', st: 'Celebrity Recording' });
  ok(ids(cv).indexOf('det_engineer') < ids(cv).indexOf('det_arranger'), 'Change a Celebrity Recording: Engineer first, as before');
  console.log('typed requests and Book Session');
  const TYPES = typesNow.map(t => t.fields.Type).concat(['Post Mixing', 'Localization Dubbing', 'Meeting']);
  const offer = async text => (await run(main, 'Form Offer', [{ json: {} }], { 'All Rooms': FX.rooms.map(r => ({ json: r })), 'All Session Types': TYPES.map(t => ({ json: { fields: { Type: t } } })),
    'All Bookers': bookers.map(b => ({ json: b })), 'Slack Trigger': [{ json: { text, channel: 'D1', ts: '1' } }], 'Gate Context': [{ json: { datesInMessage: '2027-10-22', confirmed: false, gate: {} } }],
    'Booked For': [{ json: { requesterText: text } }], 'Get Recent Messages': [] }))[0].json.formOffer.prefill;
  for (const [text, want] of [['book studio f tomorrow 2-4pm vocal recording', 'Music Recording'], ['book studio f tomorrow 2-4pm music recording', 'Music Recording'],
    ['book studio 7 tomorrow 2-4pm for arranging', 'Music Arranging'], ['book studio f tomorrow 2-4pm music presentation', 'Music Presentation'], ['book studio 7 tomorrow 2-4pm music mixing', 'Music Mixing']]) {
    const P = await offer(text); ok(P.p === want, JSON.stringify(text) + ' -> ' + want, P.p);
  }
  for (const [text, want] of [['book studio 7 tomorrow 2-4pm voiceover', 'VO Recording'], ['book studio 7 tomorrow 2-4pm voice over', 'VO Recording'], ['book studio 7 tomorrow 2-4pm vo recording', 'VO Recording']]) {
    const P = await offer(text); ok(P.p === want, JSON.stringify(text) + ' -> ' + want + ' (Howard: careful with voiceover)', P.p);
  }
  ok((await offer('book studio 7 tomorrow 2-4pm voice recording')).p !== 'Music Recording', '"voice recording" is not taken as Music Recording (voice is not vocal)');
  const st = JSON.stringify(main.nodes.find(n => n.name === 'Session Types').parameters);
  ok(/Music Arranging, Music Mixing, Music Presentation, Music Recording/.test(st) && !/Music Vocal Recording/.test(st), 'main: the Session Types lookup lists the new Music types');
  const cc = bs.nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode;
  ok(/'music': \['Music Recording', 'Music Vocal Recording', 'Band Recording', 'Music Mixing', 'Music Arranging', 'Music Presentation'\]/.test(cc), 'Book Session: the Music types, the old name kept for old bookings');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
