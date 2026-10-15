#!/usr/bin/env python3
"""main v273 (v272 fixed): v272 put the message's date / time / room on Book a room under an answer (open_book value
{d, s, e, r}). Form Offer took any Jessie message whose Book a room carried such a value for its own "Here's what I have
so far" offer, and read the next message as more details for it (Slack 15 Oct 16:57):
  "is studio 8 free tomorrow 3-5?" -> answer;  "what do I have this week?" -> "Here's what I have so far: Studio 8 · 3-5 PM"
  then "what's in studio 4 on thursday?" -> "Here's what I have so far: Studio 4 · Thursday, October 21 · 3-5 PM".
Fixed:
  1. Form Offer: only its own message counts as an offer (first section "Here's what I have so far:" / "Let's book it with
     the form.").
  2. Form Offer: a question after an offer is never more details - it goes on to My bookings / the agent.
  3. Menu Check: likewise, only an offer counts as "waiting for an answer" ("thanks" after an answer -> the menu).
  4. Change Offer read "have" as a title word (Slack 16:58: "cancel a booking i have next friday" -> 'couldn't find a
     booking of yours called "have"'; "cancel a booking for next friday" worked). More everyday words are not title words.
Built on workflows/imported/project-jessie-v272-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v272-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v273.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


OFFER_RE = r"/^(?:Here’s what I have so far:|Let’s book it with the form\.)/"

# ---- 1 + 2: Form Offer
patch("Form Offer", [
    ("""  let prev = null;
  try { for (const b of (lastBot && lastBot.blocks) || []) for (const e of b.elements || [])
    if (e.action_id === 'open_book' && /^\\{/.test(String(e.value || ''))) prev = JSON.parse(e.value); } catch (e) { prev = null; }""",
     """  // v273: only Form Offer's own message is an offer - since v272 Book a room under an answer carries a value too
  const lastFirst = String(((((lastBot && lastBot.blocks) || [])[0] || {}).text || {}).text || '');
  const lastIsOffer = """ + OFFER_RE + """.test(lastFirst);
  let prev = null;
  try { if (lastIsOffer) for (const b of (lastBot && lastBot.blocks) || []) for (const e of b.elements || [])
    if (e.action_id === 'open_book' && /^\\{/.test(String(e.value || ''))) prev = JSON.parse(e.value); } catch (e) { prev = null; }"""),
    ("""  else if (!intent && !prev) skip('not a booking request');""",
     """  else if (!intent && !prev) skip('not a booking request');
  // v273: a question after an offer is not more details ("what do I have this week?", "what's in studio 4 on thursday?")
  else if (!intent && (/\\?/.test(t) || /^\\s*(?:what|whats|what’s|what's|when|where|who|whos|whose|which|why|how|is|are|am|can|could|do|does|did|will|would|should|may|any|have|has)\\b/i.test(t))) skip('a question after an offer');"""),
])

# ---- 3: Menu Check
patch("Menu Check", [
    ("""      || (/\\?\\s*$/.test(lastText) && !opener) || lastButtons.some(x => x === 'open_book:{');""",
     """      || (/\\?\\s*$/.test(lastText) && !opener)
      || (lastButtons.some(x => x === 'open_book:{') && """ + OFFER_RE + """.test(String((((last && last.blocks) || [])[0] || {}).text && last.blocks[0].text.text || '')));   // v273: only an offer waits"""),
])

# ---- 4: Change Offer - everyday words are not title words
patch("Change Offer", [
    ("""      + 'oct october nov november dec december am pm nn noon instead hours hour mins minutes until till by with no not just also again actually').split(' '));""",
     """      + 'oct october nov november dec december am pm nn noon instead hours hour mins minutes until till by with no not just also again actually '
      + 'have has had got get did does done book booked reserve reserved schedule scheduled upcoming coming planned set there here any all '   // v273
      + 'which what when where who was were are is been only last first other same thing something kindly naman yung yun mga lang pa-cancel pa-move pa-change pa-resched pa-book').split(' '));"""),
])

wf["name"] = "Project Jessie — v273 (v272 fixed)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
