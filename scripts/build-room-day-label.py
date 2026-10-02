#!/usr/bin/env python3
"""Room Availability v14 (day named) - decided 2 Oct 12:44: a free-room answer says which day it is about. Live 12:44,
"what studios are free tomorrow?" answered for the wrong day (Mon 4 Oct 2027, not Sun 3 Oct) and nothing in the reply
said so. The one-window reply now starts with the day ("Sunday, October 3:"); a range already lists its days.
  scripts/build-room-day-label.py <ra-live> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = """  if (reqEnd - reqStart >= 8 * 3600000) {   // a day asked about without a time (8+ hours on one day)
    const _wl = __wholeDay(reqStart, reqEnd, _sOnly);
    out.reply_text = _wl.length ? _wl.join('\\n') : (_sOnly ? 'No studio is free that day.' : 'Nothing is free that day.');
  }"""
NEW = OLD + r"""
  // v14 (decided 2 Oct): name the day - "Sunday, October 3:" - so a wrong day shows at once
  try {
    const _dl = new Date(reqStart).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
    const _hm = t => new Date(t).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    const _whole = reqEnd - reqStart >= 8 * 3600000;
    out.reply_text = _dl + (_whole ? '' : ', ' + _hm(reqStart) + ' – ' + _hm(reqEnd)) + ':\n' + out.reply_text;
  } catch (e) {}"""
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Room Availability — v14 (day named)"
c = node(w, "Compute Availability")["parameters"]; c["jsCode"] = sub1(c["jsCode"], OLD, NEW, "label")
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
