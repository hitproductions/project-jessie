#!/usr/bin/env python3
"""Builds workflows/book-session-v112.json - "Jessie — Book Session", v112 (faster booking + single-room types), round 8
(19 Oct, docs/design/round-8-plan.md). Measured 19 Oct 10:30: the booking run took 14.0 s after a 3.8 s prepare run.

  1. The room's answer: read back at ~1.5 s, 3 s and 6 s after creating the event (was a fixed 6 s), going on as soon as every
     room on it has answered (accepted / declined). A room that never answers still gets the full 6 s; a decline is still
     caught and the event deleted (PENDING 44).
  2. The log sheets after the reply: Build Log Row now makes both rows (the Jessie Log row and, for a new client, the New
     Clients row) and hands them to the new "Jessie — Log Booking" workflow without waiting for it (Execute Workflow with
     "wait for completion" off). Log to Sheet / New Client? / New Client Row / Log New Client move there.
  3. No second round of client lookups: the prepare run returns what Get Client / Client Aliases / All Client Names found
     (client_cache, on Prepared Out); a booking run that carries it for the same client (within 3 minutes) skips the three
     Airtable reads and Check Conflicts reads the cached rows. Without it (chat, Book Series, consent) nothing changes.
  4. Single-room booking types: any type with "Atmos" in its name only in Studio C, Van Recording only in Studio M, and Studio M
     only for Van Recording - refused otherwise (ROOM_UNSUITABLE), whatever the caller sends.
Built on workflows/imported/book-session-v111-imported.json (the live download). Log Booking's workflow id is filled in by
scripts/set-log-booking-id.py once it is imported (placeholder LOG_BOOKING_ID until then).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v111-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v112.json")
LOG_SRC = os.path.join(ROOT, "workflows", "log-booking-v1.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) >= 1, (node, a[:90])
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def add_node(name, ntype, ver, params, pos, extra=None):
    node = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    node.update(extra or {})
    wf["nodes"].append(node)
    by[name] = node
    return node


def remove_node(name):
    wf["nodes"].remove(by.pop(name))
    C.pop(name, None)
    for src in C.values():
        for outs in src.get("main", []):
            if outs:
                outs[:] = [c for c in outs if c["node"] != name]


def wire(a, b, out=0):
    C.setdefault(a, {"main": []})
    while len(C[a]["main"]) <= out:
        C[a]["main"].append([])
    C[a]["main"][out] = [{"node": b, "type": "main", "index": 0}]


# ---- 3. the client lookups, cached from the prepare run --------------------------------------------------------------
by["When Executed by Another Workflow"]["parameters"]["workflowInputs"]["values"].append({"name": "client_cache"})

CACHE_JS = r"""// Client Cache (v112, round 8): a booking run right after its prepare run (the form) carries what the prepare run's
// client lookups found (client_cache, from Prepared Out). Same client and under 3 minutes old -> use: the three Airtable
// reads are skipped and Check Conflicts reads these rows. Anything else -> use false, the lookups run as before.
const REQ = $('When Executed by Another Workflow').first().json || {};
const norm = s => String(s || '').replace(/\s*\([^()]*\)\s*$/, '').trim().toLowerCase().replace(/^none$/, '');
let c = null; try { c = JSON.parse(String(REQ.client_cache || '')); } catch (e) { c = null; }
const prep = String(REQ.mode || '').trim().toLowerCase() === 'prepare';
const fresh = c && c.v === 1 && c.at && (Date.now() - new Date(c.at).getTime()) < 3 * 60 * 1000;
const use = !!(c && !prep && fresh && norm(c.client) === norm(REQ.client) && Array.isArray(c.gc));
return [{ json: use ? { use: true, gc: c.gc, al: c.al || [], an: c.an || null } : { use: false } }];"""
add_node("Client Cache", "n8n-nodes-base.code", 2, {"jsCode": CACHE_JS},
         [by["All Bookers"]["position"][0] + 80, by["All Bookers"]["position"][1] + 160])
add_node("Cached?", "n8n-nodes-base.if", 2.3, {
    "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 3},
                   "combinator": "and",
                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $('Client Cache').first().json.use === true }}",
                                   "rightValue": True, "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]},
    "options": {}}, [by["All Bookers"]["position"][0] + 240, by["All Bookers"]["position"][1] + 160])
assert C["All Bookers"]["main"][0][0]["node"] == "Get Client"
wire("All Bookers", "Client Cache")
wire("Client Cache", "Cached?")
wire("Cached?", "Get Events In Window", 0)
wire("Cached?", "Get Client", 1)

# Every read of the lookup nodes reads the cached rows when Client Cache said use, else the node itself. Inline (no shared
# helper), so each piece of code still runs on its own - test-nodes runs pieces of Check Conflicts by themselves.
def cached(key, node):
    return ("((() => { try { const c = $('Client Cache').first().json; if (c && c.use && Array.isArray(c." + key + ")) return c." + key
            + ".map(j => ({ json: j })); } catch (e) {} return $('" + node + "').all(); })())")


REPL = [("$('Get Client').all()", cached("gc", "Get Client")),
        ("$('Get Client').first()", "((() => { try { const c = $('Client Cache').first().json; if (c && c.use && Array.isArray(c.gc))"
                                    " return { json: c.gc[0] || {} }; } catch (e) {} return $('Get Client').first(); })())"),
        ("$('Client Aliases').all()", cached("al", "Client Aliases")),
        ("$('All Client Names').all()", cached("an", "All Client Names"))]


def via_cache(js):
    js2 = js
    for a, b in REPL:
        js2 = js2.replace(a, b)
    return js2


by["Check Conflicts"]["parameters"]["jsCode"] = via_cache(by["Check Conflicts"]["parameters"]["jsCode"])

# Prepared Out hands the lookups back with the prepared booking.
patch("Prepared Out", [("prep_stored: (function () {", """client_cache: (function () {   // v112: for the booking run that follows (Client Cache)
  try {
    const rows = n => n.map(i => i.json || {});
    let an = null; try { an = rows($('All Client Names').all()); } catch (e) { an = null; }
    let al = []; try { al = rows($('Client Aliases').all()); } catch (e) { al = []; }
    const F = (JSON.parse(i.json.prep_payload || '{}') || {}).F || {};
    return JSON.stringify({ v: 1, at: new Date().toISOString(), client: String(F['Client'] || ''), gc: rows($('Get Client').all()), al, an });
  } catch (e) { return ''; }
})(), prep_stored: (function () {""")])

# ---- 4. single-room booking types ------------------------------------------------------------------------------------
patch("Check Conflicts", [("""const keys = Object.keys(ROOMS);
const wanted = [];
for (const name of wantedNames) {""", """// v112 (round 8): single-room booking types - Atmos only in Studio C, Van Recording only in Studio M (the mobile studio
// van), and Studio M only for Van Recording. Whatever the caller sends, room_override included.
{
  const _st = String(REQ.session_type || '').trim(), _lc = wantedNames.map(r => r.toLowerCase());
  const _only = /atmos/i.test(_st) ? 'Studio C' : /^van recording$/i.test(_st) ? 'Studio M' : '';
  if (_only && _lc.indexOf(_only.toLowerCase()) === -1)
    return [{ json: { verdict:'REJECTED', reason:'ROOM_UNSUITABLE', unsuitable: wantedNames, priority: [_only], last_resort: [],
      human: _st + ' can only be booked in ' + _only + '. Nothing was booked.' } }];
  if (!/^van recording$/i.test(_st) && _lc.indexOf('studio m') !== -1)
    return [{ json: { verdict:'REJECTED', reason:'ROOM_UNSUITABLE', unsuitable: ['Studio M'], priority: [], last_resort: [],
      human: 'Studio M is only for Van Recording. Nothing was booked.' } }];
}
const keys = Object.keys(ROOMS);
const wanted = [];
for (const name of wantedNames) {""")])

# ---- 1. the room's answer, read as soon as it is there ---------------------------------------------------------------
wait = by["Wait for Room"]
reread = by["Reread Event"]
wait["parameters"] = {"amount": 1.5}
ANSWERED = ("={{ (function(){ try { const e = $json || {}; if (!e.id) return true;"
            " const rs = (e.attendees || []).filter(a => a.resource);"
            " return !rs.length || rs.every(a => a.responseStatus && a.responseStatus !== 'needsAction'); }"
            " catch (x) { return true; } })() }}")


def answered(name, pos):
    return add_node(name, "n8n-nodes-base.if", 2.3, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 3},
                       "combinator": "and",
                       "conditions": [{"id": str(uuid.uuid4()), "leftValue": ANSWERED, "rightValue": True,
                                       "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]},
        "options": {}}, pos)


x0, y0 = reread["position"]
answered("Room Answered?", [x0 + 80, y0 + 200])
add_node("Wait for Room 2", "n8n-nodes-base.wait", 1.1, {"amount": 1.5}, [x0 + 240, y0 + 200], {"webhookId": str(uuid.uuid4())})
reread2 = json.loads(json.dumps(reread)); reread2.update({"id": str(uuid.uuid4()), "name": "Reread Event 2", "position": [x0 + 400, y0 + 200]})
wf["nodes"].append(reread2); by["Reread Event 2"] = reread2
answered("Room Answered 2?", [x0 + 560, y0 + 200])
add_node("Wait for Room 3", "n8n-nodes-base.wait", 1.1, {"amount": 3}, [x0 + 720, y0 + 200], {"webhookId": str(uuid.uuid4())})
reread3 = json.loads(json.dumps(reread)); reread3.update({"id": str(uuid.uuid4()), "name": "Reread Event 3", "position": [x0 + 880, y0 + 200]})
wf["nodes"].append(reread3); by["Reread Event 3"] = reread3
assert C["Reread Event"]["main"][0][0]["node"] == "Verify"
wire("Reread Event", "Room Answered?")
wire("Room Answered?", "Verify", 0)
wire("Room Answered?", "Wait for Room 2", 1)
wire("Wait for Room 2", "Reread Event 2")
wire("Reread Event 2", "Room Answered 2?")
wire("Room Answered 2?", "Verify", 0)
wire("Room Answered 2?", "Wait for Room 3", 1)
wire("Wait for Room 3", "Reread Event 3")
wire("Reread Event 3", "Verify")
patch("Verify", [("// v106 (PENDING 44): the event as read back a few seconds after it was made",
                  "// v112: read back at ~1.5 / 3 / 6 s, as soon as every room has answered (was a fixed 6 s).\n"
                  "// v106 (PENDING 44): the event as read back a few seconds after it was made")])

# ---- 2. the log sheets, after the reply ------------------------------------------------------------------------------
NEWCLIENT_EXPR = by["New Client?"]["parameters"]["conditions"]["conditions"][0]["leftValue"]
assert NEWCLIENT_EXPR.startswith("={{ (function(){") and NEWCLIENT_EXPR.endswith("})() }}")
new_client_fn = via_cache(NEWCLIENT_EXPR[len("={{ "):-len(" }}")])
log_js = by["Build Log Row"]["parameters"]["jsCode"]
helpers = log_js.split("const V = $('Verify').first().json || {};", 1)[0].strip()
assert "function manila" in helpers and "function timeRange" in helpers
by["Build Log Row"]["parameters"]["jsCode"] = helpers + "\n" + r"""
// Build Log Row (v112): both sheet rows, handed to Jessie — Log Booking, which writes them after the reply has gone (Book
// Session no longer waits for Google Sheets). The New Clients row only for a client the Clients table does not know - the
// old New Client? test, reading the cached lookups when the prepare run's were reused.
const V = $('Verify').first().json || {};
const REQ = $('When Executed by Another Workflow').first().json || {};
const CC = $('Check Conflicts').first().json || {};
const desc = String(REQ.description || '');
const booker = ((desc.match(/Booked by:\s*([^|]+)/) || [])[1] || '').trim();
const rooms = Array.isArray(REQ.rooms) ? REQ.rooms.join(', ') : String(REQ.rooms || '');
const log = {
  'Timestamp': manila(),
  'Action': 'BOOKED',
  'Title': String(V.title || REQ.summary || ''),
  'Room(s)': rooms,
  'Date': dateOnly(REQ.start_iso),
  'Time': REQ.all_day ? 'all day' : timeRange(REQ.start_iso, REQ.end_iso),
  'Department': String(REQ.department || ''),
  'Booker': booker,
  'Done by': booker,
  'Event ID': String(V.event_id || ''),
  'Note': String(REQ.bookingType || '')
};
const isNew = """ + new_client_fn + r""";
let client = null;
if (isNew) {
  const t = String(CC.final_summary || REQ.summary || '').split(' / ');
  client = {
    'Client': String(CC.final_client || '').trim() || (t.length >= 3 ? t[1].trim() : ''),
    'Status': 'For Review',
    'Booked by': booker,
    'Project': String(t[0] || '').trim(),
    'Session Type': String(REQ.session_type || ''),
    'Department': String(REQ.department || ''),
    'Booking Date': (CC.final_start || REQ.start_iso) ? manila(CC.final_start || REQ.start_iso).slice(0, 10) : '',
    'Room(s)': rooms,
    'Calendar Title': String(V.title || REQ.summary || ''),
    'Event ID': String(V.event_id || ''),
    'Added': manila()
  };
}
return [{ json: { log: JSON.stringify(log), client: client && client['Client'] ? JSON.stringify(client) : '' } }];"""

lx, ly = by["Log to Sheet"]["position"]
for n in ["Log to Sheet", "New Client?", "New Client Row", "Log New Client"]:
    remove_node(n)
add_node("Log Booking", "n8n-nodes-base.executeWorkflow", 1.2, {
    "workflowId": {"__rl": True, "mode": "id", "value": "LOG_BOOKING_ID", "cachedResultName": "Jessie — Log Booking"},
    "workflowInputs": {"mappingMode": "defineBelow", "value": {"log": "={{ $json.log }}", "client": "={{ $json.client }}"},
                       "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
    "options": {"waitForSubWorkflow": False}}, [lx, ly], {"onError": "continueRegularOutput", "alwaysOutputData": True})
wire("Build Log Row", "Log Booking")
wire("Log Booking", "Return Booked")

wf["name"] = "Jessie — Book Session — v112 (faster booking + single-room types)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
