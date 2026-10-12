#!/usr/bin/env python3
"""Book Session v108 + Move Booking v29 - from the 12 Oct 13:24-13:28 Slack round on batch 2.

  - "client is anj" (13:28) still booked as "QATEST4 / Anj / HL": Client Aliases (the clients whose Notes say "goes by") is
    read only for an on-behalf booking ("(for ...)"), so v107's check had no client aliases to compare. Offline it passed
    because the sim fed the alias in directly.
  - "move QATEST3 tomorrow to 3-5pm" (13:27): the move card offered 3-5 PM although Studio 7 is booked 3-6 PM - Move Booking
    builds the card before it reads the new window (long-standing); the yes was then refused with v28's free times.
Book Session v108: Client Aliases is read for every booking being prepared that names a client (or is on-behalf).
Move Booking v29: before the yes, the new window is checked too - Resolve Booking hands the card on (preview_card) and Check
  New Window returns it only when the new time is free; taken -> ROOM_OCCUPIED with the room's nearest free times (v28).
  When the requester's session outranks the one in the way, Decide Preempt hands the card back instead of opening a
  request, so the priority request still happens at the yes, as before.

  scripts/build-v108-v29.py <book-v107> <book-out> <move-v28> <move-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
CA_OLD = "  if (String(R.mode || '').trim().toLowerCase() !== 'prepare' || !/\\(for\\s+[^)]+\\)/i.test(String(R.description || ''))) { return 'FALSE()'; }"
CA_NEW = ("  // v108 (live 12 Oct 13:28, \"client is anj\"): also for any booking being prepared that names a client - v107 asks when the\n"
          "  // client given is both a client's nickname and a staff member's\n"
          "  var _cl = String(R.client || '').trim() || (String(R.summary || '').split(' / ').length >= 3 ? String(R.summary).split(' / ')[1].trim() : '');\n"
          "  if (String(R.mode || '').trim().toLowerCase() !== 'prepare' || (!/\\(for\\s+[^)]+\\)/i.test(String(R.description || '')) && !_cl)) { return 'FALSE()'; }")
RB_OLD = """  return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED', title, card_text: card,
    human: 'Nothing was moved yet. The move card is sent to the requester automatically - do not write one. When they reply yes, '
         + 'call Move Booking again with exactly the same title, booking date and new times.' } }];
}"""
RB_NEW = """  // v29 (live 12 Oct 13:27): the card waits for the new window to be checked (Check New Window hands it back when free)
  var __previewCard = card;
}"""
RB2_OLD = """  notify, bookerRef, bookerName, engInitials, engFilter, roomNote } }];"""
RB2_NEW = """  notify, bookerRef, bookerName, engInitials, engFilter, roomNote,
  preview_card: typeof __previewCard === 'string' ? __previewCard : '' } }];   // v29"""
CNW_OLD = "return [{ json: Object.assign({}, R, { verdict:'CLEAR' }) }];"
CNW_NEW = """// v29: before the yes, a free new time gives the move card; nothing is moved yet
if (R.preview_card) return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED', title: R.title, card_text: R.preview_card,
  human: 'Nothing was moved yet. The move card is sent to the requester automatically - do not write one. When they reply yes, '
       + 'call Move Booking again with exactly the same title, booking date and new times.' } }];
return [{ json: Object.assign({}, R, { verdict:'CLEAR' }) }];"""
DP_OLD = "return [{ json:{ offer:true, reason:'OUTRANKS', open:open } }];"
DP_NEW = """// v29: before the yes, an outranking move still gets its card - the request to the incumbent is opened at the yes, as before
if (R.preview_card) return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED', title: R.title, card_text: R.preview_card, offer:false,
  human: 'Nothing was moved yet. The move card is sent to the requester automatically - do not write one. When they reply yes, '
       + 'call Move Booking again with exactly the same title, booking date and new times.' } }];
return [{ json:{ offer:true, reason:'OUTRANKS', open:open } }];"""
def book(w):
    w["name"] = "Jessie — Book Session — v108 (client aliases read)"
    n = node(w, "Client Aliases")["parameters"]; n["filterByFormula"] = once(n["filterByFormula"], CA_OLD, CA_NEW, "aliases"); return w
def move(w):
    w["name"] = "Jessie — Move Booking — v29 (new time checked before the card)"
    r = node(w, "Resolve Booking")["parameters"]; c = once(r["jsCode"], RB_OLD, RB_NEW, "card"); r["jsCode"] = once(c, RB2_OLD, RB2_NEW, "clear")
    k = node(w, "Check New Window")["parameters"]; k["jsCode"] = once(k["jsCode"], CNW_OLD, CNW_NEW, "cnw")
    d = node(w, "Decide Preempt")["parameters"]; d["jsCode"] = once(d["jsCode"], DP_OLD, DP_NEW, "preempt")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(move(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
