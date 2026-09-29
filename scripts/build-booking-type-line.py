#!/usr/bin/env python3
"""Book Session v64 (bug 9 fix) - QA bug 9 (28 Sep), root cause found in live QA 29 Sep (exec 16795).
  scripts/build-booking-type-line.py <book-pull> <book-out>

Summaries were inconsistent on the "Booking Type" line. When the model sends no booking type, Check Conflicts works
it out (the client's Client Type, "personal" / "client work" in the requester's words, or External for Localization)
and the event is written with it - but Render Summary read the model's empty input, so the line was left out. Check
Conflicts now returns the booking type it settled on (final_booking_type) and Render Summary shows that one. At the
yes, the summary's line is what Prepared Booking passes back, so the booked event carries the same value.
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
CLEAR_OLD = "final_rooms: REQ.rooms, room_suggested: __roomSuggested,   // v63"
CLEAR_NEW = "final_rooms: REQ.rooms, room_suggested: __roomSuggested, final_booking_type: String(REQ.bookingType || '').trim(),   // v63, v64"
RS_OLD = "  'Booking Type': internal ? '' : String(REQ.bookingType || '').trim(),"
RS_NEW = "  'Booking Type': internal ? '' : String(CC.final_booking_type || REQ.bookingType || '').trim(),   // v64: what Check Conflicts settled on"
def fix(w):
    w["name"] = "Jessie — Book Session — v64 (bug 9 fix)"
    c = node(w, "Check Conflicts")["parameters"]
    s = c["jsCode"]
    if s.count(CLEAR_OLD) != 2: raise SystemExit(f"returns: expected 2, found {s.count(CLEAR_OLD)}")
    c["jsCode"] = s.replace(CLEAR_OLD, CLEAR_NEW)
    r = node(w, "Render Summary")["parameters"]; r["jsCode"] = sub1(r["jsCode"], RS_OLD, RS_NEW, "render")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
