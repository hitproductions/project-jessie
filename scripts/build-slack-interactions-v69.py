#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v69.json - Jessie — Slack Interactions — v69 (shorter wait line), 4 Nov.

Howard, 4 Nov: "reduce to 'Keep this window open.' no need for '– the dates are shown right here'". v64's wait lines while dates or
free rooms are checked read "Keep this window open – the dates show here." / "… – the free rooms show here." - now just
"Keep this window open." (Read Step 1's two loading lines, Read Step 2's series check). Nothing else changes.
Built on workflows/imported/slack-interactions-v68-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v68-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


p = by["Read Step 1"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "_wait + (series ? ' Keep this window open – the dates show here.' : ' Keep this window open – the free rooms show here.')",
    "_wait + ' Keep this window open.'   /* v69 (Howard): shorter */")
p = by["Read Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "' Keep this window open – the dates show here.'", "' Keep this window open.'   /* v69 (Howard): shorter */")

wf["name"] = "Jessie — Slack Interactions — v69 (shorter wait line)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v69.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
