#!/usr/bin/env node
// The 20 Nov round: Slack Interactions v82 ("Bookings" first in What's it for? - M booth, Meeting, Event - then the session types)
// and **Post Processing renamed Multimedia Post** in Airtable (Post Mixing unchanged): every Post Processing rule holds for
// Multimedia Post - Studio E, the title "MULTIMEDIA POST - <PROJECT> / <who>", the colour, no client lookups, the AI's type list, a
// typed "post processing" - across Slack Interactions v82, main v295, Book Session v131, Move v45, Book Series v12, Room Check v3.
//   node scripts/sim-multimedia-post.js
const fs = require('fs');
const L = f => JSON.parse(fs.readFileSync('workflows/' + f + '.json', 'utf8'));
const SI = L('slack-interactions-v82'), MAIN = L('project-jessie-v295'), BS = L('book-session-v131'), MV = L('move-booking-v45'), BSR = L('book-series-v12'), RC = L('room-check-v3');
const OLD = { SI: L('slack-interactions-v81'), MAIN: L('project-jessie-v294'), BS: L('book-session-v130'), MV: L('move-booking-v44'), BSR: L('book-series-v11'), RC: L('room-check-v2') };
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const jsOf = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const run = async (w, name, input, O) => new Function('$', '$input', 'return (async function(){' + jsOf(w, name) + '\n})();')($f(O), { first: () => input[0] || { json: {} }, all: () => input });
const roomId = n => (FX.rooms.find(r => r.fields['Room Name'] === n) || {}).id;
const TYPES = FX.sessionTypes.filter(t => !/^(Post Processing|Post Mixing)$/.test(t.fields.Type)).concat([
  { id: 'stMP', fields: { Type: 'Multimedia Post', Priority: [roomId('Studio E')].filter(Boolean) } }, { id: 'stPM', fields: { Type: 'Post Mixing', Priority: [] } }, { id: 'stEv', fields: { Type: 'Event', Priority: [] } }]);
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: TYPES, bookers: FX.bookers }) } }];

