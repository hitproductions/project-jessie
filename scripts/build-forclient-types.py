#!/usr/bin/env python3
"""Book Session v76 (client-work guard) - fixes v73: the on-behalf guard (MISSING_CLIENT, 23 Sep - the colleague a
booking is FOR is never its client) ran only when the booking type was "External". Since v73 the types are Advertising
/ Entertainment / Internal / Personal, so it never ran. It now runs for client work: Advertising, Entertainment, or a
legacy External.
  scripts/build-forclient-types.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
OLD = "if (bookedFor && String(REQ.bookingType || '').trim().toLowerCase() === 'external') {"
NEW = "if (bookedFor && /^(external|advertising|entertainment)$/i.test(String(REQ.bookingType || '').trim())) {   // v76: client work under the four types (v73 left it External-only)"
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Book Session — v76 (client-work guard)"
cc = node(w, "Check Conflicts")["parameters"]
assert cc["jsCode"].count(OLD) == 1
cc["jsCode"] = cc["jsCode"].replace(OLD, NEW)
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
