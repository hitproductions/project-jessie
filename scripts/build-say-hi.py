#!/usr/bin/env python3
"""Builds workflows/say-hi-v1.json - Jessie — Say Hi — v1, 6 Nov.

Howard, 6 Nov: "i want to roll out jessie to ms. letty, but i want to make it easier for her to find the app on slack because on mobile you
can't really access all apps easily. is there a way we can trigger jessie to message her the default, hi, i'm jessie! with buttons".
A new workflow, run by hand only (Manual Trigger - no webhook, no schedule, never needs to be published): Jessie DMs everyone in the
`Who` node's list the same greeting main's Menu Check sends ("Hi, I’m Jessie!" + Book a room / My bookings). Posting to a person's user
id opens the DM with the app, as Jessie — Reminders does, so Jessie then sits in their DM list on a phone. The buttons are the menu's own
(open_book / my_bookings, value "menu"), handled by Slack Interactions like any other. For the next roll-out (Audio Post, Music), edit the
list in `Who` and run it again; `Report` says who got it and who did not.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}   # the one Reminders / main post with

WHO = r"""// Who Jessie says hi to - one line each: the Slack member id (profile -> ⋯ -> Copy member ID), then a name for the report.
// Edit this list and run the workflow (Execute workflow) - each person gets one message per run.
const WHO = [
  ['U026JML76', 'Letty'],
];
// The greeting main sends (Menu Check, main v275+): "Hi, I’m Jessie!" + Book a room / My bookings.
const blocks = [
  { type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } },
  { type: 'actions', elements: [
    { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] }
];
const seen = new Set(), out = [];
for (const [id0, name] of WHO) {
  const id = String(id0 || '').trim();
  if (!/^[UW][A-Z0-9]{6,}$/.test(id)) throw new Error('Not a Slack member id: "' + id + '" (' + name + ')');
  if (seen.has(id)) continue;
  seen.add(id);
  out.push({ json: { channel: id, name: String(name || id), text: 'Hi, I’m Jessie!', blocks } });
}
if (!out.length) throw new Error('The list in Who is empty');
return out;
"""

REPORT = r"""// One line per person: sent, or why Slack refused (e.g. user_not_found, not_allowed_token_type).
const who = $('Who').all();
const lines = $input.all().map((r, i) => {
  const j = r.json || {}, p = (who[i] || {}).json || {};
  const ok = j.ok === true;
  return { json: { name: p.name, id: p.channel, sent: ok, dm: ok ? j.channel : '', error: ok ? '' : String(j.error || (j.message) || 'no answer') } };
});
return lines;
"""

def node(name, typ, ver, pos, params, **extra):
    return dict({"parameters": params, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "jessie-say-hi/" + name)), "name": name,
                 "type": typ, "typeVersion": ver, "position": pos}, **extra)

nodes = [
    node("Run by hand", "n8n-nodes-base.manualTrigger", 1, [0, 0], {}),
    node("Who", "n8n-nodes-base.code", 2, [220, 0], {"jsCode": WHO}),
    node("Send Hi", "n8n-nodes-base.httpRequest", 4.2, [440, 0], {
        "method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
        "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}", "options": {}},
        credentials=CRED, onError="continueRegularOutput"),
    node("Report", "n8n-nodes-base.code", 2, [660, 0], {"jsCode": REPORT}),
    node("Note", "n8n-nodes-base.stickyNote", 1, [160, -260], {
        "content": "## Jessie — Say Hi\nRun by hand (Execute workflow). Jessie DMs everyone listed in **Who** her greeting with Book a room / "
                   "My bookings, so she shows up in their Slack DMs (easier to find on a phone).\n\nEdit the list in **Who**, run once, "
                   "read **Report**. Each run sends again - take people off the list once they have it. No need to publish.",
        "height": 220, "width": 440}),
]
connections = {
    "Run by hand": {"main": [[{"node": "Who", "type": "main", "index": 0}]]},
    "Who": {"main": [[{"node": "Send Hi", "type": "main", "index": 0}]]},
    "Send Hi": {"main": [[{"node": "Report", "type": "main", "index": 0}]]},
}
wf = {"name": "Jessie — Say Hi — v1", "nodes": nodes, "pinData": {}, "connections": connections, "active": False,
      "settings": {"executionOrder": "v1"}, "tags": []}
out = os.path.join(ROOT, "workflows", "say-hi-v1.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(nodes), "nodes")
