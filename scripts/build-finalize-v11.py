#!/usr/bin/env python3
"""Builds workflows/finalize-consent-v11.json - "Jessie — Finalize Consent", v11 (messages updated in place), 21 Oct.

Slice 2 (docs/design/slice-2-approvals.md). Built on the live 29 Sep snapshot
(workflows/live/jessie-finalize-consent__TO1UnZTZ2LhtE9J3.json) - NOT on the unimported v10 candidate.
  1. The row is read again from the sheet first (Read Row): a request already ended (or withdrawn) is never placed - the
     callers pass a copy of the row that can be minutes old (the Sweep, Move's tail hook, Slack Interactions).
  2. WITHDRAWN is an ending too (the requester's Withdraw request button).
  3. The plain "Done - ..." DMs to the requester and the holder go: Jessie — Request Messages (mode end) updates every
     message of the request in place - the requester's card becomes the Booked card (Change / Cancel, Book another), the
     booker's / engineer's / holder's request says it is done. v10's DMs went to the row's ids as stored; since Open Consent
     Request v12 those are the real people, so they would have reached real staff during QA.
  4. A placement that failed updates the messages the same way ("Couldn't book … after all").
The Request Messages workflow id is set by scripts/set-request-messages-id.py after it is imported.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "live", "jessie-finalize-consent__TO1UnZTZ2LhtE9J3.json")
OUT = os.path.join(ROOT, "workflows", "finalize-consent-v11.json")
SW = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "live", "jessie-consent-sweep__QHHDevaWhMk8gSBX.json")))["nodes"]}
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
REQUEST_MESSAGES_ID = "REQUEST_MESSAGES_ID"   # scripts/set-request-messages-id.py
C = wf["connections"]


def code(name, js, pos):
    return {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}


def msgs(name, row_expr, extra_expr, pos):
    return {"parameters": {"workflowId": {"__rl": True, "mode": "id", "value": REQUEST_MESSAGES_ID, "cachedResultName": "Jessie — Request Messages"},
                           "workflowInputs": {"mappingMode": "defineBelow", "value": {"mode": "end", "row": row_expr, "extra": extra_expr},
                                              "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                           "options": {}},
            "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": pos,
            "alwaysOutputData": True, "onError": "continueRegularOutput"}


T = "When Executed by Another Workflow"
x0, y0 = by[T]["position"]
read = json.loads(json.dumps(SW["Read Pending Rows"]))
read.update({"id": str(uuid.uuid4()), "name": "Read Row", "position": [x0 + 110, y0 + 200], "executeOnce": True, "alwaysOutputData": True,
             "onError": "continueRegularOutput"})
wf["nodes"].append(read)
assert C[T]["main"][0][0]["node"] == "Plan"
C[T] = {"main": [[{"node": "Read Row", "type": "main", "index": 0}]]}
C["Read Row"] = {"main": [[{"node": "Plan", "type": "main", "index": 0}]]}

plan = by["Plan"]["parameters"]["jsCode"]
a = "const row = safeParse(IN.row) || {};"
assert plan.count(a) == 1
plan = plan.replace(a, "const row0 = safeParse(IN.row) || {};\n"
    "// v11: the row as the sheet has it now - a request that ended (or was withdrawn) since the caller read it is never placed\n"
    "let fresh = null; try { fresh = $('Read Row').all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(row0['Request ID'])) || null; } catch (e) { fresh = null; }\n"
    "const row = Object.assign({}, row0, fresh || {});")
a = "if(['DONE','REJECTED','EXPIRED','FAILED'].indexOf(status)!==-1)"
assert plan.count(a) == 1
plan = plan.replace(a, "if(['DONE','REJECTED','EXPIRED','FAILED','WITHDRAWN'].indexOf(status)!==-1)")   # v11
by["Plan"]["parameters"]["jsCode"] = plan

INFO = r"""// v11: how it ended, for Jessie — Request Messages - the row as written, and the requester's new booking (Change / Cancel)
const P = $('Plan').first().json, IN = $('When Executed by Another Workflow').first().json || {};
let row = {}; try { row = JSON.parse(IN.row || '{}') || {}; } catch (e) { row = {}; }
try { const f = $('Read Row').all().map(i => i.json || {}).find(r => String(r['Request ID'] || '') === String(row['Request ID'] || '')); if (f) row = Object.assign({}, row, f); } catch (e) {}
let ev = {};
try { const b = $('Book Requester').first().json || {}; if (b.event_id) ev = { id: b.event_id, title: b.title || b.summary || '' }; } catch (e) {}
try { if (!ev.id) { const m = $('Move Requester').first().json || {}; if (m.event_id) ev = { id: m.event_id, title: m.title || '' }; } } catch (e) {}
const upd = __UPD__;
return [{ json: { row: JSON.stringify(Object.assign({}, row, upd)), extra: JSON.stringify({ how: IN.resolvedVia || '', by: IN.attestedBy || '', event: ev,
  why: __WHY__ }) } }];
"""
done_info = code("Done Info", INFO.replace("__UPD__", "P.rowDone").replace("__WHY__", "''"), [0, 0])
fail_info = code("Fail Info", INFO.replace("__UPD__", "P.rowFailPlace").replace("__WHY__", "'it’s still taken then'"), [0, 0])
done_msgs = msgs("Done Messages", "={{ $json.row }}", "={{ $json.extra }}", [0, 0])
fail_msgs = msgs("Fail Messages", "={{ $json.row }}", "={{ $json.extra }}", [0, 0])
for new, old in ((done_info, "Notify Incumbent"), (done_msgs, "Notify Requester OK"), (fail_info, "Notify Place Fail")):
    new["position"] = list(by[old]["position"])
fail_msgs["position"] = [by["Notify Place Fail"]["position"][0] + 220, by["Notify Place Fail"]["position"][1] + 160]
wf["nodes"] = [n for n in wf["nodes"] if n["name"] not in ("Notify Incumbent", "Notify Requester OK", "Notify Place Fail")] + [done_info, done_msgs, fail_info, fail_msgs]
L = lambda a: {"main": [[{"node": a, "type": "main", "index": 0}]]}
assert C["Mark Done"]["main"][0][0]["node"] == "Notify Incumbent" and C["Mark Failed Place"]["main"][0][0]["node"] == "Notify Place Fail"
C["Mark Done"] = L("Done Info"); C["Done Info"] = L("Done Messages"); C["Done Messages"] = L("Return Done")
C["Mark Failed Place"] = L("Fail Info"); C["Fail Info"] = L("Fail Messages"); C["Fail Messages"] = L("Return Place Fail")
for k in ("Notify Incumbent", "Notify Requester OK", "Notify Place Fail"):
    C.pop(k, None)
by["About"]["parameters"]["content"] = by["About"]["parameters"]["content"] + (
    "\n\nv11 (slice 2): reads the row again first (an ended / withdrawn request is never placed); the outcome updates every message of "
    "the request through Jessie — Request Messages instead of plain DMs.")
wf["name"] = "Jessie — Finalize Consent — v11 (messages updated in place)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
