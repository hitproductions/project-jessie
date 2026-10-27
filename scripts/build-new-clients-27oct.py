#!/usr/bin/env python3
"""Builds PENDING 133 (27 Oct): a new client kept through Change is logged, and every New Clients row says what it is close to.

  workflows/book-session-v123.json        Jessie — Book Session — v123 (Close to)
  workflows/log-booking-v3.json           Jessie — Log Booking — v3 (a client row on its own)
  workflows/slack-interactions-v47.json   Jessie — Slack Interactions — v47 (new client on Change)

Howard (27 Oct, Slack test of SI v46): "Jem Lin" kept through the Change form (after "Did you mean Jem Lim?") went into the title
but not the New Clients sheet - only a new booking writes it. And at review a row gave no hint it may be a misspelling.
  - Book Session v123: Build Log Row adds "Close to" - the Airtable client names near the typed one (Check Conflicts' own
    near-miss rule, on the names the run already read: the client cache or All Client Names). Empty when nothing is close.
  - Log Booking v3: Client Row runs straight from the trigger (it ran after Log to Sheet, so a call with no log row wrote
    nothing).
  - Slack Interactions v47: a change that kept a client Airtable does not know (Read Change's clientTyped, not in Client Names)
    -> New Client C writes the row (Close to included) and Log Client C hands it to Log Booking without waiting.
The "Close to" header was added to the New Clients tab by Howard (27 Oct, column L).
Built on the live downloads.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMP = os.path.join(ROOT, "workflows", "imported")


def load(name):
    wf = json.load(open(os.path.join(IMP, name)))
    return wf, {n["name"]: n for n in wf["nodes"]}, wf["connections"]


def save(wf, title, out):
    wf["name"] = title
    p = os.path.join(ROOT, "workflows", out)
    with open(p, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(p, ROOT), len(wf["nodes"]), "nodes")


# Check Conflicts' near-miss rule (Book Session v122), as one function: the Airtable names close to the typed client
NEAR = r"""function closeTo(typed, names) {   // Check Conflicts' near-miss rule (CLIENT_CHECK), up to three names
  const _nz = s => String(s || '').toLowerCase().replace(/['’]s\b/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
  const _ed = (a, b) => { if (Math.abs(a.length - b.length) > 2) return 9; const d = Array.from({ length: a.length + 1 }, (_, i) => [i].concat(Array(b.length).fill(0)));
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) {
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1); }
    return d[a.length][b.length]; };
  const _tt = _nz(typed), _ttok = _tt.split(' ').filter(x => x.length >= 3);
  if (!_tt) return [];
  const _close = (a, b2) => a === b2 || (a.length >= 4 && b2.length >= 4 && _ed(a, b2) <= (Math.min(a.length, b2.length) >= 7 ? 2 : 1));
  const _near = n => { const nn = _nz(n); if (!nn || nn === _tt) return false; if (_ed(_tt, nn) <= Math.max(1, Math.floor(Math.max(_tt.length, nn.length) * 0.2))) return true;
    const nt = nn.split(' ').filter(x => x.length >= 3); return _ttok.length > 0 && _ttok.every(a => nt.some(b2 => _close(a, b2))); };
  return [...new Set((names || []).map(x => String(x || '').trim()).filter(Boolean))].filter(_near).slice(0, 3);
}
"""

# ---------------------------------------------------------------- Book Session v123
wf, by, C = load("book-session-v122-imported.json")
js = by["Build Log Row"]["parameters"]["jsCode"]
a = "    'Added': manila()\n  };\n}"
assert js.count(a) == 1
js = js.replace(a, "    'Added': manila(),\n"
    "    'Close to': (() => { try {   // v123 (PENDING 133): the Airtable names it is close to - a likely misspelling at review\n"
    "      let rows = []; try { const c = $('Client Cache').first().json; if (c && c.use && Array.isArray(c.an)) rows = c.an; } catch (e) {}\n"
    "      if (!rows.length) { try { rows = $('All Client Names').all().map(i => i.json || {}); } catch (e) { rows = []; } }\n"
    "      return closeTo(String(CC.final_client || ''), rows.map(r => ((r && r.fields) || {}).Name)).join(', ');\n"
    "    } catch (e) { return ''; } })()\n  };\n}")
by["Build Log Row"]["parameters"]["jsCode"] = NEAR + js
save(wf, "Jessie — Book Session — v123 (Close to)", "book-session-v123.json")

# ---------------------------------------------------------------- Log Booking v3
wf, by, C = load("log-booking-v2-imported.json")
assert [x["node"] for x in C["Log to Sheet"]["main"][0]] == ["Client Row"]
C["Log to Sheet"]["main"] = [[]]
del C["Log to Sheet"]
C["When Executed by Another Workflow"]["main"][0].append({"node": "Client Row", "type": "main", "index": 0})
cr = by["Client Row"]["parameters"]["jsCode"]
by["Client Row"]["parameters"]["jsCode"] = cr.replace(
    "// Client Row: the New Clients row, only for a client the Clients table did not know - none, no item, nothing written.",
    "// Client Row: the New Clients row, only for a client the Clients table did not know - none, no item, nothing written.\n"
    "// v3 (27 Oct, PENDING 133): straight from the trigger - a client kept through Change comes with no log row")
assert by["Client Row"]["parameters"]["jsCode"] != cr
save(wf, "Jessie — Log Booking — v3 (a client row on its own)", "log-booking-v3.json")

# ---------------------------------------------------------------- Slack Interactions v47
wf, by, C = load("slack-interactions-v46-imported.json")
NEWC = NEAR + r"""
// New Client C (v47, 27 Oct, PENDING 133): a change kept a client the Clients table does not know ("Jem Lin" after "Did you
// mean Jem Lim?") - its New Clients row, like a new booking's (Book Session's Build Log Row), with what it is close to.
// Log Client C hands it to Jessie — Log Booking without waiting. Nothing new -> no item.
const A = $('After Move').first().json || {};
if (A.ok !== true) return [];
const R = $('Read Change').first().json || {};
const typed = String(R.clientTyped || '').trim();
if (!typed) return [];
const names = $('Client Names').all().map(i => String((((i.json || {}).fields) || {}).Name || (i.json || {}).Name || '').trim()).filter(Boolean);
if (names.some(x => x.toLowerCase() === typed.toLowerCase())) return [];
let data = null; try { const rows = $('Read Cache 7').all().map(i => i.json || {}); for (const r of rows) { if (r.cache_key !== 'jessie-reference') continue; try { data = JSON.parse(r.payload); } catch (e) {} } } catch (e) {}
const me = (((data && data.bookers) || []).map(x => x.fields || {}).find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(R.user) !== -1) || {}).Name || '';
const manila = d => { const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  .formatToParts(d || new Date()).reduce((o, x) => (o[x.type] = x.value, o), {}); return p.year + '-' + p.month + '-' + p.day + ' ' + p.hour + ':' + p.minute; };
const title = String(R.newTitle || ((R.b || {}).t) || '');
const row = { 'Client': typed, 'Status': 'For Review', 'Booked by': me, 'Project': String(title.split(' / ')[0] || '').trim(),
  'Session Type': String(((R.d || {}).st) || ((R.b || {}).st) || ''), 'Department': '', 'Booking Date': String(((R.n || {}).d) || ''),
  'Room(s)': String(R.newRooms || ''), 'Calendar Title': title, 'Event ID': String(((A.nb || {}).id) || ''), 'Added': manila(),
  'Close to': closeTo(typed, names).join(', ') };
return [{ json: { log: '', client: JSON.stringify(row), project: '' } }];"""
am = by["After Move"]["position"]
newc = {"parameters": {"jsCode": NEWC}, "id": str(uuid.uuid4()), "name": "New Client C", "type": "n8n-nodes-base.code",
        "typeVersion": 2, "position": [am[0] + 200, am[1] + 400]}
bs, _, _ = load("book-session-v122-imported.json")
lb = json.loads(json.dumps([n for n in bs["nodes"] if n["name"] == "Log Booking"][0]))
lb["name"] = "Log Client C"; lb["id"] = str(uuid.uuid4()); lb["position"] = [am[0] + 400, am[1] + 400]
assert lb["parameters"]["workflowId"]["value"] == "vmmb0fDD0PXd9443" and lb["parameters"]["options"]["waitForSubWorkflow"] is False
wf["nodes"] += [newc, lb]
C["After Move"]["main"][0].append({"node": "New Client C", "type": "main", "index": 0})
C["New Client C"] = {"main": [[{"node": "Log Client C", "type": "main", "index": 0}]]}
save(wf, "Jessie — Slack Interactions — v47 (new client on Change)", "slack-interactions-v47.json")
