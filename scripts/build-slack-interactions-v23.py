#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v23.json - "Jessie — Slack Interactions", v23 (round 6: small notes): the note Book
Session adds when a session runs longer or shorter than usual ("That is a bit shorter than Localization Dubbing sessions
usually run (4–10 hours is typical).") sat at the end of the Booked card in full-size text. It is now a small context line
under the card (block bkn_<id>), on the form's result and in the DM, above Change / Cancel; a change or a cancel that goes
through removes it (it was about the old length). With Book Session v111 (the note in hours).
Built on workflows/imported/slack-interactions-v22-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v22-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v23.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:90], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("After Book", [
    ("""const view = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Done' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card } }] };
const text = card + (r.duration_note ? '\\n' + r.duration_note : '');""",
     """// v23: the length note is a small line under the card, not part of it
const durNote = String(r.duration_note || '').trim();
const view = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Done' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card } }].concat(durNote ? [{ type: 'context', elements: [{ type: 'mrkdwn', text: durNote }] }] : []) };
const text = card;"""),
    ("""const blocks = [{ type: 'section', block_id: 'bk_' + (bk.id || 'new'), text: { type: 'mrkdwn', text } }].concat(bk.id ? [bkButtons(bk)] : []);""",
     """const blocks = [{ type: 'section', block_id: 'bk_' + (bk.id || 'new'), text: { type: 'mrkdwn', text } }]
  .concat(durNote ? [{ type: 'context', block_id: 'bkn_' + (bk.id || 'new'), elements: [{ type: 'mrkdwn', text: durNote }] }] : [])   // v23
  .concat(bk.id ? [bkButtons(bk)] : []);"""),
])
patch("After Cancel", [
    ("""  blocks = blocks.filter(x => x.block_id !== 'bka_' + b.id);""",
     """  blocks = blocks.filter(x => x.block_id !== 'bka_' + b.id && x.block_id !== 'bkn_' + b.id);   // v23: its length note goes too"""),
])
patch("Fix Message", [
    ("""const j = blocks.findIndex(x => x.block_id === 'bka_' + old);""",
     """{ const k = blocks.findIndex(x => x.block_id === 'bkn_' + old); if (k !== -1) blocks.splice(k, 1); }   // v23: the old length note
const j = blocks.findIndex(x => x.block_id === 'bka_' + old);"""),
])
wf["name"] = "Jessie — Slack Interactions — v23 (round 6: small notes)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
