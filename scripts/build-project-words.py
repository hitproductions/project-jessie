#!/usr/bin/env python3
"""main v211 (multi-word project) - live 2 Oct 01:50: "book project thank you ..." was booked "THANK / ruff lopez / ..."
- Booked For's project reader kept only capitalised words after the first, so "thank you" became "thank"; and the
model's "THANK" stayed in the title because the requester did type that word. Decided 2 Oct: a project typed in
lowercase runs on over lowercase words until something that is plainly other information (a date or time word, a
number, "for / with / at / in / on", a room, a session word, client / engineer / arranger ...); at most 5 words. A model
title that is just the start of the typed project ("THANK" of "THANK YOU") is replaced with the whole of it.
  scripts/build-project-words.py <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

TN_OLD = "      if (/^[A-Z0-9À-Þ]/.test(t) && !STOPW.test(t) && !OKNEXT.test(t)) { keep.push(t); continue; }\n      break;"
TN_NEW = """      if (/^[A-Z0-9À-Þ]/.test(t) && !STOPW.test(t) && !OKNEXT.test(t)) { keep.push(t); continue; }
      // v211 (live 2 Oct, "project thank you"): a lowercase project runs on over lowercase words until other information
      if (allowLowerFirst && /^[a-zà-ÿ][a-zà-ÿ'’-]*$/.test(t) && /^[a-zà-ÿ]/.test(keep[0]) && !STOPW.test(t) && !OKNEXT.test(t) && !PSTOP.test(t)) { keep.push(t); continue; }
      break;"""
PSTOP_ANCHOR = "  const JOINW = /^(&|and|of|de|del|la|x)$/i;"
PSTOP_NEW = PSTOP_ANCHOR + """
  // v211: words that end a lowercase project name - other information starts here
  const PSTOP = /^(?:tomorrow|today|tonight|later|tmrw|tom|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december|week|weekend|month|morning|afternoon|evening|noon|am|pm|every|weekly|daily|until|till|from|then|so|also|but|because|i|me|my|we|our|he|she|they|his|her|their|it|that|which|who|need|needs|want|can|could|would|will|book|booking|reserve|schedule|studio|studios|room|rooms|booth|booths|likha|katha|salin|lobby|m[1-8]|vo|voice|voiceover|isr|record|recording|mix|mixing|edit|editing|dub|dubbing|qc|band|vocal|vocals|celeb|celebrity|music|post|localization|loc|meeting|event|session|sessions|client|clients|producer|engineer|arranger|for|with|at|in|on|by|to|of|please|pls|thanks|asap)$/i;"""
SUM_OLD = "if (want && !typedP(p[0], b)) p[0] = want;"
SUM_NEW = "if (want && (!typedP(p[0], b) || (want.toLowerCase().indexOf(String(p[0]).toLowerCase() + ' ') === 0))) p[0] = want;"

w = json.load(open(sys.argv[1])); w["name"] = "Project Jessie — v211 (multi-word project)"
bf = node(w, "Booked For")["parameters"]; s = bf["jsCode"]
s = sub1(s, PSTOP_ANCHOR, PSTOP_NEW, "pstop"); s = sub1(s, TN_OLD, TN_NEW, "takeName"); bf["jsCode"] = s
for nm in ("Prepare Booking", "Book Session", "Book Series"):
    v = node(w, nm)["parameters"]["workflowInputs"]["value"]; v["summary"] = sub1(v["summary"], SUM_OLD, SUM_NEW, nm)
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
