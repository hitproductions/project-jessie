#!/usr/bin/env python3
"""Cancel Booking v24 + Move Booking v26 (near title on the card) - found on main v243 (Haiku), 8 Oct 20:03: "cancel QATEST on
december 14 2027" -> Prepare Cancel(title "QATEST") -> REJECTED AMBIGUOUS_TITLE, whose text told the model to "Show the
requester the booking you mean ... (end with "Confirm to cancel. (yes/no)")" - an instruction from before Prepare Cancel
existed. Haiku did exactly that, and main v238 rightly withdrew the self-written card (twice). Move Booking had the same text.

Now, only when a card is being prepared (Cancel: prepare mode; Move: not yet confirmed): ONE booking that date whose title
is a near or partial match of the one given is the booking - the card shows its full real title, and the yes is carried out
on that exact title (unchanged, strict). Several near matches: "Ask exactly this: "Which booking do you mean? ..."", and the
cancel / move is prepared again with the title they pick. Never "end with Confirm to ...".
  scripts/build-near-title.py <cancel-v23> <cancel-out> <move-v25> <move-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

def cancel(w):
    w["name"] = "Jessie — Cancel Booking — v24 (near title on the card)"
    co = node(w, "Check Ownership")["parameters"]; s = co["jsCode"]
    a = s.index("    if (cands.length) {\n    return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_TITLE',\n      human: 'Nothing was cancelled - no booking on that date is titled exactly")
    end_marker = "Only after they reply yes, call Cancel Booking again with that exact title.' } }];\n  }"
    b = s.index(end_marker, a) + len(end_marker)
    new = ("    // v24 (8 Oct, Haiku): \"cancel QATEST\" for \"QATEST / Jem Lim / HL\" was refused here and the model was told to write its own\n"
           "    // confirmation. Preparing a card, ONE near match is the booking: the card shows its full title, and the yes cancels\n"
           "    // exactly that title (the confirmed path below stays exact). Several: one question, word for word.\n"
           "    if (cands.length === 1 && prepareMode) { ev = cands[0]; how = 'near title'; }\n"
           "    else if (cands.length) {\n"
           "      const _q = 'Which booking do you mean?\\n' + cands.map(e => '- ' + e.summary + ' ' + when(e)).join('\\n');\n"
           "      return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_TITLE',\n"
           "        human: 'Nothing was cancelled - no booking on that date is titled exactly \"' + wantedTitle + '\". Ask exactly this, in one message: \"' + _q.replace(/\"/g, '\\\\\"') + '\" Then prepare the cancel again with the title they pick.' } }];\n"
           "    }")
    s = s[:a] + new + s[b:]
    s = once(s, "+ '\\nAsk the requester which one they mean, then call Cancel Booking again with that exact title.' } }];",
             "+ '\\nAsk the requester which one they mean, then prepare the cancel again with that exact title.' } }];", "hits>1")
    s = once(s, "+ '\\nIf one of them is the booking, call Cancel Booking again with that title exactly. If none of them is, '",
             "+ '\\nIf one of them is the booking, prepare the cancel again with that title exactly. If none of them is, '", "not on calendar")
    if "Confirm to cancel. (yes/no)\\\")" in s or 'end with "Confirm to cancel' in s: raise SystemExit("old confirm instruction still there")
    co["jsCode"] = s
    return w

def move(w):
    w["name"] = "Jessie — Move Booking — v26 (near title on the card)"
    rb = node(w, "Resolve Booking")["parameters"]; s = rb["jsCode"]
    old_start = "    if (cands.length) return bad('AMBIGUOUS_TITLE',\n      'Nothing was moved - no booking on that date is titled exactly"
    a = s.index(old_start)
    end_marker = "Only after they reply yes, call Move Booking again with that exact title.');"
    b = s.index(end_marker, a) + len(end_marker)
    new = ("    // v26 (8 Oct, Haiku): as Cancel Booking v24 - before the yes, ONE near match is the booking and its card shows the full\n"
           "    // title (Move Direct moves exactly that title at the yes); several: one question, word for word.\n"
           "    if (cands.length === 1 && !confirmed) { ev = cands[0]; how = 'near title'; }\n"
           "    else if (cands.length) {\n"
           "      const _q = 'Which booking do you mean?\\n' + cands.map(e => '- ' + e.summary + ' ' + when(e)).join('\\n');\n"
           "      return bad('AMBIGUOUS_TITLE', 'Nothing was moved - no booking on that date is titled exactly \"' + wantedTitle + '\". Ask exactly this, in one message: \"' + _q.replace(/\"/g, '\\\\\"') + '\" Then call Move Booking again with the title they pick.');\n"
           "    }")
    s = s[:a] + new + s[b:]
    if 'end with "Confirm to move' in s: raise SystemExit("old confirm instruction still there")
    rb["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(cancel(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(move(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
