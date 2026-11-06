#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v73.json - Jessie — Slack Interactions — v73 (back to v70's fields), 6 Nov.

Howard, 6 Nov (testing v72): "form loading is too slow... let's revert to just using multiple select for engineers. except for
localization session types. revert also to showing multiple studios without a tick". v73 puts back v70's code in the nine nodes v71 /
v72 changed (Check Signature, Build Step 2, Read Step 2, Build Change, Read Change, To Move, After Move, Note Toggle, Build Change C):
Engineer and Arranger multi-selects outside Localization, "+ Multiple studios" shown without a tick, no "Multiple engineers" tick.
One change on top: a phone shows a one-pick multi-select as "1 selected", so the "Picked:" line under Engineer / Arranger shows from
one pick (drawn with the form - no extra call).
Built on workflows/imported/slack-interactions-v72-imported.json (the live download); those nine nodes from
workflows/imported/slack-interactions-v70-imported.json.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v72-imported.json")))
v70 = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v70-imported.json")))["nodes"]}
NODES = ("Check Signature", "Build Step 2", "Read Step 2", "Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")
by = {n["name"]: n for n in wf["nodes"]}
for name in NODES:
    by[name]["parameters"] = json.loads(json.dumps(v70[name]["parameters"]))

PICK_OLD = "    if (os.length >= 2) bl.splice(i + 1, 0,"
PICK_NEW = "    if (os.length >= (/^(?:det_)?(?:engineer|arranger)_pick$/.test(String(e.action_id)) ? 1 : 2)) bl.splice(i + 1, 0,   /* v73: a person from one pick (a phone shows \"1 selected\") */"
for name in ("Build Step 2", "Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C"):
    p = by[name]["parameters"]
    assert p["jsCode"].count(PICK_OLD) == 1, (name, p["jsCode"].count(PICK_OLD))
    p["jsCode"] = p["jsCode"].replace(PICK_OLD, PICK_NEW)

wf["name"] = "Jessie — Slack Interactions — v73 (back to v70's fields)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v73.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
