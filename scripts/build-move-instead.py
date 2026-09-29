#!/usr/bin/env python3
"""Live QA 29 Sep ~13:59 PHT (v185): "Booked." then "make that 3pm instead" - Booked For recognised the change (3-5 PM)
and told the model to call Move Booking, but the model called Prepare Booking anyway (a prompt instruction, ignored).
Enforced now:
  scripts/build-move-instead.py <main-pull> <main-out> <book-pull> <book-out>
main  Prepare Booking gets a new input, move_instead: the booking just made and the new times, whenever Booked For has
      a change to it. More change words: "make that", "change it", "how about", "can we do", "let's do".
book  Check Conflicts, prepare mode: with move_instead set, nothing is prepared (MOVE_INSTEAD) and the model is told to
      call Move Booking for that booking, with its title, date and the new times. Move's own confirmation follows, and
      v185 makes the yes use the worked-out times.
"""
import json, sys, copy
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

MI = ("={{ (() => { const b = ($('Booked For').first().json || {}); if (!b.changeJustBooked || !b.justBooked) return ''; "
      "return JSON.stringify({ title: b.justBooked.title || '', iso: b.justBooked.iso || '', date: b.justBooked.date || '', "
      "time: b.justBooked.time || '', room: b.justBooked.room || '', start: b.moveStart || '', end: b.moveEnd || '' }); })() }}")
CH_OLD = "const CHANGE = /\\b(actually|instead|make it|change|move|push|shift|extend|shorten|earlier|later|until|till|reschedule|switch)\\b/i;"
CH_NEW = "const CHANGE = /\\b(actually|instead|make it|make that|make this|change|move|push|shift|extend|shorten|earlier|later|until|till|reschedule|switch|how about|can we do|could we do|let'?s do)\\b/i;"

def main_fix(w):
    w["name"] = "Project Jessie — v186 (move instead)"
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], CH_OLD, CH_NEW, "change words")
    wi = node(w, "Prepare Booking")["parameters"]["workflowInputs"]
    wi["value"]["move_instead"] = MI
    tmpl = next(x for x in wi["schema"] if x["id"] == "requester_text")
    e = copy.deepcopy(tmpl); e["id"] = "move_instead"; e["displayName"] = "move_instead"; wi["schema"].append(e)
    return w

BS_OLD = "if (__prep && !__series) {\n  const _named = String(REQ.expected_date || '')"
BS_NEW = """// v62 (live QA 29 Sep): a change right after a booking is a move of that booking. Booked For worked it out and main
// passes it as move_instead; told only in the prompt, the model still prepared a second booking.
if (__prep && String(REQ.move_instead || '').trim()) {
  let _mi = {}; try { _mi = JSON.parse(String(REQ.move_instead)); } catch (e) {}
  if (_mi.title) {
    const _iso = t => _mi.iso && t ? _mi.iso + 'T' + t + ':00+08:00' : '';
    return [{ json: { verdict:'REJECTED', reason:'MOVE_INSTEAD', move: _mi,
      human: 'Nothing was prepared - this is a change to the booking just made, "' + _mi.title + '" (' + [_mi.date, _mi.time, _mi.room].filter(Boolean).join(', ') + '). '
        + 'Call Move Booking for it now: title "' + _mi.title + '"' + (_mi.iso ? ', booking_date ' + _mi.iso : '')
        + (_mi.start ? ', new_start ' + _iso(_mi.start) + ', new_end ' + _iso(_mi.end) : '')
        + ', then show the requester the move and ask them to confirm it. Do not prepare a new booking.' } }];
  }
}
""" + BS_OLD

def book_fix(w):
    w["name"] = "Jessie — Book Session — v62 (move instead)"
    t = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    if not any(x.get("name") == "move_instead" for x in t): t.append({"name": "move_instead"})
    n = node(w, "Check Conflicts")["parameters"]; n["jsCode"] = sub1(n["jsCode"], BS_OLD, BS_NEW, "move instead")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(book_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
