#!/usr/bin/env python3
"""Book Session v78 (type question wording) - decided 1 Oct after the live run at 15:30 ("Advertising or internal?"
read as cryptic): the booking-type question reads "Is this advertising work, or internal?". Built from the options
the code offers (a client's own Client Type tags, or all four when nothing decides it):
  two      -> "Is this advertising work, or internal?" / "Is this advertising work, or entertainment work?"
  four     -> "Is this advertising work, entertainment work, internal, or personal?"
  arranger -> unchanged: "Client work or your own project?"
Also fixes v73: the client + type question reached Slack cut off at its inner quotes ("Who's the client (or").
  scripts/build-type-question.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
OLD = """const __tyQuestion = d => { const a = d.ask.map((x, i) => i ? x.toLowerCase() : x);
  return a.length === 2 ? a[0] + ' or ' + a[1] + '?' : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1] + '?'; };"""
NEW = """const __tyQuestion = d => {
  if (d.arranger) { const a = d.ask.map((x, i) => i ? x.toLowerCase() : x);
    return a.length === 2 ? a[0] + ' or ' + a[1] + '?' : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1] + '?'; }
  // v78 (decided 1 Oct): "Is this advertising work, or internal?" - plainer than "Advertising or internal?"
  const W = { advertising: 'advertising work', entertainment: 'entertainment work', internal: 'internal', personal: 'personal' };
  const a = d.ask.map(x => W[String(x).toLowerCase()] || String(x).toLowerCase());
  return 'Is this ' + (a.length === 1 ? a[0] : a.slice(0, -1).join(', ') + ', or ' + a[a.length - 1]) + '?'; };"""
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Book Session — v78 (type question wording)"
cc = node(w, "Check Conflicts")["parameters"]
assert cc["jsCode"].count(OLD) == 1
cc["jsCode"] = cc["jsCode"].replace(OLD, NEW)
# fixes v73: the client + type question put raw quotes round "none" inside the quoted question, so main's word-for-word
# relay (Guard Probe v203) stopped at the first inner quote and sent "Who's the client (or". Escaped like NEED_CLIENT.
Q_OLD = "'Who’s the client (or \"none\")? And '"
Q_NEW = "'Who’s the client? (or \\\\\"none\\\\\") And '"
assert cc["jsCode"].count(Q_OLD) == 1, cc["jsCode"].count(Q_OLD)
cc["jsCode"] = cc["jsCode"].replace(Q_OLD, Q_NEW)
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
