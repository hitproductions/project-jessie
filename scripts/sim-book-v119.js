#!/usr/bin/env node
// Book Session v119 (20 Oct): the most specific session type named wins. Since Music Vocal Recording became Music Recording ({music}
// once "recording" is left out), every Music type booked from the form was refused NEED_SESSION_TYPE ("Which one - Music Presentation
// or Music Recording?" - execution 53049, 22:00). Runs the form's Read Step 2 and To Prepare, then Book Session's whole Check Conflicts.
// Usage: node scripts/sim-book-v119.js [slack-interactions] [book-session v119]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const si = require(P + (process.argv[2] || 'workflows/imported/slack-interactions-v33-imported.json'));
const bs = require(P + (process.argv[3] || 'workflows/book-session-v119.json'));
const si2 = process.argv[2] ? require(P + process.argv[2]) : null;
const FX = require(P + 'scripts/sim-fixture-rooms.js');
const node = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
const run = async (wf, name, input, outs) => { const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(wf, name) + '\n})();')($, $input); };
const ST = (t, roles, pri) => ({ id: 'st-' + t.replace(/\s/g, ''), fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '', 'Min Duration': 0, 'Max Duration': 0 } });
const MM = ['Music Arranger', 'Music Engineer'];
const sessionTypes = FX.sessionTypes.filter(t => !/^Music/.test(t.fields.Type)).concat([ST('Music Presentation', MM, ['rf', 'r7', 'r8', 'rc']), ST('Music Arranging', MM, ['rf', 'r7', 'r8', 'rc']), ST('Music Mixing', MM, ['rf', 'r7', 'r8', 'rc']), ST('Music Recording', MM, ['rf', 'rc']), ST('Band Recording', MM, ['rf', 'rc']), ST('Post Processing', ['Multimedia Specialist'], ['re'])]);

const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: [dept], Authority: ['Standard'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.', 'Audio Post'), B('b2', 'Angelo Villegas', 'AV', 'U3', 'Music Arranger, Goes by Anj, Angelo.', 'Music'),
  B('b3', 'Dilan Diaz', 'DD', 'U7', 'Multimedia Specialist, Goes by Dilan.', 'Marketing')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes, bookers }) } }];
const one = async PURPOSE => {
  const s = { date: '2027-10-21', t0: '12:00', t1: '14:00', purpose: PURPOSE, kind: 'studio', requester: 'U1', channel: 'D1', ext: 'x', label: PURPOSE, when: 'x',
    pre: { d: '2027-10-21', s: '12:00', e: '14:00', r: 'Studio E', p: 'Post Processing', fn: 'Dilan' }, asked: '' };
  const vals = { 'room~1': { room_radio: { selected_option: { value: 'Studio F' } } }, project: { project_in: { value: 'musicpres' } }, client: { client_in: { value: 'jem lim' } },
    arranger: { arranger_pick: { selected_option: { value: 'U3' } } }, engineer: { engineer_pick: { selected_option: { value: 'U1' } } } };
  const r2 = (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Cache 3': cache,
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(s), blocks: [], state: { values: vals } } } } }] }))[0].json;
  const tp = (await run(si, 'To Prepare', [], { 'Read Step 2': [{ json: r2 }], 'Read Cache 3': cache }))[0].json;
  const outs = { 'When Executed by Another Workflow': [{ json: tp }], 'Get Events In Window': [{ json: { items: [] } }], 'All Bookers': bookers.map(b => ({ json: b })),
    'Client Cache': [{ json: { use: false } }], 'Get Client': [{ json: { id: 'recJ', fields: { Name: 'Jem Lim', 'Client Type': 'Advertising' } } }], 'Client Aliases': [{ json: {} }], 'All Client Names': [{ json: { fields: { Name: 'Jem Lim' } } }] };
  const $ = n => ({ first: () => (outs[n] || [{ json: {} }])[0], all: () => outs[n] || [] });
  const cc = new Function('$', '$input', node(bs, 'Check Conflicts'))($, { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json;
  return cc;
};

let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
(async () => {
  if (!/v119 \(20 Oct\): the most specific type named wins/.test(JSON.stringify(bs.nodes))) { console.log('0 ok, 0 failed (v119 on; this build is older)'); process.exit(0); }
  for (const t of ['Music Presentation', 'Music Mixing', 'Music Arranging', 'Music Recording', 'Band Recording']) {
    const cc = await one(t);
    ok(cc.verdict === 'CLEAR' && cc.final_summary === 'MUSICPRES / Jem Lim / HL x AV', t + ' from the form (Studio F, Angelo + you) -> clear, not "Which one -"', { v: cc.verdict, r: cc.reason, h: String(cc.human || '').slice(0, 120) });
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
