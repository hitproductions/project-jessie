#!/usr/bin/env python3
"""Builds workflows/project-jessie-v298.json - Project Jessie — v298 (M booth all day), 20 Nov.

Howard (20 Nov, before the commercial roll-out): an M booth asked for by typing with no times ("book M3 tomorrow", "an m booth
for friday", "M4 next week mon to fri") opens the form as **All day** - the M booths are held for whole days. Times typed
("M3 tomorrow 2-4pm") are kept as before. Form Offer only. Built on workflows/project-jessie-v297.json (== live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "project-jessie-v297.json")))
p = [n for n in wf["nodes"] if n["name"] == "Form Offer"][0]["parameters"]
OLD = ("if (P.p === '__booth' || P.p === 'Event') { P.ad = 1; delete P.s; delete P.e; } else { P.s = '00:00'; P.e = '23:59'; delete P.ad; }\n"
       "    }\n")
assert p["jsCode"].count(OLD) == 1
p["jsCode"] = p["jsCode"].replace(OLD, OLD +
    "    if (P.p === '__booth' && !P.s && !P.e && !P.ad) P.ad = 1;   // v298 (Howard, 20 Nov): an M booth with no times typed is All day\n")
wf["name"] = "Project Jessie — v298 (M booth all day)"
out = os.path.join(ROOT, "workflows", "project-jessie-v298.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
