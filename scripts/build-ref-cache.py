#!/usr/bin/env python3
"""Build the reference-cache pair from fresh pulls (2026-09-29).

  scripts/build-ref-cache.py <refresh-pull.json> <main-pull.json> <refresh-out.json> <main-out.json>

Refresh:  three triggers -> All Rooms -> All Session Types -> All Bookers -> Build Cache -> Save Reference Cache
Main:     Gate Context -> Read Reference Cache -> Check Reference Cache -> Cache Fresh?
              yes -> Reference Snapshot
              no  -> Refresh Cache Now (runs the refresh workflow, waits) -> Reference Snapshot
          Reference Snapshot -> Reference OK?
              yes -> All Rooms -> All Session Types -> All Bookers -> Booked For ... (unchanged)
              no  -> Reference Lookup Failed -> Send Reply
All Rooms / All Session Types / All Bookers keep their names and become Code adapters returning the same
{id, fields} items the Airtable nodes did, all from the one validated snapshot. Get Booker stays live.
"""
import json, sys, uuid

REFRESH_ID = "DxByjma1WLGMLR0L"
TABLE = {"__rl": True, "value": "CsdJhgDxCsqq9K9j", "mode": "list", "cachedResultName": "Jessie Reference Cache",
         "cachedResultUrl": "/projects/518sXYqvqTl1cuns/datatables/CsdJhgDxCsqq9K9j"}
KEY_FILTER = {"conditions": [{"keyName": "cache_key", "condition": "eq", "keyValue": "jessie-reference"}]}

# Shared by Check Reference Cache and Reference Snapshot: one rule for what a usable cache row is.
VALIDATE = r"""
const REQUIRED = { rooms: 'Room Name', sessionTypes: 'Type', bookers: 'Name' };
function readRow(row) {
  if (!row || row.error || row.cache_key !== 'jessie-reference') return { ok: false, reason: 'no cache row' };
  const at = Date.parse(row.refreshed_at || '');
  if (isNaN(at)) return { ok: false, reason: 'refreshed_at missing or not a date' };
  let data;
  try { data = JSON.parse(row.payload); } catch (e) { return { ok: false, reason: 'payload is not JSON' }; }
  if (!data || typeof data !== 'object') return { ok: false, reason: 'payload is not an object' };
  for (const [k, f] of Object.entries(REQUIRED)) {
    const a = data[k];
    if (!Array.isArray(a) || !a.length) return { ok: false, reason: k + ' missing or empty' };
    for (const r of a) {
      if (!r || typeof r.id !== 'string' || !r.fields || typeof r.fields !== 'object' || !String(r.fields[f] || '').trim())
        return { ok: false, reason: k + ' has a malformed record' };
    }
  }
  return { ok: true, at, refreshed_at: row.refreshed_at, data };
}
// Upsert is not relied on to keep the key unique: with duplicate keyed rows, the newest valid one wins.
function newest(rows) {
  let best = null, why = 'no cache row';
  for (const r of rows) {
    const v = readRow(r);
    if (!v.ok) { if (r && r.cache_key) why = v.reason; continue; }
    if (!best || v.at > best.at) best = v;
  }
  return best || { ok: false, reason: why };
}
"""

BUILD_CACHE = r"""// Build Cache: exactly ONE item for Save Reference Cache, or a thrown error so the previous cache is never
// overwritten by an empty or failed read. Accepts nested ({id, fields}) and flattened ({id, ...fields}) records
// and always writes {id, fields}, the shape main's Booked For / Room Table / tool inputs read.
const REQUIRED = { 'All Rooms': 'Room Name', 'All Session Types': 'Type', 'All Bookers': 'Name' };
function read(name) {
  const rows = $(name).all().map(i => i.json);
  if (!rows.length) throw new Error(name + ': no records returned; cache not changed.');
  const seen = new Set();
  return rows.map(r => {
    if (!r || r.error || typeof r.id !== 'string' || !r.id.startsWith('rec'))
      throw new Error(name + ': invalid or failed Airtable read; cache not changed.');
    if (seen.has(r.id)) throw new Error(name + ': duplicate record ' + r.id + '; cache not changed.');
    seen.add(r.id);
    let fields;
    if (r.fields && typeof r.fields === 'object' && !Array.isArray(r.fields)) fields = r.fields;
    else { const { id, createdTime, ...rest } = r; fields = rest; }
    if (!String(fields[REQUIRED[name]] || '').trim())
      throw new Error(name + ': missing ' + REQUIRED[name] + ' in ' + r.id + '; cache not changed.');
    return { id: r.id, fields };
  });
}
const data = { rooms: read('All Rooms'), sessionTypes: read('All Session Types'), bookers: read('All Bookers') };
return [{ json: { cache_key: 'jessie-reference', payload: JSON.stringify(data), refreshed_at: new Date().toISOString() } }];"""

