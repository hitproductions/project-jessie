// Booking type sweep (22 Oct, QA): every Airtable booking type booked from the form, against the words that reach Book Session's type
// check with it - the department its people decide (a Music engineer / arranger), and project / client names holding another type's word
// ("mix tape", "band demo", "vo spot", "event teaser", "qc pass"...). Every one must come back CLEAR (Book Session v121; v120 failed 100+).
// Usage: node scripts/sim-type-sweep.js [book-session] [slack-interactions]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const si = require(P + (process.argv[3] || 'workflows/imported/slack-interactions-v38-imported.json'));
const bsFile = process.argv[2] || 'workflows/book-session-v121.json'; const bs = require(P + bsFile);
const FX = require(P + 'scripts/sim-fixture-rooms.js');
FX.rooms.push({ id: 'rm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Recording Control Room'] } });
const node = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
const run = (wf, name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(wf, name) + '\n})();')(n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }), { first: () => input[0], all: () => input });
const R = { 'Celebrity Recording': [['Music Engineer','Post Engineer','Music Arranger'],'rf'], 'QC': [['Loc Engineer'],'r3'], 'Van Recording': [['Post Engineer','Music Arranger'],'rm'], 'Post Mixing': [['Post Engineer'],'r7'],
  'Localization Editing': [['Loc Engineer'],'r1'], 'Post Processing': [['Multimedia Specialist'],'re'], 'Music Recording': [['Music Engineer','Music Arranger'],'rf'], 'Localization Mixing': [['Loc Engineer'],'r1'],
  'Music Presentation': [['Music Arranger','Music Engineer'],'rf'], 'Band Recording': [['Music Engineer','Music Arranger'],'rf'], 'Localization Dubbing': [['Loc Engineer'],'r1'], 'Localization Atmos Mixing': [['Loc Engineer'],'rc'],
  'Music Mixing': [['Music Engineer','Music Arranger'],'rf'], 'Music Arranging': [['Music Arranger','Music Engineer'],'rf'], 'VO Recording': [['Post Engineer'],'r7'] };
const sessionTypes = Object.keys(R).map(t => ({ id: 'st' + t.replace(/\s/g, ''), fields: { Type: t, Priority: [R[t][1]], 'Last Resort': [], 'Engineer Role Required': R[t][0], 'Room Requirements': '' } }))
  .concat([{ id: 'stMeeting', fields: { Type: 'Meeting', Priority: ['lk'], 'Engineer Role Required': ['None'] } }, { id: 'stEvent', fields: { Type: 'Event', Priority: ['lo'], 'Engineer Role Required': ['None'] } }]);
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: [dept], Authority: ['Standard'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer', 'Audio Post'), B('b2', 'Mike Villegas', 'MV', 'U3', 'Head of Music, Arranger', 'Music'),
  B('b3', 'Rico Gonzales', 'RG', 'U4', 'Music Engineer', 'Music'), B('b4', 'Lea Lim', 'LL', 'U5', 'Loc Engineer', 'Localization'), B('b5', 'Dilan Diaz', 'DD', 'U7', 'Multimedia Specialist', 'Marketing')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes, bookers }) } }];
const kindOf = t => /^(Localization|QC)/.test(t) ? 'loc' : t === 'Post Processing' ? 'post' : /Atmos/.test(t) ? 'atmos' : 'studio';
const roomName = id => FX.rooms.find(r => r.id === id).fields['Room Name'];
async function one(t, project, client, eng, arr) {
  const s = { date: '2027-10-23', t0: '09:30', t1: '14:30', purpose: t, kind: kindOf(t), requester: 'U1', channel: 'D1', ext: 'x', label: t, when: 'x', pre: {}, asked: '' };
  const v = { 'room~1': { room_radio: { selected_option: { value: roomName(R[t][1]) } } }, project: { project_in: { value: project } }, client: { client_in: { value: client } }, code: { code_in: { value: 'NFX-' + project.replace(/\W/g, '').toUpperCase() } },
    forname: { forname_in: { value: 'Dilan' } } };
  if (eng) v.engineer = { engineer_pick: { selected_option: { value: eng } } };
  if (arr) v.arranger = { arranger_pick: { selected_option: { value: arr } } };
  const r2 = (await run(si, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1' } }], 'Read Cache 3': cache, 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(s), blocks: [], state: { values: v } } } } }] }))[0].json;
  if (!r2.valid) return 'INVALID ' + JSON.stringify(r2.errors || r2.answer && r2.answer.errors);
  const tp = (await run(si, 'To Prepare', [], { 'Read Step 2': [{ json: r2 }], 'Read Cache 3': cache }))[0].json;
  const outs = { 'When Executed by Another Workflow': [{ json: tp }], 'Get Events In Window': [{ json: { items: [] } }], 'All Bookers': bookers.map(b => ({ json: b })), 'Client Cache': [{ json: { use: false } }],
    'Get Client': [{ json: {} }], 'Client Aliases': [{ json: {} }], 'All Client Names': [{ json: { fields: { Name: 'Jem Lim' } } }] };
  const cc = new Function('$', '$input', node(bs, 'Check Conflicts'))(n => ({ first: () => (outs[n] || [{ json: {} }])[0], all: () => outs[n] || [] }), { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json;
  return cc.verdict === 'CLEAR' ? 'CLEAR' : cc.reason + (cc.options ? ' ' + JSON.stringify(cc.options) : '') + (cc.session_type ? ' -> ' + cc.session_type : '');
}
(async () => {
  const projects = ['plain', 'mix tape', 'band demo', 'music video', 'post promo', 'presentation deck', 'dubbing reel', 'qc pass', 'event teaser', 'atmos trailer', 'vo spot', 'celebrity ad', 'van tour'];
  const people = [['U1', ''], ['U4', ''], ['', 'U3'], ['U1', 'U3'], ['U5', ''], ['U7', '']];
  const bad = {}; let n = 0;
  for (const t of Object.keys(R)) for (const pj of projects) for (const [e, a] of people) {
    const roles = R[t][0];
    if (e === 'U5' && !roles.includes('Loc Engineer')) continue; if (e === 'U7' && t !== 'Post Processing') continue;
    if (kindOf(t) === 'loc' && (a || (e && e !== 'U5'))) continue;
    n++; const r = await one(t, pj, pj === 'plain' ? '' : 'Acme', e, a);
    if (r !== 'CLEAR' && !/^INVALID/.test(r)) (bad[t + ' | ' + r] = bad[t + ' | ' + r] || []).push(pj + ' [' + [e, a].filter(Boolean).join('+') + ']');
  }
  const nb = Object.values(bad).reduce((a, x) => a + x.length, 0);
  console.log(bsFile, n, 'cases;', nb ? 'NOT clear:' : 'all clear');
  for (const k of Object.keys(bad)) console.log('  ' + k + '  <- ' + bad[k].slice(0, 6).join('; ') + (bad[k].length > 6 ? ' … (' + bad[k].length + ')' : ''));
  console.log((n - nb) + ' ok, ' + nb + ' failed'); process.exit(nb ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
