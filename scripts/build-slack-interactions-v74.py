#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v74.json - Jessie — Slack Interactions — v74 (no Picked: on people / studios), 6 Nov.

Howard, 6 Nov (v73 live): "remove the 'Picked: ' i think it's redundant since i already see it. remove that as well for multiple studios
select. just need to accept that mobile has limited views only". The "Picked: …" line is gone under Engineer, Arranger and + Multiple
studios / rooms (Book a room and Change), and those fields no longer call n8n when they change (that call only redrew the line). Vocal
booths and Holding rooms keep their line (the Localization feedback, 3 Nov). Nothing else changes.
Built on workflows/imported/slack-interactions-v73-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v73-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


ACT_OLD = "const ACT = ['booth_pick', 'more_rooms_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick', 'more_c_pick', 'engineer_pick', 'arranger_pick', 'det_engineer_pick', 'det_arranger_pick'];"
ACT_NEW = "const ACT = ['booth_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick'];   // v74 (Howard): not people or + Multiple studios - the field shows them"
PICK_OLD = "    if (os.length >= (/^(?:det_)?(?:engineer|arranger)_pick$/.test(String(e.action_id)) ? 1 : 2)) bl.splice(i + 1, 0,   /* v73: a person from one pick (a phone shows \"1 selected\") */"
PICK_NEW = "    if (os.length >= 2) bl.splice(i + 1, 0,"
for name in ("Build Step 2",) + CHANGE_NODES:
    code(name, lambda js: sub(sub(js, ACT_OLD, ACT_NEW), PICK_OLD, PICK_NEW))
code("Build Step 2", lambda js: sub(sub(js, "blk.dispatch_action = true; ", ""),
    "{ type: 'input', dispatch_action: true, block_id: 'more_rooms',", "{ type: 'input', block_id: 'more_rooms',"))
for name in CHANGE_NODES:
    code(name, lambda js: sub(sub(js, "el && el.type === 'multi_static_select' ? { dispatch_action: true } : {}",
        "el && el.type === 'multi_static_select' && /^(?:booth|holding)_c_pick$/.test(String(el.action_id)) ? { dispatch_action: true } : {}   /* v74: only where a Picked: line is drawn */"),
        "out.push({ type: 'input', dispatch_action: true, block_id: meet ? 'rooms_c' : 'studios_c',", "out.push({ type: 'input', block_id: meet ? 'rooms_c' : 'studios_c',"))

wf["name"] = "Jessie — Slack Interactions — v74 (no Picked: on people / studios)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v74.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
