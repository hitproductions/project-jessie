#!/usr/bin/env node
// Book Session v121 (22 Oct, QA): the form's booking type wins when it is one of those named - Van Recording with an arranger (the
// department "Music" in the form's words named Music Recording too) was refused NEED_SESSION_TYPE. Every Airtable type from the form.


// Usage: node scripts/sim-book-v119.js [slack-interactions] [book-session v119]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const si = require(P + (process.argv[2] || 'workflows/imported/slack-interactions-v38-imported.json'));
const bs = require(P + (process.argv[3] || 'workflows/book-session-v121.json'));
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
const one = async (PURPOSE, ROOM) => {
  const s = { date: '2027-10-21', t0: '12:00', t1: '14:00', purpose: PURPOSE, kind: 'studio', requester: 'U1', channel: 'D1', ext: 'x', label: PURPOSE, when: 'x',
    pre: { d: '2027-10-21', s: '12:00', e: '14:00', r: 'Studio E', p: 'Post Processing', fn: 'Dilan' }, asked: '' };
  const vals = { 'room~1': { room_radio: { selected_option: { value: ROOM } } }, project: { project_in: { value: 'musicpres' } }, client: { client_in: { value: 'jem lim' } },
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
  
  for (const [t, rm] of [['Van Recording','Studio M'],['Music Presentation','Studio F'],['Celebrity Recording','Studio F'],['Band Recording','Studio F'],['Music Mixing','Studio F'],['VO Recording','Studio 7']]) {
    const cc = await one(t, rm);
    ok(cc.verdict === 'CLEAR', t + ' in ' + rm + ' with an arranger (department Music) -> clear', { v: cc.verdict, r: cc.reason, o: cc.options });
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
