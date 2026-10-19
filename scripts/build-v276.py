#!/usr/bin/env python3
"""main v276 (the year on the offer): round 9 note 1 (19 Oct) - a typed booking's offer says the date with its year
("Your booking details so far: 🗓️ Studio 7 · Wednesday, October 20, 2027 · 4:00 PM – 6:00 PM"), and a series' "until" too.
Built on workflows/imported/project-jessie-v275-imported.json (the live download). With Slack Interactions v26.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v275-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v276.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Form Offer"][0]
js = n["parameters"]["jsCode"]
a = "toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })"
assert js.count(a) == 2, js.count(a)
n["parameters"]["jsCode"] = js.replace(a, "toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })   /* v276: the year */")
wf["name"] = "Project Jessie — v276 (the year on the offer)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
