#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v62.json - Jessie — Slack Interactions — v62 (v61 fixed), 3 Nov.

Howard's Slack test of v61, 3 Nov: a date picked in "Or until" went back to blank. v61 redraws Or until under a new block_id
and fills it from the modal's saved state; the date just picked is not in that state when its own action arrives (v60 kept the
same block_id, so Slack kept the pick on screen by itself, gotcha 47). The How often / On handlers (v57 / v58) always took the
action's own value; How many times, Or until and the first date did not.

v62: the field that sent the action takes the action's own value (selected_date / selected_option) before the redraw and the
Repeats line are worked out - Or until, How many times and the first date keep what was just picked. Nothing else changes.
Built on workflows/imported/slack-interactions-v61-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v61-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Note Toggle"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "{ const ni = blocks.findIndex(b => b.block_id === 'rep_note');\n  if (ni !== -1) {\n",
    "// v62 (v61 fixed): the field that sent this action keeps what was just picked - the modal's saved state does not have it yet\n"
    "// (v61 redrew Or until under a new id from that state, so a picked end date went blank)\n"
    "if (which === 'rep_until_pick' || which === 'rep_count_pick' || which === 'date_pick') {\n"
    "  const tb = blocks.find(b => b.type === 'input' && b.element && b.element.action_id === a.action_id);\n"
    "  if (tb) { const e = tb.element;\n"
    "    if (a.selected_date) e.initial_date = a.selected_date;\n"
    "    if (a.selected_option) { const o = (e.options || []).find(x => x.value === a.selected_option.value); if (o) e.initial_option = o; } }\n"
    "}\n"
    "{ const ni = blocks.findIndex(b => b.block_id === 'rep_note');\n  if (ni !== -1) {\n")

wf["name"] = "Jessie — Slack Interactions — v62 (v61 fixed)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v62.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
