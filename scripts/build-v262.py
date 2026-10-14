#!/usr/bin/env python3
"""main v262 (menu): a greeting, "menu" or "help" gets the Slack-app menu (Book a room · My bookings) instead of the
agent. Everything else goes on exactly as in v261. Slice 1 step A of the Slack-app pivot (docs/design/slack-app-v1-scope.md).

Built on workflows/imported/project-jessie-v261-imported.json (the live download). New nodes after Duplicate? (not a
duplicate): Menu Check -> Menu? -> Send Menu -> Turn Log Row + Clear Ack; otherwise All Rooms as before.
The buttons are handled by Jessie — Slack Interactions (v3).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v261-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v262.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}

wf = json.load(open(SRC))
nodes = wf["nodes"]
by = {n["name"]: n for n in nodes}
assert "Menu Check" not in by
dup = by["Duplicate?"]
x, y = dup["position"]

MENU_CHECK = r"""// Menu Check (main v262): a greeting, "menu" or "help" - the whole message, nothing else in it - gets the Slack-app
// menu (Book a room · My bookings) instead of the agent. Anything with more in it ("hi, book studio 7 tomorrow") goes on
// to the agent as before. The menu's buttons are handled by Jessie — Slack Interactions.
const raw = String(($('Slack Trigger').first().json || {}).text || '');
const t = raw.replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]+>/g, ' ').replace(/:[a-z0-9_+\-]+:/gi, ' ')
  .toLowerCase().replace(/[^a-z\s]/g, ' ').replace(/\s+/g, ' ').trim();
const FILL = new Set(['jessie', 'po', 'there', 'again', 'pls', 'please', 'naman', 'ulit']);
const phrase = t.split(' ').filter(w => w && !FILL.has(w)).join(' ');
const GREET = ['hi', 'hello', 'hey', 'heya', 'hiya', 'yo', 'sup', 'hola', 'good morning', 'good afternoon', 'good evening',
  'good day', 'morning', 'afternoon', 'evening', 'gm', 'menu', 'help', 'start', 'options', 'kumusta', 'musta', 'hoy', 'uy'];
const menu = raw.trim() !== '' && (phrase === '' || GREET.indexOf(phrase) !== -1 || /^(h+i+|he+y+|hel+o+)$/.test(phrase));
let first = '';
try { first = String((($('Get Booker').first().json || {}).fields || {}).Name || '').trim().split(/\s+/)[0]; } catch (e) {}
const blocks = [
  { type: 'section', text: { type: 'mrkdwn', text: 'Hi' + (first ? ' ' + first : '') + '! What would you like to do?' } },
  { type: 'actions', elements: [
    { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] },
  { type: 'context', elements: [{ type: 'mrkdwn', text: 'Or just type it, like _book studio 7 tomorrow 2-4pm_ or _is studio 8 free friday?_' }] }
];
return [{ json: { menu, phrase, blocks, channel: String(($('Slack Trigger').first().json || {}).channel || '') } }];"""

new_nodes = [
    {"parameters": {"jsCode": MENU_CHECK}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x + 200, y + 220],
     "id": str(uuid.uuid4()), "name": "Menu Check"},
    {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $json.menu }}", "rightValue": True,
                                                   "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                   "combinator": "and"}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [x + 400, y + 220], "id": str(uuid.uuid4()), "name": "Menu?"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $json.channel, text: 'What would you like to do?', blocks: $json.blocks }) }}",
                    "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 600, y + 120], "id": str(uuid.uuid4()),
     "name": "Send Menu", "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
]
nodes.extend(new_nodes)

C = wf["connections"]
outs = C["Duplicate?"]["main"]
assert [c["node"] for c in outs[1]] == ["All Rooms"], outs
outs[1] = [{"node": "Menu Check", "type": "main", "index": 0}]
C["Menu Check"] = {"main": [[{"node": "Menu?", "type": "main", "index": 0}]]}
C["Menu?"] = {"main": [[{"node": "Send Menu", "type": "main", "index": 0}], [{"node": "All Rooms", "type": "main", "index": 0}]]}
C["Send Menu"] = {"main": [[{"node": "Turn Log Row", "type": "main", "index": 0}, {"node": "Clear Ack", "type": "main", "index": 0}]]}

wf["name"] = "Project Jessie — v262 (menu)"
for k in ("activeVersion", "versionId", "id", "meta", "shared", "tags", "triggerCount", "updatedAt", "createdAt", "isArchived"):
    pass  # keep the full export shape (ground rule); n8n ignores what it does not need on import
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
