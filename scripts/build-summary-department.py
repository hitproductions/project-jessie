#!/usr/bin/env python3
"""Book Session v69 (department line fix) - live QA 30 Sep 13:29 PHT (Turn Log exec 18529).
  scripts/build-summary-department.py <book-live> <book-out>

"external booking. move to 6pm" -> the QAORANGE2 summary had no *Department:* line (the one two minutes earlier did).
When the model sends no department, Check Conflicts works it out from the session type (v52) and writes "Dept: ..." into
the event description, but Render Summary read the department from the tool's raw input, where it is still empty. The
summary is what the yes books (Book Direct reads it back), so the booking would have gone in without its department -
and the department scopes who may move or cancel it.

Render Summary now falls back to the "Dept:" segment Check Conflicts settled on.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = "  'Department': String(REQ.department || '').trim(),\n"
NEW = "  'Department': String(REQ.department || '').trim() || seg(/^dept\\s*:\\s*/i),   // v69: or what Check Conflicts worked out\n"

def fix(w):
    w["name"] = "Jessie — Book Session — v69 (department line fix)"
    r = node(w, "Render Summary")["parameters"]; r["jsCode"] = sub1(r["jsCode"], OLD, NEW, "department")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
