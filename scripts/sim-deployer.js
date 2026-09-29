#!/usr/bin/env node
// Offline tests for 'Jessie — Deploy from GitHub' (workflows/deploy-from-github-v1.json): its Plan, Check and Verify code
// run on the real repo files, with GitHub and n8n replaced by the files themselves. No network.
//   node scripts/sim-deployer.js
const fs = require('fs'), path = require('path');
const R = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', f)));
const D = R(process.env.DEPLOYER || 'workflows/deploy-from-github-v1.json');
const code = n => D.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + String(d).slice(0, 300))); } };
const wrap = it => ({ first: () => it[0], all: () => it });
const cfg = new Function(code('Config'))()[0].json;
const run = (n, $map, input) => new Function('$', '$input', 'Buffer', code(n))(k => { if (!$map[k]) throw new Error('no ' + k); return wrap($map[k]); }, wrap(input || [{ json: {} }]), Buffer);
const J = x => ({ json: x });
const man = R('deploy/next.json');
const plan = run('Plan', { Config: [J(cfg)] }, [J(man)]).map(i => i.json);
ok(plan.length === 2 && plan[0].workflow_id === 'EUG3sGXkfsJSYIMz' && plan[1].expect === 'Project Jessie', 'deploy/next.json: two entries, Book Session then main');
const thr = f => { try { f(); return ''; } catch (e) { return e.message; } };
ok(/is not a Jessie workflow/.test(thr(() => run('Plan', { Config: [J(cfg)] }, [J({ deploys: [{ workflow_id: 'POSTY123', file: 'workflows/a.json', base: 'workflows/b.json', version_name: 'x' }] })]))), 'a workflow that is not Jessie -> refused');
ok(/is not a workflows\/\*\.json file/.test(thr(() => run('Plan', { Config: [J(cfg)] }, [J({ deploys: [{ workflow_id: 'EUG3sGXkfsJSYIMz', file: '../.env', base: 'workflows/b.json', version_name: 'x' }] })]))), 'a path outside workflows/ -> refused');
ok(/lists no deploys/.test(thr(() => run('Plan', { Config: [J(cfg)] }, [J({ deploys: [] })]))), 'an empty list -> refused');

const files = plan.map(p => R(p.file)), bases = plan.map(p => R(p.base));
const ctx = (lives, dry = false) => ({ 'Get Manifest': [J({ ...man, dry_run: dry })], Plan: plan.map(J), 'Get File': files.map(J), 'Get Base': bases.map(J), 'Get Live': lives.map(J) });
let chk = run('Check', ctx(bases));
ok(chk.length === 2 && chk[0].json.body.name === files[0].name && Object.keys(chk[0].json.body).sort().join() === 'connections,name,nodes,settings', 'live == base -> both pass; the body is schema-clean {name, nodes, connections, settings}');
ok(chk.every(c => Object.keys(c.json.body.settings).every(k => ['saveExecutionProgress', 'saveManualExecutions', 'saveDataErrorExecution', 'saveDataSuccessExecution', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'].includes(k))), 'settings pruned to the API-allowed keys');
ok(/DRY RUN OK - nothing written\. Would deploy: v66 - proposed time to Jessie — Book Session — v65 \(arranger question fix\); v192 - move range fix to Project Jessie — v191 \(find by title\)/.test(thr(() => run('Check', ctx(bases, true)))), 'dry_run: every check, then stops before any write, naming what it would deploy');
const edited = JSON.parse(JSON.stringify(bases[1])); edited.nodes.find(n => n.name === 'Guard Probe').parameters.jsCode += '\n// browser edit';
ok(/nothing deployed.*changed since.*Guard Probe/.test(thr(() => run('Check', ctx([bases[0], edited])))), 'a browser edit to main since the base -> the whole run refused (Book Session not deployed either)');
const wrongLive = JSON.parse(JSON.stringify(bases[0])); wrongLive.id = 'other';
ok(/could not read the live workflow/.test(thr(() => run('Check', ctx([wrongLive, bases[1]])))), 'the live workflow read is not the target id -> refused');
const already = [files[0], files[1]].map(f => ({ ...f, id: undefined }));
already[0].id = 'EUG3sGXkfsJSYIMz'; already[1].id = 'uVVYVB2M7kxpLleI';
ok(/changed since/.test(thr(() => run('Check', ctx(already)))), 'running the same list again after it deployed -> refused (live is no longer the base)');
const wrongTitle = JSON.parse(JSON.stringify(files[1])); wrongTitle.name = 'Posty — v3';
ok(/is not Project Jessie/.test(thr(() => run('Check', { ...ctx(bases), 'Get File': [files[0], wrongTitle].map(J) }))), 'a file whose title is not the target workflow -> refused');

const stored = chk.map(c => ({ ...c.json.body, id: c.json.workflow_id, active: true }));
let v = run('Verify', { Check: chk, 'Get Stored': stored.map(J), Publish: [J({}), J({})] })[0].json;
ok(v.ok === true && v.results.every(r => r.stored_matches_built) && /^OK - v66 - proposed time, v192 - move range fix$/.test(v.summary), 'stored == built -> ok, summary names both versions', v.summary);
ok(JSON.parse(Buffer.from(v.content_b64, 'base64').toString('utf8')).ok === true, 'the result file content decodes to the same result');
const drift = JSON.parse(JSON.stringify(stored)); drift[1].nodes.find(n => n.name === 'Booked For').parameters.jsCode = 'x';
v = run('Verify', { Check: chk, 'Get Stored': drift.map(J), Publish: [J({}), J({})] })[0].json;
ok(v.ok === false && v.results[1].differing_nodes.includes('Booked For'), 'stored differs from built -> not ok, the node is named');
ok(JSON.stringify(D).indexOf('X-N8N-API-KEY') !== -1 && !/ghp_|github_pat_|n8n_api_[a-z0-9]{10}/i.test(JSON.stringify(D)), 'no token or key in the workflow file (credentials are set in n8n)');
ok(D.nodes.every(n => n.type !== 'n8n-nodes-base.webhook' && n.type !== 'n8n-nodes-base.formTrigger'), 'no webhook or form trigger: it runs only when someone presses it');
console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
