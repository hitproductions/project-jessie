#!/usr/bin/env python3
"""Builds workflows/move-booking-v32.json - "Jessie — Move Booking", v32 (rooms line): new_details may carry "Rooms" - the
booking's rooms in order (studio, booth, holding rooms), written by the form (Slack Interactions v22) because Google returns
room attendees in its own order. '' removes the line (one room left). Nothing else changes.
Built on workflows/imported/move-booking-v31-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "move-booking-v31-imported.json")
OUT = os.path.join(ROOT, "workflows", "move-booking-v32.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Resolve Booking"][0]
js = n["parameters"]["jsCode"]
a = """    if ('team' in nd) put('team', nd.team, false);"""
assert js.count(a) == 1
js = js.replace(a, a + """
    if ('Rooms' in nd) put('Rooms', nd.Rooms, false);   // v32: studio, booth, holding rooms in order (Slack Interactions v22)""")
n["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Move Booking — v32 (rooms line)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
