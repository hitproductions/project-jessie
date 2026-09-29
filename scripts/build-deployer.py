#!/usr/bin/env python3
"""Builds workflows/deploy-from-github-v1.json - "Jessie — Deploy from GitHub" (29 Sep 2026).

Why: from 29 Sep IT does not want Claude connecting to the n8n server. n8n pulls instead: Howard presses the
workflow's run button; it reads deploy/next.json from this repo (GitHub API, read with a fine-grained token), and for
each entry fetches the new file and the build it replaces, checks the LIVE workflow still matches that build (the
"pull before you change anything" rule - a browser edit since then refuses everything), PUTs the schema-clean body to
n8n's own API on localhost, publishes it with the version name, reads it back and checks stored == built, then writes
deploy/last-result.json back to the repo so the result can be checked without touching the server.
Nothing reaches into the server. Only the Jessie workflow ids below can be deployed to.

Credentials (created in n8n by Howard, never in this repo):
  GitHub API  - fine-grained token, this repo only, Contents: read and write
  n8n API     - Header Auth, name X-N8N-API-KEY, value an n8n API key made on the account that owns Jessie
  scripts/build-deployer.py [out]
"""
import json, sys, uuid

OUT = sys.argv[1] if len(sys.argv) > 1 else "workflows/deploy-from-github-v1.json"
ALLOWED = {
    "uVVYVB2M7kxpLleI": "Project Jessie", "EUG3sGXkfsJSYIMz": "Jessie — Book Session",
    "bAyDw7udhmY0NL38": "Jessie — Cancel Booking", "t7lwR2km4tfN8DbM": "Jessie — Move Booking",
    "yzirq12O227VTFp8": "Jessie — Find Booking", "e7tBQB458nstrqei": "Jessie — Room Availability",
    "hkx9PXcgW9nrzY2a": "Jessie — Expand Series", "UAwFoifgkfL1xNP2": "Jessie — Book Series",
    "K2tPBykMwKcQGMub": "Jessie — Prune Executions", "nEHnCMMXS0am59Zy": "Jessie — Open Consent Request",
    "TO1UnZTZ2LhtE9J3": "Jessie — Finalize Consent", "QHHDevaWhMk8gSBX": "Jessie — Consent Sweep",
    "DxByjma1WLGMLR0L": "Jessie — Refresh Reference Cache", "atJ87j360xVKHHzD": "Jessie — Envoy Mirror",
}

COMMON = r"""
const stable = v => Array.isArray(v) ? '[' + v.map(stable).join(',') + ']'
  : (v && typeof v === 'object') ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + stable(v[k])).join(',') + '}'
  : JSON.stringify(v === undefined ? null : v);
const nodeMap = w => { const m = {}; for (const n of ((w && w.nodes) || [])) m[n.name] = stable(n.parameters || {}); return m; };
const diff = (a, b) => { const A = nodeMap(a), B = nodeMap(b); return [...new Set(Object.keys(A).concat(Object.keys(B)))].filter(k => A[k] !== B[k]); };
const stableTitle = t => String(t || '').replace(/\s+[—-]\s+v\d+\b.*$/, '').trim();
"""

CONFIG = "// Deploy settings. n8n is the server's own API from inside its container; change it if n8n listens elsewhere.\n" \
    "return [{ json: { owner: 'hitproductions', repo: 'project-jessie', branch: 'main',\n" \
    "  manifest: 'deploy/next.json', result: 'deploy/last-result.json', n8n: 'http://localhost:5678',\n" \
    "  allowed: " + json.dumps(ALLOWED, ensure_ascii=False) + " } }];\n"

PLAN = r"""// Reads deploy/next.json: { "deploys": [ { workflow_id, file, base, version_name, description } ] }.
// Refuses the whole run (nothing is deployed) if any entry is not a Jessie workflow or not a workflows/*.json file.
const cfg = $('Config').first().json, m = $input.first().json || {};
const list = [].concat(m.deploys || []);
if (!list.length) throw new Error('Refused: deploy/next.json lists no deploys.');
const bad = [];
list.forEach((d, i) => {
  if (!cfg.allowed[d.workflow_id]) bad.push('#' + (i + 1) + ' ' + d.workflow_id + ' is not a Jessie workflow');
  for (const k of ['file', 'base']) if (!/^workflows\/[A-Za-z0-9._-]+\.json$/.test(String(d[k] || ''))) bad.push('#' + (i + 1) + ' ' + k + ' "' + d[k] + '" is not a workflows/*.json file');
  if (!String(d.version_name || '').trim()) bad.push('#' + (i + 1) + ' has no version_name');
});
if (bad.length) throw new Error('Refused, nothing deployed: ' + bad.join('; '));
return list.map((d, i) => ({ json: { i, workflow_id: d.workflow_id, file: d.file, base: d.base, version_name: String(d.version_name).trim(),
  description: String(d.description || '').trim(), expect: cfg.allowed[d.workflow_id] } }));
"""

