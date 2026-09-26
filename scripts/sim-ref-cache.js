// Offline simulation of the v158 cache nodes against real data from exec 12158.
const fs = require('fs');
const S = process.argv[2] || './';            // folder holding run12158.json (an exec --raw dump)
const wf = JSON.parse(fs.readFileSync('workflows/project-jessie-v158.json', 'utf8'));
const run = JSON.parse(fs.readFileSync(S + 'run12158.json', 'utf8')).data.resultData.runData;
const code = n => wf.nodes.find(x => x.name === n).parameters.jsCode;
const out = n => run[n][0].data.main[0];               // real items from the live run

let fails = 0;
const ok = (c, m) => { console.log((c ? '  ok    ' : '  FAIL  ') + m); if (!c) fails++; };

function exec(name, produced, statics) {
  const $ = n => {
    const items = produced[n];
    if (!items) throw new Error('Referenced node is unexecuted: ' + n);
    return { all: () => items, first: () => items[0] };
  };
  const fn = new Function('$', '$getWorkflowStaticData', code(name));
  return fn($, () => statics);
}

const trigger = [{ json: { user: 'U026N6E1R' } }];
const fetched = { 'Fetch Rooms': out('All Rooms'), 'Fetch Session Types': out('All Session Types'), 'Fetch Bookers': out('All Bookers') };

function turn(statics, fetchOverride) {
  const p = { 'Slack Trigger': trigger };
  p['Ref Cache'] = exec('Ref Cache', p, statics);
  if (!p['Ref Cache'][0].json.fresh) {
    Object.assign(p, fetchOverride || fetched);
    p['Ref Store'] = exec('Ref Store', p, statics);
  }
  for (const n of ['All Rooms', 'All Session Types', 'All Bookers', 'Get Booker']) p[n] = exec(n, p, statics);
  return p;
}

console.log('A. cold start (no cache)');
const st = { global: {} };
const g = st.global;
let a = turn(g);
ok(a['Ref Cache'][0].json.fresh === false, 'Ref Cache says stale');
ok(a['Ref Store'][0].json.cached === true, 'Ref Store cached a complete read (' + JSON.stringify(a['Ref Store'][0].json) + ')');
ok(a['All Rooms'].length === 25 && a['All Session Types'].length === 14 && a['All Bookers'].length === 58, 'tables passed through from the fresh read: 25 / 14 / 58');
ok(a['Get Booker'][0].json.fields && a['Get Booker'][0].json.fields.Name, 'Get Booker found the sender: ' + (a['Get Booker'][0].json.fields || {}).Name);
ok(JSON.stringify(a['Get Booker'][0].json) === JSON.stringify(out('Get Booker')[0].json), 'Get Booker output identical to the old Airtable search');

console.log('B. warm cache');
let b = turn(g);
ok(b['Ref Cache'][0].json.fresh === true, 'Ref Cache says fresh (age ' + b['Ref Cache'][0].json.ageSeconds + 's)');
ok(!b['Ref Store'], 'no Airtable read, no store');
const strip = items => items.map(i => i.json);
ok(JSON.stringify(strip(b['All Rooms'])) === JSON.stringify(strip(out('All Rooms'))), 'All Rooms from cache identical to Airtable');
ok(JSON.stringify(strip(b['All Session Types'])) === JSON.stringify(strip(out('All Session Types'))), 'All Session Types from cache identical to Airtable');
ok(b['All Bookers'].length === 58 && b['All Bookers'].every(i => !('Email' in i.json.fields)), 'All Bookers from cache: 58 staff, no Email');
const want = ['Name', 'Initials', 'Department', 'Authority', 'Info', 'Slack User ID'];
const gb = (b['Get Booker'][0].json.fields || {});
ok(want.every(k => JSON.stringify(gb[k]) === JSON.stringify(out('Get Booker')[0].json.fields[k])), 'Get Booker from cache: every field Jessie reads matches the old search');

console.log('C. expired cache');
g.refCache.at = Date.now() - 11 * 60 * 1000;
ok(exec('Ref Cache', { }, g)[0].json.fresh === false, 'an 11-minute-old cache is stale');

console.log('D. Airtable fails on refresh');
const before = JSON.stringify(g.refCache);
const broken = { 'Fetch Rooms': [{ json: {} }], 'Fetch Session Types': out('All Session Types'), 'Fetch Bookers': out('All Bookers') };
let dd = turn(g, broken);
ok(dd['Ref Store'][0].json.cached === false, 'an incomplete read is not cached');
ok(JSON.stringify(g.refCache) === before, 'the previous cache is left untouched');
ok(dd['All Rooms'].length === 1 && Object.keys(dd['All Rooms'][0].json).length === 0, 'All Rooms passes the empty item on, as the Airtable node did');

console.log('E. sender not in Bookers');
const p = { 'Slack Trigger': [{ json: { user: 'UNOBODY' } }], 'All Bookers': out('All Bookers') };
ok(JSON.stringify(exec('Get Booker', p, g)) === JSON.stringify([{ json: {} }]), 'one empty item, like the old search with alwaysOutputData');

console.log('F. Booked For output unchanged on the cached path');
const bfCode = code('Booked For');
function runBF(produced) {
  const $ = n => { const items = produced[n] || (run[n] ? run[n][0].data.main[0] : null); if (!items) throw new Error('unexecuted ' + n); return { all: () => items, first: () => items[0] }; };
  return JSON.stringify(new Function('$', bfCode)($));
}
ok(runBF({ 'All Bookers': out('All Bookers'), 'Get Booker': out('Get Booker') }) === runBF({ 'All Bookers': b['All Bookers'], 'Get Booker': b['Get Booker'] }), 'Booked For identical: Airtable path vs cached path');

console.log(fails ? '\n' + fails + ' FAILED' : '\nall passed');
process.exit(fails ? 1 : 0);
