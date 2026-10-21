#!/usr/bin/env python3
"""Builds workflows/project-jessie-v280.json - main "Project Jessie", v280 (summary on separate lines), 22 Oct.

Howard (22 Oct): the date · time · type summaries on separate lines instead of dots (Slack Interactions v40 does the forms).
Here: a typed booking request's "Your booking details so far:" - the room, the date and the time each on their own bold line,
then the session type, project, client and people each on their own line (were one " · " line each). The series pattern
("🔁 Every Monday · 4 times") stays one line.
Built on workflows/imported/project-jessie-v279-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v279-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v280.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def sub(node, a, b):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == 1, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


sub("Form Offer", ".concat(head ? ['🗓️ *' + head + '*'] : []).concat(pat ? ['🔁 ' + pat] : []).concat(more ? [more] : [])",
    ".concat(head ? ['🗓️ ' + head.split(' · ').map(x => '*' + x + '*').join('\\n')] : []).concat(pat ? ['🔁 ' + pat] : []).concat(more ? [more.split(' · ').join('\\n')] : [])   /* v280: one per line */")
wf["name"] = "Project Jessie — v280 (summary on separate lines)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
