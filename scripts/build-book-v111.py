#!/usr/bin/env python3
"""Builds workflows/book-session-v111.json - "Jessie — Book Session", v111 (lengths in hours): the note on a booking whose
length is outside what the session type usually runs said minutes - "(240-600 minutes is typical)". It says hours now, as
the prepare summary's heads-up already did: "(4–10 hours is typical)", "1 hour 30 minutes", "up to 3 hours". Round 6 of the
Slack-test notes (15 Oct). Nothing else changes.
Built on workflows/imported/book-session-v110-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v110-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v111.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Check Conflicts"][0]
js = n["parameters"]["jsCode"]
a = """  const typical = hasMin && hasMax ? (minD + '-' + maxD + ' minutes')
                : hasMax ? ('up to ' + maxD + ' minutes')
                : ('at least ' + minD + ' minutes');"""
b = """  // v111 (round 6, 15 Oct): hours, not minutes - "(4–10 hours is typical)"
  const _hm = m => { const h = Math.floor(m / 60), r = m % 60;
    return (h ? h + ' hour' + (h === 1 ? '' : 's') : '') + (h && r ? ' ' : '') + (r ? r + ' minutes' : ''); };
  const typical = hasMin && hasMax ? (minD % 60 === 0 && maxD % 60 === 0 ? (minD / 60) + '–' + (maxD / 60) + ' hours' : _hm(minD) + ' – ' + _hm(maxD))
                : hasMax ? ('up to ' + _hm(maxD))
                : ('at least ' + _hm(minD));"""
assert js.count(a) == 1
n["parameters"]["jsCode"] = js.replace(a, b)
wf["name"] = "Jessie — Book Session — v111 (lengths in hours)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
