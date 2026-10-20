#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v36.json - "Jessie — Slack Interactions", v36 (shortcut buttons), 21 Oct.

  1. Shortcut buttons at the end of results (slice 2, Howard 20 Oct): the Booked DM ends with *Book another* / *My bookings*
     (a block of its own, block_id "nav", under the booking's Change / Cancel); a booked series' DM says *Book another* (was
     Book a room); the Changed DM ends with *Book a room* / *My bookings*; a cancel that leaves a one-booking message with no
     way on (a Booked DM from before v36, a chat reply) adds *Book a room* / *My bookings* under ❌ Cancelled. My bookings
     lists (their own Previous / Next) and reminders (their own My bookings) are left as they are. The buttons are the
     menu's own (open_book "menu", my_bookings "menu"), so main reads the message as a menu, never as an offer (gotcha 44).
  2. A booking's own message is never used as the "source" of the next one: *Book another* on a Booked DM used to put
     "Your booking details: … ⏳ Booking…" over that card while the new booking ran (and, unbooked with the window gone,
     left it there - the card and its Change / Cancel lost). Mark Source / Mark Source Series leave a message that holds a
     booking row (bk_<id>) alone; the result comes as its own DM as always.
  3. Post Processing's "Who is it for?" (a staff member): the notice says "<booker> booked this for you." (was "booked you as
     the engineer").
Built on workflows/imported/slack-interactions-v35-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v35-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v36.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def sub(node, a, b, count=1):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == count, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


NAV = ("// v36: shortcut buttons at the end of a result - the menu's own buttons (value \"menu\": main reads them as the menu)\n"
       "const NAV = book => ({ type: 'actions', block_id: 'nav', elements: [\n"
       "  { type: 'button', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: book } },\n"
       "  { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] });\n")

# 1a. Booked (single)
sub("After Book", "// After Book: CREATED -> the form says Booked", NAV + "// After Book: CREATED -> the form says Booked")
sub("After Book", "  .concat(bk.id ? [bkButtons(bk)] : []);", "  .concat(bk.id ? [bkButtons(bk), NAV('Book another')] : []);   // v36")
# 1b. Booked (series)
sub("After Book Series", "  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },",
    "  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: booked.length ? 'Book another' : 'Book a room' } },   // v36")
# 1c. Changed
sub("After Move", "// After Move (v11):", NAV + "// After Move (v11):")
sub("After Move", "dmBlocks: [{ type: 'section', block_id: 'bk_' + nb.id, text: { type: 'mrkdwn', text: card } }, bkButtons(nb)] } }];",
    "dmBlocks: [{ type: 'section', block_id: 'bk_' + nb.id, text: { type: 'mrkdwn', text: card } }, bkButtons(nb), NAV('Book a room')] } }];   // v36")
# 1d. Cancelled
sub("After Cancel", "// After Cancel (v11):", NAV + "// After Cancel (v11):")
sub("After Cancel", "  blocks = dropLead(blocks);\n} else {",
    "  blocks = dropLead(blocks);\n"
    "  // v36: a one-booking message with no way on gets Book a room / My bookings (lists and reminders keep their own)\n"
    "  if (blocks.filter(x => /^bk_/.test(String(x.block_id || ''))).length === 1 && !blocks.some(x => x.block_id === 'my_nav' || x.block_id === 'nav'\n"
    "      || (x.elements || []).some(e => e.action_id === 'open_book' || e.action_id === 'my_bookings'))) blocks.push(NAV('Book a room'));\n"
    "} else {")
# 2. a booking's message is never the source
SRC_A = "  if (!m) return { ok: false };\n"
SRC_B = ("  if (!m) return { ok: false };\n"
         "  if ((m.blocks || []).some(b => /^bk_/.test(String(b.block_id || '')))) return { ok: false };   // v36: a booking's own message (Book another) is left as it is\n")
for nm in ("Mark Source", "Mark Source Series"):
    sub(nm, SRC_A, SRC_B)
# 3. Post Processing's notice
sub("Booked Notices", "return notices([{ id: R.engineerId, role: 'engineer', verb: 'booked', name: whoIs(data, R.engineerId) },",
    "return notices([Object.assign({ id: R.engineerId, role: 'engineer', verb: 'booked', name: whoIs(data, R.engineerId) }, R.s.kind === 'post' ? { line: 'booked this for you' } : {}),   // v36: Post Processing's Who is it for?")

wf["name"] = "Jessie — Slack Interactions — v36 (shortcut buttons)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
