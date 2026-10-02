#!/usr/bin/env python3
"""Room Availability v15 (calendar headline) - decided 2 Oct 12:56: the free-room reply opens with a calendar line and
breathing room:
    🗓️ October 3 (Sunday)

    Free all day:

    Studios 1, 2, 3, 4, 5, 6, 8, E, F, and M.
    Vocal booths A, B, and D.
    M2, M4, M5, M6, M7, M8.

    Studio 7 (free except for 11:00 AM – 12:00 PM).
A set time adds it to the headline ("🗓️ October 3 (Sunday), 2:00 PM – 4:00 PM"); a range gives each day its own headline.
  scripts/build-room-calendar-head.py <ra-live> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
CAL = "\\uD83D\\uDDD3\\uFE0F"   # 🗓️ as JS escapes (survives any file encoding)
HEAD_FN = """function __head(t, extra) { return '""" + CAL + """ ' + new Date(t).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', month: 'long', day: 'numeric' })
  + ' (' + new Date(t).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long' }) + ')' + (extra || ''); }   // v15 (hoisted: the day-by-day reply is built above)
"""
R = [
  ("lines.push('Free all day:', ...L);", "lines.push('Free all day:', '', ...L);   // v15: a blank line after the heading", "free all day"),
  ("out.reply_text = _lines.length ? (_sOnly ? 'Free studios:' : 'Free rooms:') + '\\n' + _lines.join('\\n')",
   "out.reply_text = _lines.length ? (_sOnly ? 'Free studios:' : 'Free rooms:') + '\\n\\n' + _lines.join('\\n')", "set time list"),
  ("    out.reply_text = _dl + (_whole ? '' : ', ' + _hm(reqStart) + ' – ' + _hm(reqEnd)) + ':\\n' + out.reply_text;",
   "    out.reply_text = __head(reqStart, _whole ? '' : ', ' + _hm(reqStart) + ' – ' + _hm(reqEnd)) + '\\n\\n' + out.reply_text;   // v15: 🗓️ headline", "single head"),
  ("outM.reply_text = (_studiosOnly ? 'Free studios' : 'Free rooms') + (_allWhole ? ', day by day' : ', ' + hours) + ':\\n\\n'",
   "outM.reply_text = (_allWhole ? '' : (_studiosOnly ? 'Free studios' : 'Free rooms') + ', ' + hours + ':\\n\\n')", "multi head"),
  ("return d.label + ':\\n' + (_wl.length ? _wl.join('\\n') : 'Nothing free.'); }",
   "return __head(_ws) + '\\n\\n' + (_wl.length ? _wl.join('\\n') : 'Nothing free.'); }", "multi whole day"),
  ("return d.label + ':\\n' + (d.free_rooms && d.free_rooms.length ? __layout(d.free_rooms).join('\\n') : 'Nothing free.'); }).join('\\n\\n');",
   "return __head(_ws) + '\\n\\n' + (d.free_rooms && d.free_rooms.length ? __layout(d.free_rooms).join('\\n') : 'Nothing free.'); }).join('\\n\\n');", "multi set time"),
]
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Room Availability — v15 (calendar headline)"
c = node(w, "Compute Availability")["parameters"]; s = c["jsCode"]
for o, n, l in R: s = sub1(s, o, n, l)
s = sub1(s, "function __layout(list) {", HEAD_FN + "function __layout(list) {", "head fn")
c["jsCode"] = s
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
