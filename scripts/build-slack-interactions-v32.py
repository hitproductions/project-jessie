#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v32.json - "Jessie — Slack Interactions", v32 (steadier wait estimates), 20 Oct.

Found 20 Oct 20:36: one booking hung 2 min 12 s on an Airtable call (Book Session v116 / v117 remove that call) and became the
whole "book" estimate - the first five runs kept the slowest, so the next bookings would have said "Usually under 3 minutes".
  1. Next Estimate starts from the measured fallback (book / change 30 s, a series 30 s a date, rooms 10 s, checking 5 s a
     date) and tracks the 90th percentile from the first run - one slow run moves it up once and fades (each faster run takes
     it down a little). The loading views are unchanged (fewer than 5 runs: never under the fallback).
  2. The time is taken as soon as the answer is on screen: Timing Sample sits above the other steps after each Show node, so
     with n8n's top-to-bottom order it runs first - before the DMs and notices, which no longer count.
Built on workflows/imported/slack-interactions-v31-imported.json (the live download). Before using it, delete the "book" row
in Jessie Timings (148.6 s, from that run) so the estimate starts fresh.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v31-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v32.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Next Estimate", [
    ("// Next Estimate (v31): the scenario's estimate after this run. The first 5 runs: the slowest so far. Then the time 9 in 10 runs\n"
     "// finish within, tracked - a slower run moves it up by 0.9 of a step, a faster one down by 0.1 (a step = 30% of it).",
     "// Next Estimate (v31; v32): the scenario's estimate after this run - the time 9 in 10 runs finish within, tracked from the\n"
     "// measured fallback: a slower run moves it up by 0.9 of a step, a faster one down by 0.1 (a step = 30% of it). v31 kept the\n"
     "// slowest of the first 5 runs, so one 2-minute hang (20 Oct 20:36) became the estimate."),
    ("let q = cur ? Number(cur.seconds) || 0 : 0;",
     "const FB = { rooms: 10, 'rooms-series': 5, book: 30, check: 5, series: 30, change: 30 };   // the same fallbacks as the loading views\n"
     "let q = cur ? Number(cur.seconds) || 0 : 0;\nif (!(q > 0)) q = FB[S.scenario] || 30;"),
    ("if (k < 5) q = Math.max(q, x);\nelse { const step = Math.max(0.5, q * 0.3); q = Math.max(1, q + (x > q ? 0.9 : -0.1) * step); }",
     "{ const step = Math.max(0.5, q * 0.3); q = Math.max(1, q + (x > q ? 0.9 : -0.1) * step); }"),
])

ends = ["Show Step 2", "Show Result", "Show Series Step", "Show Series Result", "Show Change Result"]
ys = [by[c["node"]]["position"][1] for e in ends for c in C[e]["main"][0] if c["node"] != "Timing Sample"]
ys += [by[e]["position"][1] for e in ends]
top = min(ys) - 400
by["Timing Sample"]["position"] = [by["Timing Sample"]["position"][0], top]
by["Read Timing"]["position"] = [by["Read Timing"]["position"][0], top]
by["Next Estimate"]["position"] = [by["Next Estimate"]["position"][0], top]
by["Save Timing"]["position"] = [by["Save Timing"]["position"][0], top]
patch("Timing Sample", [("// Timing Sample (v31, round 12 #1): how long this run took, from the click (Read Request) to the answer on screen - one sample\n"
                         "// for its scenario in Jessie Timings. It runs after the answer is shown, so nobody waits for it; anything odd -> no sample.",
                         "// Timing Sample (v31, round 12 #1): how long this run took, from the click (Read Request) to the answer on screen - one sample\n"
                         "// for its scenario in Jessie Timings. It runs after the answer is shown, so nobody waits for it; anything odd -> no sample.\n"
                         "// v32: placed above the other steps after each Show node, so it runs first (n8n runs branches top to bottom) - the DMs\n"
                         "// and notices after the answer are not counted.")])

wf["name"] = "Jessie — Slack Interactions — v32 (steadier wait estimates)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes; Timing Sample at y", top)
