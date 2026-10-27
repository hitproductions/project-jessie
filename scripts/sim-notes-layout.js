#!/usr/bin/env node
// (harness from sim-book-v121.js) Book Session v121 (22 Oct, QA): the form's booking type wins when it is one of those named - Van Recording with an arranger (the
// department "Music" in the form's words named Music Recording too) was refused NEED_SESSION_TYPE. Every Airtable type from the form.


// Usage: node scripts/sim-book-v119.js [slack-interactions] [book-session v119]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const si = require(P + (process.argv[2] || 'workflows/imported/slack-interactions-v43-imported.json'));
const bs = require(P + (process.argv[3] || 'workflows/book-session-v122.json'));
const si2 = process.argv[2] ? require(P + process.argv[2]) : null;
const FX = require(P + 'scripts/sim-fixture-rooms.js');
const node = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
const run = async (wf, name, input, outs) => { const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(wf, name) + '\n})();')($, $input); };
const ST = (t, roles, pri) => ({ id: 'st-' + t.replace(/\s/g, ''), fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '', 'Min Duration': 0, 'Max Duration': 0 } });
const MM = ['Music Arranger', 'Music Engineer'];
const ALLT=['Celebrity Recording','QC','Van Recording','Post Mixing','Localization Editing','Post Processing','Event','Music Recording','Localization Mixing','Meeting','Music Presentation','Band Recording','Localization Dubbing','Localization Atmos Mixing','Music Mixing','Music Arranging','VO Recording'];
const sessionTypes = ALLT.map(t => ST(t, t==='Van Recording'?['Post Engineer','Music Arranger']:MM, t==='Van Recording'?['rm']:['rf','r7','r8','rc']));
FX.rooms.push({ id: 'rm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Recording Control Room'] } });

const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: [dept], Authority: ['Standard'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.', 'Audio Post'), B('b2', 'Mike Villegas', 'MV', 'U3', 'Head of Music, Arranger', 'Music'),
  B('b3', 'Dilan Diaz', 'DD', 'U7', 'Multimedia Specialist, Goes by Dilan.', 'Marketing')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes, bookers }) } }];
