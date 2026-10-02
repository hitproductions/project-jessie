#!/usr/bin/env python3
"""main v215 + Book Session v87 (short weekdays + kept context) - live 2 Oct 13:20-13:27 (Turn Log 21765-21796), a
confusing booking:
  1. "what studios are free on thurs?" - Gate Context knew only full weekday names, so "thurs" was no date (the model
     worked Thursday out itself). Now thu / thur / thurs / tue / tues / wed / weds / mon / fri / sat / sun count.
  2. With no date in the conversation, Gate Context's fallback read earlier messages - past the finished DIGICON ISR
     booking - found its "today" (Sat 2 Oct), and Prepare Booking's date pin moved the new booking to Saturday, where
     that booking made Studio 8 "taken". The fallback now stops at a finished booking ("Booked." / "Moved" / "Cancelled").
  3. "yes so i can book ito. i already said 11am-3pm" contains "book", so Booked For took it as a new request and forgot
     the session type, the project and the client typed before it (asked again; "Michael V" not typed). A reply that
     starts like an answer ("yes", "so", "ok", "i already said", ...) is not a new request.
  4. "Booked. That is a bit longer than VO Recording sessions usually run (...)" repeated the card's heads-up: Book
     Session v87's Booked reply is "Booked." (the note stays in duration_note).
  scripts/build-thurs-context.py <book-live> <book-out> <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
DAY_OLD = "const DAYRE = '(sunday|monday|tuesday|wednesday|thursday|friday|saturday)';"
DAY_NEW = "const DAYRE = '(sunday|monday|tuesday|wednesday|thursday|friday|saturday|thurs|thur|thu|tues|tue|weds|wed|mon|fri|sat|sun)';   // v215: short forms (\"thurs\")"
IDX_OLD = "const dayIndex = n => DAYS.map(d => d.toLowerCase()).indexOf(String(n).toLowerCase());"
IDX_NEW = "const __DAB = { sun: 'sunday', mon: 'monday', tue: 'tuesday', tues: 'tuesday', wed: 'wednesday', weds: 'wednesday', thu: 'thursday', thur: 'thursday', thurs: 'thursday', fri: 'friday', sat: 'saturday' };   // v215\nconst dayIndex = n => { const k = String(n).toLowerCase(); return DAYS.map(d => d.toLowerCase()).indexOf(__DAB[k] || k); };"
FB_OLD = "  for (const m of msgs) {\n    if (!m || isBot(m) || String(m.ts || '') === String(trigger.ts || '')) continue;"
FB_NEW = "  for (const m of msgs) {\n    // v215 (live 2 Oct 13:23): a finished booking ends the search - its date is not the new booking's\n    if (m && isBot(m) && /^\\s*\\*?(?:booked\\b|moved\\b|cancell?ed\\b)/i.test(clean(m.text || ''))) break;\n    if (!m || isBot(m) || String(m.ts || '') === String(trigger.ts || '')) continue;"
NR_OLD = "const isNewRequest = t => /\\b(book|rebook|reschedule)\\b/i.test(t) && t.length > 20;"
NR_NEW = "const isNewRequest = t => /\\b(book|rebook|reschedule)\\b/i.test(t) && t.length > 20\n    && !/^\\s*(?:yes|yeah|yep|yup|ye|yea|ok|okay|sure|so|and|also|but|no|nope|i already|you already|already|i said|like i said|as i said)\\b/i.test(t) && !/\\balready (?:said|told|gave|typed)\\b/i.test(t);   // v215: an answer that says \"book\" is not a new request"
VER_OLD = "  duration_note: note, human: note ? 'Booked. ' + note : 'Booked.' } }];"
VER_NEW = "  duration_note: note, human: 'Booked.' } }];   // v87: the card already gave the heads-up"
def book(w):
    w["name"] = "Jessie — Book Session — v87 (no repeated heads-up)"
    v = node(w, "Verify")["parameters"]; v["jsCode"] = sub1(v["jsCode"], VER_OLD, VER_NEW, "verify")
    return w
def main(w):
    w["name"] = "Project Jessie — v215 (short weekdays + kept context)"
    g = node(w, "Gate Context")["parameters"]; s = g["jsCode"]
    s = sub1(s, DAY_OLD, DAY_NEW, "dayre"); s = sub1(s, IDX_OLD, IDX_NEW, "dayindex"); s = sub1(s, FB_OLD, FB_NEW, "fallback"); g["jsCode"] = s
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], NR_OLD, NR_NEW, "new request")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
