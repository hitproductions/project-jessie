#!/usr/bin/env python3
"""Builds workflows/book-session-v114.json - "Jessie — Book Session", v114 (shorter length note), round 12 (20 Oct).

The note under a Booked card when a session runs longer or shorter than its type usually does (Airtable Session Types Min /
Max Duration - what a session usually runs, never a limit):
  was  "That is a bit longer than Music Vocal Recording sessions usually run (1–2 hours is typical)."
  now  "That's a bit longer than a usual Music Vocal Recording session (1–2 hours)."
Same for "shorter", and the ranges as before ("up to 2 hours", "at least 4 hours", "1 hour 30 minutes – 3 hours"). Code-written
(Check Conflicts' durationNote), not the model. The chat card's "Heads up: … usually runs (…)" (Render Summary) is left as is -
the chat no longer books (main v271).
Built on workflows/imported/book-session-v113-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v113-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v114.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Check Conflicts", [
    ("""    durationNote = 'That is a bit longer than ' + kind + ' sessions usually run ('
                 + typical + ' is typical).';""",
     """    durationNote = 'That’s a bit longer than a usual ' + kind + ' session (' + typical + ').';   // v114 (round 12): shorter"""),
    ("""    durationNote = 'That is a bit shorter than ' + kind + ' sessions usually run ('
                 + typical + ' is typical).';""",
     """    durationNote = 'That’s a bit shorter than a usual ' + kind + ' session (' + typical + ').';"""),
])

wf["name"] = "Jessie — Book Session — v114 (shorter length note)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
