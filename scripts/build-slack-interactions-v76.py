#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v76.json - Jessie — Slack Interactions — v76 (calendar link), 9 Nov.

Howard, 9 Nov: "Check your booking in GCalendar [insert GCalendar event link]" on the booking confirmation. With Book Session v129's
html_link, the Booked card (the form's last screen and the DM) ends with a link line, "Check your booking in Google Calendar". It is
part of the card's section, so Cancel and Change - which write a fresh card over it - take it off (a cancelled or replaced event's
link would lead nowhere). The message's plain text (notifications, what Jessie reads back) and the engineer / arranger notices stay
as before. No link (an older Book Session, anything not a Google Calendar link) -> the card as before.
Built on workflows/imported/slack-interactions-v75-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v75-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:120])
    return js.replace(a, b)


def f(js):
    js = sub(js, "// v23: the length note is a small line under the card, not part of it\n",
             "// v76 (Howard, 9 Nov): the event's Google Calendar link under the card (blocks only - the plain text stays as it was)\n"
             "const _gl = String(r.html_link || '');\n"
             "const cardL = card + (/^https:\\/\\/(?:www\\.)?google\\.com\\/calendar\\/event\\?eid=[A-Za-z0-9_-]+$/.test(_gl) ? '\\n\\n<' + _gl + '|Check your booking in Google Calendar>' : '');\n"
             "// v23: the length note is a small line under the card, not part of it\n")
    js = sub(js, "  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card } }].concat(durNote",
             "  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: cardL } }].concat(durNote")
    js = sub(js, "const blocks = [{ type: 'section', block_id: 'bk_' + (bk.id || 'new'), text: { type: 'mrkdwn', text } }]",
             "const blocks = [{ type: 'section', block_id: 'bk_' + (bk.id || 'new'), text: { type: 'mrkdwn', text: cardL } }]")
    return js


by["After Book"]["parameters"]["jsCode"] = f(by["After Book"]["parameters"]["jsCode"])
wf["name"] = "Jessie — Slack Interactions — v76 (calendar link)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v76.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
