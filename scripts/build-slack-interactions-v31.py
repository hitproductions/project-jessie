#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v31.json - "Jessie — Slack Interactions", v31 (wait estimates), round 12 (20 Oct).

  1. The loading views say how long it usually takes ("Usually under 30 seconds."), per scenario, rounded up (Howard, 20 Oct:
     never disappoint). Self-updating: the n8n data table **Jessie Timings** (xZAKroMpWBdt0lib) holds one row per scenario -
     `seconds` = the time 9 in 10 runs finish within (per date for a series), `dates` = how many runs it has learned from.
       rooms (step 1 -> step 2) · rooms-series (per date) · book · check (a series' dates, per date) · series (booking a
       series, per date) · change
     Read: one row, right before the loading view (Timings 1 / 2 / 13 / 10 - get by scenario, the shape Read Cache uses).
     Learn: after the answer is on screen (Show Step 2 / Show Result / Show Series Step / Show Series Result / Show Change Result)
     -> Timing Sample (click -> answer, Read Request's receivedAt) -> Read Timing -> Next Estimate -> Save Timing (upsert by
     scenario, the shape Store Prepared uses). Nobody waits for it; any failure leaves the estimate as it was.
     Fewer than 5 runs: the slowest so far, at least the measured fallback (book 30 s, change 30 s, a series 30 s a date, rooms
     10 s, checking 5 s a date). Then the 90th percentile, tracked (up 0.9 / down 0.1 of a step of 30%).
     Seconds round up to the next 10 (at least 10); a minute or more rounds up to whole minutes.
  8. Localization Projects at step 2 only when a code is already filled in ("Book a room" again from a DM) - the only time
     step 2 uses it. A normal Localization booking reads the table zero times while booking (Log Booking v2 checks the code
     after the reply).