CHECK = "// Check Reference Cache (main v173): is the cached reference data usable and at most 15 minutes old?\n" \
        "// Reads every row the key matched (normally one). Emits one small item; the payload stays in Read Reference Cache.\n" \
        + VALIDATE + r"""
const MAX_AGE_MS = 15 * 60 * 1000;
const c = newest($input.all().map(i => i.json || {}));
const age = c.ok ? Date.now() - c.at : null;
const fresh = c.ok && age <= MAX_AGE_MS && age >= -2 * 60 * 1000;   // a clock skew of 2 min is tolerated
return [{ json: {
  cacheFresh: fresh,
  cacheState: !c.ok ? c.reason : (fresh ? 'fresh' : 'stale'),
  cacheRefreshedAt: c.ok ? c.refreshed_at : '',
  cacheAgeSec: c.ok ? Math.round(age / 1000) : null,
} }];"""

SNAPSHOT = "// Reference Snapshot (main v173): the one validated copy of rooms, session types and bookers this turn uses.\n" \
           "// Fresh cache -> the row from Read Reference Cache. Otherwise -> the row Refresh Cache Now just wrote.\n" \
           + VALIDATE + r"""
const inp = $input.first().json || {};
let rows, source;
if (Object.prototype.hasOwnProperty.call(inp, 'cacheFresh')) {
  source = 'cache';
  rows = $('Read Reference Cache').all().map(i => i.json || {});
} else {
  source = 'refresh';
  rows = $input.all().map(i => i.json || {});
}
const c = newest(rows);
if (!c.ok) {
  const err = inp.error ? ('refresh failed: ' + (inp.error.message || inp.error)) : c.reason;
  return [{ json: { ok: false, source, reason: String(err).slice(0, 300) } }];
}
return [{ json: { ok: true, source, refreshed_at: c.refreshed_at,
  rooms: c.data.rooms, sessionTypes: c.data.sessionTypes, bookers: c.data.bookers } }];"""

def adapter(name, key):
    return (f"// {name} (main v173): was an Airtable read on every message; now served from the reference cache.\n"
            "// Same items the Airtable node returned - {id, fields} - so every $('" + name + "').all() downstream is unchanged.\n"
            "const s = $('Reference Snapshot').first().json;\n"
            f"const rows = Array.isArray(s.{key}) ? s.{key} : [];\n"
            "const out = rows.map(r => ({ json: { id: r.id, fields: r.fields }, pairedItem: { item: 0 } }));\n"
            "return out.length ? out : [{ json: {}, pairedItem: { item: 0 } }];")

FAILED = r"""// Reference Lookup Failed (main v173): the cache was unusable and the refresh failed, so there is no trustworthy
// room / session type / staff list. Say so plainly rather than let the model answer without it.
const why = String(($input.first().json || {}).reason || '');
return [{ json: {
  output: "I couldn't load the room and staff lists just now, so I can't check or book anything yet. Please try again in a few minutes.",
  referenceLookup: { ok: false, reason: why },
} }];"""

