#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v39.json - "Jessie — Slack Interactions", v39 (No booth / engineer / arranger again), 22 Oct.

QA (22 Oct 12:43, Howard on mobile): a Vocal booth picked could not be taken off again. Slack's desktop app gives an optional
dropdown a "Clear selection" line; the phone app does not - so since v26 (which dropped the "No …" options because desktop
showed both) an optional booth / engineer / arranger, once picked, could not be emptied on a phone. The optional dropdowns get
their "No …" choice back, last in the list: Book (Vocal booth when not required, Engineer when an arranger also counts, Arranger
unless it is the only role) and Change (Vocal booth, Engineer when optional, Arranger). Every reader already treats "none" as empty.
Built on workflows/imported/slack-interactions-v38-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v38-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v39.json")
wf = json.load(open(SRC))
NO = lambda w: "{ text: { type: 'plain_text', text: 'No " + w + "' }, value: 'none' }"
REPS = [
    ("const opts = list.slice(0, 100).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n }));   // v26: no \"No booth\" - empty is no booth",
     "const opts = list.slice(0, 99).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n })).concat(BX.need ? [] : [" + NO("booth") + "]);   // v39: \"No booth\" back - a phone shows no \"Clear selection\""),
    ("options: engOrder.slice(0, 100).map(popt) };   // v26: no \"No engineer\"",
     "options: engOrder.slice(0, 99).map(popt).concat(RR.either ? [NONE_E] : []) };   // v39: \"No engineer\" back when optional (phones cannot clear)"),
    ("options: arrs.slice(0, 100).map(popt) };   // v26: no \"No arranger\"",
     "options: arrs.slice(0, 99).map(popt).concat((RR.known && RR.arr && !RR.eng) ? [] : [NONE_A]) };   // v39: \"No arranger\" back unless required"),
    ("placeholder: pt('No booth'), options: bo }, bi ? { initial_option: bi } : {}) }); }",
     "placeholder: pt('No booth'), options: bo.concat([" + NO("booth") + "]) }, bi ? { initial_option: bi } : {}) }); }   // v39: \"No booth\" back"),
    ("sel('det_engineer_pick', engs, V.en, opt ? 'No engineer' : 'Select an engineer')",
     "sel('det_engineer_pick', opt ? engs.concat([" + NO("engineer") + "]) : engs, V.en, opt ? 'No engineer' : 'Select an engineer')"),
    ("sel('det_arranger_pick', arrs, V.ar, 'No arranger')",
     "sel('det_arranger_pick', arrs.concat([" + NO("arranger") + "]), V.ar, 'No arranger')"),
]
hits = {i: 0 for i in range(len(REPS))}
for n in wf["nodes"]:
    js = n["parameters"].get("jsCode")
    if not js:
        continue
    for i, (a, b) in enumerate(REPS):
        c = js.count(a)
        if c:
            js = js.replace(a, b)
            hits[i] += c
    n["parameters"]["jsCode"] = js
assert all(hits.values()), hits
print("replacements:", hits)
wf["name"] = "Jessie — Slack Interactions — v39 (No booth / engineer / arranger again)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
