#!/usr/bin/env python3
"""Book Session v74 (engineer note removed) - decided 1 Oct 13:45 PHT.
  scripts/build-no-engineer-note.py <book-live> <book-out>

"You're down as the engineer." is dropped from the summary: the initials at the end of the title already say who the
engineer is (QADEMO / Jem Lim / HL). The requester is still put in as the engineer by the same rules, and the
calendar event still carries "Engineer: <name> (<role>)".
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
OLD = "if (CC.self_engineer) notes.push('You\\u2019re down as the engineer.');\n"
NEW = "// v74 (decided 1 Oct): no engineer note - the title's initials already say who the engineer is.\n"
def fix(w):
    w["name"] = "Jessie — Book Session — v74 (engineer note removed)"
    r = node(w, "Render Summary")["parameters"]
    old = next((o for o in (OLD, OLD.replace("\\u2019", "\u2019")) if r["jsCode"].count(o) == 1), None)
    if not old: raise SystemExit("note not found")
    r["jsCode"] = r["jsCode"].replace(old, NEW)
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