def if_node(name, expr, pos):
    return {"parameters": {"conditions": {"combinator": "and", "conditions": [{
                "id": str(uuid.uuid4()), "leftValue": expr,
                "operator": {"name": "filter.operator.equals", "operation": "equals", "type": "string"},
                "rightValue": "yes"}],
              "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3}},
            "options": {}},
            "id": str(uuid.uuid4()), "name": name, "position": pos, "type": "n8n-nodes-base.if", "typeVersion": 2.3}

def code_node(name, code, pos, **extra):
    n = {"parameters": {"mode": "runOnceForAllItems", "jsCode": code}, "id": str(uuid.uuid4()), "name": name,
         "position": pos, "type": "n8n-nodes-base.code", "typeVersion": 2}
    n.update(extra); return n

def link(conns, src, dst, branch=0):
    arr = conns.setdefault(src, {}).setdefault("main", [])
    while len(arr) <= branch: arr.append([])
    arr[branch].append({"node": dst, "type": "main", "index": 0})

# ---------------------------------------------------------------- refresh
def build_refresh(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Jessie — Refresh Reference Cache — v2"
    sched = next(n for n in w["nodes"] if n["type"].endswith("scheduleTrigger"))
    sched["parameters"] = {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}}
    for nm in ("All Rooms", "All Session Types", "All Bookers"):
        n = N[nm]
        n["parameters"]["returnAll"] = True                  # the node pages through Airtable itself
        n["executeOnce"] = True                              # one read per execution, whatever triggered it
        n["alwaysOutputData"] = True                         # an empty read reaches Build Cache, which refuses it
        n["onError"] = "stopWorkflow"                        # a failed read stops before Save
        n.pop("retryOnFail", None)
    N["All Rooms"]["parameters"]["filterByFormula"] = "={{ '{Active / Bookable}' }}"
    bc = N["Build Cache"]; bc["parameters"] = {"mode": "runOnceForAllItems", "jsCode": BUILD_CACHE}
    bc.pop("onError", None); bc.pop("alwaysOutputData", None); bc.pop("executeOnce", None)
    sv = N["Save Reference Cache"]
    sv["parameters"] = {"resource": "row", "operation": "upsert", "dataTableId": TABLE, "matchType": "allConditions",
        "filters": KEY_FILTER,
        "columns": {"mappingMode": "defineBelow",
                    "value": {"cache_key": "={{ $json.cache_key }}", "payload": "={{ $json.payload }}",
                              "refreshed_at": "={{ $json.refreshed_at }}"},
                    "matchingColumns": [],
                    "schema": [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True,
                                "type": "string", "readOnly": False, "removed": False}
                               for c in ("cache_key", "payload", "refreshed_at")],
                    "attemptToConvertTypes": False, "convertFieldsToString": False},
        "options": {}}
    sv["onError"] = "stopWorkflow"
    for n in w["nodes"]:
        if n["type"].endswith("stickyNote"):
            n["parameters"]["content"] = (
                "## Jessie — Refresh Reference Cache\n"
                "Every 5 min (and on demand from main, when its cache is missing or older than 15 min): reads Rooms "
                "(Active / Bookable), Session Types and Bookers once each, builds ONE item and upserts the row "
                "cache_key = jessie-reference in the Jessie Reference Cache data table.\n\n"
                "A failed, empty or malformed read throws in Build Cache, so Save never runs and the last good row stays.\n"
                "Old blank rows are left alone.")
    trig = [n["name"] for n in w["nodes"] if n["type"].endswith(("manualTrigger", "scheduleTrigger", "executeWorkflowTrigger"))]
    C = {}
    for t in trig: link(C, t, "All Rooms")
    for a, b in (("All Rooms", "All Session Types"), ("All Session Types", "All Bookers"),
                 ("All Bookers", "Build Cache"), ("Build Cache", "Save Reference Cache")): link(C, a, b)
    w["connections"] = C
    w.setdefault("settings", {})["executionOrder"] = "v1"
    return w

