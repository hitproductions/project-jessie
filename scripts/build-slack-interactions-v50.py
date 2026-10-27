#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v50.json - Jessie — Slack Interactions — v50 (no slash in typed titles), 27 Oct.

Howard's Slack test, 27 Oct ~18:02: Kristine typed the project "Backyard Live // Test Session", and the title came out
"BACKYARD LIVE // TEST SESSION / SONY MUSIC / AEG x BPV" - four parts. A title's parts are joined and split on " / "
(PROJECT / Client / initials), so a slash typed inside a part breaks every reader: one " / " in a project makes Change
read the project as the first half and the client as the rest, and Book Session's three-part checks skip it. Every typed
part of a title - project, client, project code, meeting title, "Who is it for?" - now has its slashes turned into " - "
("Backyard Live // Test Session" -> "Backyard Live - Test Session"), on Book a room (Read Step 2) and on Change (Read
Change, the one node that reads the Change form; the other Change nodes take its values). Titles already on the calendar
are left as they are. Built on workflows/imported/slack-interactions-v49-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v49-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}

NS = ("// v50 (27 Oct): a slash typed inside a title part becomes \" - \" - titles are split on \" / \" (PROJECT / Client / initials)\n"
      "const noSlash = x => String(x || '').replace(/\\s*\\/+\\s*/g, ' - ').trim().replace(/^-\\s*|\\s*-$/g, '').trim();\n")


def sub(js, a, b):
    assert js.count(a) == 1, a
    return js.replace(a, b)


# Book a room: every typed title part
js = by["Read Step 2"]["parameters"]["jsCode"]
a = "const project = String(val('project', 'project_in')).trim().replace(/^(project|proj)\\s+/i, '');"
js = sub(js, a, NS + "const project = noSlash(String(val('project', 'project_in')).trim().replace(/^(project|proj)\\s+/i, ''));")
js = sub(js, "const client = capWords(String(val('client', 'client_in')).trim());",
         "const client = capWords(noSlash(val('client', 'client_in')));")
js = sub(js, "const code = String(val('code', 'code_pick') || val('code', 'code_in')).replace(/^new:/, '').trim().toUpperCase();",
         "const code = noSlash(String(val('code', 'code_pick') || val('code', 'code_in')).replace(/^new:/, '')).toUpperCase();")
js = sub(js, "const forName = cap1(val('forname', 'forname_in'));", "const forName = cap1(noSlash(val('forname', 'forname_in')));")
js = sub(js, "const title = String(val('title', 'title_in')).trim();", "const title = noSlash(val('title', 'title_in'));")
by["Read Step 2"]["parameters"]["jsCode"] = js

# Change: the details typed on the Change form
js = by["Read Change"]["parameters"]["jsCode"]
js = sub(js, "  d.client = capWords(d.client);   // v19\n",
         "  d.client = capWords(d.client);   // v19\n"
         "  // v50 (27 Oct): a slash typed inside a title part becomes \" - \" - titles are split on \" / \"\n"
         "  ['project', 'client', 'code', 'title', 'forname'].forEach(k => { d[k] = String(d[k] || '').replace(/\\s*\\/+\\s*/g, ' - ').trim().replace(/^-\\s*|\\s*-$/g, '').trim(); });\n")
by["Read Change"]["parameters"]["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v50 (no slash in typed titles)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v50.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
