#!/usr/bin/env python3
"""main v245 (cancel it after Moved) - found in the 8 Oct Slack round on v244 (20:23): "cancel it" right after "Moved ..."
was answered "That's already moved - nothing else was changed." Gate Context's YES list includes "cancel it" and "book it"
(a reply to a card), and Prepared Cancel's repeat-yes guard (QA bug 17, 29 Sep) took any YES after a finished action as a
second yes to it. Long-standing; the same on Gemini.

Now a yes that names an action only repeats that same action: "cancel it" is a repeat only after "Cancelled", "book it"
only after "Booked"; after anything else it goes on to the model as a new request. A bare "yes" / "ok" is unchanged.
  scripts/build-v245.py <main-v244> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """  if (g2.saidYes === true && !d.use && !_waits) {
    if (/^Booked\\b/.test(bt)) done = "That's already booked - nothing else was changed.";
    else if (/^Cancelled\\b/.test(bt)) done = "That's already cancelled - nothing else was changed.";
    else if (/^Moved\\b/.test(bt)) done = "That's already moved - nothing else was changed.";
  }"""
NEW = """  // v245 (8 Oct 20:23): "cancel it" is in Gate Context's YES list (a reply to a cancel card), so "cancel it" right after
  // "Moved ..." was answered "That's already moved". A yes that names an action only repeats that same action.
  const _sd = String(g2.said || '').toLowerCase();
  const _verb = /\\bcancel it\\b/.test(_sd) ? 'cancel' : /\\bbook it\\b/.test(_sd) ? 'book' : '';
  if (g2.saidYes === true && !d.use && !_waits) {
    if (/^Booked\\b/.test(bt) && (!_verb || _verb === 'book')) done = "That's already booked - nothing else was changed.";
    else if (/^Cancelled\\b/.test(bt) && (!_verb || _verb === 'cancel')) done = "That's already cancelled - nothing else was changed.";
    else if (/^Moved\\b/.test(bt) && !_verb) done = "That's already moved - nothing else was changed.";
  }"""

def main(w):
    w["name"] = "Project Jessie — v245 (cancel it after Moved)"
    pc = node(w, "Prepared Cancel")["parameters"]
    pc["jsCode"] = once(pc["jsCode"], OLD, NEW, "repeat-yes guard")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
