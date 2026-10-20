#!/usr/bin/env python3
"""Builds workflows/room-check-v2.json - "Jessie — Room Check", v2 (changes too), 20 Oct.

  1. Move Booking (v34) calls it too, with kind "move". A change creates the new event and then deletes the old one, so a room
     that turns the new time down must NOT have its event deleted (that would leave no booking at all): the person who changed
     it is DM'd - the booking is on the calendar at the new time but the room has not accepted it - with Change (the booking,
     to pick another room or time) and My bookings. Nothing is deleted; the Log row says so. A new booking (kind "" or "book" -
     Book Session's call, which sends no kind) works as in v1: deleted, DM'd, logged.
  2. "Book a room" on a declined Post Processing booking: its title is "POST PROCESSING - <PROJECT> / <who>" (Slack
     Interactions v33) - the project and the name are read from it (v1 took "POST PROCESSING - <PROJECT>" as the project).
Built on workflows/imported/room-check-v1-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "room-check-v1-imported.json")
OUT = os.path.join(ROOT, "workflows", "room-check-v2.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
T = "When Executed by Another Workflow"

vals = by[T]["parameters"]["workflowInputs"]["values"]
assert [v["name"] for v in vals] == ["event_id", "title", "rooms", "requester", "start_iso", "end_iso", "all_day", "session_type"], vals
vals.append({"name": "kind"})

# Decide -> Delete? -> (a new booking) Delete Declined -> Build DM | (a change) Build DM
ans = json.loads(json.dumps(by["Answered?"]))
x, y = by["Delete Declined"]["position"]
ans.update({"id": str(uuid.uuid4()), "name": "Delete?", "position": [x - 112, y + 200]})
ans["parameters"]["conditions"]["conditions"] = [{"id": str(uuid.uuid4()),
    "leftValue": "={{ String($('" + T + "').first().json.kind || '').trim().toLowerCase() !== 'move' }}",
    "rightValue": True, "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]
wf["nodes"].append(ans)
by["Delete?"] = ans
assert C["Decide"]["main"][0][0]["node"] == "Delete Declined"
C["Decide"]["main"][0] = [{"node": "Delete?", "type": "main", "index": 0}]
C["Delete?"] = {"main": [[{"node": "Delete Declined", "type": "main", "index": 0}], [{"node": "Build DM", "type": "main", "index": 0}]]}

DM = r"""// DM (Room Check v1; v2): what the person reads, in Slack Interactions' card style. A new booking: the event was deleted -
// Book a room (the form filled in again) and My bookings. A change (kind "move", Move Booking v34): nothing is deleted - the
// booking is on the calendar at the new time but the room has not accepted it - Change (the booking) and My bookings.
const T = $('When Executed by Another Workflow').first().json || {};
const D = $('Decide').first().json || {};
const isMove = String(T.kind || '').trim().toLowerCase() === 'move';
const del = $input.first().json || {};
const removed = !isMove && !(del && (del.error || del.errorMessage));
const iso = String(T.start_iso || ''), iso2 = String(T.end_iso || '');
const ymd = iso.slice(0, 10), hm = s => (String(s).match(/T(\d{2}:\d{2})/) || [])[1] || '';
const t12 = v => { if (!v) return ''; let [h, m] = v.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const x = /^\d{4}-\d{2}-\d{2}$/.test(ymd) ? new Date(ymd + 'T12:00:00Z') : null;
const allDay = String(T.all_day) === 'true';
const when = (x ? DL[x.getUTCDay()] + ', ' + ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear() : '') + (allDay ? ' · All day' : (hm(iso) ? ' · ' + t12(hm(iso)) + ' – ' + t12(hm(iso2)) : ''));
const rm = D.declined.join(' and ');
const title = String(D.title || '');
const head = isMove
  ? '⚠️ *' + rm + ' turned down this change* - its calendar shows it is taken then. The booking is on the calendar at the new time, but the room hasn’t accepted it - change it to another room or time.'
  : '❌ *' + rm + ' turned this booking down* - its calendar shows it is taken then. '
    + (removed ? 'It was taken off the calendar, so nothing is booked.' : 'Nothing is booked, but the event could not be removed - delete it from the calendar.');
let actions;
if (isMove) {
  const bk = { id: String(D.event_id || ''), d: ymd, s: allDay ? '' : hm(iso), e: allDay ? '' : hm(iso2), r: String(T.rooms || ''), t: title.slice(0, 150), st: String(T.session_type || '') };
  actions = [{ type: 'button', style: 'primary', action_id: 'bk_change', value: JSON.stringify(bk), text: { type: 'plain_text', text: 'Change' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }];
} else {
  const st = String(T.session_type || '').trim();
  const again = { d: ymd, s: allDay ? '' : hm(iso), e: allDay ? '' : hm(iso2), p: st || (/^M\d+/i.test(String(T.rooms || '').trim()) ? '__booth' : '') };
  const pp = title.match(/^\s*POST PROCESSING\s+-\s+(?:(.+?)\s+\/\s+)?(.+?)\s*$/i);   // v2: "POST PROCESSING - <PROJECT> / <who>"
  if (pp) { again.p = again.p || 'Post Processing'; if (pp[1]) again.pj = pp[1].trim(); again.fn = pp[2].trim(); }
  else { const first = title.split(' / ')[0].trim();
    if (/^(localization|qc)\b/i.test(st)) again.cd = first; else if (title.indexOf(' / ') !== -1) again.pj = first; }
  Object.keys(again).forEach(k => { if (!again[k]) delete again[k]; });
  actions = [{ type: 'button', style: 'primary', action_id: 'open_book', value: JSON.stringify(again).slice(0, 1900), text: { type: 'plain_text', text: 'Book a room' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }];
}
const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: head + '\n\n*' + title + '*\n' + when } }, { type: 'actions', elements: actions }];
return [{ json: { channel: D.requester, text: rm + (isMove ? ' turned down the change to ' + title + '.' : ' turned down ' + title + ' - nothing is booked.'), blocks, removed, isMove } }];"""
by["Build DM"]["parameters"]["jsCode"] = DM

js = by["Declined Row"]["parameters"]["jsCode"]
a = "  'Note': D.declined.join(', ') + ' declined' + (M.removed ? '; removed' : '; NOT removed - delete it by hand') } }];"
assert js.count(a) == 1, js.count(a)
by["Declined Row"]["parameters"]["jsCode"] = js.replace(a, "  'Note': D.declined.join(', ') + ' declined' + (M.isMove ? ' a change; the booking kept at the new time (not removed)' : M.removed ? '; removed' : '; NOT removed - delete it by hand') } }];   // v2")
by["Note"]["parameters"]["content"] = by["Note"]["parameters"]["content"] + "\n\nv2: Move Booking calls it too (kind \"move\") - a declined change is reported, never deleted."

wf["name"] = "Jessie — Room Check — v2 (changes too)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
