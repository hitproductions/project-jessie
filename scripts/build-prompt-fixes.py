#!/usr/bin/env python3
"""Prompt and notice conflicts (ChatGPT review of v180, checked by hand; Tara approved 1-6, 29 Sep).

  scripts/build-prompt-fixes.py <main-pull.json> <main-out.json>

1  Gate Context cancelNotice said "your next action is one call to Cancel Booking" on any yes to a cancel marker. The
   AI only sees it when Cancel Direct declined: a card the AI wrote itself (no check code), or a Prepare Cancel card
   too old or incomplete. Both now mean a fresh Prepare Cancel card; Cancel Booking only for a confirmed list.
2  Clients tool / prompt: allow the lookup that resolves an unlabelled name (Who is who says search Clients and Bookers).
3  "You cannot call any Airtable tool without [session type]" is limited to looking things up for a booking.
4  Prepare Booking / "never write a summary yourself" is scoped to single bookings; a series goes through Expand Series.
5  List Events' end-date input no longer tells the AI to default to 2 weeks for "a general availability question".
6  "A booking a search no longer returns is gone" -> not found in what was checked; only Cancel Booking's success
   means a booking was removed.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

CN_OLD = """const cancelNotice = confirmedCancel
  ? 'THE CANCELLATION IS ALREADY APPROVED. They have just said yes to the summary you showed them. '
    + 'Your next action is one call to Cancel Booking, with the booking title and date exactly as you '
    + 'showed them. Do not search first - Cancel Booking finds the booking itself, and searching instead '
    + 'of cancelling is the one failure this notice exists to stop. Do not present that summary again '
    + 'and do not ask again. When it comes back, say what it tells you and nothing more.'
  : '';
"""
CN_NEW = """// 29 Sep (review of v180): a yes to a valid Prepare Cancel card is carried out by Cancel Direct and never reaches
// the model, so the model only sees this when that path declined - a card it wrote itself (no check code), or a
// Prepare Cancel card too old or incomplete. The old text told it to call Cancel Booking anyway.
const _cancelCard = /_check [0-9a-f]{8}_/.test(lastBotText);
const cancelNotice = !confirmedCancel ? ''
  : _cancelCard
  ? 'NOTHING HAS BEEN CANCELLED. The card they said yes to could not be carried out automatically (it is too old '
    + 'or incomplete). Call Prepare Cancel again with that booking\\'s title and date and send its new card as your '
    + 'whole reply. Do not call Cancel Booking.'
  : 'NOTHING HAS BEEN CANCELLED YET. They said yes to a cancel confirmation you wrote. If it listed several bookings '
    + 'to cancel together, call Cancel Booking for each with its raw event id from Find Booking, then say what it '
    + 'tells you. If it was one booking, call Prepare Cancel for it and send its card as your whole reply - do not '
    + 'call Cancel Booking.';
"""

P = [
    ("A booking a search no longer returns is gone — never offer it.",
     "Never offer a booking a search no longer returns — say no match was found in what was checked, not that it was "
     "deleted; only Cancel Booking's success means a booking was removed.", "6 tools are the truth"),
    ("*Wait for confirmation before creating anything.* Gather the details, then call Prepare Booking",
     "*Wait for confirmation before creating anything.* For a single booking (a studio, the Lobby or a conference "
     "room), gather the details, then call Prepare Booking", "4 scope"),
    ("never retry, rephrase or try another room.\n",
     "never retry, rephrase or try another room. A series is the exception: it goes through Expand Series and Book "
     "Series (see *Recurring bookings*), never Prepare Booking.\n", "4 series exception"),
    ("Session type goes first: it sets the room, typical duration and department, and you cannot call any Airtable tool without it.",
     "Session type goes first: it sets the room, typical duration and department, and you look nothing up for a "
     "booking without it. A question that is not a booking (which rooms do Atmos, who someone is) needs no session type.",
     "3 session type"),
    ("use the Clients tool only to answer a question about them.",
     "use the Clients tool only to answer a question about them or to check an unlabelled name (see *Never guess what "
     "role an unlabelled name holds*).", "2 prompt clients"),
]
CL_OLD = "Call this only when the requester has given a name and identified it as the client or the producer."
CL_NEW = ("Call this when the requester has named someone as the client or the producer, or to check a name whose role "
          "they did not say (search Bookers too).")
LE_OLD = " If they ask a general availability question, default to 2 weeks out."

def apply(w):
    w["name"] = "Project Jessie — v181 (prompt conflicts)"
    g = node(w, "Gate Context"); g["parameters"]["jsCode"] = sub1(g["parameters"]["jsCode"], CN_OLD, CN_NEW, "1 cancel notice")
    a = node(w, "Jessie AI Agent")["parameters"]["options"]; s = a["systemMessage"]
    for old, new, label in P: s = sub1(s, old, new, label)
    a["systemMessage"] = s
    c = node(w, "Clients")["parameters"]; c["toolDescription"] = sub1(c["toolDescription"], CL_OLD, CL_NEW, "2 clients tool")
    le = node(w, "List Events")["parameters"]; le["timeMax"] = sub1(le["timeMax"], LE_OLD, "", "5 list events")
    return w

if __name__ == "__main__":
    w = apply(json.load(open(sys.argv[1]))); json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    print("wrote", sys.argv[2], len(w["nodes"]), "nodes")
