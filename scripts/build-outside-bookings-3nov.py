#!/usr/bin/env python3
"""Builds Room Availability v25 and Book Session v125 (rooms booked outside KDC Bookings), 3 Nov - PENDING 148.

29 Oct: "M4 - Ate Weng" (30 Oct, all day) was booked from a personal calendar by inviting the M4 room - it is on M4's own
calendar, not on KDC Bookings. Room Availability and Book Session read KDC Bookings only, so Jessie offered M4 as free; the room
declined Jessie's booking and Room Check removed it.

Both workflows now also ask Google which rooms are busy in the window (one free/busy call for all 27 room calendars - "Room Free
Busy", placed before "Get Events In Window" so the code still reads the KDC events from its input as before). Time a room is busy
that no KDC booking for that room covers (by attendee, location or title, as the code already matches rooms) is added as a
booking "Booked outside KDC Bookings" - so the room shows taken, Book Session refuses it (ROOM_OCCUPIED), and it is never offered
for a request (no ref:, no Booked by). A failed free/busy read (or a room it could not read) changes nothing - the KDC-only
answer as before. The excluded event of a change is a KDC booking, so its own time is never counted twice.
Built on the live downloads: room-availability-v24-imported.json, book-session-v124-imported.json.
"""
import copy
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


INJECT = r"""// v25 / v125 (PENDING 148, 3 Nov): a room booked from someone's own calendar (the room invited, not on KDC Bookings) is busy on
// the room's own calendar only. "Room Free Busy" reads every room's busy times; time busy there that no KDC booking for that room
// covers becomes a booking "Booked outside KDC Bookings" (taken; no ref:, so never offered for a request). A failed read: nothing.
try {
  const _fb = (($('Room Free Busy').first() || {}).json) || {};
  const _cals = _fb.calendars || {};
  const _t = v => Date.parse(String(v || ''));
  const _evT = ev => [_t((ev.start || {}).dateTime || ((ev.start || {}).date ? ev.start.date + 'T00:00:00+08:00' : '')),
    _t((ev.end || {}).dateTime || ((ev.end || {}).date ? ev.end.date + 'T00:00:00+08:00' : ''))];
  const _iso = n => new Date(n + 8 * 3600e3).toISOString().slice(0, 19) + '+08:00';
  for (const _k of Object.keys(ROOMS)) {
    const _c = _cals[ROOMS[_k]];
    if (!_c || (_c.errors && _c.errors.length) || !Array.isArray(_c.busy)) continue;
    const _lk = _k.toLowerCase(), _em = String(ROOMS[_k]).toLowerCase();
    const _kdc = __LIST__.filter(ev => ev && !ev.__outside && ev.status !== 'cancelled' && (
      (ev.attendees || []).some(a => String(a.email || '').toLowerCase() === _em) || String(ev.location || '').toLowerCase().indexOf(_lk) !== -1
      || String(ev.summary || '').split(' - ')[0].trim().toLowerCase() === _lk)).map(_evT);
    for (const b of _c.busy) {
      let parts = [[_t(b.start), _t(b.end)]];
      for (const [s, e] of _kdc) parts = parts.flatMap(([ps, pe]) => (e <= ps || s >= pe) ? [[ps, pe]] : [[ps, Math.min(pe, s)], [Math.max(ps, e), pe]].filter(([x, y]) => y > x));
      for (const [s, e] of parts) if (e - s >= 60000) __LIST__.push({ id: 'outside-' + _k.replace(/\s+/g, '') + '-' + s, status: 'confirmed', __outside: true,
        summary: 'Booked outside KDC Bookings', start: { dateTime: _iso(s) }, end: { dateTime: _iso(e) },
        attendees: [{ email: ROOMS[_k], resource: true, responseStatus: 'accepted' }], description: '' });
    }
  }
} catch (e) {}
"""


def add_freebusy(wf, events_node, room_ids, before_targets_from):
    """Insert "Room Free Busy" in front of events_node: every connection into events_node goes to Room Free Busy instead."""
    ev = next(n for n in wf["nodes"] if n["name"] == events_node)
    qp = {p["name"]: p["value"] for p in ev["parameters"]["queryParameters"]["parameters"]}
    strip = lambda v: v[3:-2].strip() if v.startswith("={{") and v.endswith("}}") else json.dumps(v)
    body = ("={{ JSON.stringify({ timeMin: (" + strip(qp["timeMin"]) + "), timeMax: (" + strip(qp["timeMax"]) + "), timeZone: 'Asia/Manila', items: "
            + json.dumps([{"id": i} for i in room_ids]) + " }) }}")
    node = {
        "parameters": {"method": "POST", "url": "https://www.googleapis.com/calendar/v3/freeBusy", "authentication": "predefinedCredentialType",
                       "nodeCredentialType": "googleCalendarOAuth2Api", "sendBody": True, "specifyBody": "json", "jsonBody": body,
                       "options": {"timeout": 10000}},
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": [ev["position"][0] - 220, ev["position"][1] - 180],
        "id": str(uuid.uuid4()), "name": "Room Free Busy", "alwaysOutputData": True, "executeOnce": True,
        "credentials": copy.deepcopy(ev["credentials"]), "onError": "continueRegularOutput"}
    wf["nodes"].append(node)
    n_in = 0
    for src, outs in wf["connections"].items():
        for branch in outs.get("main", []):
            for c in branch or []:
                if c["node"] == events_node:
                    c["node"] = "Room Free Busy"; n_in += 1
    assert n_in == before_targets_from, (events_node, n_in)
    wf["connections"]["Room Free Busy"] = {"main": [[{"node": events_node, "type": "main", "index": 0}]]}


def room_ids(js):
    import re
    i = js.index("const ROOMS"); j = js.index("};", i)
    return re.findall(r"'(?:[^']+)'\s*:\s*'([^']+@resource\.calendar\.google\.com)'", js[i:j])


# ---- Room Availability v25
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "room-availability-v24-imported.json")))
ca = next(n for n in wf["nodes"] if n["name"] == "Compute Availability")
js = ca["parameters"]["jsCode"]
ids = room_ids(js); assert len(ids) == 27, len(ids)
js = sub(js, "})();\n\nconst ms = v => new Date(v).getTime();\nconst reqStart",
    "})();\n" + INJECT.replace("__LIST__", "events") + "\nconst ms = v => new Date(v).getTime();\nconst reqStart")
ca["parameters"]["jsCode"] = js
add_freebusy(wf, "Get Events In Window", ids, 1)
wf["name"] = "Jessie — Room Availability — v25 (rooms booked outside KDC)"
out = os.path.join(ROOT, "workflows", "room-availability-v25.json")
json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False); open(out, "a").write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")

# ---- Book Session v125
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-session-v124-imported.json")))
cc = next(n for n in wf["nodes"] if n["name"] == "Check Conflicts")
js = cc["parameters"]["jsCode"]
ids2 = room_ids(js); assert sorted(ids2) == sorted(ids), (len(ids2),)
js = sub(js, "\n};\n\n// v104 (PENDING 110, live 9 Oct 15:09 on Haiku)",
    "\n};\n" + INJECT.replace("__LIST__", "EVENTS") + "\n// v104 (PENDING 110, live 9 Oct 15:09 on Haiku)")
cc["parameters"]["jsCode"] = js
add_freebusy(wf, "Get Events In Window", ids, 3)
wf["name"] = "Jessie — Book Session — v125 (rooms booked outside KDC)"
out = os.path.join(ROOT, "workflows", "book-session-v125.json")
json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False); open(out, "a").write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
