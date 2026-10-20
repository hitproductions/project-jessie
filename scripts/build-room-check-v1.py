#!/usr/bin/env python3
"""Builds workflows/room-check-v1.json - "Jessie — Room Check", v1 (new, 20 Oct): the rooms' answer, read after "Booked.".

Book Session v117 shows "Booked." as soon as the event is created (Howard, 20 Oct: every booking goes through Jessie; the
Envoy tablets mirror onto KDC Bookings, so the check before booking sees them) and calls this without waiting. It reads the
event back at ~2 / 6 / 16 s until every room resource has answered. A room that declined (two bookings in the same seconds,
or a booking made outside Jessie): the event is deleted (PENDING 44, decided 13 Oct), the person who booked is DM'd with Book a
room (the form filled in again) and My bookings, and a ROOM_DECLINED row goes to the Jessie Log sheet. Accepted, still silent
after 16 s, or the event gone (cancelled meanwhile): nothing happens.
Inputs (text): event_id, title, rooms, requester (Slack id), start_iso, end_iso, all_day, session_type.
Nodes copied from Book Session v116 (Wait for Room, Reread Event, Room Answered?, Delete Declined), Slack Interactions v31
(DM Booked) and Log Booking v2 (Log to Sheet), so the credentials and shapes are the live ones.
Import into a NEW workflow (it has no id yet), publish it, then run scripts/set-room-check-id.py <its id> so Book Session v117
calls it; then import Book Session v117.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BOOK = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "book-session-v116.json")))["nodes"]}
SI = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v31-imported.json")))["nodes"]}
LOG = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "log-booking-v2-imported.json")))["nodes"]}
OUT = os.path.join(ROOT, "workflows", "room-check-v1.json")
T = "When Executed by Another Workflow"
CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"


def node(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    return n


def copy(src, name, newname, pos, params=None):
    n = json.loads(json.dumps(src[name]))
    n["id"] = str(uuid.uuid4())
    n["name"] = newname
    n["position"] = pos
    if "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    if params is not None:
        n["parameters"] = params
    return n


INPUTS = ["event_id", "title", "rooms", "requester", "start_iso", "end_iso", "all_day", "session_type"]
nodes = [node(T, "n8n-nodes-base.executeWorkflowTrigger", 1.1, {"workflowInputs": {"values": [{"name": k} for k in INPUTS]}}, [0, 0])]
REREAD_URL = ("=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events/"
              "{{ encodeURIComponent(String($('" + T + "').first().json.event_id || '')) }}")
answered = json.loads(json.dumps(BOOK["Room Answered?"]["parameters"]))
x = 224
for i, secs in enumerate([2, 4, 10], start=1):
    sfx = "" if i == 1 else " " + str(i)
    wnode = copy(BOOK, "Wait for Room", "Wait" + sfx, [x, 0], {"amount": secs})
    rnode = copy(BOOK, "Reread Event", "Reread" + sfx, [x + 224, 0], {"url": REREAD_URL, "authentication": "predefinedCredentialType",
                                                                      "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}})
    nodes += [wnode, rnode]
    if i < 3:
        a = copy(BOOK, "Room Answered?", "Answered" + sfx + "?", [x + 448, 0], json.loads(json.dumps(answered)))
        for c in a["parameters"]["conditions"]["conditions"]:
            c["id"] = str(uuid.uuid4())
        nodes.append(a)
    x += 672

DECIDE = r"""// Decide (Room Check v1): the event as read back. A room resource that declined -> delete the event and tell the person who
// booked. Accepted, still silent, or the event gone (cancelled meanwhile, or an error reading it) -> nothing to do.
const T = $('When Executed by Another Workflow').first().json || {};
const ev = $input.first().json || {};
if (!ev.id || ev.error || ev.status === 'cancelled') return [];
const declined = (ev.attendees || []).filter(a => a.resource && a.responseStatus === 'declined').map(a => String(a.displayName || a.email || ''));
if (!declined.length) return [];
const rooms = declined.map(x => (x.match(/(Studio [0-9A-Z]|M[1-8]|Salin|Katha|Likha|Lobby)\b/) || [])[1] || x);
return [{ json: { event_id: ev.id, declined: rooms, title: String(T.title || ev.summary || ''), requester: String(T.requester || '') } }];"""

DM = r"""// DM (Room Check v1): what the person who booked reads - in Slack Interactions' card style - with Book a room (the form filled in
// again: date, times, booking type) and My bookings. The "Booked." card they already have stays; its Change / Cancel find
// nothing now and say so.
const T = $('When Executed by Another Workflow').first().json || {};
const D = $('Decide').first().json || {};
const del = $input.first().json || {};
const removed = !(del && (del.error || del.errorMessage));
const iso = String(T.start_iso || ''), iso2 = String(T.end_iso || '');
const ymd = iso.slice(0, 10), hm = s => (String(s).match(/T(\d{2}:\d{2})/) || [])[1] || '';
const t12 = v => { if (!v) return ''; let [h, m] = v.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const x = /^\d{4}-\d{2}-\d{2}$/.test(ymd) ? new Date(ymd + 'T12:00:00Z') : null;
const allDay = String(T.all_day) === 'true';
const when = (x ? DL[x.getUTCDay()] + ', ' + ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear() : '') + (allDay ? ' · All day' : (hm(iso) ? ' · ' + t12(hm(iso)) + ' – ' + t12(hm(iso2)) : ''));
const rm = D.declined.join(' and ');
const head = '❌ *' + rm + ' turned this booking down* - its calendar shows it is taken then. '
  + (removed ? 'It was taken off the calendar, so nothing is booked.' : 'Nothing is booked, but the event could not be removed - delete it from the calendar.');
const st = String(T.session_type || '').trim(), first = String(D.title || '').split(' / ')[0].trim();
const again = { d: ymd, s: allDay ? '' : hm(iso), e: allDay ? '' : hm(iso2), p: st || (/^M\d+/i.test(String(T.rooms || '').trim()) ? '__booth' : '') };
if (/^(localization|qc)\b/i.test(st)) again.cd = first; else if (D.title && String(D.title).indexOf(' / ') !== -1) again.pj = first;
Object.keys(again).forEach(k => { if (!again[k]) delete again[k]; });
const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: head + '\n\n*' + D.title + '*\n' + when } },
  { type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: 'open_book', value: JSON.stringify(again).slice(0, 1900), text: { type: 'plain_text', text: 'Book a room' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] }];
