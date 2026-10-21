#!/usr/bin/env python3
"""Puts Jessie — Request Messages' workflow id into every node that calls it, once it has been imported (n8n gives a new
workflow its id on import - it is in the URL, /workflow/<id>): the newest builds of Open Consent Request (Post Messages),
Finalize Consent (Done Messages, Fail Messages), Consent Sweep (Expire Messages) and Slack Interactions (End Messages).
Usage: scripts/set-request-messages-id.py <id>
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if len(sys.argv) < 2 or not re.fullmatch(r"[A-Za-z0-9]{10,24}", sys.argv[1]):
    sys.exit(__doc__)
wid = sys.argv[1]
for stem, names in (("open-consent-request", ["Post Messages"]), ("finalize-consent", ["Done Messages", "Fail Messages"]),
                    ("consent-sweep", ["Expire Messages"]), ("slack-interactions", ["End Messages"])):
    files = glob.glob(os.path.join(ROOT, "workflows", stem + "-v*.json"))
    path = max(files, key=lambda p: int(re.search(r"-v(\d+)\.json$", p).group(1)))
    wf = json.load(open(path))
    hit = [n for n in wf["nodes"] if n["name"] in names]
    if len(hit) != len(names):
        sys.exit("missing " + ", ".join(names) + " in " + path)
    for n in hit:
        n["parameters"]["workflowId"]["value"] = wid
    with open(path, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Request Messages ->", wid, "in", os.path.relpath(path, ROOT), "(" + ", ".join(names) + ")")
