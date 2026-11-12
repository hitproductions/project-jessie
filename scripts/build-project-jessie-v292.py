#!/usr/bin/env python3
"""Builds workflows/project-jessie-v292.json - Project Jessie — v292 (no typed cancel), 12 Nov.

12 Nov: a booking was cancelled by mistake. The requester typed "cancel my booking on nov 12 2028" to remove a test booking (on
1 Nov 2028). Jessie answered "I couldn't find a booking of yours on Sun, Nov 12 from today on." - no year, and today is 12 Nov
2026 - and within the minute the same day's real Likha booking was cancelled with a button (Booking Log 11:54). Howard: "don't
allow cancelling using free text. only through the cancel buttons. and apply the other fixes you found".

- Change Reply: a typed cancel ("cancel / delete / remove ...") gets no booking card and no Cancel button - one line pointing to
  My bookings (where each booking has its own Cancel, with Slack's confirm box) and the My bookings button. A typed change is
  unchanged (it opens the Change form; nothing is cancelled from it).
- Prepared Cancel: the old chat path (a typed yes to a "Confirm to cancel." card) never cancels - it answers with the same line.
  Nothing has written such a card since v271, so this closes a dormant path rather than a used one.
- Dates carry the year when it is not this year: "Sun, Nov 12, 2028" (Change Reply's cards, Slack's confirm box, "I couldn't
  find a booking of yours on ...").
- The search for a typed change reaches the typed date: it ran from today to 61 days ahead, so a booking further out (the test
  on 1 Nov 2028) could never be found. Now to the later of that and the day after the furthest date typed.
Built on workflows/project-jessie-v291.json (== live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "project-jessie-v291.json")))
by = {n["name"]: n for n in wf["nodes"]}
NOCANCEL = "To cancel a booking, open *My bookings* and tap *Cancel* on it."


def rep(node, old, new, count=1):
    p = by[node]["parameters"]
    assert p["jsCode"].count(old) == count, (node, old[:60], p["jsCode"].count(old))
    p["jsCode"] = p["jsCode"].replace(old, new)


# Change Offer: today kept for Change Reply; the window reaches the furthest date typed
rep("Change Offer",
    "    co.timeMax = new Date(Date.parse(today + 'T12:00:00Z') + 61 * 86400000).toISOString().slice(0, 10) + 'T00:00:00+08:00';",
    "    co.today = today;   // v292: Change Reply shows the year on dates not in this year\n"
    "    // v292 (12 Nov): to 61 days ahead, or the day after the furthest date typed - a booking in 2028 was out of reach\n"
    "    const _far = co.fDates.concat(co.n && co.n.d ? [co.n.d] : []).filter(x => /^\\d{4}-\\d{2}-\\d{2}$/.test(x)).sort().pop() || '';\n"
    "    const _hi = [new Date(Date.parse(today + 'T12:00:00Z') + 61 * 86400000).toISOString().slice(0, 10),\n"
    "      _far ? new Date(Date.parse(_far + 'T12:00:00Z') + 86400000).toISOString().slice(0, 10) : ''].sort().pop();\n"
    "    co.timeMax = _hi + 'T00:00:00+08:00';")

# Change Reply: the year; no cancel from typed text
rep("Change Reply",
    "function dayShort(d) { const x = new Date(d + 'T12:00:00Z'); return _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); }",
    "const _Y = String((((($('Change Offer').first() || {}).json || {}).changeOffer || {}).today) || new Date(Date.now() + 8 * 3600000).toISOString()).slice(0, 4);\n"
    "function dayShort(d) { const x = new Date(d + 'T12:00:00Z'); return _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate()\n"
    "  + (String(d).slice(0, 4) !== _Y ? ', ' + String(d).slice(0, 4) : ''); }   // v292 (12 Nov): the year when it is not this year")
rep("Change Reply",
    "if (!ok && !fromRecent) blocks.push(",
    "if (co.kind === 'cancel') {   // v292 (Howard, 12 Nov): no cancelling from typed text - only a booking's own Cancel button\n"
    "  list = [];\n"
    "  blocks.push({ type: 'section', text: md(" + json.dumps(NOCANCEL) + ") },\n"
    "    { type: 'actions', elements: [{ type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] });\n"
    "}\n"
    "else if (!ok && !fromRecent) blocks.push(")

# Prepared Cancel: a typed yes to an old chat cancel card never cancels
rep("Prepared Cancel",
    "return [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d, _alreadyDone: done }) }];",
    "if (d && d.use) { d = { use: false, reason: 'v292: no typed cancel' }; done = " + json.dumps(NOCANCEL) + "; }   // v292 (Howard, 12 Nov)\n"
    "return [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d, _alreadyDone: done }) }];")

wf["name"] = "Project Jessie — v292 (no typed cancel)"
out = os.path.join(ROOT, "workflows", "project-jessie-v292.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