return [{ json: { channel: D.requester, text: rm + ' turned down ' + D.title + ' - nothing is booked.', blocks, removed } }];"""

LOGROW = r"""// Declined Row (Room Check v1): a ROOM_DECLINED row for the Jessie Log sheet, beside the BOOKED row Log Booking wrote.
const T = $('When Executed by Another Workflow').first().json || {};
const D = $('Decide').first().json || {}, M = $('Build DM').first().json || {};
const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  .formatToParts(new Date()).reduce((o, x) => (o[x.type] = x.value, o), {});
return [{ json: { 'Timestamp': p.year + '-' + p.month + '-' + p.day + ' ' + p.hour + ':' + p.minute, 'Action': 'ROOM_DECLINED', 'Title': D.title || '',
  'Room(s)': String(T.rooms || ''), 'Date': String(T.start_iso || '').slice(0, 10), 'Event ID': D.event_id || '',
  'Note': D.declined.join(', ') + ' declined' + (M.removed ? '; removed' : '; NOT removed - delete it by hand') } }];"""

y = 260
nodes.append(node("Decide", "n8n-nodes-base.code", 2, {"jsCode": DECIDE}, [x, y]))   # an error here stops the run - never a delete on a guess
nodes.append(copy(BOOK, "Delete Declined", "Delete Declined", [x + 224, y],
                  {"method": "DELETE", "url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events/"
                   "{{ encodeURIComponent(String($('Decide').first().json.event_id || '')) }}",
                   "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}}))
nodes.append(node("Build DM", "n8n-nodes-base.code", 2, {"jsCode": DM}, [x + 448, y], {"onError": "continueRegularOutput"}))
dmp = json.loads(json.dumps(SI["DM Booked"]["parameters"]))
dmp["jsonBody"] = "={{ JSON.stringify({ channel: $('Build DM').first().json.channel, text: $('Build DM').first().json.text, blocks: $('Build DM').first().json.blocks }) }}"
nodes.append(copy(SI, "DM Booked", "Send DM", [x + 672, y], dmp))
nodes.append(node("Declined Row", "n8n-nodes-base.code", 2, {"jsCode": LOGROW}, [x + 896, y], {"onError": "continueRegularOutput"}))
nodes.append(copy(LOG, "Log to Sheet", "Log Declined", [x + 1120, y]))
nodes.append(node("Note", "n8n-nodes-base.stickyNote", 1, {"content": (
    "## Jessie — Room Check\nThe rooms' answer, read after \"Booked.\" (Book Session v117+ calls it without waiting). A room that "
    "declined: the event is deleted, the person who booked is DM'd (Book a room / My bookings), and a ROOM_DECLINED row goes to the "
    "Log sheet. Accepted or silent: nothing happens."), "width": 460}, [0, -260]))

L = lambda a: [{"node": a, "type": "main", "index": 0}]
C = {T: {"main": [L("Wait")]}, "Wait": {"main": [L("Reread")]}, "Reread": {"main": [L("Answered?")]},
     "Answered?": {"main": [L("Decide"), L("Wait 2")]}, "Wait 2": {"main": [L("Reread 2")]}, "Reread 2": {"main": [L("Answered 2?")]},
     "Answered 2?": {"main": [L("Decide"), L("Wait 3")]}, "Wait 3": {"main": [L("Reread 3")]}, "Reread 3": {"main": [L("Decide")]},
     "Decide": {"main": [L("Delete Declined")]}, "Delete Declined": {"main": [L("Build DM")]}, "Build DM": {"main": [L("Send DM")]},
     "Send DM": {"main": [L("Declined Row")]}, "Declined Row": {"main": [L("Log Declined")]}}
wf = {"name": "Jessie — Room Check — v1 (the rooms' answer after Booked)", "nodes": nodes, "connections": C, "pinData": {},
      "active": False, "settings": {"executionOrder": "v1"}, "meta": {}, "tags": []}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
