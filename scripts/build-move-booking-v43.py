#!/usr/bin/env python3
"""Builds workflows/move-booking-v43.json - Jessie — Move Booking — v43 (calendar colours), 4 Nov.

PENDING 151 (with Book Session v127). A change creates the replacement event before removing the original; until now it carried no
colour. The replacement's colour: for a booking Jessie made (Dept / SType in its description), the colour rule (scripts/jessie_colour.py)
for its details after the change - when it had no colour, or the colour the rule gives its details before the change (Jessie's); any
other colour was set by hand and is kept. A booking made by hand keeps its colour, or none - nothing is recoloured in bulk. Resolve Booking works it out (color_id); Create Replacement sends it.
Built on workflows/imported/move-booking-v42-imported.json (the live download).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jessie_colour import JC  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "move-booking-v42-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Resolve Booking"]["parameters"]
js = JC + p["jsCode"]
js = sub(js, "return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title: __title, team,",
    "// v43 (PENDING 151): the replacement's colour - the rule for the booking as changed, unless the original's colour was set by hand\n"
    "let __colour = '';\n"
    "try {\n"
    "  const _rooms = loc => (String(loc || '').match(/Studio [0-9A-Z]\\b|\\bM[1-8]\\b|Salin|Katha|Likha|Lobby/g) || []);\n"
    "  const _of = (d, loc) => { const s = String(d || ''); return __jColour(((s.match(/\\n\\s*SType:\\s*([^\\n]*)/) || [])[1] || ''),\n"
    "    ((s.split(/\\n/)[0].match(/(?:^|\\|)\\s*Dept:\\s*([^|]+)/) || [])[1] || ''), _rooms(loc)); };\n"
    "  const _was = String(ev.colorId || '');\n"
    "  const _jessie = /(?:^|\\|)\\s*Dept:|\\n\\s*SType:/.test(String(ev.description || ''));   // made by Jessie (a hand-made booking keeps its colour, or none)\n"
    "  __colour = _jessie && (!_was || _was === _of(ev.description, ev.location)) ? _of(__desc, outLocation) : _was;\n"
    "} catch (e) { __colour = String(ev.colorId || ''); }\n"
    "return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title: __title, team, color_id: __colour,")
p["jsCode"] = js
cr = by["Create Replacement"]["parameters"]
old = "start: { dateTime: $json.new_start, timeZone: 'Asia/Manila' }, end: { dateTime: $json.new_end, timeZone: 'Asia/Manila' } }) }}"
assert cr["jsonBody"].count(old) == 1
cr["jsonBody"] = cr["jsonBody"].replace(old, "start: { dateTime: $json.new_start, timeZone: 'Asia/Manila' }, end: { dateTime: $json.new_end, timeZone: 'Asia/Manila' }, colorId: ($('Resolve Booking').first().json.color_id || undefined) }) }}")

wf["name"] = "Jessie — Move Booking — v43 (calendar colours)"
out = os.path.join(ROOT, "workflows", "move-booking-v43.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
