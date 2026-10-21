#!/usr/bin/env python3
"""Builds workflows/book-session-v120.json - "Jessie — Book Session", v120 (requests only when asked), 21 Oct.

Slice 2 (docs/design/slice-2-approvals.md):
  1. New input request_ok. A taken room opens a request (priority or shared booth) only when the caller asked for one - the
     form's "Booked – ask to use" (Slack Interactions v37 sends request_ok true). Anything else that finds the room taken is
     refused as before (ROOM_OCCUPIED): a room taken between step 2 and Book no longer opens a request nobody asked for, and
     Finalize's own placement can never open a second request.
  2. A priority request keeps every room it was made with (the studio and its booth / holding rooms), so they are placed
     together once the room is free - it kept only the contested room.
  3. Return Offer passes on what Open Consent Request v12 answers - the request id, its deadline, who was asked, and whether
     it was already open - for the form's "Request sent".
Built on workflows/imported/book-session-v119-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v119-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v120.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
T = "When Executed by Another Workflow"
vals = by[T]["parameters"]["workflowInputs"]["values"]
assert vals[-1]["name"] == "client_cache"
vals.append({"name": "request_ok"})

js = by["Decide Preempt"]["parameters"]["jsCode"]
a = "const REQ = $('When Executed by Another Workflow').first().json || {};\n"
assert js.count(a) == 1
js = js.replace(a, a + "// v120 (slice 2): a request only when the caller asked for one (the form's \"Booked – ask to use\") - otherwise a taken room\n"
                    "// is refused as before (ROOM_OCCUPIED)\n"
                    "if (!(REQ.request_ok === true || String(REQ.request_ok).toLowerCase() === 'true')) return [{ json: Object.assign({}, cc, { offer:false, preemptReason:'NOT_ASKED' }) }];\n")
b = "const reqPayload = JSON.stringify({ summary:REQ.summary, start_iso:REQ.start_iso, end_iso:REQ.end_iso, rooms:inc.room||REQ.rooms,"
assert js.count(b) == 1
js = js.replace(b, "const reqPayload = JSON.stringify({ summary:REQ.summary, start_iso:REQ.start_iso, end_iso:REQ.end_iso, rooms:REQ.rooms||inc.room,   /* v120: every room asked for (a booth, holding rooms) - placed together */")
by["Decide Preempt"]["parameters"]["jsCode"] = js

ro = by["Return Offer"]["parameters"]["jsCode"]
a = "return [{ json: { status:'PREEMPT_PENDING', request_id: r.request_id || '',\n"
assert ro.count(a) == 1
ro = ro.replace(a, "return [{ json: { status:'PREEMPT_PENDING', request_id: r.request_id || '', deadline: r.deadline || '', asked: r.asked || '', existing: r.existing === true,   // v120\n")
by["Return Offer"]["parameters"]["jsCode"] = ro

wf["name"] = "Jessie — Book Session — v120 (requests only when asked)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
