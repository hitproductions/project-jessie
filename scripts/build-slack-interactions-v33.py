#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v33.json - "Jessie — Slack Interactions", v33 (M booth "for" name), round 13 (20 Oct).

With main v277: "book m4 for japs" -> the M booth's "Who is it for?" starts on Japs (pre.fn from Form Offer); without one, the
booker's first name as before. "Book a room" again (a DM when the window is gone, a decline from Room Check) carries the name.
Also (Howard, 20 Oct): Dylan Diaz is "Dilan Diaz" in Bookers - the Post Processing fallbacks (an old form; a Change form whose
booking's initials match no one) find him by either spelling. The dropdowns read names from Bookers and need nothing.
Built on workflows/imported/slack-interactions-v32-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v32-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v33.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Build Step 2", [("blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(mine.name || '').split(/\\s+/)[0])), notes);",
                        "blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(pre.fn || '').trim().slice(0, 40) || String(mine.name || '').split(/\\s+/)[0])), notes);   // v33: \"for <name>\" typed (main v277)")])
patch("Read Step 2", [("  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId };",
                       "  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId, fn: s.kind === 'booth' ? forName : '' };   // v33: the M booth's name")])
# Howard, 20 Oct: Dylan Diaz is "Dilan Diaz" in Bookers now - the two fallbacks that looked him up by name take either spelling
patch("Read Step 2", [
    ("const pb = (data.bookers || []).map(b => b.fields || {}).find(f => String(f.Name || '').trim() === 'Dylan Diaz');",
     "const pb = (data.bookers || []).map(b => b.fields || {}).find(f => /^d[iy]lan\\s+diaz$/i.test(String(f.Name || '').trim()));   // v33: Dilan (was Dylan)"),
    ("'Dylan Diaz isn’t in Bookers yet - ask for the booker to be added.'", "'Dilan Diaz isn’t in Bookers yet - ask for the booker to be added.'")])
for n in ["Build Change", "Read Change", "To Move", "After Move", "Note Toggle"]:
    patch(n, [("const dyl = st.find(x => x.name === 'Dylan Diaz');", "const dyl = st.find(x => /^d[iy]lan\\s+diaz$/i.test(x.name));   // v33: Dilan (was Dylan)")])
wf["name"] = "Jessie — Slack Interactions — v33 (M booth for name)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
