#!/usr/bin/env python3
"""main v209 (later = today) - live 1 Oct 16:51: "book studio 7 ... later at 9-11pm" named no date for Gate Context
(it knows today / tonight / tomorrow / weekdays / dates), so Book Session asked "Which day?" (and at 16:29 a date
carried from an earlier turn - tomorrow - was used instead, the wrong day). "later", "later today", "this afternoon /
evening / morning" now read as today in both of Gate Context's date readers. Not a time shift: "an hour later", "a bit
later", "later this week", "later than", "later in the month" are left alone.
  scripts/build-later-today.py <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
TODAY = r"(?:today|tonight|this\s+(?:afternoon|evening|morning)|(?<!\b(?:hours?|hrs?|minutes?|mins?|days?|weeks?|an|a|bit|little|much|or|sooner|\d+)\s)later(?:\s+today)?(?!\s+(?:this|next|in|than|on|that|date|day|week|month)\b))"
OLD1 = "if (/\\b(today|tonight)\\b/i.test(msgText)) note('today', today);"
NEW1 = "if (/\\b" + TODAY + "\\b/i.test(msgText)) note('today', today);   // v209: later / this afternoon = today"
OLD2 = "if ((m = t.match(/\\b(today|tonight)\\b/i))) add(m.index, today);"
NEW2 = "if ((m = t.match(/\\b" + TODAY + "\\b/i))) add(m.index, today);   // v209"
w = json.load(open(sys.argv[1])); w["name"] = "Project Jessie — v209 (later = today)"
g = node(w, "Gate Context")["parameters"]; s = g["jsCode"]
for o, n in ((OLD1, NEW1), (OLD2, NEW2)):
    assert s.count(o) == 1, (o, s.count(o)); s = s.replace(o, n)
g["jsCode"] = s
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
