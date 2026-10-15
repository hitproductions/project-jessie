#!/usr/bin/env python3
"""Cancel Booking v27 + Move Booking v30 (team may change): decided 14 Oct - the booker AND the session's engineer and
arranger may change or cancel a booking (the Slack-app slice 1 rule; no "Booking for" field). Book Session v109+ writes
their Slack ids on the event as "team: U… U…" (form bookings). Check Ownership (Cancel) and Resolve Booking (Move) now
also allow a requester whose id is in that list. When a team member - not the booker - changes or cancels it, the booker
is told (the same notice a coordinator's change sends; Build Recipients never tells the person who did it).
Built on the live downloads: workflows/imported/cancel-booking-v26-imported.json, move-booking-v29-imported.json.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JOBS = [("cancel-booking-v26-imported.json", "cancel-booking-v27.json", "Check Ownership", "cancel",
         "Jessie — Cancel Booking — v27 (team may cancel)"),
        ("move-booking-v29-imported.json", "move-booking-v30.json", "Resolve Booking", "move",
         "Jessie — Move Booking — v30 (team may change)")]
for src, out, node, verb, name in JOBS:
    wf = json.load(open(os.path.join(ROOT, "workflows", "imported", src)))
    n = {x["name"]: x for x in wf["nodes"]}[node]
    js = n["parameters"]["jsCode"]
    for a, b in [
        ("const owner = ref[1] === me;",
         "const owner = ref[1] === me;\n"
         "// v27/v30 (decided 14 Oct): the session's engineer and arranger (\"team:\" Slack ids, written by form bookings) may " + verb + " it too\n"
         "const team = ((desc.match(/team:\\s*([^|]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean);\n"
         "const onTeam = !!me && team.indexOf(me) !== -1;"),
        ("if (!(owner || isHaistDev || coordInDept))", "if (!(owner || onTeam || isHaistDev || coordInDept))"),
        ("const notify = !owner && (coordInDept || isHaistDev);", "const notify = !owner && (onTeam || coordInDept || isHaistDev);"),
    ]:
        assert js.count(a) == 1, (node, a)
        js = js.replace(a, b)
    n["parameters"]["jsCode"] = js
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out)
