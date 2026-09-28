#!/usr/bin/env python3
"""Shorter fixed replies (Tara, 29 Sep), applied to fresh builds.

  scripts/build-concise.py <main-in> <main-out> <book-pull> <book-out> <expand-pull> <expand-out>

- Summary notes (Book Session Render Summary):
    "Assuming 1 hour, the usual VO Recording length - tell me if it should be different." -> "Assumed 1 hour (usual for VO Recording)."
    "Studio 3 is not a room normally used for VO Recording - booking it as you asked."     -> "Studio 3 isn't a usual VO Recording room - booking it as asked."
  Prepared Booking (main) reads the override from that note, so it accepts both wordings.
- Guard Probe / Gate Context: the model-side "Assuming 3 hours - tell me if that is wrong." -> "Assumed 3 hours."
- Series summary (Expand Series): no introduction line; the time once, not on every date.
- Prompt: greetings get one short line; a clarifying question is only the question.
- Error message: "Something went wrong - please try again."
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

def main_fix(w):
    n = node(w, "Prepared Booking")
    n["parameters"]["jsCode"] = sub1(n["parameters"]["jsCode"], "'Override': /booking it as you asked\\./i.test(t) ? 'yes' : ''",
        "'Override': /booking it as (?:you )?asked\\./i.test(t) ? 'yes' : ''", "prepared booking override")
    g = node(w, "Guard Probe")
    g["parameters"]["jsCode"] = sub1(g["parameters"]["jsCode"], "text = 'Assuming ' + len + ' \\u2014 tell me if that is wrong.\\n\\n' + text;",
        "text = 'Assumed ' + len + '.\\n\\n' + text;", "guard probe assuming")
    gc = node(w, "Gate Context")
    gc["parameters"]["jsCode"] = sub1(gc["parameters"]["jsCode"], 'for example "Assuming 3 \'\n    + \'hours, tell me if that is wrong."',
        'for example "Assumed 3 \'\n    + \'hours."', "gate assuming")
    e = node(w, "Error message")
    e["parameters"]["text"] = "Something went wrong - please try again."
    a = node(w, "Jessie AI Agent")["parameters"]["options"]
    a["systemMessage"] = sub1(a["systemMessage"], "Keep replies short, helpful and professional — this is a fast-moving production environment.",
        "Keep replies short, helpful and professional — this is a fast-moving production environment. A greeting or small talk "
        "gets one short line, such as \"Hi <first name>! What do you need?\" When you need something from the requester, ask only "
        "the question — don't say what you will do once they answer.", "prompt")
    return w

def book_fix(w):
    w["name"] = "Jessie — Book Session — v58 (v56 fixed)"
    n = node(w, "Render Summary"); c = n["parameters"]["jsCode"]
    c = sub1(c, "notes.push('Assuming ' + (_h ? _h + ' hour' + (_h === 1 ? '' : 's') : '') + (_h && _m ? ' ' : '') + (_m ? _m + ' minutes' : '') + ', the usual ' + st + ' length - tell me if it should be different.');",
             "notes.push('Assumed ' + (_h ? _h + ' hour' + (_h === 1 ? '' : 's') : '') + (_h && _m ? ' ' : '') + (_m ? _m + ' minutes' : '') + (st ? ' (usual for ' + st + ')' : '') + '.');", "assumed note")
    c = sub1(c, "if (override) notes.push(rooms + ' is not a room normally used for ' + (st || 'this') + ' - booking it as you asked.');",
             "if (override) notes.push(rooms + \" isn't a usual \" + (st ? st + ' room' : 'room for this') + ' - booking it as asked.');", "override note")
    n["parameters"]["jsCode"] = c
    return w

def expand_fix(w):
    w["name"] = "Jessie — Expand Series — v4"
    n = node(w, "Expand Dates"); c = n["parameters"]["jsCode"]
    c = sub1(c, "res.human = 'Present these dates in ONE summary: every date with its weekday and the time, plus the booking details, '",
             "res.human = 'Present these dates in ONE summary, with no introduction line: every date with its weekday (the time once, not on each date), plus the booking details, '",
             "expand human")
    n["parameters"]["jsCode"] = c
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    for fn, i, o in ((main_fix, a[0], a[1]), (book_fix, a[2], a[3]), (expand_fix, a[4], a[5])):
        w = fn(json.load(open(i))); json.dump(w, open(o, "w"), indent=2, ensure_ascii=False); print("wrote", o)
