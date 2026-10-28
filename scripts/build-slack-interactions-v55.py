#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v55.json - Jessie — Slack Interactions — v55 (note kept), 28 Oct.

Howard's Slack test of v54, 28 Oct: step 2 opened again from the DM (the window had been closed - "Continue booking" / "Book a
room") with every pick back but the Note empty. The DM button carries the form's answers (Read Step 2's `again`), and the note was
never one of them (v27-v54). And when those answers were longer than the button allows (1,900 characters) the button carried none
of them at all.

v55: the answers carry the note (`nt`, at most 600 characters) and step 2 fills the Note in from it; if the answers are still too
long for the button, the note is left off first (the other answers kept) before giving up. Built on
workflows/imported/slack-interactions-v54-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v54-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Read Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "  mr: moreRooms.join(','), bo: booths.join(','), ho: holding.join(',') };",
    "  mr: moreRooms.join(','), bo: booths.join(','), ho: holding.join(','),\n"
    "  nt: notes.slice(0, 600) };   // v55 (Howard, 28 Oct): the note too - it was the one answer a DM's Continue booking lost")

p = by["Build Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "  const notes = input('notes', 'Note', txtIn('notes_in', '', { multiline: true }), { optional: true });   // v24: shown, no tick box\n",
    "  const _ntEl = txtIn('notes_in', '', { multiline: true }), _nt = String(pre.nt || '').trim().slice(0, 600);   // v55: the note saved from an earlier try\n"
    "  if (_nt) _ntEl.initial_value = _nt;\n"
    "  const notes = input('notes', 'Note', _ntEl, { optional: true });   // v24: shown, no tick box\n")

OLD = "const again = (R) => { const v = JSON.stringify((R && R.again) || {}); return v.length <= 1900 ? v : '{}'; };"
NEW = ("const again = (R) => { const g = (R && R.again) || {}; const v = JSON.stringify(g); if (v.length <= 1900) return v;   // v55: too long for the button -\n"
       "  const w = JSON.stringify(Object.assign({}, g, { nt: undefined })); return w.length <= 1900 ? w : '{}'; };   // the note left off first, the rest kept")
for nm in ["Question DM", "Result DM", "Series DM"]:
    p = by[nm]["parameters"]
    p["jsCode"] = sub(p["jsCode"], OLD, NEW)

wf["name"] = "Jessie — Slack Interactions — v55 (note kept)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v55.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
