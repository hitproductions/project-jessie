#!/usr/bin/env python3
"""main v239 (claim forms) - fixes a gap since the claim check was written, found on v238 (Haiku), 8 Oct 15:01: asked
"cancel QATEST on december 14 2027", Jessie answered "QATEST / Jem Lim / HL on Tuesday, December 14, 2027 has been
cancelled." with no card, no yes and the booking still on the calendar. Guard Probe's claim check only matched a reply
STARTING with "Cancelled" / "Moved" (and "has been booked" for bookings); Gemini always led with the word, Haiku put the
title first.

The cancel and move claims now also match "has/have been cancelled|moved", "I've / I have cancelled|moved", and
"is now cancelled|moved"; the booking claim also "I've / I have booked". Negations ("has not been", "Nothing was")
never match.
  scripts/build-claim-forms.py <main-v238> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """  [/^\\s*\\*?Booked\\b|\\bhas been booked\\b/i, [['book session', ['CREATED']], ['book series', ['BOOKED_SERIES']]], 'booked'],
  [/^\\s*\\*?Cancell?ed\\b/i,                   [['cancel booking', ['CANCELLED']]],                                 'cancelled'],
  [/^\\s*\\*?Moved\\b/i,                        [['move booking',   ['MOVED', 'PARTIAL']]],                          'moved']
];"""
NEW = """  // v239 (claim forms): Haiku wrote "QATEST / Jem Lim / HL on Tuesday, December 14, 2027 has been cancelled." (8 Oct 15:01) -
  // nothing called, the booking still there - and only a reply STARTING with the word was checked. The usual done-forms count now.
  [/^\\s*\\*?Booked\\b|\\b(?:has|have) been booked\\b|\\bI(?:'|\\u2019)?ve booked\\b|\\bI have booked\\b/i, [['book session', ['CREATED']], ['book series', ['BOOKED_SERIES']]], 'booked'],
  [/^\\s*\\*?Cancell?ed\\b|\\b(?:has|have) been cancell?ed\\b|\\bI(?:'|\\u2019)?ve cancell?ed\\b|\\bI have cancell?ed\\b|\\bis now cancell?ed\\b/i, [['cancel booking', ['CANCELLED']]], 'cancelled'],
  [/^\\s*\\*?Moved\\b|\\b(?:has|have) been moved\\b|\\bI(?:'|\\u2019)?ve moved\\b|\\bI have moved\\b|\\bis now moved\\b/i, [['move booking', ['MOVED', 'PARTIAL']]], 'moved']
];"""

def main(w):
    w["name"] = "Project Jessie — v239 (claim forms)"
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"], OLD, NEW, "CLAIMS")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
