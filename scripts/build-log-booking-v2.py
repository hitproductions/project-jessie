#!/usr/bin/env python3
"""Builds workflows/log-booking-v2.json - "Jessie — Log Booking", v2 (new project codes), round 12 item 8 (20 Oct).

A Localization / QC booking's project code is checked against Airtable Localization Projects AFTER the reply (Log Booking runs
without Book Session waiting, v112): a code the table does not have goes to the "New Projects" tab of the Jessie Log
spreadsheet, Status For Review, one row per code (appendOrUpdate on Code) - like New Clients. Howard adds it to Airtable.
Nothing in the booking path reads Localization Projects for this; no "Did you mean" (Howard, 20 Oct).

  When Executed (+ input `project`) -> Log Row -> Log to Sheet -> Client Row -> Log New Client        (as v1)
                                    -> Project Row -> Find Project -> New Project? -> Log New Project  (v2, its own branch)
A lookup that errors is not evidence either way: nothing is written. An empty code never queries (gotcha 7).
Built on workflows/imported/log-booking-v1-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "log-booking-v1-imported.json")
OUT = os.path.join(ROOT, "workflows", "log-booking-v2.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]

trig = by["When Executed by Another Workflow"]
names = [v["name"] for v in trig["parameters"]["workflowInputs"]["values"]]
assert names == ["log", "client"], names
trig["parameters"]["workflowInputs"]["values"].append({"name": "project"})

PROJECT_ROW = r"""// Project Row (v2): a Localization / QC booking's project code, handed over by Book Session (v115+) - none, no item, nothing
// looked up or written.
let r = null; try { r = JSON.parse(String($('When Executed by Another Workflow').first().json.project || '')); } catch (e) { r = null; }
const code = r && typeof r === 'object' ? String(r['Code'] || '').trim().toUpperCase() : '';
return code ? [{ json: Object.assign({}, r, { Code: code }) }] : [];"""

FORMULA = ("={{ (function(){\n"
           "  var c = String(($('Project Row').first().json || {})['Code'] || '').trim().toUpperCase();\n"
           "  if (!c) { return 'FALSE()'; }   // gotcha 7: an empty value would match every row\n"
           "  return \"UPPER(TRIM({Project Code})) = '\" + c.replace(/'/g, \"\\\\'\") + \"'\";\n"
           "})() }}")

NEW_PROJECT = r"""// New Project? (v2): the code is new only when the lookup answered and found no record. A lookup that errored is not evidence
// either way - nothing is written.
const rows = $('Find Project').all().map(i => i.json || {});
if (rows.some(r => r.error)) return [];
if (rows.some(r => r.id)) return [];
return [{ json: $('Project Row').first().json }];"""

x0, y0 = by["Log Row"]["position"]
y1 = y0 + 200


def add(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    wf["nodes"].append(n)
    by[name] = n
    return n


add("Project Row", "n8n-nodes-base.code", 2, {"jsCode": PROJECT_ROW}, [x0, y1])
air_cred = {"airtableTokenApi": {"id": "S0hmu58Rb55jqAv0", "name": "Airtable Personal Access Token account"}}   # as Book Session's Get Client
add("Find Project", "n8n-nodes-base.airtable", 2.2,
    {"operation": "search",
     "base": {"__rl": True, "cachedResultName": "Project Jessie Knowledge Base", "mode": "list", "value": "app8GQxEInqJi1NRP"},
     "table": {"__rl": True, "cachedResultName": "Localization Projects", "mode": "list", "value": "tbljkG6z7odPUtTIf"},
     "filterByFormula": FORMULA,
     "options": {"fields": ["Project Code"]}},
    [x0 + 224, y1], {"credentials": air_cred, "alwaysOutputData": True, "executeOnce": True, "onError": "continueRegularOutput"})
add("New Project?", "n8n-nodes-base.code", 2, {"jsCode": NEW_PROJECT}, [x0 + 448, y1])
lnc = by["Log New Client"]
lnp = json.loads(json.dumps(lnc))
lnp.update({"id": str(uuid.uuid4()), "name": "Log New Project", "position": [x0 + 672, y1]})
lnp["parameters"]["sheetName"] = {"__rl": True, "mode": "name", "value": "New Projects"}
lnp["parameters"]["columns"]["matchingColumns"] = ["Code"]
wf["nodes"].append(lnp)
by["Log New Project"] = lnp

C["When Executed by Another Workflow"]["main"][0].append({"node": "Project Row", "type": "main", "index": 0})
C["Project Row"] = {"main": [[{"node": "Find Project", "type": "main", "index": 0}]]}
C["Find Project"] = {"main": [[{"node": "New Project?", "type": "main", "index": 0}]]}
C["New Project?"] = {"main": [[{"node": "Log New Project", "type": "main", "index": 0}]]}

by["Note"]["parameters"]["content"] = ("## Jessie — Log Booking\nWrites a booking's rows to the Jessie Log spreadsheet after the reply has gone. Called by "
                                       "Book Session (v112+) without waiting. A failed write never touches the booking.\n\n"
                                       "v2: a Localization / QC project code not in Airtable Localization Projects -> the New Projects tab (For Review).")

wf["name"] = "Jessie — Log Booking — v2 (new project codes)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