CHECK = COMMON + r"""
// All entries are checked before anything is written; one failure refuses the whole run.
const plan = $('Plan').all().map(i => i.json), files = $('Get File').all().map(i => i.json);
const bases = $('Get Base').all().map(i => i.json), lives = $('Get Live').all().map(i => i.json);
const ALLOW = ['saveExecutionProgress', 'saveManualExecutions', 'saveDataErrorExecution', 'saveDataSuccessExecution', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];
const bad = [], out = [];
plan.forEach((p, i) => {
  const f = files[i] || {}, b = bases[i] || {}, l = lives[i] || {};
  const tag = '#' + (i + 1) + ' ' + p.file;
  if (!Array.isArray(f.nodes)) { bad.push(tag + ': could not read the file from GitHub'); return; }
  if (!Array.isArray(b.nodes)) { bad.push(tag + ': could not read the base ' + p.base + ' from GitHub'); return; }
  if (!Array.isArray(l.nodes) || l.id !== p.workflow_id) { bad.push(tag + ': could not read the live workflow ' + p.workflow_id); return; }
  if (stableTitle(f.name) !== p.expect || stableTitle(l.name) !== p.expect) { bad.push(tag + ': title "' + f.name + '" / live "' + l.name + '" is not ' + p.expect); return; }
  const changed = diff(l, b);
  if (changed.length) { bad.push(tag + ': the live workflow is not ' + p.base + ' - changed since (browser edit or another import?): ' + changed.slice(0, 8).join(', ')); return; }
  const s = {}; for (const k of ALLOW) if (f.settings && f.settings[k] !== undefined) s[k] = f.settings[k];
  if (!Object.keys(s).length) s.executionOrder = 'v1';
  out.push({ json: { workflow_id: p.workflow_id, file: p.file, base: p.base, version_name: p.version_name, description: p.description,
    live_name_before: l.name, body: { name: f.name, nodes: f.nodes, connections: f.connections, settings: s } } });
});
if (bad.length) throw new Error('Refused, nothing deployed: ' + bad.join(' | '));
// "dry_run": true in deploy/next.json - every read and check, then stop before anything is written.
if ($('Get Manifest').first().json.dry_run === true)
  throw new Error('DRY RUN OK - nothing written. Would deploy: ' + out.map(o => o.json.version_name + ' to ' + o.json.live_name_before).join('; '));
return out;
"""

VERIFY = COMMON + r"""
// stored == built, per workflow; the result goes back to the repo as deploy/last-result.json.
const done = $('Check').all().map(i => i.json), stored = $('Get Stored').all().map(i => i.json), pub = $('Publish').all().map(i => i.json);
const results = done.map((d, i) => {
  const s = stored[i] || {}, changed = diff(s, d.body);
  return { workflow_id: d.workflow_id, file: d.file, base: d.base, version_name: d.version_name, before: d.live_name_before,
    stored_name: s.name || '', active: s.active === true, stored_matches_built: Array.isArray(s.nodes) && changed.length === 0 && s.name === d.body.name,
    differing_nodes: changed.slice(0, 20), published: !(pub[i] && pub[i].error) };
});
const ok = results.every(r => r.stored_matches_built && r.active && r.published);
const result = { ran_at: new Date().toISOString(), ok, results };
const text = JSON.stringify(result, null, 2) + '\n';
let b64 = ''; try { b64 = Buffer.from(text, 'utf8').toString('base64'); } catch (e) { b64 = btoa(unescape(encodeURIComponent(text))); }
return [{ json: { ...result, summary: (ok ? 'OK' : 'CHECK') + ' - ' + results.map(r => r.version_name).join(', '), content_b64: b64 } }];
"""

