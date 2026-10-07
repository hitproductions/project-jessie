#!/usr/bin/env python3
"""Room Availability v19 (free-room emoji) - asked 7 Oct after "what studios are available tomorrow": the free-room answer takes
the same marks as the taken-room layout (main v235):
    🗓️ October 8 (Friday)

    ✅ Free all day:
    Studios 1, 2, 3, 4, 5, 6, 8, C, E, F, and M.
    Vocal booths A, B, and D.
    M2, M3, M4, M5, M7, M8.

    ⚠️ Studio 7 (free except 3:00 PM – 5:00 PM).
A room booked for part of the day: ⚠️ and "(free except ...)" (was "(except ...)"). The other free-room headings ("Free rooms:",
"Free studios:", "Free rooms, 3:00 PM – 5:00 PM:") take ✅; "Nothing free" takes ❌. The text the model reads (human) is unchanged.
  scripts/build-ra-emoji.py <ra-v18> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
R = [
 ("""  if (L.length) lines.push('Free all day:', ...L);""", """  if (L.length) lines.push('✅ Free all day:', ...L);   // v19: ✅ free, ⚠️ booked for part of the day"""),
 ("""    for (const [n, m] of partial) lines.push(n + ' (except ' + m.map(x => _hmx(x[0]) + ' – ' + _hmx(x[1])).join(', ') + ').'); }""",
  """    for (const [n, m] of partial) lines.push('⚠️ ' + n + ' (free except ' + m.map(x => _hmx(x[0]) + ' – ' + _hmx(x[1])).join(', ') + ').'); }"""),
 ("""  out.reply_text = _lines.length ? (_sOnly ? 'Free studios:' : 'Free rooms:') + '\\n' + _lines.join('\\n') : (_sOnly ? 'No studio is free then.' : 'Nothing is free then.');""",
  """  out.reply_text = _lines.length ? (_sOnly ? '✅ Free studios:' : '✅ Free rooms:') + '\\n' + _lines.join('\\n') : (_sOnly ? '❌ No studio is free then.' : '❌ Nothing is free then.');   // v19"""),
 ("""    out.reply_text = _wl.length ? _wl.join('\\n') : (_sOnly ? 'No studio is free that day.' : 'Nothing is free that day.');""",
  """    out.reply_text = _wl.length ? _wl.join('\\n') : (_sOnly ? '❌ No studio is free that day.' : '❌ Nothing is free that day.');   // v19"""),
 ("""          outM.reply_text = (_allWhole ? '' : (_studiosOnly ? 'Free studios' : 'Free rooms') + ', ' + hours + ':\\n\\n')""",
  """          outM.reply_text = (_allWhole ? '' : (_studiosOnly ? '✅ Free studios' : '✅ Free rooms') + ', ' + hours + ':\\n\\n')   // v19"""),
]
def ra(w):
    w["name"] = "Jessie — Room Availability — v19 (free-room emoji)"
    ca = node(w, "Compute Availability")["parameters"]; s = ca["jsCode"]
    for i, (a, b) in enumerate(R): s = sub1(s, a, b, f"r{i}")
    n = s.count("'Nothing free.'"); s = s.replace("'Nothing free.'", "'❌ Nothing free.'")
    if n < 1: raise SystemExit("nothing free: not found")
    ca["jsCode"] = s
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(ra(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
