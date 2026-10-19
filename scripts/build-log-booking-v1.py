#!/usr/bin/env python3
"""Builds workflows/log-booking-v1.json - "Jessie — Log Booking", v1 (new, round 8, 19 Oct): writes a booking's rows to the
Jessie Log spreadsheet - the Log row, and for a client the Clients table does not know, the New Clients row (appendOrUpdate
on Client, Status For Review, for Howard to add to Airtable). Book Session v112 calls it without waiting, so "Booked." no
longer waits for Google Sheets. The nodes are Book Session v111's Log to Sheet and Log New Client, unchanged.
Inputs: log, client - each one row as JSON text (client empty for a known client).
Import into a NEW workflow (it has no id yet), then run scripts/set-log-booking-id.py <its id> so Book Session v112 calls it.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v111-imported.json")
OUT = os.path.join(ROOT, "workflows", "log-booking-v1.json")
book = {n["name"]: n for n in json.load(open(SRC))["nodes"]}


def node(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    return n


def copy(name, pos):
    n = json.loads(json.dumps(book[name]))
    n["id"] = str(uuid.uuid4())
    n["position"] = pos
    return n


trigger = node("When Executed by Another Workflow", "n8n-nodes-base.executeWorkflowTrigger", 1.1,
               {"workflowInputs": {"values": [{"name": "log"}, {"name": "client"}]}}, [0, 0])
log_row = node("Log Row", "n8n-nodes-base.code", 2, {"jsCode": (
    "// Log Row: the Jessie Log row Book Session made (Build Log Row), as one item for Log to Sheet.\n"
    "let r = null; try { r = JSON.parse(String($('When Executed by Another Workflow').first().json.log || '')); } catch (e) { r = null; }\n"
    "return r && typeof r === 'object' ? [{ json: r }] : [];")}, [224, 0], {"onError": "continueRegularOutput"})
log_sheet = copy("Log to Sheet", [448, 0])
client_row = node("Client Row", "n8n-nodes-base.code", 2, {"jsCode": (
    "// Client Row: the New Clients row, only for a client the Clients table did not know - none, no item, nothing written.\n"
    "let r = null; try { r = JSON.parse(String($('When Executed by Another Workflow').first().json.client || '')); } catch (e) { r = null; }\n"
    "return r && typeof r === 'object' && r['Client'] ? [{ json: r }] : [];")}, [672, 0],
                  {"onError": "continueRegularOutput", "executeOnce": True})
new_client = copy("Log New Client", [896, 0])
sticky = node("Note", "n8n-nodes-base.stickyNote", 1, {"content": (
    "## Jessie — Log Booking\nWrites a booking's rows to the Jessie Log spreadsheet after the reply has gone. Called by Book "
    "Session (v112+) without waiting. A failed write never touches the booking."), "height": 160, "width": 420}, [0, -240])
wf = {
    "name": "Jessie — Log Booking — v1 (log after the reply)",
    "nodes": [trigger, log_row, log_sheet, client_row, new_client, sticky],
    "connections": {
        trigger["name"]: {"main": [[{"node": "Log Row", "type": "main", "index": 0}]]},
        "Log Row": {"main": [[{"node": "Log to Sheet", "type": "main", "index": 0}]]},
        "Log to Sheet": {"main": [[{"node": "Client Row", "type": "main", "index": 0}]]},
        "Client Row": {"main": [[{"node": "Log New Client", "type": "main", "index": 0}]]},
    },
    "pinData": {},
    "active": False,
    "settings": {"executionOrder": "v1"},
    "meta": {},
    "tags": [],
}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
