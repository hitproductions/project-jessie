#!/usr/bin/env python3
"""main v270 (round 2: client capitals, room names): two of the notes from testing builds A + B (15 Oct), with Slack
Interactions v19.
  - a typed client gets a capital first letter on every word on the booking reply and its button ("client john smithy" ->
    John Smithy; "ACME" stays) - the form then books it that way;
  - the typed change / cancel reply names a room as the room list does ("Likha (Big Room)" -> Likha), so its Change opens
    on the right kind of room.
Built on workflows/imported/project-jessie-v269-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v269-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v270.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Form Offer", [
    ("    if (client && !/^none$/i.test(client)) P.c = cut(client, 80);",
     "    // v270: a capital first letter on every word (\"john smithy\" -> \"John Smithy\"; the rest as typed)\n"
     "    if (client && !/^none$/i.test(client)) P.c = cut(String(client).replace(/(^|[\\s\\-'’])(\\p{Ll})/gu, (m, p, c) => p + c.toUpperCase()), 80);"),
])
patch("Change Reply", [
    ("""function evRoom(e) { const r = (e.attendees || []).filter(a => a.resource || /@resource\\.calendar\\.google\\.com$/i.test(String(a.email || '')))
  .map(a => String(a.displayName || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\\s*\\(\\d+\\)\\s*$/, '').trim()).filter(Boolean);
  return r.length ? r.join(', ') : String(e.location || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\\s*\\(\\d+\\)\\s*$/, '').trim(); }""",
     """// v270: a calendar room label ("KDC Plaza-Top Level-Likha (Big Room)") -> the room's own name ("Likha")
function roomName(x) { return String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\\s*\\([^)]*\\)\\s*$/, '').trim(); }
function evRoom(e) { const r = (e.attendees || []).filter(a => a.resource || /@resource\\.calendar\\.google\\.com$/i.test(String(a.email || '')))
  .map(a => roomName(a.displayName)).filter(Boolean);
  return r.length ? r.join(', ') : roomName(e.location); }"""),
])
wf["name"] = "Project Jessie — v270 (round 2: client capitals, room names)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
