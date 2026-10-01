#!/usr/bin/env python3
"""main v210 + Book Session v83 (ye + no leaked instructions) - live 2 Oct 01:50:
  - "ye" to a card was not a yes (the gate's fixed list) - "ye" and "yea" join it (still a literal list, nothing guessed).
  - At the yes, Book Session re-ran the new-client check, did not find "ruff lopez" in the requester's recent messages
    and refused - although the card had passed that same check when it was prepared. Book Session v83: a yes to a
    verified prepared card (prepared_ok) is not refused CLIENT_UNVERIFIED again.
  - Book Direct Reply sent Book Session's refusal text as is - written for the model ("Ask the requester who the client
    is ... present the summary again"). main v210: sentences meant for the model are dropped; if nothing is left, a plain
    "Nothing was booked - something changed since that card. Send the booking again and I'll check it."
  scripts/build-yes-and-leak.py <book-live> <book-out> <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

CU_OLD = "  if (_rt.trim() && _cl && !_code && !_found && !_err && _nz(_cl)"
CU_NEW = "  const _prepYes = (REQ.prepared_ok === true || String(REQ.prepared_ok).toLowerCase() === 'true') && String(REQ.mode || '').toLowerCase() !== 'prepare';   // v83: checked when the card was prepared\n  if (!_prepYes && _rt.trim() && _cl && !_code && !_found && !_err && _nz(_cl)"

BDR_OLD = "let text = String(r.human || '').trim();"
BDR_NEW = r"""let text = String(r.human || '').trim();
// v210 (live 2 Oct 01:50): Book Session's refusal text is written for the model ("Ask the requester who the client is ...
// present the summary again") and this reply skips Guard Probe - drop every sentence meant for the model.
if (text && String(r.status || '').toUpperCase() !== 'CREATED') {
  const _MODEL = /\b(?:the requester|requester's|ask (?:them|the)|call (?:prepare|book|move|cancel)|prepare (?:it|booking)|present the summary|pass (?:client|booked_for|room)|leave (?:it|the client|booked_for) empty|room_override|tool|exactly as they type|must not (?:be|appear)|check the times with)\b/i;
  const _kept = text.split(/(?<=[.!?])\s+/).filter(x => x && !_MODEL.test(x));
  text = _kept.join(' ').trim();
  if (!text || /^Nothing was (?:booked|prepared)\.?$/i.test(text)) text = 'Nothing was booked - something changed since that card. Send the booking again and I’ll check it.';
}"""
G_OLD = "const YES = /^(y|yes|yeah|"
G_NEW = "const YES = /^(y|ye|yea|yes|yeah|"
BF_OLD = "(y|yes|yeah|"
BF_NEW = "(y|ye|yea|yes|yeah|"

def book(w):
    w["name"] = "Jessie — Book Session — v83 (no re-check at the yes)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = sub1(cc["jsCode"], CU_OLD, CU_NEW, "client unverified")
    return w
def main(w):
    w["name"] = "Project Jessie — v210 (ye + no leaked instructions)"
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], G_OLD, G_NEW, "gate yes")
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF_OLD, BF_NEW, "bf yes")
    r = node(w, "Book Direct Reply")["parameters"]; r["jsCode"] = sub1(r["jsCode"], BDR_OLD, BDR_NEW, "bdr")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
