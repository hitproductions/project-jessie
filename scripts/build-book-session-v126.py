#!/usr/bin/env python3
"""Builds workflows/book-session-v126.json - Jessie — Book Session — v126 (Studio E as a booth), 4 Nov.

Since 3 Nov Studio E is a vocal booth in Airtable (Howard: paired with a studio for Localization Dubbing). v113's rule refused any
booking with Studio E in it unless it was Post Processing. Now only Studio E as the booking's room (the first room) is Post
Processing's; Studio E after another room is a booth, for any type. Nothing else changes.
Built on workflows/book-session-v125.json (imported 4 Nov; the before-download MATCHED v124, the after-download is owed - check it
against v125 before importing this).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "book-session-v125.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Check Conflicts"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "  // v113 (round 9, 19 Oct): Studio E is Post Processing's room only\n"
    "  if (!/^post processing$/i.test(_st) && _lc.indexOf('studio e') !== -1)",
    "  // v113 (round 9, 19 Oct): Studio E is Post Processing's room only\n"
    "  // v126 (4 Nov): ... as the booking's room. After another room it is a vocal booth (Airtable, 3 Nov) - any type may pair it\n"
    "  if (!/^post processing$/i.test(_st) && _lc[0] === 'studio e')")

wf["name"] = "Jessie — Book Session — v126 (Studio E as a booth)"
out = os.path.join(ROOT, "workflows", "book-session-v126.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
