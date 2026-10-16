#!/usr/bin/env python3
"""Builds workflows/move-booking-v33.json - "Jessie — Move Booking", v33 (note + session type): new_details may carry "Notes"
(a new note from the Change form) and "SType" (a new session type). Book Session ends a booking's description with a
"\\nSType: <type>" line; it is kept last and rewritten when the type changes (Slack Interactions v24). Nothing else changes.
Built on workflows/imported/move-booking-v32-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "move-booking-v32-imported.json")
OUT = os.path.join(ROOT, "workflows", "move-booking-v33.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Resolve Booking"][0]
js = n["parameters"]["jsCode"]
for a, b in [
    ("""    let segs = desc.split('|').map(s => s.trim()).filter(Boolean);""",
     """    const _stM = desc.match(/\\n\\s*SType:\\s*([^\\n]*)\\s*$/), _desc0 = _stM ? desc.slice(0, _stM.index) : desc;   // v33: the SType line stays last
    let segs = _desc0.split('|').map(s => s.trim()).filter(Boolean);"""),
    ("""    if ('Rooms' in nd) put('Rooms', nd.Rooms, false);   // v32: studio, booth, holding rooms in order (Slack Interactions v22)
    __desc = segs.join(' | ');""",
     """    if ('Rooms' in nd) put('Rooms', nd.Rooms, false);   // v32: studio, booth, holding rooms in order (Slack Interactions v22)
    if ('Notes' in nd) put('Notes', nd.Notes, false);   // v33: a new note from the Change form
    __desc = segs.join(' | ');
    const _st = 'SType' in nd ? String(nd.SType || '').trim() : (_stM ? _stM[1].trim() : '');   // v33: a new session type
    if (_st) __desc += '\\nSType: ' + _st;"""),
]:
    assert js.count(a) == 1, a[:60]
    js = js.replace(a, b)
n["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Move Booking — v33 (note + session type)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