Built on workflows/imported/slack-interactions-v30-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v30-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v31.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
TABLE = {"__rl": True, "value": "xZAKroMpWBdt0lib", "mode": "list", "cachedResultName": "Jessie Timings",
         "cachedResultUrl": "/projects/518sXYqvqTl1cuns/datatables/xZAKroMpWBdt0lib"}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def add(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    wf["nodes"].append(n)
    by[name] = n
    return n


def insert_before(target, new, src, out=0):
    """src[out] -> target  becomes  src[out] -> new -> target"""
    outs = C[src]["main"][out]
    assert [c["node"] for c in outs] == [target], (src, outs)
    C[src]["main"][out] = [{"node": new, "type": "main", "index": 0}]
    C[new] = {"main": [[{"node": target, "type": "main", "index": 0}]]}


def add_out(a, b):
    C.setdefault(a, {"main": [[]]})
    if not C[a]["main"]:
        C[a]["main"].append([])
    C[a]["main"][0].append({"node": b, "type": "main", "index": 0})


READ_OPTS = {"alwaysOutputData": True, "executeOnce": True, "onError": "continueRegularOutput"}


def timings_get(name, key_expr, pos):
    return add(name, "n8n-nodes-base.dataTable", 1,
               {"operation": "get", "dataTableId": dict(TABLE), "matchType": "allConditions",
                "filters": {"conditions": [{"keyName": "scenario", "keyValue": key_expr}]}, "returnAll": True}, pos, dict(READ_OPTS))


# ---- 1a: read the estimate right before each loading view ---------------------------------------------------------------
P = lambda n, dx=-120, dy=160: [by[n]["position"][0] + dx, by[n]["position"][1] + dy]
timings_get("Timings 1", "={{ ((((($('Read Request').first().json || {}).payload || {}).view || {}).state || {}).values || {}).rep_freq ? 'rooms-series' : 'rooms' }}", P("Read Step 1"))
insert_before("Read Step 1", "Timings 1", "Route", 5)
timings_get("Timings 2", "={{ (function () { try { const s = JSON.parse(((($('Read Request').first().json || {}).payload || {}).view || {}).private_metadata || '{}');"
                         " return ((s.series || {}).dates || []).length > 1 ? 'check' : 'book'; } catch (e) { return 'book'; } })() }}", P("Read Step 2"))
insert_before("Read Step 2", "Timings 2", "Read Cache 3")
timings_get("Timings 13", "series", P("Read Series Confirm"))
insert_before("Read Series Confirm", "Timings 13", "Route", 13)
timings_get("Timings 10", "change", P("Read Change"))
insert_before("Read Change", "Timings 10", "Read Cache 10")

WAIT_FN = r"""// v31 (round 12 #1): how long this usually takes - the running estimate in Jessie Timings (one row per scenario: seconds = the
// time 9 in 10 runs finish within, per date for a series; dates = how many runs it has learned from). Fewer than 5 runs -> at
// least the measured fallback. Always rounded up: under 10 / 20 / … seconds, then whole minutes.
function waitLine(rows, scen, n, fb) {
  const r = (rows || []).find(x => x && x.scenario === scen && !x.error) || {};
  const k = Number(r.dates) || 0, q = Number(r.seconds) || 0;
  const s = (k >= 5 && q > 0 ? q : Math.max(q, fb)) * Math.max(1, Number(n) || 1);
  const c = Math.max(10, Math.ceil(s / 10) * 10);
  if (c < 60) return 'Usually under ' + c + ' seconds.';
  const m = Math.ceil(s / 60); return 'Usually under ' + m + ' minute' + (m === 1 ? '' : 's') + '.';
}
"""


def rows_of(node):
    return "let _tr = []; try { _tr = $('" + node + "').all().map(i => i.json || {}); } catch (e) { _tr = []; }   // v31: the estimate\n"


CLOSE_DONE = "You can close this window – we’ll let you know in your DM once it’s done."
patch("Read Step 1", [
    ("const loading = { type: 'modal', external_id: ext, callback_id: 'book_step2',",
     WAIT_FN + rows_of("Timings 1") +
     "const _wait = series ? waitLine(_tr, 'rooms-series', series.dates.length, 5) : waitLine(_tr, 'rooms', 1, 10);\n"
     "const loading = { type: 'modal', external_id: ext, callback_id: 'book_step2',"),
    ("  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: series ? '⏳ *Checking ' + series.dates.length + ' dates…*' : '⏳ *Finding free rooms…*' } }] };",
     "  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: series ? '⏳ *Checking ' + series.dates.length + ' dates…*' : '⏳ *Finding free rooms…*' } },\n"
     "    { type: 'context', elements: [{ type: 'mrkdwn', text: _wait }] }] };   // v31"),
])
patch("Read Step 2", [
    ("const working = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Close' },\n  private_metadata: JSON.stringify(s),",
     WAIT_FN + rows_of("Timings 2") +
     "const _nd = ((s.series || {}).dates || []).length, _wait = _nd > 1 ? waitLine(_tr, 'check', _nd, 5) : waitLine(_tr, 'book', 1, 30);\n"
     "const working = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Close' },\n  private_metadata: JSON.stringify(s),"),
    ("text: 'Checking availability for each date. You can close this window – we’ll let you know in your DM.' }",
     "text: 'Checking availability for each date. ' + _wait + ' You can close this window – we’ll let you know in your DM.' }"),
    ("       { type: 'context', elements: [{ type: 'mrkdwn', text: '" + CLOSE_DONE + "' }] }] };",
     "       { type: 'context', elements: [{ type: 'mrkdwn', text: _wait + ' " + CLOSE_DONE + "' }] }] };   // v31"),
])
patch("Read Series Confirm", [
    ("const working = ", WAIT_FN + rows_of("Timings 13") + "const _wait = waitLine(_tr, 'series', n, 30);\nconst working = "),
    ("text: 'Multiple bookings may take longer to process. " + CLOSE_DONE + "' }",
     "text: _wait + ' " + CLOSE_DONE + "' }"),   # v31: the estimate (was "Multiple bookings may take longer to process.")
])
patch("Read Change", [
    ("{ type: 'context', elements: [{ type: 'mrkdwn', text: '" + CLOSE_DONE + "' }] }] };",
     "{ type: 'context', elements: [{ type: 'mrkdwn', text: (function () { let _tr = []; try { _tr = $('Timings 10').all().map(i => i.json || {}); } catch (e) { _tr = []; }" +
     " return waitLine(_tr, 'change', 1, 30); })() + ' " + CLOSE_DONE + "' }] }] };   // v31"),
    ("function changeView(b, cur, warn, meta, rooms, det) {", WAIT_FN + "function changeView(b, cur, warn, meta, rooms, det) {"),
])

# ---- 1b: learn - after the answer is on screen ----------------------------------------------------------------------------
SAMPLE_JS = r"""// Timing Sample (v31, round 12 #1): how long this run took, from the click (Read Request) to the answer on screen - one sample
// for its scenario in Jessie Timings. It runs after the answer is shown, so nobody waits for it; anything odd -> no sample.
const c = $('Check Signature').first().json || {}, rq = $('Read Request').first().json || {};
const t0 = Number(rq.receivedAt) || 0;
if (!t0) return [];
const secs = (Date.now() - t0) / 1000;
const dl = s => (((s || {}).series || {}).dates || []).length;
let scenario = '', n = 1;
if (c.route === 5) { let s = null; try { s = $('Read Step 1').first().json.s; } catch (e) { s = null; } if (!s) return []; n = dl(s); scenario = n > 1 ? 'rooms-series' : 'rooms'; }
else if (c.route === 6) { let s = null; try { s = $('Read Step 2').first().json.s; } catch (e) { s = null; } if (!s) return []; n = dl(s); scenario = n > 1 ? 'check' : 'book'; }
else if (c.route === 13) { let m = null; try { m = $('Read Series Confirm').first().json.meta; } catch (e) { m = null; } n = Number((m || {}).n || 0); scenario = 'series'; }
else if (c.route === 11) scenario = 'change';
if (!scenario || !(secs > 0) || secs > 1800) return [];
n = Math.max(1, n);
return [{ json: { scenario, per: Math.round(secs / n * 10) / 10, n } }];"""
NEXT_JS = r"""// Next Estimate (v31): the scenario's estimate after this run. The first 5 runs: the slowest so far. Then the time 9 in 10 runs
// finish within, tracked - a slower run moves it up by 0.9 of a step, a faster one down by 0.1 (a step = 30% of it).
const S = $('Timing Sample').first().json;
const rows = $('Read Timing').all().map(i => i.json || {});
if (rows.some(r => r.error)) return [];   // the table could not be read - leave the estimate as it is
const cur = rows.find(r => r.scenario === S.scenario) || null;
let q = cur ? Number(cur.seconds) || 0 : 0;
const k = cur ? Number(cur.dates) || 0 : 0, x = Number(S.per) || 0;
if (!(x > 0)) return [];
if (k < 5) q = Math.max(q, x);
else { const step = Math.max(0.5, q * 0.3); q = Math.max(1, q + (x > q ? 0.9 : -0.1) * step); }
return [{ json: { scenario: S.scenario, seconds: Math.round(q * 10) / 10, dates: k + 1 } }];"""

x0, y0 = by["Show Result"]["position"]
yT = y0 + 900
add("Timing Sample", "n8n-nodes-base.code", 2, {"jsCode": SAMPLE_JS}, [x0, yT], {"onError": "continueRegularOutput"})
add("Read Timing", "n8n-nodes-base.dataTable", 1,
    {"operation": "get", "dataTableId": dict(TABLE), "matchType": "allConditions",
     "filters": {"conditions": [{"keyName": "scenario", "keyValue": "={{ $('Timing Sample').first().json.scenario }}"}]}, "returnAll": True},
    [x0 + 224, yT], dict(READ_OPTS))
add("Next Estimate", "n8n-nodes-base.code", 2, {"jsCode": NEXT_JS}, [x0 + 448, yT], {"onError": "continueRegularOutput"})
add("Save Timing", "n8n-nodes-base.dataTable", 1,
    {"operation": "upsert", "dataTableId": dict(TABLE), "matchType": "allConditions",
     "filters": {"conditions": [{"keyName": "scenario", "keyValue": "={{ $('Next Estimate').first().json.scenario }}"}]},
     "columns": {"mappingMode": "defineBelow",
                 "value": {"scenario": "={{ $('Next Estimate').first().json.scenario }}", "seconds": "={{ $('Next Estimate').first().json.seconds }}",
                           "dates": "={{ $('Next Estimate').first().json.dates }}"},
                 "matchingColumns": [],
                 "schema": [{"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "type": t, "readOnly": False, "removed": False}
                            for k, t in [("scenario", "string"), ("seconds", "number"), ("dates", "number")]],
                 "attemptToConvertTypes": False, "convertFieldsToString": False},
     "options": {}},
    [x0 + 672, yT], {"executeOnce": True, "onError": "continueRegularOutput"})
C["Timing Sample"] = {"main": [[{"node": "Read Timing", "type": "main", "index": 0}]]}
C["Read Timing"] = {"main": [[{"node": "Next Estimate", "type": "main", "index": 0}]]}
C["Next Estimate"] = {"main": [[{"node": "Save Timing", "type": "main", "index": 0}]]}
for end in ["Show Step 2", "Show Result", "Show Series Step", "Show Series Result", "Show Change Result"]:
    add_out(end, "Timing Sample")

# ---- 8: Localization Projects at step 2 only for a code already filled in -----------------------------------------------
cond = by["Loc Needed?"]["parameters"]["conditions"]["conditions"][0]
assert cond["leftValue"] == "={{ (($('Read Step 1').first().json || {}).s || {}).kind === 'loc' }}", cond["leftValue"]
cond["leftValue"] = ("={{ (($('Read Step 1').first().json || {}).s || {}).kind === 'loc'"
                     " && !!String((((($('Read Step 1').first().json || {}).s || {}).pre || {}).cd) || '').trim() }}")

wf["name"] = "Jessie — Slack Interactions — v31 (wait estimates)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