def code(name, js, x):
    return {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x, 0]}

def http(name, x, url, method="GET", auth="github", body=None, raw=False, soft=False):
    p = {"method": method, "url": url, "options": {"timeout": 60000}}
    if auth == "github":
        p.update(authentication="predefinedCredentialType", nodeCredentialType="githubApi", sendHeaders=True,
                 headerParameters={"parameters": [{"name": "Accept", "value": "application/vnd.github.raw+json" if raw else "application/vnd.github+json"},
                                                  {"name": "X-GitHub-Api-Version", "value": "2022-11-28"}]})
    else:
        p.update(authentication="genericCredentialType", genericAuthType="httpHeaderAuth")
    if raw: p["options"]["response"] = {"response": {"responseFormat": "json"}}
    if body is not None: p.update(sendBody=True, specifyBody="json", jsonBody=body)
    n = {"parameters": p, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, 0]}
    if soft: n.update(onError="continueRegularOutput", alwaysOutputData=True)
    return n

GH = "https://api.github.com/repos/{{ $('Config').first().json.owner }}/{{ $('Config').first().json.repo }}/contents/"
REF = "?ref={{ $('Config').first().json.branch }}"
N8N = "{{ $('Config').first().json.n8n }}/api/v1/workflows/"
P = "$('Plan').all()[$itemIndex].json"
C = "$('Check').all()[$itemIndex].json"

nodes = [
    {"parameters": {}, "id": str(uuid.uuid4()), "name": "Deploy", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0]},
    code("Config", CONFIG, 220),
    http("Get Manifest", 440, "=" + GH + "{{ $('Config').first().json.manifest }}" + REF, raw=True),
    code("Plan", PLAN, 660),
    http("Get File", 880, "=" + GH + "{{ " + P + ".file }}" + REF, raw=True),
    http("Get Base", 1100, "=" + GH + "{{ " + P + ".base }}" + REF, raw=True),
    http("Get Live", 1320, "=" + N8N + "{{ " + P + ".workflow_id }}", auth="n8n"),
    code("Check", CHECK, 1540),
    http("Put", 1760, "=" + N8N + "{{ $json.workflow_id }}", method="PUT", auth="n8n", body="={{ JSON.stringify($json.body) }}"),
    http("Publish", 1980, "=" + N8N + "{{ " + C + ".workflow_id }}/activate", method="POST", auth="n8n",
         body="={{ JSON.stringify({ name: " + C + ".version_name, description: " + C + ".description }) }}"),
    http("Get Stored", 2200, "=" + N8N + "{{ " + C + ".workflow_id }}", auth="n8n"),
    code("Verify", VERIFY, 2420),
    http("Get Result SHA", 2640, "=" + GH + "{{ $('Config').first().json.result }}" + REF, soft=True),
    http("Write Result", 2860, "=" + GH + "{{ $('Config').first().json.result }}", method="PUT",
         body="={{ JSON.stringify(Object.assign({ message: 'n8n deploy: ' + $('Verify').first().json.summary, content: $('Verify').first().json.content_b64, branch: $('Config').first().json.branch }, ($json && $json.sha) ? { sha: $json.sha } : {})) }}"),
    {"parameters": {"content": "## Deploy from GitHub\nPress **Execute workflow**. It deploys what `deploy/next.json` in the repo lists, only if each live workflow still matches the build it replaces; otherwise it refuses and changes nothing. The result is written to `deploy/last-result.json`.\n\n**Credentials** (set once on the HTTP nodes): *GitHub API* on Get Manifest / Get File / Get Base / Get Result SHA / Write Result; *n8n API* (Header Auth, `X-N8N-API-KEY`) on Get Live / Put / Publish / Get Stored.",
                    "height": 260, "width": 520}, "id": str(uuid.uuid4()), "name": "Read me", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, -320]},
]
order = ["Deploy", "Config", "Get Manifest", "Plan", "Get File", "Get Base", "Get Live", "Check", "Put", "Publish", "Get Stored", "Verify", "Get Result SHA", "Write Result"]
conns = {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}
wf = {"name": "Jessie — Deploy from GitHub — v1", "nodes": nodes, "connections": conns, "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
json.dump(wf, open(OUT, "w"), indent=2, ensure_ascii=False)
print("wrote", OUT)
