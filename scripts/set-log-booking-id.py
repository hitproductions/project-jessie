#!/usr/bin/env python3
"""Puts Jessie — Log Booking's workflow id into Book Session's "Log Booking" node, once Log Booking has been imported (n8n gives
a new workflow its id on import - it is in the URL, /workflow/<id>).
Usage: scripts/set-log-booking-id.py <id> [workflows/book-session-vN.json]   (default: the newest Book Session build)
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
if len(sys.argv) > 2:
    path = sys.argv[2]
else:
    files = glob.glob(os.path.join(ROOT, "workflows", "book-session-v*.json"))
    path = max(files, key=lambda p: int(re.search(r"-v(\d+)\.json$", p).group(1)))
wf = json.load(open(path))
hit = [n for n in wf["nodes"] if n["name"] == "Log Booking"]
if not hit:
    sys.exit("no Log Booking node in " + path)
hit[0]["parameters"]["workflowId"]["value"] = wid
with open(path, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("Log Booking ->", wid, "in", os.path.relpath(path, ROOT))
