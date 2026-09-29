#!/usr/bin/env python3
"""Book Session v65 (arranger question fix) - live QA 29 Sep 16:05 PHT (main exec 16937), asked the same day: confirm
the engineer when asking for the arranger.
  scripts/build-arranger-question.py <book-pull> <book-out>

"Book a music recording ..., engineer drey" -> "Music Vocal Recording sessions usually have an arranger as well as the
engineer. Who is the arranger, or is there none?" Drey had been read as Daryl Reyes and passed on, but the question did
not say so, and "as well as the engineer" read as if the engineer had not been taken in. NEED_ARRANGER now names the
engineer it has: "Daryl Reyes is down as the engineer. Music Vocal Recording sessions usually have an arranger too -
who is it, or is there none?"
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = """      human:'Nothing was prepared - ' + REQ.session_type + ' sessions usually have an arranger as well as the engineer. Ask the requester who the arranger is; '
          + 'if there is none, they can just say "no arranger". Then prepare it again, with the arranger in the description as "Arranger: <name>".' } }];"""
NEW = """      // v65 (live QA 29 Sep): say which engineer it has, so the question does not read as if the engineer was missed.
      engineer: _eng4,
      human:'Nothing was prepared. Ask exactly this, in one message: "' + (_eng4 ? _eng4 + ' is down as the engineer. ' : '')
          + REQ.session_type + ' sessions usually have an arranger too - who is it, or is there none?" '
          + 'Then prepare it again, with the arranger in the description as "Arranger: <name>" (or with no arranger if they say none).' } }];"""
PRE_OLD = "  if (_wantsArr && _music && !_hasArr && !_saidNone) {\n"
PRE_NEW = PRE_OLD + """    const _eng4 = (String(REQ.engineer || '').trim() || ((String(REQ.description || '').match(/(?:^|\\|)\\s*engineer\\s*:\\s*([^|]+)/i) || [])[1] || ''))
      .replace(/\\s*\\([^)]*\\)\\s*$/, '').trim();
"""
def fix(w):
    w["name"] = "Jessie — Book Session — v65 (arranger question fix)"
    c = node(w, "Check Conflicts")["parameters"]
    s = sub1(c["jsCode"], PRE_OLD, PRE_NEW, "pre")
    c["jsCode"] = sub1(s, OLD, NEW, "human")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
