#!/usr/bin/env python3
"""Builds workflows/consent-sweep-v3.json - "Jessie — Consent Sweep", v3 (no answer: messages updated), 21 Oct.

Slice 2 (docs/design/slice-2-approvals.md). Built on the live 29 Sep snapshot
(workflows/live/jessie-consent-sweep__QHHDevaWhMk8gSBX.json) - not on the unimported v2 candidate.
  1. A priority request with no answer by its deadline (EXPIRED): every message of it is updated - the requester's card says
     "No answer by … – <room> stays booked." with Pick another room; the booker's / engineer's says the request ended. Before,
     only the row changed and nobody was told.
  2. An M booth request with no answer is still booked for the requester through Finalize (which updates its messages).
  3. Fix: several requests due in the same sweep - Sweep Book now calls Finalize once per request (mode "each"); it passed
     them all in one call and Finalize placed only the first.
  4. Mark Expired writes only the sheet's columns (it also sent _sweepAction).
The Request Messages workflow id is set by scripts/set-request-messages-id.py after it is imported.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "live", "jessie-consent-sweep__QHHDevaWhMk8gSBX.json")
OUT = os.path.join(ROOT, "workflows", "consent-sweep-v3.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
REQUEST_MESSAGES_ID = "REQUEST_MESSAGES_ID"   # scripts/set-request-messages-id.py

js = by["Sweep Decide"]["parameters"]["jsCode"]
a = "out.push({ json: { 'Request ID':r['Request ID'], 'Status':'EXPIRED', 'Resolved Via':'sweep-expired', 'Decided At':now, _sweepAction:'expire' } });"
assert js.count(a) == 1
js = js.replace(a, "out.push({ json: { 'Request ID':r['Request ID'], 'Status':'EXPIRED', 'Resolved Via':'sweep-expired', 'Decided At':now, _sweepAction:'expire', _row:r /* v3: for its messages */ } });")
by["Sweep Decide"]["parameters"]["jsCode"] = js
by["Sweep Book"]["parameters"]["mode"] = "each"   # v3: one Finalize per request (it used to place only the first)


def code(name, src, pos):
    return {"parameters": {"jsCode": src}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}


x, y = by["Mark Expired"]["position"]
exp_row = code("Expire Row", "// v3: only the sheet's columns\nreturn $input.all().map(i => ({ json: { 'Request ID': i.json['Request ID'], 'Status': 'EXPIRED', "
               "'Resolved Via': 'sweep-expired', 'Decided At': i.json['Decided At'] } }));\n", [x, y])
by["Mark Expired"]["position"] = [x + 220, y]
exp_info = code("Expire Info", "// v3: each request that ran out - its messages say so (Jessie — Request Messages, mode end)\n"
                "return $('Sweep Decide').all().map(i => i.json || {}).filter(j => j._sweepAction === 'expire' && j._row)\n"
                "  .map(j => ({ json: { row: JSON.stringify(Object.assign({}, j._row, { 'Status': 'EXPIRED', 'Resolved Via': 'sweep-expired', 'Decided At': j['Decided At'] })),\n"
                "    extra: JSON.stringify({ how: 'sweep-expired' }) } }));\n", [x + 440, y])
exp_msgs = {"parameters": {"mode": "each", "workflowId": {"__rl": True, "mode": "id", "value": REQUEST_MESSAGES_ID, "cachedResultName": "Jessie — Request Messages"},
                           "workflowInputs": {"mappingMode": "defineBelow", "value": {"mode": "end", "row": "={{ $json.row }}", "extra": "={{ $json.extra }}"},
                                              "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                           "options": {}},
            "id": str(uuid.uuid4()), "name": "Expire Messages", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2,
            "position": [x + 660, y], "onError": "continueRegularOutput"}
wf["nodes"] += [exp_row, exp_info, exp_msgs]
assert C["Sweep Route?"]["main"][1][0]["node"] == "Mark Expired"
C["Sweep Route?"]["main"][1] = [{"node": "Expire Row", "type": "main", "index": 0}]
C["Expire Row"] = {"main": [[{"node": "Mark Expired", "type": "main", "index": 0}]]}
C["Mark Expired"] = {"main": [[{"node": "Expire Info", "type": "main", "index": 0}]]}
C["Expire Info"] = {"main": [[{"node": "Expire Messages", "type": "main", "index": 0}]]}
wf["name"] = "Jessie — Consent Sweep — v3 (no answer: messages updated)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
