#!/usr/bin/env python3
"""main v216 (relay Book Session questions) - fixes v203: Guard Probe's word-for-word relay of Book Session's questions
never fired on a live turn. Book Session's Return Rejection node hands the agent `status` ("REJECTED"), not `verdict`, and
the relay tested `verdict` only (the offline sims fed it Check Conflicts' raw output, which has `verdict`). Live 2 Oct 13:41
(exec 21813): Book Session asked "Is this internal, or personal?" (Vic Icasas: Internal + Personal) and the model sent
"Is this advertising, entertainment, internal, or personal?". The relay now reads either field.
  scripts/build-relay-status.py <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = "    if (_o9 && _o9.verdict === 'REJECTED' && !_prepared) {"
NEW = "    if (_o9 && (_o9.verdict || _o9.status) === 'REJECTED' && !_prepared) {   // v216: Return Rejection sends `status`"
def main(w):
    w["name"] = "Project Jessie — v216 (relay Book Session questions)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], OLD, NEW, "relay")
    return w
if __name__ == "__main__":
    json.dump(main(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
