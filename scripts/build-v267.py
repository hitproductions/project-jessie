#!/usr/bin/env python3
"""main v267 (menu after a booking reply): Slack 15 Oct 11:11 on v266 - "lhkjf;kj" right after a booking reply (the Book a
room button) went to the agent ("That message didn't come through clearly. What do you need?"). After an offer every message
is a possible detail, so Menu Check leaves it to Form Offer, which found nothing new, and Change Offer found no cancel /
change. Now: nothing new after an offer, not a question and not a cancel / change -> the menu ("Anytime! Anything else?"
for thanks). Change Offer decides; Change Offer? (no) -> Late Menu? -> Send Late Menu, else Early Room Plan as before.
Turn Log Row logs it as "menu". Built on workflows/imported/project-jessie-v266-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v266-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v267.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
assert "Late Menu?" not in by


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70])
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Change Offer", [
    ("item.changeOffer = co;\nreturn [{ json: item }];",
     """// v267 (live 11:11): nothing new after a booking reply, not a question, not a cancel / change -> the menu, not the agent
try {
  const fo = item.formOffer || {};
  const tx = String((($('Slack Trigger').first().json || {}).text) || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim();
  const tl = tx.toLowerCase().replace(/[’']/g, '');
  const question = /\\?/.test(tx) || /^(?:what|when|where|who|whos|whose|which|why|how|is|are|am|can|could|do|does|did|will|would|should|may|any|have|has)\\b/.test(tl);
  if (!co.go && fo.why === 'nothing new after an offer' && !question && co.why === 'not a cancel or change') {
    const thanks = /^(?:thanks?|thank you|thank u|ty|tysm|salamat|thanks a lot|ok(?:ay)?|ok thanks|okay thanks|cool|great|nice|got it|noted|sige)[.! ]*$/i.test(tl);
    co.menu = true;
    co.menuBlocks = [{ type: 'section', text: { type: 'mrkdwn', text: thanks ? 'Anytime! Anything else?' : 'I can help with bookings - what would you like to do?' } },
      { type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
        { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] }];
  }
} catch (e) {}
item.changeOffer = co;
return [{ json: item }];"""),
])
cx, cy = by["Change Offer?"]["position"]
wf["nodes"].extend([
    {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ ($json.changeOffer || {}).menu === true }}", "rightValue": True,
                                                   "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                   "combinator": "and"}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [cx + 200, cy + 260], "id": str(uuid.uuid4()), "name": "Late Menu?"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $json.changeOffer.channel, text: $json.changeOffer.menuBlocks[0].text.text, blocks: $json.changeOffer.menuBlocks }) }}",
                    "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [cx + 400, cy + 360], "id": str(uuid.uuid4()),
     "name": "Send Late Menu", "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
])
C = wf["connections"]
assert [c["node"] for c in C["Change Offer?"]["main"][1]] == ["Early Room Plan"]
C["Change Offer?"]["main"][1] = [{"node": "Late Menu?", "type": "main", "index": 0}]
C["Late Menu?"] = {"main": [[{"node": "Send Late Menu", "type": "main", "index": 0}], [{"node": "Early Room Plan", "type": "main", "index": 0}]]}
C["Send Late Menu"] = {"main": [[{"node": "Turn Log Row", "type": "main", "index": 0}, {"node": "Clear Ack", "type": "main", "index": 0}]]}
patch("Turn Log Row", [
    ("  let cr = null; try { cr = $('Send Change Reply').first().json || null; } catch (e) {}   // v265\n",
     "  let cr = null; try { cr = $('Send Change Reply').first().json || null; } catch (e) {}   // v265\n"
     "  try { if (!mn) mn = $('Send Late Menu').first().json || null; } catch (e) {}   // v267\n"),
])
wf["name"] = "Project Jessie — v267 (menu after a booking reply)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
