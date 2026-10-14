#!/usr/bin/env python3
"""Book Session v109 (declined event removed): PENDING 44, decided 13 Oct - when a room turns a booking down, Jessie deletes
her own event, so the calendar never keeps a booking the room refused. Built on the v108 download
(workflows/imported/book-session-v108-imported.json). Verify's ROOM_DECLINED used to go straight out (Logged? -> Return
Booked) with the event left on the calendar; now Logged? (not CREATED) -> Declined? -> Delete Declined -> Return Declined.
Everything else is v108. Both the chat (Book Direct) and the Slack-app form read the answer.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v108-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v109.json")
CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "6D1r3kaq6KaFdL0a", "name": "Google Calendar account"}}

wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
assert "Declined?" not in by
x, y = by["Return Booked"]["position"]

RETURN_DECLINED = r"""// Return Declined (Book Session v109, PENDING 44): the room turned the booking down, and Jessie's own event was deleted so
// the calendar never keeps a booking the room refused. If the delete failed, say so - the event is then still there.
const v = $('Verify').first().json || {};
const del = $input.first().json || {};
const removed = !(del && (del.error || del.errorMessage));
const rm = [].concat(v.declined || []).map(x => (String(x).match(/(Studio [0-9A-Z]|M[1-8]|Salin|Katha|Likha|Lobby)\b/) || [])[1] || String(x)).join(' and ');
return [{ json: { status: 'ROOM_DECLINED', event_id: v.event_id || '', declined: v.declined || [], removed,
  human: '❌ ' + (rm || 'The room') + ' turned this booking down - its own calendar shows it is taken then. '
    + (removed ? 'It was taken off the calendar, so nothing is booked.' : 'Nothing is booked, but the event could not be removed - delete it from the calendar.')
    + ' Want another time or studio?' } }];"""

new = [
    {"parameters": {"conditions": {"combinator": "and", "conditions": [
        {"id": str(uuid.uuid4()), "leftValue": "={{ $('Verify').first().json.status }}",
         "operator": {"name": "filter.operator.equals", "operation": "equals", "type": "string"}, "rightValue": "ROOM_DECLINED"}],
        "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 3}}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.3, "position": [x, y + 200], "id": str(uuid.uuid4()), "name": "Declined?"},
    {"parameters": {"method": "DELETE",
                    "url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events/{{ encodeURIComponent(String($('Verify').first().json.event_id || '')) }}",
                    "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 220, y + 200], "id": str(uuid.uuid4()),
     "name": "Delete Declined", "credentials": GCAL_CRED, "onError": "continueRegularOutput"},
    {"parameters": {"jsCode": RETURN_DECLINED}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x + 440, y + 200],
     "id": str(uuid.uuid4()), "name": "Return Declined"},
]
wf["nodes"].extend(new)
C = wf["connections"]
assert [c["node"] for c in C["Logged?"]["main"][1]] == ["Return Booked"]
C["Logged?"]["main"][1] = [{"node": "Declined?", "type": "main", "index": 0}]
C["Declined?"] = {"main": [[{"node": "Delete Declined", "type": "main", "index": 0}], [{"node": "Return Booked", "type": "main", "index": 0}]]}
C["Delete Declined"] = {"main": [[{"node": "Return Declined", "type": "main", "index": 0}]]}
wf["name"] = "Jessie — Book Session — v109 (declined event removed)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
