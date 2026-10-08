#!/usr/bin/env python3
"""main v244 + Book Session v98 + Book Series v8 (no self-written cards) - the 8 Oct review after three Claude builds in a
row failed on old text that told the model to write a confirmation itself. Cards come only from tools (main v163-v226)
and main v238 withdraws a card no tool made, so each of these was a dead end. Found by scripts/audit-model-text (new).

main v244 (on v243):
  - Prompt, Rescheduling: steps 1 and 3 told the model to find the booking first and to "Show the booking and the new
    time, end that message with the line `Confirm to move. (yes/no)`". Now: call Move Booking (it finds the booking,
    near titles too since Move v26, and before the yes returns the move card, sent automatically). Step 4 stays (fallback).
  - Cancel Booking / Move Booking tool descriptions: the yes is to the card from Prepare Cancel / Move Booking, not to
    "a message ending with the line ...".
  - Guard Probe: a markdown heading ("## Heading") becomes bold - Slack shows "##" as it is, and the prompt itself is
    written with # headings, which Claude tends to copy.
Book Session v98: NOT_CONFIRMED said "Present the complete booking summary now, end it with the line "Confirm to book.""
  -> call Prepare Booking and stop; MISSING_DETAILS and TITLE_INITIALS said "present the summary again" -> call Prepare
  Booking again.
Book Series v8: NOT_CONFIRMED said "Present the full list of dates, end with the line "Confirm to book."" -> call Prepare
  Series and stop.
  scripts/build-v244.py <main-v243> <main-out> <book-v97> <book-out> <series-v7> <series-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

def main(w):
    w["name"] = "Project Jessie — v244 (no self-written cards)"
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]
    sm = ag["systemMessage"]
    sm = once(sm, "1. Find the booking. If several match, list them with times and ask which.\n",
              "1. When they name the booking - its title or project - you don't need to find it first: Move Booking finds it, near titles too. If they don't say which booking, ask.\n", "resched 1")
    sm = once(sm, "3. Show the booking and the new time, end that message with the line `Confirm to move. (yes/no)` on its own, and stop.\n",
              "3. Call Move Booking with the title as they gave it (or as it was shown), the date it is on now, and the new start and end (and room, if changing). Before their yes it changes nothing: it checks the booking and returns the move card, which is sent to the requester automatically. Reply with one short line such as \"Here it is.\" and stop. Never write a move confirmation yourself.\n", "resched 3")
    ag["systemMessage"] = sm
    cb = node(w, "Cancel Booking")["parameters"]
    cb["description"] = once(cb["description"], 'or if they have not yet replied yes to a message from you that ended with the line "Confirm to cancel. (yes/no)".',
                             "or if they have not yet replied yes to the cancel card from Prepare Cancel.", "Cancel Booking desc")
    mb = node(w, "Move Booking")["parameters"]
    mb["description"] = once(mb["description"], 'or if they have not replied yes to a message ending with the line "Confirm to move. (yes/no)".',
                             "or if they have not replied yes yet - then it changes nothing and returns the move card, which is sent to the requester automatically.", "Move Booking desc")
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"], "text = text.replace(/\\*{2,}/g, '*');\n",
        "// v244: a markdown heading (\"## Heading\") is bold in Slack, which shows \"##\" as it is. The prompt is written with # headings and\n"
        "// Claude copies the style. Before the ** collapse, so \"## *Title*\" does not become **Title**.\n"
        "text = text.replace(/^[ \\t]*#{1,6}[ \\t]+(.+?)[ \\t]*#*[ \\t]*$/gm, (w, t) => '*' + t.replace(/^\\*+|\\*+$/g, '') + '*');\n"
        "text = text.replace(/\\*{2,}/g, '*');\n", "headings")
    return w

def book(w):
    w["name"] = "Jessie — Book Session — v98 (no self-written cards)"
    cc = node(w, "Check Conflicts")["parameters"]
    s = cc["jsCode"]
    s = once(s, "human:'Nothing was booked, because the requester has not approved this booking yet. '\n        + 'Present the complete booking summary now, end it with the line \"Confirm to book.\", '\n        + 'and stop. Book it only after they reply approving it. Do not call this tool again '\n        + 'in this response.' } }];",
             "human:'Nothing was booked, because the requester has not approved this booking yet. '\n        + 'Call Prepare Booking with the booking details now and stop - its summary is sent to them automatically, '\n        + 'for their yes. Never write a summary yourself. Do not call this tool again '\n        + 'in this response.' } }];", "NOT_CONFIRMED")
    s = once(s, ". Ask the requester for what is missing, then present the summary again.' } }];",
             ". Ask the requester for what is missing, then call Prepare Booking again.' } }];", "MISSING_DETAILS")
    s = once(s, "and present the summary again.' } }];", "and call Prepare Booking again.' } }];", "TITLE_INITIALS")
    cc["jsCode"] = s
    return w

def series(w):
    w["name"] = "Jessie — Book Series — v8 (no self-written cards)"
    ag = node(w, "Aggregate")["parameters"]
    ag["jsCode"] = once(ag["jsCode"], "human: 'This series is not approved yet. Present the full list of dates, end with the line \"Confirm to book.\", and stop - then book only after they reply yes.'",
                        "human: 'This series is not approved yet. Call Prepare Series with the same pattern and booking details and stop - its card is sent to the requester automatically, for their yes. Never write the dates or a summary yourself.'", "series NOT_CONFIRMED")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 6: print(__doc__.strip()); sys.exit(2)
    for f, src, out in ((main, a[0], a[1]), (book, a[2], a[3]), (series, a[4], a[5])):
        json.dump(f(json.load(open(src))), open(out, "w"), indent=2, ensure_ascii=False); print("wrote", out)
