#!/usr/bin/env python3
"""Builds workflows/reminders-v3.json - "Jessie — Reminders", v3 (a reminder, Change / Cancel), 21 Oct.

Howard, 21 Oct, after the first day-before reminder arrived: angle it as a reminder with options to change or cancel - nothing to
confirm, a booking stays as it is by default.
  - The header: "🔔 *REMINDER: You have a booking tomorrow*" - "bookings" when there are more (and "… this week" on Mondays, with
    the week's dates under it).
  - Each booking as the Booked card does it: the title, then Date, Time, Room (and Holding room), with Change / Cancel under it
    (Cancel keeps Slack's "Cancel this booking?" - a cancel cannot be undone). A line between bookings when there are several.
  - No Still on / Keep button (Slack Interactions keeps its rm_keep route for reminders already sent), no "Still on?" line;
    My bookings only when there are more than 15 (Slack takes 50 blocks a message: 15 cards with their buttons and lines is 46).
  - The "Test: this reminder is for X" line at the bottom.
Built on workflows/imported/reminders-v2-imported.json (the live download). Only Build Reminders changes.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "reminders-v2-imported.json")
OUT = os.path.join(ROOT, "workflows", "reminders-v3.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Build Reminders"]["parameters"]["jsCode"]
a = js[js.index("  const blocks = [];\n"):js.index("return out;")]
b = r"""  const blocks = [], n = rows.length, one = n === 1;
  // v3 (Howard, 21 Oct): a reminder - the bookings as cards with Change / Cancel; nothing to confirm (a booking stays by default)
  blocks.push({ type: 'section', text: md(W.kind === 'daily'
    ? '🔔 *REMINDER: You have ' + (one ? 'a booking' : 'bookings') + ' tomorrow*'
    : '🔔 *REMINDER: You have ' + (one ? 'a booking' : 'bookings') + ' this week*\n' + dayShort(W.start) + ' – ' + dayShort(addDays(W.end, -1))) });
  rows.slice(0, 15).forEach((b, i) => {
    if (i > 0) blocks.push({ type: 'divider' });
    blocks.push({ type: 'section', block_id: 'bk_' + b.id, text: md(bkCard(b, '').replace(/^\n\n/, '')) });
    blocks.push(bkButtons(b));
  });
  if (n > 15) blocks.push({ type: 'context', elements: [md('And ' + (n - 15) + ' more – see *My bookings*.')] },
    { type: 'actions', block_id: 'rm_nav', elements: [{ type: 'button', action_id: 'my_bookings', value: 'menu', text: pt('My bookings') }] });
  if (to !== id) blocks.push({ type: 'context', elements: [md('_Test: this reminder is for ' + (nameOf(id) || id) + '._')] });
  out.push({ json: { channel: to, person: id, text: 'Reminder: you have ' + (one ? 'a booking' : n + ' bookings') + (W.kind === 'daily' ? ' tomorrow' : ' this week'), blocks } });
}
"""
js = js.replace(a, b)
assert js.count("const to = DEV_REDIRECT && (ALL_TO_DEV || ALLOW.indexOf(id) === -1) ? DEV_REDIRECT : id;") == 1
by["Build Reminders"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Reminders — v3 (a reminder, Change / Cancel)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