(async () => {
  console.log('Post Mixing is kept, everywhere');
  for (const [k, w] of Object.entries({ SI, MAIN, BS, MV, BSR, RC })) {
    const n = s => (JSON.stringify(s.nodes).match(/post mixing/gi) || []).length;
    ok(n(w) === n(OLD[k]), k + ': "Post Mixing" references unchanged (' + n(w) + ')');
  }
  const tool = JSON.stringify(MAIN.nodes.find(n => n.name === 'Session Types').parameters);
  ok(/Meeting, Multimedia Post, Music Arranging/.test(tool) && /Music Recording, Post Mixing, QC/.test(tool) && !/Post Processing/.test(tool), 'the AI\'s type list: Multimedia Post in, Post Mixing kept, Post Processing out');

  console.log('Slack Interactions v82');
  const s1 = (await run(SI, 'Build Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }], 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: 'menu' }] } } }] }))[0].json;
  const g = (s1.view || {}).blocks.find(b => b.element && b.element.action_id === 'purpose_pick').element.option_groups;
  ok(g[0].label.text === 'Bookings' && g[0].options.map(o => o.value).join() === '__booth,Meeting,Event', '"Bookings" first: M booth, Meeting, Event', g.map(x => [x.label.text, x.options.map(o => o.value)]));
  ok(g[1].label.text === 'Sessions' && ['Multimedia Post', 'Post Mixing'].every(t => g[1].options.some(o => o.value === t)), 'then "Sessions" - Multimedia Post and Post Mixing both there', g[1].options.map(o => o.value));
  const ra = new Function(jsOf(SI, 'Build Step 2').match(/function roomAllowed[\s\S]*?\n}/)[0] + '\nreturn roomAllowed;')();
  ok(ra('Studio E', 'Multimedia Post') && ra('Studio E', 'Post Processing') && !ra('Studio E', 'VO Recording') && !ra('Studio E', 'Post Mixing') && ra('Studio 7', 'Multimedia Post'),
    'Studio E: only for Multimedia Post (old name too) - not for VO Recording or Post Mixing');
  ok(/'MULTIMEDIA POST - ' \+ \(project/.test(jsOf(SI, 'Read Step 2')), 'a new booking\'s title: "MULTIMEDIA POST - <PROJECT> / <who>"');
  ok(/kind: 'post'/.test(jsOf(SI, 'Read Step 1')) || /\? 'post' :/.test(jsOf(SI, 'Read Step 1')), 'Multimedia Post is the "post" kind (Booker, Who is it for?)');
  const k1 = new Function('purpose', 'return ' + jsOf(SI, 'Read Step 1').match(/\/atmos\/i\.test\(purpose\) \? 'atmos' : [^;]+/)[0] + ';');
  ok(k1('Multimedia Post') === 'post' && k1('Post Mixing') === 'studio', 'Read Step 1: Multimedia Post -> post kind; Post Mixing -> studio, as before');

  console.log('Book Session v131 (whole Check Conflicts)');
  const refRooms = FX.rooms.map(x => ({ id: x.id, name: x.fields['Room Name'], vocalBooth: !!x.fields['Vocal Booth'], booth: false, common: /conference|lobby/i.test(String(x.fields['Room Type'] || '')) }));
  const refTypes = TYPES.map(s => ({ type: s.fields.Type, priority: [].concat(s.fields.Priority || []).map(id => (FX.rooms.find(x => x.id === id) || { fields: {} }).fields['Room Name']).filter(Boolean), lastResort: [], min: 30, max: 600, requirements: '' }));
  const STAFF = [{ Name: 'Eng Person', Initials: 'EP', 'Slack User ID': 'U9', Info: 'Post Engineer', Department: ['Audio Post'] }];
  const req = o => Object.assign({ mode: 'prepare', confirmed: false, summary: 'MULTIMEDIA POST - ORANGE / Juan', start_iso: '2026-11-24T10:00:00+08:00', end_iso: '2026-11-24T12:00:00+08:00', rooms: 'Studio E',
    all_day: false, session_type: 'Multimedia Post', client: '', engineer: '', bookingType: '', department: 'Audio Post', authority: '', expected_date: '2026-11-24',
    requester_text: 'Multimedia Post in Studio E on 2026-11-24 10:00 am-12:00 pm, project ORANGE, for Juan, no client', staff_data: JSON.stringify(STAFF),
    reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: {} }), description: 'Booked by: Eng Person | ref: U9 | Dept: Audio Post', exclude_event_id: '', room_override: false, series: false }, o);
  const cc = (w, r) => { const outs = { 'When Executed by Another Workflow': [r], 'Get Events In Window': [{ items: [] }], 'Room Free Busy': [{}], 'All Bookers': STAFF.map(f => ({ fields: f })), 'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
    return new Function('$', '$input', jsOf(w, 'Check Conflicts'))(n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) }), { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json; };
  let b = cc(BS, req({}));
  ok(b.verdict !== 'REJECTED', 'Multimedia Post in Studio E, "MULTIMEDIA POST - ORANGE / Juan" -> not refused', { v: b.verdict, r: b.reason, h: String(b.human || '').slice(0, 200) });
  ok(b.final_color === '1' || /"final_color":"1"/.test(JSON.stringify(b)), 'its colour: Lavender (1), as Post Processing', b.final_color);
  b = cc(BS, req({ session_type: 'VO Recording', summary: 'ORANGE / EP', requester_text: 'VO Recording in Studio E on 2026-11-24 10:00 am-12:00 pm, project ORANGE, no client' }));
  ok(b.verdict === 'REJECTED' && /Studio E is only for Multimedia Post/.test(b.human || ''), 'VO Recording in Studio E -> "Studio E is only for Multimedia Post."', { r: b.reason, h: b.human });
  b = cc(OLD.BS, req({}));
  ok(b.verdict === 'REJECTED' && /Studio E is only for Post Processing/.test(b.human || ''), 'v130 (live) with Airtable already renamed: Multimedia Post in Studio E is refused - the gap this closes', { r: b.reason, h: b.human });
  ok(/multimedia post\|meeting\|event/.test(jsOf(BS, 'Client Cache')), 'no client lookups for Multimedia Post');

  console.log('Move v45, Book Series v12, Room Check v3');
  ok(/t === 'multimedia post'\) return '1'/.test(jsOf(MV, 'Resolve Booking')), 'Move: a changed Multimedia Post booking keeps Lavender');
  ok(/\(\?:post processing\|multimedia post\)/.test(jsOf(BSR, 'Aggregate')), 'Book Series: a Multimedia Post series is the post kind');
  const pp = jsOf(RC, 'Build DM').match(/title\.match\((\/[^\n]*?\/i)\)/)[1];
  const re = new Function('return ' + pp)();
  ok(re.test('MULTIMEDIA POST - ORANGE / Juan') && re.test('POST PROCESSING - ORANGE / Juan') && /again\.p \|\| 'Multimedia Post'/.test(jsOf(RC, 'Build DM')), 'Room Check: both titles read; Book a room again filled in as Multimedia Post');

  console.log('main v295 (Form Offer)');
  const offer = async text => { Date.now = () => Date.parse('2026-11-20T03:00:00Z');
    const base = { 'Slack Trigger': [{ json: { text, user: 'U1', ts: '1794500000.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '1794500000.1', text, user: 'U1' } }],
      'Get Booker': [{ json: { fields: FX.bookers[0].fields } }], 'All Bookers': FX.bookers.map(x => ({ json: x })), 'All Rooms': FX.rooms.map(r => ({ json: r })), 'All Session Types': TYPES.map(t => ({ json: t })) };
    base['Gate Context'] = [{ json: new Function('$', '$input', '$getWorkflowStaticData', jsOf(MAIN, 'Gate Context'))($f(base), { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json }];
    base['Booked For'] = [{ json: new Function('$', '$input', jsOf(MAIN, 'Booked For'))($f(base), { first: () => ({ json: {} }) })[0].json }];
    return (await run(MAIN, 'Form Offer', [{ json: { keep: 1 } }], base))[0].json.formOffer; };
  for (const [t, want] of [['book studio 7 tomorrow 2-4pm for post processing', 'Multimedia Post'], ['book studio e tomorrow 2-4pm', 'Multimedia Post'],
    ['book studio 7 tomorrow 2-4pm multimedia post', 'Multimedia Post'], ['book studio 7 tomorrow 2-4pm post mixing', 'Post Mixing']]) {
    const fo = await offer(t); ok(fo && fo.prefill && fo.prefill.p === want, JSON.stringify(t) + ' -> ' + want, fo && fo.prefill); }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