# ---------------------------------------------------------------- main
def build_main(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Project Jessie — v173 (reference cache)"
    x0, y0 = N["Gate Context"]["position"]
    new = [
        {"parameters": {"resource": "row", "operation": "get", "dataTableId": TABLE, "matchType": "allConditions",
                        "filters": KEY_FILTER, "returnAll": True},
         "id": str(uuid.uuid4()), "name": "Read Reference Cache", "position": [x0, y0 - 320],
         "type": "n8n-nodes-base.dataTable", "typeVersion": 1,
         "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput"},
        code_node("Check Reference Cache", CHECK, [x0 + 176, y0 - 320]),
        if_node("Cache Fresh?", "={{ $json.cacheFresh === true ? 'yes' : 'no' }}", [x0 + 352, y0 - 320]),
        {"parameters": {"workflowId": {"__rl": True, "value": REFRESH_ID, "mode": "list",
                                       "cachedResultName": "Jessie — Refresh Reference Cache",
                                       "cachedResultUrl": "/workflow/" + REFRESH_ID},
                        "workflowInputs": {"mappingMode": "defineBelow", "value": {}, "matchingColumns": [], "schema": [],
                                           "attemptToConvertTypes": False, "convertFieldsToString": True},
                        "options": {}},
         "id": str(uuid.uuid4()), "name": "Refresh Cache Now", "position": [x0 + 528, y0 - 208],
         "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2,
         "executeOnce": True, "onError": "continueRegularOutput"},
        code_node("Reference Snapshot", SNAPSHOT, [x0 + 704, y0 - 320]),
        if_node("Reference OK?", "={{ $json.ok === true ? 'yes' : 'no' }}", [x0 + 880, y0 - 320]),
        code_node("Reference Lookup Failed", FAILED, [x0 + 1056, y0 - 176]),
    ]
    for nm, key in (("All Rooms", "rooms"), ("All Session Types", "sessionTypes"), ("All Bookers", "bookers")):
        old = N[nm]
        rep = code_node(nm, adapter(nm, key), old["position"])
        rep["id"] = old["id"]
        w["nodes"][w["nodes"].index(old)] = rep
    w["nodes"].extend(new)
    C = w["connections"]
    C["Gate Context"] = {"main": [[{"node": "Read Reference Cache", "type": "main", "index": 0}]]}
    link(C, "Read Reference Cache", "Check Reference Cache")
    link(C, "Check Reference Cache", "Cache Fresh?")
    link(C, "Cache Fresh?", "Reference Snapshot", 0)
    link(C, "Cache Fresh?", "Refresh Cache Now", 1)
    link(C, "Refresh Cache Now", "Reference Snapshot")
    link(C, "Reference Snapshot", "Reference OK?")
    link(C, "Reference OK?", "All Rooms", 0)
    link(C, "Reference OK?", "Reference Lookup Failed", 1)
    link(C, "Reference Lookup Failed", "Send Reply")
    return w

GET_BOOKER = r"""// Get Booker (main v175): who is asking, now from the reference cache instead of a live Airtable read (Tara,
// 29 Sep: staff changes are rare, so up to 15 minutes stale is accepted). Same result as the Airtable search
// {Slack User ID} = "<sender>": the matching Bookers records as {id, fields}, or one empty item when none match.
const user = String($('Slack Trigger').first().json.user || '').trim();
const s = $('Reference Snapshot').first().json;
const rows = (Array.isArray(s.bookers) ? s.bookers : [])
  .filter(r => user && String((r.fields || {})['Slack User ID'] || '').trim() === user);
const out = rows.map(r => ({ json: { id: r.id, fields: r.fields }, pairedItem: { item: 0 } }));
return out.length ? out : [{ json: {}, pairedItem: { item: 0 } }];"""

def cache_get_booker(w):
    """v175: the cache block moves in front of Get Booker, which becomes a cache adapter."""
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Project Jessie — v175 (Get Booker cached)"
    old = N["Get Booker"]
    rep = code_node("Get Booker", GET_BOOKER, old["position"]); rep["id"] = old["id"]
    w["nodes"][w["nodes"].index(old)] = rep
    C = w["connections"]
    for br in C["Consent Reject?"]["main"]:
        for t in br:
            if t["node"] == "Get Booker": t["node"] = "Read Reference Cache"
    C["Reference OK?"]["main"][0] = [{"node": "Get Booker", "type": "main", "index": 0}]
    C["Gate Context"] = {"main": [[{"node": "All Rooms", "type": "main", "index": 0}]]}
    row = {"Read Reference Cache": [73232, 5440], "Check Reference Cache": [73408, 5440], "Cache Fresh?": [73584, 5440],
           "Refresh Cache Now": [73760, 5584], "Reference Snapshot": [73936, 5440], "Reference OK?": [74112, 5440],
           "Reference Lookup Failed": [74288, 5584]}
    for n in w["nodes"]:
        if n["name"] in row: n["position"] = row[n["name"]]
    return w

if __name__ == "__main__":
    if sys.argv[1] == "--get-booker":
        w = cache_get_booker(json.load(open(sys.argv[2])))
        json.dump(w, open(sys.argv[3], "w"), indent=2, ensure_ascii=False)
        print("wrote", sys.argv[3], len(w["nodes"]), "nodes"); sys.exit(0)
    rin, min_, rout, mout = sys.argv[1:5]
    r = build_refresh(json.load(open(rin)))
    m = build_main(json.load(open(min_)))
    for w, p in ((r, rout), (m, mout)):
        json.dump(w, open(p, "w"), indent=2, ensure_ascii=False)
        print("wrote", p, len(w["nodes"]), "nodes")
