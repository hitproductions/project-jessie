#!/usr/bin/env python3
"""Builds the slice-1 click-through prototype and its Block Kit files.

  python3 scripts/slice1-proto/build.py

Writes docs/design/blockkit/slice1/<id>.json (paste into app.slack.com/block-kit-builder: Modal Preview for forms,
Message Preview for messages) and docs/design/slack-app-slice1-prototype.html (self-contained; opens in any browser).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from flows import FLOWS  # noqa: E402
from screens import S  # noqa: E402

out = os.path.join(ROOT, "docs", "design", "blockkit", "slice1")
os.makedirs(out, exist_ok=True)
emb = {}
for sid, (kind, payload) in S.items():
    with open(os.path.join(out, sid + ".json"), "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    emb[sid] = {"kind": kind, "json": payload}

# every screen a flow names must exist, and every "go" button must be on that state's screen
problems = []
for fl in FLOWS:
    for i, st in enumerate(fl["states"]):
        ids = [v for w, v in st["dm"] if w == "j"] + ([st["modal"]] if st["modal"] else [])
        for sid in ids:
            if sid not in S:
                problems.append("%s[%d]: no screen %s" % (fl["id"], i, sid))
        text = json.dumps([S[x][1] for x in ids if x in S])
        for a, nxt in st["go"].items():
            if not a.startswith("__") and '"action_id": "%s"' % a not in text:
                problems.append("%s[%d]: button %s not on screen" % (fl["id"], i, a))
            if nxt >= len(fl["states"]):
                problems.append("%s[%d]: goes to missing state %d" % (fl["id"], i, nxt))
        if "auto" in st and st["auto"] >= len(fl["states"]):
            problems.append("%s[%d]: auto to missing state" % (fl["id"], i))
if problems:
    sys.exit("\n".join(problems))

safe = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
html = open(os.path.join(HERE, "template.html")).read().replace("/*SCREENS*/", safe(emb)).replace("/*FLOWS*/", safe(FLOWS))
dest = os.path.join(ROOT, "docs", "design", "slack-app-slice1-prototype.html")
with open(dest, "w") as f:
    f.write(html)
used = {v for fl in FLOWS for st in fl["states"] for w, v in st["dm"] if w == "j"} | {st["modal"] for fl in FLOWS for st in fl["states"] if st["modal"]}
print("%d screens, %d flows -> %s (%d KB); unused screens: %s" % (len(S), len(FLOWS), os.path.relpath(dest, ROOT), len(html) // 1024, sorted(set(S) - used)))
