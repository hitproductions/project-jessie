#!/usr/bin/env python3
"""Builds workflows/move-booking-v34.json - "Jessie — Move Booking", v34 (the room's answer after a change), 20 Oct.

Move Booking never checked whether the rooms accepted a change (Book Session did for new bookings; since v117 Jessie — Room
Check does it after "Booked."). Now, once a change has gone through (the new event created, the old one deleted, the notices
sent), "Room Check" calls Jessie — Room Check (CB3JPU052OfHFIQr) without waiting, with kind "move": a room that turns the new
time down is reported to the person who changed it (DM with Change / My bookings) - never deleted, since the old event is gone.
Built on workflows/imported/move-booking-v33-imported.json (the live download). Import Room Check v2 first.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "move-booking-v33-imported.json")
BOOK = os.path.join(ROOT, "workflows", "imported", "book-session-v119-imported.json")
OUT = os.path.join(ROOT, "workflows", "move-booking-v34.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
T = "When Executed by Another Workflow"
rc = json.loads(json.dumps([n for n in json.load(open(BOOK))["nodes"] if n["name"] == "Room Check"][0]))
x, y = by["Return Moved"]["position"]
rc.update({"id": str(uuid.uuid4()), "position": [x - 200, y + 160]})
assert rc["parameters"]["workflowId"]["value"] == "CB3JPU052OfHFIQr"
R = "$('Resolve Booking').first().json"
CR = "($('Create Replacement').first().json || {})"
Q = "$('" + T + "').first().json"
rc["parameters"]["workflowInputs"] = {"mappingMode": "defineBelow", "value": {
    "event_id": "={{ " + CR + ".id || '' }}",
    "title": "={{ " + CR + ".summary || " + R + ".title || '' }}",
    "rooms": "={{ " + R + ".location || " + Q + ".new_rooms || '' }}",
    "requester": "={{ " + Q + ".requester || '' }}",
    "start_iso": "={{ " + R + ".new_start || '' }}",
    "end_iso": "={{ " + R + ".new_end || '' }}",
    "all_day": "={{ String(!/T\\d/.test(String(" + R + ".new_start || ''))) }}",
    "session_type": "={{ ((String(" + R + ".description || '').match(/SType:\\s*([^\\n|]+)/i) || [])[1] || '').trim() }}",
    "kind": "move"},
    "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True}
rc["parameters"]["options"] = {"waitForSubWorkflow": False}
rc["executeOnce"] = True   # Send DMs passes one item per notice - one Room Check per change
wf["nodes"].append(rc)
# Notify? (no) -> Return Moved and Send DMs -> Return Moved become ... -> Room Check -> Return Moved
assert [c["node"] for c in C["Notify?"]["main"][1]] == ["Return Moved"] and [c["node"] for c in C["Send DMs"]["main"][0]] == ["Return Moved"]
C["Notify?"]["main"][1] = [{"node": "Room Check", "type": "main", "index": 0}]
C["Send DMs"]["main"][0] = [{"node": "Room Check", "type": "main", "index": 0}]
C["Room Check"] = {"main": [[{"node": "Return Moved", "type": "main", "index": 0}]]}
assert "$input" not in by["Return Moved"]["parameters"]["jsCode"]
wf["name"] = "Jessie — Move Booking — v34 (the room's answer after a change)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
