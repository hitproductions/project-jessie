#!/usr/bin/env python3
"""main v205 (series client question) - fixes v204 + long-standing: live Slack E2E 1 Oct 14:20-14:22.
  scripts/build-series-client.py <main-live> <main-out>

A model-written series summary with no client: Guard Probe takes "Book it?" off and asks "Who's the client? (or
"none")" (v162). Two things then went wrong:
  1. The Expand Series dates (v183) and the short series card (v204) both only ran on a summary ending in "Book it?" -
     and they run after the client question, so the summary went out long, with the model's "(Mon)" dates.
  2. The model's memory holds its own reply (ending "Book it?"), not the question Guard Probe sent. "none" then read
     as an answer to nothing, and she replied "What do you need?" (series forgotten, nothing booked).
Now: both rewrites also run on a series summary ending in the client question (and the cut on a plain "*Dates:*"
header); and Booked For tells the model when the requester is answering that question - "none" = no client, anything
else = the client - so it shows the same booking again with it.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

CQ = r'Who(?:’|\x27)s the client\? \(or "none"\)'   # the question Guard Probe asks (v202 wording)

GP_183_OLD = r"""  if (!_prepared && steps && /(Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i.test(text)) {"""
GP_183_NEW = (r"""  // v205: also when the client question has replaced "Book it?" (it runs first) - live 1 Oct, the dates stayed the model's
  if (!_prepared && steps && /(Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?|""" + CQ + r""")\s*$/i.test(text)) {""")
GP_CUT_OLD = r"""if (!_prepared && /\*Dates \(\d+\):\*/.test(text) && /(?:Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i.test(text.trim())) {"""
GP_CUT_NEW = (r"""// v205: also a plain "*Dates:*" header, and a summary ending in the client question (live 1 Oct: it went out long).
if (!_prepared && /\*Dates(?: \(\d+\))?:\*/.test(text) && /(?:Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?|""" + CQ + r""")\s*$/i.test(text.trim())) {""")

BF_OLD = "  if (out.forClient) {"
BF_NEW = r"""  // v205 (live 1 Oct 14:22): Guard Probe asked "Who's the client? (or "none")" in place of the model's "Book it?" - the
  // model's memory has its own version, so "none" read as an answer to nothing ("What do you need?", the series lost).
  try {
    const _lq = String(theirs[0] || ''), _ca = String(mine[0] || '').replace(/\*Sent using\*.*$/is, '').trim().replace(/[.!]+$/, '');
    if (/Who(?:’|')s the client\? \(or "none"\)\s*$/i.test(_lq) && _ca && _ca.split(/\s+/).length <= 6) {
      const _none = /^(none|no|nope|wala|n\/?a|no client|walang client|personal|internal|my own|own project)$/i.test(_ca);
      out.clientAnswer = _none ? 'none' : _ca;
      notes.push('THE REQUESTER IS ANSWERING YOUR LAST QUESTION, "Who is the client?" (it was asked in place of "Book it?"): "' + _ca + '" means '
        + (_none ? 'there is no client' : 'the client is ' + _ca) + '. Carry on with the same booking - show its summary again with '
        + (_none ? '"Client: None"' : 'that client') + ', ending in "Book it? Reply yes or no." Do not start over or greet them.');
    }
  } catch (e) {}
  if (out.forClient) {"""

def main(w):
    w["name"] = "Project Jessie — v205 (series client question)"
    gp = node(w, "Guard Probe")["parameters"]; s = gp["jsCode"]
    s = sub1(s, GP_183_OLD, GP_183_NEW, "gp v183"); s = sub1(s, GP_CUT_OLD, GP_CUT_NEW, "gp cut"); gp["jsCode"] = s
    bf = node(w, "Booked For")["parameters"]; bf["jsCode"] = sub1(bf["jsCode"], BF_OLD, BF_NEW, "bf")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
