#!/usr/bin/env python3
"""Builds workflows/project-jessie-v290.json - Project Jessie — v290 (Studio M note), 4 Nov.

Howard, 4 Nov (after v289): "book studio 1 and m" passed Studio M to the form under + Multiple studios, where it is never offered
(Studio M - the van - is only for Van Recording), so it was dropped without a word. Now Form Offer says so:
- several rooms typed with Studio M, not Van Recording -> Studio M is left off, and the offer says
  "⚠️ Studio M is only for Van Recording, so it's left off.";
- Studio M with other rooms for Van Recording ("van" typed) -> Studio M only, "⚠️ Van Recording is in Studio M only, so the other
  rooms are left off.";
- "studio 1 or m" (a choice) and Studio M alone - as before.
Built on workflows/imported/project-jessie-v289-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "project-jessie-v289-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Form Offer"]["parameters"]
js = p["jsCode"]
js = sub(js, "    const rNow = _asked.length >= 2 ? _asked : roomsIn(t), rAll = roomsIn(ctx);\n",
    "    let _rn = _asked.length >= 2 ? _asked : roomsIn(t);\n"
    "    // v290 (Howard, 4 Nov): Studio M (the van) is only for Van Recording - with other rooms it was dropped in the form without a word\n"
    "    if (_rn.length > 1 && _rn.indexOf('Studio M') !== -1 && !/\\b(?:or|either)\\b/i.test(t)) {\n"
    "      if (/\\bvan\\b/i.test(t)) { _rn = ['Studio M']; fo.mNote = 'Van Recording is in Studio M only, so the other rooms are left off.'; }\n"
    "      else { _rn = _rn.filter(n => n !== 'Studio M'); fo.mNote = 'Studio M is only for Van Recording, so it’s left off.'; }\n"
    "    }\n"
    "    const rNow = _rn, rAll = roomsIn(ctx);\n")
js = sub(js, "      fo.text = lines.join('\\n');", "      fo.text = lines.concat(fo.mNote ? ['⚠️ ' + fo.mNote] : []).join('\\n');   // v290")
p["jsCode"] = js

wf["name"] = "Project Jessie — v290 (Studio M note)"
out = os.path.join(ROOT, "workflows", "project-jessie-v290.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
