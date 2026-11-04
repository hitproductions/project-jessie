#!/usr/bin/env python3
"""Builds workflows/book-session-v127.json - Jessie — Book Session — v127 (calendar colours), 4 Nov.

PENDING 151 (Howard, 4 Nov: "go ahead with the colors, peacock and grape are fine"). Every booking Jessie creates gets a colour
(scripts/jessie_colour.py): Localization Peacock, Audio Post Blueberry, Music Grape, M booths Basil, celebrity bookings Tomato,
Meeting Banana, Event Tangerine, Van Recording Flamingo, Post Processing Lavender, several departments Sage, the rest Graphite.
Check Conflicts works it out (final_color); Create Event sets it. A series is booked through Book Session, so its dates get it too.
New bookings only - nothing already on the calendar is recoloured.
Built on workflows/imported/book-session-v126-imported.json (the live download).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jessie_colour import JC  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-session-v126-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Check Conflicts"]["parameters"]
js = JC + p["jsCode"]
js = sub(js, "  final_client: String(REQ.client || '').trim() || (_t2.length >= 3 ? _t2[1].trim() : '') } }];",
    "  final_client: String(REQ.client || '').trim() || (_t2.length >= 3 ? _t2[1].trim() : ''),\n"
    "  final_color: __jColour(REQ.session_type, REQ.department, String(REQ.rooms || '').split(',')) } }];   // v127 (PENDING 151)")
p["jsCode"] = js
af = by["Create Event"]["parameters"]["additionalFields"]
assert "color" not in af
af["color"] = "={{ $('Check Conflicts').first().json.final_color || '8' }}"

wf["name"] = "Jessie — Book Session — v127 (calendar colours)"
out = os.path.join(ROOT, "workflows", "book-session-v127.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
