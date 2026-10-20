#!/usr/bin/env node
// Book Session v118 offline (20 Oct): a Post Processing title "POST PROCESSING - <PROJECT> / <who it is for>" (or "POST PROCESSING -
// <who>") goes through Check Conflicts whole - in the prepare run and the booking run - not refused for initials, not asked for a
// project, not rewritten; other titles as before. Runs the whole Check Conflicts node.
// Usage: node scripts/sim-book-v118.js [book-session v118]
const fs = require('fs');
const B = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/book-session-v118.json', 'utf8'));
if (!/v118 \(Howard, 20 Oct\)/.test(JSON.stringify(B.nodes))) { console.log('0 ok, 0 failed (v118 on; this build is older)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const FX = require('./sim-fixture-rooms.js');
const code = B.nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode;
const STAFF = [{ Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.', Department: ['Audio Post'] },
  { Name: 'Dilan Diaz', Initials: 'DD', 'Slack User ID': 'U0BQ77XKWA3', Info: 'Multimedia Specialist, Goes by Dilan, Dylan.', Department: ['Marketing'] }];
const refRooms = FX.rooms.map(r => ({ id: r.id, name: r.fields['Room Name'], vocalBooth: !!r.fields['Vocal Booth'], booth: false, common: /conference|lobby/i.test(String(r.fields['Room Type'] || '')) }));
const refTypes = FX.sessionTypes.map(s => ({ type: s.fields.Type, priority: [].concat(s.fields.Priority || []).map(id => (FX.rooms.find(r => r.id === id) || { fields: {} }).fields['Room Name']).filter(Boolean), lastResort: [], min: 60, max: 480, requirements: s.fields['Room Requirements'] || '' }));
const run = (REQ) => {
  const outs = { 'When Executed by Another Workflow': [REQ], 'Get Events In Window': [{ items: [] }], 'All Bookers': STAFF.map(f => ({ fields: f })),
    'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
  const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
  const $input = { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] };
  return new Function('$', '$input', code)($, $input)[0].json;
};
const base = { mode: 'prepare', start_iso: '2027-10-21T12:00:00+08:00', end_iso: '2027-10-21T14:00:00+08:00', rooms: 'Studio E', all_day: false, confirmed: false,
  session_type: 'Post Processing', client: '', engineer: 'Dilan Diaz', bookingType: '', department: 'Marketing', authority: '', expected_date: '2027-10-21',
  requester_text: 'Post Processing in Studio E on 2027-10-21 12:00 pm-2:00 pm, no client, engineer Dilan Diaz', staff_data: JSON.stringify(STAFF), reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: {} }),
  description: 'Engineer: Dilan Diaz | Booked by: Howard Luistro | ref: U1', exclude_event_id: '', room_override: false, series: false };
const one = (mode, t, extra) => { const pj = (t.match(/^POST PROCESSING - (.+?) \/ /) || t.match(/^(.+?) \/ /) || [])[1] || '';
  return run(Object.assign({}, base, { mode, confirmed: mode !== 'prepare', summary: t, requester_text: base.requester_text + (pj ? ', project ' + pj : '') }, extra || {})); };
for (const mode of ['prepare', '']) {
  const lbl = mode ? 'prepare run' : 'booking run';
  for (const t of ['POST PROCESSING - TRAILER CUT / Dilan', 'POST PROCESSING - Dilan', 'POST PROCESSING - TRAILER / Sasa Abella']) {
    const r = one(mode, t);
    ok(r.verdict === 'CLEAR' && r.final_summary === t && !r.final_client, lbl + ': ' + JSON.stringify(t) + ' -> kept as it is', r);
  }
  const old = one(mode, 'TRAILER / DD');
  ok(old.verdict === 'CLEAR' && old.final_summary === 'TRAILER / DD', lbl + ': an old-style "TRAILER / DD" -> as before');
  const vo = run(Object.assign({}, base, { mode, confirmed: mode !== 'prepare', summary: 'ORANGE / Dilan', session_type: 'VO Recording', rooms: 'Studio 7', engineer: 'Howard Luistro', description: 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1', department: 'Audio Post',
    requester_text: 'VO Recording in Studio 7 on 2027-10-21 12:00 pm-2:00 pm, project ORANGE, no client, engineer Howard Luistro' }));
  ok(vo.verdict === 'CLEAR' && vo.final_summary === 'ORANGE / HL', lbl + ': a VO Recording "ORANGE / Dilan" -> still gets the engineer\'s initials (ORANGE / HL) - only Post Processing titles are kept', vo.final_summary);
}
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
