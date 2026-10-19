#!/usr/bin/env python3
"""main v275 (greeting + fewer words), round 8 (19 Oct, docs/design/round-8-plan.md):
  7. "Hi, I'm Jessie!" with the two buttons - for hi, "what can you do", and "reset" (answered by code now; the AI wrote
     "Hi, I'm Jessie. Ask me about room availability, …"). No "Or just type it, like …" line. "Anytime!" for thanks;
     "I can only help with bookings." for anything else.
  8. A typed booking's offer: "Your booking details so far:" (was "Here's what I have so far:"), no line under the buttons;
     older offers still count as offers. Typed change / cancel: "Here's the booking:", "Your change so far:". "Use *Book a
     room* or *My bookings* below." for a booking question; "Still booking that series - I'll post here when it's done."
Built on workflows/imported/project-jessie-v274-imported.json (the live download). With Slack Interactions v25.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v274-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v275.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) >= 1, (node, a[:90])
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


OFFER_RE_OLD = "/^(?:Here’s what I have so far:|Let’s book it with the form\\.)/"
OFFER_RE_NEW = "/^(?:Your booking details so far:|Here’s what I have so far:|Let’s book it with the form\\.)/"   # v275 (older offers too)

patch("Menu Check", [
    ("if (!menu && ABOUT.test(phrase)) { menu = true; why = 'about'; }   // v271",
     "if (!menu && ABOUT.test(phrase)) { menu = true; why = 'about'; }   // v271\n"
     "if (!menu && /^reset$/.test(phrase)) { menu = true; why = 'reset'; }   // v275: answered here, not by the AI (Gate Context still resets)"),
    (OFFER_RE_OLD, OFFER_RE_NEW),
    ("""const head = why === 'about' ? 'I book studios and rooms at Hit Productions - tap *Book a room*, or *My bookings* to see, change or cancel yours. You can also ask me what’s free or booked, and about the rooms.' : why === 'thanks' ? 'Anytime! Anything else?' : why === 'not a booking or a question' ? 'I can help with bookings - what would you like to do?'
  : 'Hi' + (first ? ' ' + first : '') + '! What would you like to do?';""",
     """// v275 (round 8): short - the two buttons say the rest
const head = why === 'thanks' ? 'Anytime!' : why === 'not a booking or a question' ? 'I can only help with bookings.' : 'Hi, I’m Jessie!';"""),
    (""",
  { type: 'context', elements: [{ type: 'mrkdwn', text: 'Or just type it, like _"book studio 7 tomorrow 2-4pm"_ or _"is studio 8 free friday?"_' }] }
];""", """
];   // v275: no "Or just type it, like …" line"""),
])
patch("Change Offer", [("text: thanks ? 'Anytime! Anything else?' : 'I can help with bookings - what would you like to do?' }",
                        "text: thanks ? 'Anytime!' : 'I can only help with bookings.' }   /* v275 */")])
patch("Form Offer", [
    (OFFER_RE_OLD, OFFER_RE_NEW),
    ("const lines = any ? ['Here’s what I have so far:']", "const lines = any ? ['Your booking details so far:']   /* v275 */"),
    ("""
        { type: 'context', elements: [{ type: 'mrkdwn', text: any ? 'Opens the form with these filled in - only free rooms are offered.' : 'Pick the date, time and room in the form.' }] }
      ];""", """
      ];   // v275: no line under the buttons"""),
])
patch("Change Reply", [("""md(!one ? 'Which one?' : co.kind === 'cancel' ? 'Here’s the booking – press *Cancel* to cancel it.'
    : hasNew ? 'Here’s your proposed change – press *Change* to check the new time.' : 'Here’s the booking – press *Change* to pick the new time.')""",
                        """md(!one ? 'Which one?' : hasNew && co.kind !== 'cancel' ? 'Your change so far:' : 'Here’s the booking:')   /* v275: the buttons say the rest */""")])
patch("Build Reply", [("text = 'Tap *Book a room* below - the form asks for everything it needs. To change or cancel, open *My bookings*.';",
                       "text = 'Use *Book a room* or *My bookings* below.';   // v275")])
by["Series Busy Reply"]["parameters"] = json.loads(json.dumps(by["Series Busy Reply"]["parameters"], ensure_ascii=False).replace(
    "Still booking that series - I’ll post what was booked here when it’s done.", "Still booking that series - I’ll post here when it’s done."))
assert "I’ll post here when it’s done" in json.dumps(by["Series Busy Reply"]["parameters"], ensure_ascii=False)

wf["name"] = "Project Jessie — v275 (greeting + fewer words)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
