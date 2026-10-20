#!/usr/bin/env python3
"""Builds workflows/book-session-v117.json - "Jessie — Book Session", v117 (Booked without the room wait), 20 Oct.

Includes v116 (no client lookups without a client). Howard, 20 Oct: every booking goes through Jessie and the Envoy tablets
mirror onto KDC Bookings, so the check before booking (Get Events In Window, KDC Bookings) sees every booking; "Booked." can
show as soon as the event is created, and a room that declines is only reported.
  - Create Event -> Verify at once (Verify reads the create response: times checked, no room has answered yet). The read-backs
    at ~1.5 / 3 / 6 s (Wait for Room, Reread Event, Room Answered? x3) are gone - 1.5-6 s off every booking, every date of a
    series.
  - After Log Booking, "Room Check" calls Jessie — Room Check without waiting: it reads the rooms' answer after "Booked." and,
    on a decline, deletes the event, DMs the person who booked and logs ROOM_DECLINED.
Built on workflows/book-session-v116.json (v116, built on the v115 download; not imported - import this instead).
The Room Check node carries a placeholder id: import Jessie — Room Check first, then scripts/set-room-check-id.py <id>.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "book-session-v116.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v117.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
T = "When Executed by Another Workflow"

GONE = ["Wait for Room", "Reread Event", "Room Answered?", "Wait for Room 2", "Reread Event 2", "Room Answered 2?", "Wait for Room 3", "Reread Event 3"]
assert C["Create Event"]["main"][0][0]["node"] == "Wait for Room", C["Create Event"]
C["Create Event"]["main"][0] = [{"node": "Verify", "type": "main", "index": 0}]
for n in GONE:
    wf["nodes"].remove(by.pop(n))
    C.pop(n, None)
for src in C.values():
    for outs in src.get("main", []):
        if outs:
            outs[:] = [c for c in outs if c["node"] not in GONE]

js = by["Verify"]["parameters"]["jsCode"]
a = "// v112: read back at ~1.5 / 3 / 6 s, as soon as every room has answered (was a fixed 6 s).\n"
assert js.count(a) == 1
by["Verify"]["parameters"]["jsCode"] = js.replace(a, "// v117: the create response itself - \"Booked.\" without waiting for the rooms; Jessie — Room Check reads their answer\n"
                                                   "// afterwards and reports a decline (v112-v116: read back at ~1.5 / 3 / 6 s).\n")

lb = by["Log Booking"]
assert C["Log Booking"]["main"][0][0]["node"] == "Return Booked", C["Log Booking"]
rc = json.loads(json.dumps(lb))
rc.update({"id": str(uuid.uuid4()), "name": "Room Check", "position": [lb["position"][0] + 200, lb["position"][1] + 120]})
rc["parameters"]["workflowId"] = {"__rl": True, "mode": "id", "value": "ROOM_CHECK_ID", "cachedResultName": "Jessie — Room Check"}
V = "$('Verify').first().json"
CCx = "($('Check Conflicts').first().json || {})"
R = "$('" + T + "').first().json"
rc["parameters"]["workflowInputs"] = {"mappingMode": "defineBelow", "value": {
    "event_id": "={{ " + V + ".event_id || '' }}",
    "title": "={{ " + V + ".title || " + CCx + ".final_summary || " + R + ".summary || '' }}",
    "rooms": "={{ " + CCx + ".final_rooms || " + R + ".rooms || '' }}",
    "requester": "={{ (String(" + R + ".description || '').match(/ref:\\s*([A-Z0-9]+)/i) || [])[1] || '' }}",
    "start_iso": "={{ " + CCx + ".final_start || " + R + ".start_iso || '' }}",
    "end_iso": "={{ " + CCx + ".final_end || " + R + ".end_iso || '' }}",
    "all_day": "={{ String(" + R + ".all_day === true || " + R + ".all_day === 'true') }}",
    "session_type": "={{ " + R + ".session_type || '' }}"},
    "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True}
rc["parameters"]["options"] = {"waitForSubWorkflow": False}
wf["nodes"].append(rc)
C["Log Booking"]["main"][0] = [{"node": "Room Check", "type": "main", "index": 0}]
C["Room Check"] = {"main": [[{"node": "Return Booked", "type": "main", "index": 0}]]}

wf["name"] = "Jessie — Book Session — v117 (Booked without the room wait)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
