#!/usr/bin/env python3
"""Colours (Howard, 20 Nov): meetings and conference room bookings Sage, like bookings of several departments.
  Book Session v134 (Check Conflicts) and Move Booking v48 (Resolve Booking): the shared rule (scripts/jessie_colour.py JC) -
  a Meeting -> Sage (was Banana); any booking whose main (first) room is Salin, Katha or Likha -> Sage, after the type rules
  (an Event there stays Tangerine, an M booth Basil, a celebrity booking Tomato).
  Move v48: a colour the 4 Nov rule gave (a meeting still Banana) is Jessie's, not hand-set - recoloured on its next change.
Built on book-session-v133 and move-booking-v47 (each == live)."""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from jessie_colour import JC, JC_V1
W = lambda f: json.load(open(os.path.join(ROOT, "workflows", f)))
def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False); fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")
def rep(wf, nd, old, new):
    n = [x for x in wf["nodes"] if x["name"] == nd][0]; c = n["parameters"]["jsCode"]
    assert c.count(old) == 1, (nd, old[:70], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)

bs = W("book-session-v133.json")
rep(bs, "Check Conflicts", JC_V1, JC)
save(bs, "book-session-v134.json", "Jessie — Book Session — v134 (meetings Sage)")

mv = W("move-booking-v47.json")
rep(mv, "Resolve Booking", JC_V1, JC)
V1 = JC_V1.replace("function __jColour(", "function __jColourV1(")
rep(mv, "Resolve Booking", JC, JC + "// v48: the 4 Nov rule (Move v43-v47) - a colour it gave is Jessie's too, not a hand-set one (a meeting's Banana)\n" + V1[V1.index("function __jColourV1("):])
rep(mv, "Resolve Booking", "__colour = _jessie && (!_was || _was === _of(ev.description, ev.location)) ? _of(__desc, outLocation) : _was;",
    "// v48: or the colour the 4 Nov rule gave it (a meeting still Banana is recoloured Sage on its next change)\n"
    "  const _ofV1 = (d, loc) => { const s = String(d || ''); return __jColourV1(((s.match(/\\n\\s*SType:\\s*([^\\n]*)/) || [])[1] || ''),\n"
    "    ((s.split(/\\n/)[0].match(/(?:^|\\|)\\s*Dept:\\s*([^|]+)/) || [])[1] || ''), _rooms(loc)); };\n"
    "  __colour = _jessie && (!_was || _was === _of(ev.description, ev.location) || _was === _ofV1(ev.description, ev.location)) ? _of(__desc, outLocation) : _was;")
save(mv, "move-booking-v48.json", "Jessie — Move Booking — v48 (meetings Sage)")