const one = async (PURPOSE, ROOM, NOTE) => {
  const s = { date: '2027-10-21', t0: '12:00', t1: '14:00', purpose: PURPOSE, kind: 'studio', requester: 'U1', channel: 'D1', ext: 'x', label: PURPOSE, when: 'x',
    pre: { d: '2027-10-21', s: '12:00', e: '14:00', r: 'Studio E', p: 'Post Processing', fn: 'Dilan' }, asked: '' };
  const vals = { 'room~1': { room_radio: { selected_option: { value: ROOM } } }, project: { project_in: { value: 'musicpres' } }, client: { client_in: { value: 'jem lim' } },
    arranger: { arranger_pick: { selected_option: { value: 'U3' } } }, engineer: { engineer_pick: { selected_option: { value: 'U1' } } } };
  if (NOTE) vals.notes = { notes_in: { value: NOTE } };
  const r2 = (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Cache 3': cache,
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(s), blocks: [], state: { values: vals } } } } }] }))[0].json;
  const tp = (await run(si, 'To Prepare', [], { 'Read Step 2': [{ json: r2 }], 'Read Cache 3': cache }))[0].json;
  const outs = { 'When Executed by Another Workflow': [{ json: tp }], 'Get Events In Window': [{ json: { items: [] } }], 'All Bookers': bookers.map(b => ({ json: b })),
    'Client Cache': [{ json: { use: false } }], 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim', 'Client Type': 'Advertising' } } }], 'Client Aliases': [{ json: {} }], 'All Client Names': [{ json: { fields: { Name: 'Jem Lim' } } }] };
  const $ = n => ({ first: () => (outs[n] || [{ json: {} }])[0], all: () => outs[n] || [] });
  const cc = new Function('$', '$input', node(bs, 'Check Conflicts'))($, { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json;
  return { cc, tp };
};


// Book Session v122 / Move v37 / Cancel v31 (26 Oct, Howard): the note on its own under the technical lines -
//   Engineer: … | Booked by: … | ref: … | Type: … | Dept: …
//   SType: …
//
//   Notes:
//   <the note>
// and Cancel / Move read the booking's department to the line's end (it took the SType line along).
// Usage: node scripts/sim-notes-layout.js [slack-interactions] [book-session v122] [move v37] [cancel v31]
const mv = require(P + (process.argv[4] || 'workflows/move-booking-v37.json'));
const cx = require(P + (process.argv[5] || 'workflows/cancel-booking-v31.json'));
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
// what Create Event writes: its description expression, worked out
const descOf = (cc, tp) => { const ex = bs.nodes.find(n => n.name === 'Create Event').parameters.additionalFields.description.replace(/^=\{\{|\}\}$/g, '');
  const $ = n => ({ first: () => ({ json: n === 'Check Conflicts' ? cc : tp }) }); return new Function('$', 'return (' + ex + ');')($); };
(async () => {
  console.log('Book Session v122');
  let { cc, tp } = await one('VO Recording', 'Studio 7', 'Bring the script.\nTalent arrives 9:30');
  ok(/Notes: Bring the script/.test(tp.description), 'the form still sends the note inline (Slack Interactions unchanged)');
  ok(cc.verdict === 'CLEAR' && !/Notes/.test(cc.final_description) && cc.final_notes === 'Bring the script.\nTalent arrives 9:30', 'Check Conflicts: the note leaves the technical line', [cc.final_description, cc.final_notes]);
  let d = descOf(cc, tp);
  ok(/^Engineer: [^\n]+\| ref: U1[^\n]*\nSType: VO Recording\n\nNotes:\nBring the script\.\nTalent arrives 9:30$/.test(d), 'the event: the technical line, SType, a blank line, Notes: and the note', d);
  ({ cc, tp } = await one('VO Recording', 'Studio 7', ''));
  d = descOf(cc, tp);
  ok(!/Notes/.test(d) && /\nSType: VO Recording$/.test(d), 'no note -> no Notes block, as before', d);
  console.log('Move v37');
  const rb = mv.nodes.find(n => n.name === 'Resolve Booking').parameters.jsCode;
  const i = rb.indexOf('let __title = title, __desc = desc'), j = rb.indexOf("} catch (e) { __title = title; __desc = desc;", i);   // v39: + __teamChanged
  const rewrite = (desc, nd) => new Function('desc', 'title', 'REQ', 'const team = [];\n' + rb.slice(i, j) + "} catch (e) { __title = title; __desc = desc; }\nreturn __desc;")(desc, 'T / HL', { new_details: nd });
  const NEW = 'Engineer: Howard Luistro | Booked by: Camy Caridad | ref: U08JL17A50A | team: U1 | Type: Entertainment | Dept: Localization\nSType: Localization Dubbing\n\nNotes:\nBring the script.';
  const OLD = 'Engineer: Howard Luistro | Booked by: Camy Caridad | ref: U08JL17A50A | team: U1 | Notes: Bring the script. | Type: Entertainment | Dept: Localization\nSType: Localization Dubbing';
  let r = rewrite(NEW, { Rooms: 'Studio 1, Studio A' });
  ok(r === 'Engineer: Howard Luistro | Booked by: Camy Caridad | ref: U08JL17A50A | team: U1 | Type: Entertainment | Dept: Localization | Rooms: Studio 1, Studio A\nSType: Localization Dubbing\n\nNotes:\nBring the script.', 'a change keeps the note in its own block', r);
  r = rewrite(OLD, { Rooms: 'Studio 1, Studio A' });
  ok(/\| Dept: Localization \| Rooms: Studio 1, Studio A\nSType: Localization Dubbing\n\nNotes:\nBring the script\.$/.test(r) && !/\| Notes:/.test(r), 'an older booking (the note inline) comes out in the new layout', r);
  r = rewrite(NEW, { Notes: 'New note' });
  ok(/\nSType: Localization Dubbing\n\nNotes:\nNew note$/.test(r) && !/Bring/.test(r), 'a new note from the Change form replaces it', r);
  r = rewrite(NEW, { SType: 'Localization Editing' });
  ok(/\nSType: Localization Editing\n\nNotes:\nBring the script\.$/.test(r), 'a new type: SType changes, the note stays below', r);
  console.log('The department (Cancel v31 / Move v37)');
  for (const [wf, nm] of [[cx, 'Check Ownership'], [mv, 'Resolve Booking']]) { const js = wf.nodes.find(n => n.name === nm).parameters.jsCode;
    const _a = js.indexOf('bookingDept = ((descH.match(') !== -1 ? 'bookingDept = ((descH.match(' : 'bookingDept = ((desc.match(', k = js.indexOf(_a) + _a.length, re = new Function('return ' + js.slice(k, js.indexOf(') || [])[1]', k)))();
    ok(((NEW.match(re) || [])[1] || '').toLowerCase().trim() === 'localization' && ((OLD.match(re) || [])[1] || '').toLowerCase().trim() === 'localization', nm + ': "Dept: Localization" read on its own (was "localization\\nstype: …")'); }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
