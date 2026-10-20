#!/usr/bin/env python3
"""Builds workflows/reminders-v2.json - "Jessie — Reminders", v2 (all to Howard in QA), 20 Oct.

  Howard (20 Oct): during testing EVERY reminder goes to him, the QA roster on ALLOW included. ALL_TO_DEV = true sends each
  one to DEV_REDIRECT, still marked "Test: this reminder is for X". Not a new launch switch: DEV_REDIRECT '' at launch sends
  every reminder to its real person whatever ALL_TO_DEV says (flip-launch-switches already does that).
Built on workflows/imported/reminders-v1-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "reminders-v1-imported.json")
OUT = os.path.join(ROOT, "workflows", "reminders-v2.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Build Reminders"]["parameters"]["jsCode"]
a = "const DEV_REDIRECT = 'U08V3CKDGJF';\n"
assert js.count(a) == 1
js = js.replace(a, a + "// v2 (Howard, 20 Oct): during QA every reminder goes to DEV_REDIRECT, ALLOW included (inert once DEV_REDIRECT is '')\nconst ALL_TO_DEV = true;\n")
b = "  const to = DEV_REDIRECT && ALLOW.indexOf(id) === -1 ? DEV_REDIRECT : id;"
assert js.count(b) == 1
js = js.replace(b, "  const to = DEV_REDIRECT && (ALL_TO_DEV || ALLOW.indexOf(id) === -1) ? DEV_REDIRECT : id;")
by["Build Reminders"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Reminders — v2 (all to Howard in QA)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
