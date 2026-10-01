#!/usr/bin/env python3
"""Book Session v79 (type reminder) - decided 1 Oct after the live 15:40 run ("no" to "Is this advertising work, or
internal?" was asked the same question again): when Jessie's last message was the booking-type question and the reply
named no type, the reply is a reminder listing all four - "Please choose a booking type: Advertising, Entertainment,
Internal or Personal." Any type named (offered or not) is still taken as before.
  scripts/build-type-reminder.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
OLD = """      const _q = __tyQuestion(_d);
      const _both = _needCli && !_d.arranger;"""
NEW = """      // v79 (decided 1 Oct): the type question was just asked and the reply named no type -> a reminder with all four.
      // asked_text is Jessie's messages for this booking, newest first.
      const _reAsk = /^\\s*(?:Is this (?:advertising|entertainment|internal|personal)\\b|Who\\u2019s the client\\? \\(or "none"\\) And is this |Please choose a booking type|Client work or your own project\\?)/i.test(String(REQ.asked_text || ''));
      const _q = _reAsk ? 'Please choose a booking type: Advertising, Entertainment, Internal or Personal.' : __tyQuestion(_d);
      const _both = _needCli && !_d.arranger && !_reAsk;"""
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Book Session — v79 (type reminder)"
cc = node(w, "Check Conflicts")["parameters"]
assert cc["jsCode"].count(OLD) == 1
cc["jsCode"] = cc["jsCode"].replace(OLD, NEW)
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
