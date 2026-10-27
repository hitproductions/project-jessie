#!/usr/bin/env node
// PENDING 133 (27 Oct): every New Clients row says what Airtable client it is close to ("Close to"), and a client kept through
// the Change form is logged too. Book Session v123 (Build Log Row), Log Booking v3 (Client Row from the trigger), Slack
// Interactions v47 (New Client C -> Log Client C).
// Usage: node scripts/sim-new-clients.js [book-session v123] [log-booking v3] [slack-interactions v47]
const fs = require('fs');
const L = (i, d) => JSON.parse(fs.readFileSync(process.argv[i] || d, 'utf8'));
const B = L(2, 'workflows/book-session-v123.json'), LB = L(3, 'workflows/log-booking-v3.json'), si = L(4, 'workflows/slack-interactions-v47.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (!si.nodes.some(n => n.name === 'New Client C')) { console.log('0 ok, 0 failed (an older build: PENDING 133 not in it)'); process.exit(0); }
const node = (wf, n) => wf.nodes.find(x => x.name === n), code = (wf, n) => node(wf, n).parameters.jsCode;
const wrap = it => ({ first: () => it[0], all: () => it, isExecuted: true });
const nx = (wf, n) => ((wf.connections[n] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
const NAMES = ['Jem Lim', 'Acme Records', 'Netflix', 'Spotify Philippines'].map((Name, i) => ({ id: 'rec' + i, fields: { Name } }));

console.log('Book Session v123 - Build Log Row');
{
  const REQ = { summary: 'ATLAS / Jem Lin / TL', client: 'Jem Lin', rooms: 'Studio 6', start_iso: '2027-10-20T13:00:00+08:00', end_iso: '2027-10-20T15:00:00+08:00',
    description: 'Engineer: Tara Lim | Booked by: Howard Luistro | ref: U1', department: 'Audio Post', bookingType: 'Advertising', session_type: 'VO Recording' };
  const run = (client, opt) => new Function('$', code(B, 'Build Log Row'))(n => n === 'Verify' ? wrap([{ json: { status: 'CREATED', event_id: 'ev1', title: REQ.summary } }])
    : n === 'When Executed by Another Workflow' ? wrap([{ json: Object.assign({}, REQ, { client }) }])
    : n === 'Check Conflicts' ? wrap([{ json: { final_client: client, final_summary: REQ.summary.replace('Jem Lin', client), final_start: REQ.start_iso } }])
    : n === 'Client Cache' ? wrap([{ json: opt.cache ? { use: true, gc: [{}], an: NAMES } : { use: false } }])
    : n === 'Get Client' ? (opt.cache ? { all: () => { throw new Error('not executed'); } } : wrap([{ json: {} }]))
    : n === 'All Client Names' ? (opt.noNames ? { all: () => { throw new Error('not executed'); } } : wrap(NAMES.map(j => ({ json: j })))) : wrap([]))[0].json;
  let cl = JSON.parse(run('Jem Lin', {}).client);
  ok(cl.Client === 'Jem Lin' && cl['Close to'] === 'Jem Lim' && cl.Status === 'For Review', '"Jem Lin" -> Close to: Jem Lim', cl);
  cl = JSON.parse(run('Jem Lin', { cache: true }).client);
  ok(cl['Close to'] === 'Jem Lim', 'the same from the client cache (All Client Names never ran)');
  cl = JSON.parse(run('Spotify', {}).client);
  ok(cl['Close to'] === 'Spotify Philippines', '"Spotify" -> Close to: Spotify Philippines (every word close)', cl['Close to']);
  cl = JSON.parse(run('Brand New Studio Co', {}).client);
  ok(cl['Close to'] === '', 'a name nothing is close to -> Close to empty (a real new client)');
  cl = JSON.parse(run('Jem Lin', { noNames: true }).client);
  ok(cl['Close to'] === '' && cl.Client === 'Jem Lin', 'no names read -> Close to empty, the row still written');
  const o = run('Jem Lin', {}), lg = JSON.parse(o.log);
  ok(lg.Action === 'BOOKED' && !('Close to' in lg), 'the Jessie Log row unchanged');
}

console.log('Log Booking v3');
ok(nx(LB, 'When Executed by Another Workflow') === 'Log Row+Project Row+Client Row' && nx(LB, 'Log to Sheet') === '' && nx(LB, 'Client Row') === 'Log New Client',
   'Client Row straight from the trigger (a call with no log row still writes the client)', nx(LB, 'When Executed by Another Workflow'));
{ const cr = (inp) => new Function('$', code(LB, 'Client Row'))(n => wrap([{ json: inp }]));
  ok(cr({ log: '', client: JSON.stringify({ Client: 'Jem Lin', 'Close to': 'Jem Lim' }) }).length === 1 && cr({ log: '{}', client: '' }).length === 0, 'a client row -> written; none -> nothing'); }

console.log('Slack Interactions v47 - a client kept through Change');
ok(nx(si, 'After Move').split(' | ')[0].split('+').slice(-1)[0] === 'New Client C' && nx(si, 'After Move').split(' | ')[0].split('+')[0] === 'Show Change Result'
   && nx(si, 'New Client C') === 'Log Client C', 'After Move -> (the answer first) New Client C -> Log Client C', nx(si, 'After Move'));
const lc = node(si, 'Log Client C');
ok(lc.type === 'n8n-nodes-base.executeWorkflow' && lc.parameters.workflowId.value === 'vmmb0fDD0PXd9443' && lc.parameters.options.waitForSubWorkflow === false
   && lc.onError === 'continueRegularOutput' && lc.parameters.workflowInputs.value.client === '={{ $json.client }}', 'Log Client C: Jessie — Log Booking, not waited for, never fails the change');
const cache = [{ json: { cache_key: 'jessie-reference', payload: JSON.stringify({ bookers: [{ fields: { Name: 'Howard Luistro', 'Slack User ID': 'U1' } }], rooms: [], sessionTypes: [] }) } }];
const RC = { user: 'U1', clientTyped: 'Jem Lin', newTitle: 'REQUEST-TEST THREE / Jem Lin / AEG', newRooms: 'Studio F', b: { id: 'e1', t: 'REQUEST-TEST THREE / Jem Lim / AEG', st: 'Celebrity Recording' },
  n: { d: '2027-10-27', s: '10:00', e: '14:00' }, d: { st: '' } };
const nc = (A, R, names) => new Function('$', code(si, 'New Client C'))(n => n === 'After Move' ? wrap([{ json: A }]) : n === 'Read Change' ? wrap([{ json: R }])
  : n === 'Client Names' ? wrap((names || NAMES).map(j => ({ json: j }))) : n === 'Read Cache 7' ? wrap(cache)
  : n === 'Move' ? wrap([{ json: { status: 'MOVED', description: 'Engineer: Elijah Gan | Booked by: Howard Luistro | ref: U1 | team: U2 | Type: Advertising | Dept: Audio Post\nSType: VO Recording\n\nNotes:\nDept: Music' } }]) : wrap([]));
let r = nc({ ok: true, nb: { id: 'e9' } }, RC);
const row = r.length ? JSON.parse(r[0].json.client) : {};
ok(r.length === 1 && r[0].json.log === '' && row.Client === 'Jem Lin' && row['Close to'] === 'Jem Lim' && row['Booked by'] === 'Howard Luistro' && row.Project === 'REQUEST-TEST THREE'
   && row['Calendar Title'] === RC.newTitle && row['Event ID'] === 'e9' && row['Booking Date'] === '2027-10-27' && row['Session Type'] === 'Celebrity Recording' && row.Status === 'For Review',
   '"Jem Lin" kept through Change -> its New Clients row, Close to: Jem Lim', row);
if (/v48/.test(code(si, 'New Client C'))) ok(row.Department === 'Audio Post', 'v48: the department from the changed event\'s first line (not the note\'s "Dept: Music")', row.Department);
ok(nc({ ok: false }, RC).length === 0, 'not changed -> nothing logged');
ok(nc({ ok: true }, Object.assign({}, RC, { clientTyped: '' })).length === 0, 'the client not changed -> nothing logged');
ok(nc({ ok: true }, Object.assign({}, RC, { clientTyped: 'jem lim' })).length === 0, 'a client Airtable knows -> nothing logged');

console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
