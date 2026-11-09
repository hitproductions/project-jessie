#!/usr/bin/env python3
"""Builds workflows/book-session-v129.json - Jessie — Book Session — v129 (calendar link), 9 Nov.

Howard, 9 Nov: "is there a way to include a 'Check your booking in GCalendar [insert GCalendar event link]' at the booking
confirmation message?" Google's create answer carries the event's own link (htmlLink); Verify kept only the id and title.
v129: Verify's CREATED answer also carries html_link - Google's htmlLink, or, if it is ever missing, the same link built from
the event id and the KDC Bookings calendar (https://www.google.com/calendar/event?eid=<base64 "id calendar">). Nothing else changes;
Slack Interactions v76 shows it on the Booked card.
Built on workflows/imported/book-session-v128-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-session-v128-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}

OLD = """return [{ json: { status:'CREATED', event_id: ev.id, title: ev.summary,
  duration_note: note, human: 'Booked.' } }];"""
NEW = """// v129 (Howard, 9 Nov): the event's Google Calendar link for the Booked card - Google's own htmlLink, else built from the id
const html_link = (function () {
  const h = String(ev.htmlLink || '');
  if (/^https:\\/\\/(?:www\\.)?google\\.com\\/calendar\\/event\\?eid=[A-Za-z0-9_-]+/.test(h)) return h;
  try { return 'https://www.google.com/calendar/event?eid=' + Buffer.from(ev.id + ' c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com').toString('base64').replace(/=+$/, ''); }
  catch (e) { return ''; }
})();
return [{ json: { status:'CREATED', event_id: ev.id, title: ev.summary, html_link,
  duration_note: note, human: 'Booked.' } }];"""
p = by["Verify"]["parameters"]
assert p["jsCode"].count(OLD) == 1
p["jsCode"] = p["jsCode"].replace(OLD, NEW)

wf["name"] = "Jessie — Book Session — v129 (calendar link)"
out = os.path.join(ROOT, "workflows", "book-session-v129.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
