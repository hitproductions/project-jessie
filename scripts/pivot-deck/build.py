#!/usr/bin/env python3
"""Builds the Slack-app pivot deck and the Block Kit files it shows.

  python3 scripts/pivot-deck/build.py

Writes docs/design/blockkit/<id>.json (one per screen; paste into app.slack.com/block-kit-builder - Modal Preview for
modals, Message Preview for messages) and docs/design/slack-app-pivot-deck.html (self-contained; opens in any browser).
The deck renders each screen from the same JSON it writes to blockkit/.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import before  # noqa: E402
import screens  # noqa: E402

out_dir = os.path.join(ROOT, "docs", "design", "blockkit")
os.makedirs(out_dir, exist_ok=True)

embedded = {}
for sid, (kind, payload) in screens.S.items():
    with open(os.path.join(out_dir, sid + ".json"), "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    embedded[sid] = {"kind": kind, "json": payload}

safe = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
tpl = open(os.path.join(HERE, "template.html")).read()
html = tpl.replace("/*SCREENS*/", safe(embedded)).replace("/*BEFORE*/", safe(before.B))

used = set()
import re  # noqa: E402
for m in re.finditer(r'data-screen="([^"]+)"', tpl):
    used.add(m.group(1))
missing = used - set(screens.S)
chats = set(re.findall(r'data-chat="([^"]+)"', tpl)) - set(before.B)
if missing or chats:
    sys.exit("missing screens: %s; missing chats: %s" % (sorted(missing), sorted(chats)))

deck = os.path.join(ROOT, "docs", "design", "slack-app-pivot-deck.html")
with open(deck, "w") as f:
    f.write(html)
print("%d screens -> %s; deck -> %s (%d KB); unused screens: %s"
      % (len(embedded), os.path.relpath(out_dir, ROOT), os.path.relpath(deck, ROOT), len(html) // 1024,
         sorted(set(screens.S) - used)))
