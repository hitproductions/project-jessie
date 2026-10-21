#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v40.json - Jessie — Slack Interactions v40 (summary on separate lines), 22 Oct.

Howard (22 Oct, phone): "for the date · time · session type summary, let's separate them with line breaks instead of dots so
it's clearer to look at. apply on similar instances" - the summary headers only (decided: booking rows in lists and cards keep
one line, so a week of bookings stays short).
  1. Step 2's header: "🗓️ *Friday, Oct 22, 2027*" / "*11:00 AM–3:00 PM*" / "*VO Recording*", each on its own line (a series:
     "*4 dates*" / the time / the type). Slack's bold does not cross a line break, so each line is bolded on its own.
  2. The DM's "Your booking details:" header (working, booked, not booked yet; one booking and a series): the room, the date
     and the time on their own lines. `when` itself keeps its " · " (After Book reads it back), only the drawing changes.
Built on workflows/imported/slack-interactions-v39-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v39-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v40.json")
wf = json.load(open(SRC))

REPS = [
    ("? '🗓️ *' + SER.dates.length + ' dates · ' + fmtT(s.t0) + '–' + fmtT(s.t1) + ' · ' + label + '*'",
     "? '🗓️ ' + [SER.dates.length + ' dates', fmtT(s.t0) + '–' + fmtT(s.t1), label].filter(Boolean).map(x => '*' + x + '*').join('\\n')   /* v40: one per line */"),
    (": '🗓️ *' + when + ' · ' + label + '*') }];",
     ": '🗓️ ' + String(when).split(' · ').concat([label]).filter(Boolean).map(x => '*' + x + '*').join('\\n')) }];   // v40: date / time / type, one per line"),
    ("text: 'Your booking details:\\n🗓️ *' + [r, when].filter(Boolean).join(' · ') + '*' } };",
     "text: 'Your booking details:\\n🗓️ ' + [r].concat(String(when || '').split(' · ')).filter(Boolean).map(x => '*' + x + '*').join('\\n') } };   // v40: room / date / time, one per line"),
]
hits = {i: 0 for i in range(len(REPS))}
for n in wf["nodes"]:
    js = n.get("parameters", {}).get("jsCode")
    if not js:
        continue
    for i, (a, b) in enumerate(REPS):
        c = js.count(a)
        if c:
            js = js.replace(a, b)
            hits[i] += c
    n["parameters"]["jsCode"] = js
assert hits == {0: 1, 1: 1, 2: 4}, hits
print("replacements:", hits)
wf["name"] = "Jessie — Slack Interactions — v40 (summary on separate lines)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
