#!/usr/bin/env python3
"""Book Session v77 + main v208 (default room) - Bookers "Default Type" holds each person's default room (Tel, 1 Oct;
decided 1 Oct: use it if free and suitable).
  scripts/build-default-room.py <book-live> <book-out> <main-live> <main-out>

When the requester names no room (prepare mode, the v63 pick), the room is the default room of the person the booking
is for (the booked-for colleague, else the requester) when it is free then and one of the session type's usual
(Priority) rooms. Otherwise the pick is as before: the first free ranked room. A named room always wins; a default room
that is busy, unsuitable or not a studio the type runs in is skipped silently. The card note reads "Your usual room."
main v208: the staff list sent to Prepare Booking / Book Session / Book Direct carries "Default Type" (it already sat
in the reference cache - Refresh Reference Cache reads every Bookers field).
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BS_OLD = "    const _top = _ranked.find(r => !_busy.has(r.toLowerCase()));"
BS_NEW = r"""    let _top = _ranked.find(r => !_busy.has(r.toLowerCase()));
    // v77 (1 Oct): the default room (Bookers "Default Type") of the person the booking is for - the booked-for
    // colleague, else the requester - when it is free and one of this session type's usual (Priority) rooms.
    try {
      const _forName = ((String(REQ.description || '').match(/\(for\s+([^)]+)\)/i) || [])[1] || '').trim().toLowerCase();
      let _who = __reqStaff;
      if (_forName) { const _f = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).find(f => String(f.Name || '').trim().toLowerCase() === _forName); if (_f) _who = _f; }
      const _prio = new Set(priorityIds.map(id => String(nameById[id] || '').toLowerCase()).filter(Boolean));
      const _defs = _who ? [].concat(_who['Default Type'] || []).map(x => String((x && x.name) || x).trim()).filter(Boolean) : [];
      const _key = n => Object.keys(ROOMS).find(k => k.toLowerCase() === n.toLowerCase());
      for (const d of _defs) {
        const k = _key(d);
        if (k && _prio.has(k.toLowerCase()) && !_busy.has(k.toLowerCase()) && !_common.has(k.toLowerCase()) && !isBooth[k.toLowerCase()]) { _top = k; __roomDefault = k; break; }
      }
    } catch (e) {}"""

STAFF_OLD = "Department: f.Department || [] })"
STAFF_NEW = "Department: f.Department || [], 'Default Type': f['Default Type'] || [] })"

DECL_OLD = "let __roomSuggested = '';"
DECL_NEW = "let __roomSuggested = '', __roomDefault = '';   // v77: __roomDefault = the suggested room is the person's default"
RET_OLD = "room_suggested: __roomSuggested,"
RET_NEW = "room_suggested: __roomSuggested, room_default: __roomDefault,"
RS_OLD = "if (CC.room_suggested) notes.push('I picked ' + CC.room_suggested + '. Tell me if you\u2019d like another room.');"
RS_OLD2 = "if (CC.room_suggested) notes.push('I picked ' + CC.room_suggested + '. Tell me if you’d like another room.');"
RS_NEW = "if (CC.room_suggested) notes.push(CC.room_default ? 'Your usual room. Tell me if you’d like another.' : 'I picked ' + CC.room_suggested + '. Tell me if you’d like another room.');   // v77"

def book(w):
    w["name"] = "Jessie — Book Session — v77 (default room)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, BS_OLD, BS_NEW, "bs default room"); s = sub1(s, DECL_OLD, DECL_NEW, "bs decl")
    if s.count(RET_OLD) < 1: raise SystemExit("bs returns")
    s = s.replace(RET_OLD, RET_NEW); cc["jsCode"] = s
    rs = node(w, "Render Summary")["parameters"]; t = rs["jsCode"]
    old = RS_OLD if RS_OLD in t else RS_OLD2
    rs["jsCode"] = sub1(t, old, RS_NEW, "render note")
    return w

def main(w):
    w["name"] = "Project Jessie — v208 (default room)"
    for nm in ("Book Direct", "Prepare Booking", "Book Session"):
        v = node(w, nm)["parameters"]["workflowInputs"]["value"]
        v["staff_data"] = sub1(v["staff_data"], STAFF_OLD, STAFF_NEW, nm + " staff_data")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
