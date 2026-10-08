#!/usr/bin/env python3
"""main v247 + Book Session v99 (brevity) - 8 Oct, after the Haiku 5.5 rounds: replies the model writes itself came out
longer than on Flash Lite. Every code-written reply from the Gemini build still applies (cards, results, "already booked",
heads-ups, Book Session's word-for-word questions); this moves the long model-written ones into code or trims them.

main v247 (on v246):
  1. A "no" to a card is answered in code (Prepared Cancel -> Already Done Reply, the "already booked" path):
     book / series: "No problem - nothing was booked. What would you like to change?"; cancel: "Okay - it stays booked.";
     move: "Okay - it stays where it is." Before: "Understood, the booking won't go ahead. Nothing was created. What would
     you like changed on the QATEST2 session, or should I leave it there?"
  2. Guard Probe brevity pass (never on a card, a code reply or Room Availability's layout): drops filler openers ("Got it",
     "Understood", "Sure", ...), recaps ("You asked for 2:00 to 3:00 PM earlier, so ...", "Studio 8 it is.") and "let me
     know" closers; a question asking for two or more booking details becomes one fixed question - "What's the session
     type, project and client? (or "none" for no client)". Left alone when it carries times, room states, options or
     anything outside that set (department, booking type, which conference room).
  3. Prompt: a length rule - one or two short sentences, no opener, no recap, no closer.
Book Session v99 (on v98): ROOM_NOT_PRIORITY was an instruction the model reworded at length ("VO Recording isn't normally
  run in Studio 3. The usual rooms are ... Do you want one of those, or still Studio 3?"); it is now "Ask exactly this" -
  "Studio 3 isn't a usual VO Recording room - Studio 7 and Studio 8 are free then. One of those, or still Studio 3?" - which
  Guard Probe (v203) sends word for word.
  scripts/build-v247.py <main-v246> <main-out> <book-v98> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

DECLINE = r"""  // v247 (brevity): a "no" to a card is answered here, in code - the model wrote "Understood, the booking won't go ahead.
  // Nothing was created. What would you like changed on the QATEST2 session, or should I leave it there?"
  if (g2.saidNo === true && !d.use && _waits) {
    if (/Cancel it\? Reply yes or no\.\s*$|Confirm to cancel\./i.test(bt)) done = 'Okay - it stays booked.';
    else if (/Move it\? Reply yes or no\.\s*$|Confirm to move\./i.test(bt)) done = 'Okay - it stays where it is.';
    else done = 'No problem - nothing was booked. What would you like to change?';
  }
"""

BREVITY = r"""// --- v247 (brevity, 8 Oct): replies short. Haiku writes longer than Flash Lite did. Never on a card, a code-written reply or
// Room Availability's layout: drops filler openers, recaps and "let me know" closers, and a question asking for two or more
// booking details becomes one fixed question.
try {
  if (!_prepared && !_codeCard && !/\*Date:\*|\*Dates|\*Moving to:\*|\*Now:\*|Book it\?|Cancel it\?|Move it\?|Confirm to|🗓️|^\s*(?:❌|✅)/.test(text)) {
    const _FILL = /^\s*(?:(?:got it|understood|sure(?: thing)?|alright|all right|great|perfect|noted|of course|absolutely|certainly)\b[,.!:]*\s*(?:[-–—]\s*)?)+/i;
    const _drop = x => /^(?:You (?:asked|said|wanted|mentioned|requested)\b[^?]*[.!]$|(?:Just )?let me know\b|Feel free\b|Happy to help\b|I(?:'|’)m happy to help\b|Hope (?:that|this) helps\b)/i.test(x.trim())
      || /^\S+(?:\s+\S+){0,3}\s+it is[.!]$/i.test(x.trim());
    const _hadFill = _FILL.test(text);
    let _t = text.replace(_FILL, '');
    _t = _t.split('\n').map(l => /^\s*(?:[*_•-]|❌|✅|⚠️|Heads up)/.test(l) ? l : l.split(/(?<=[.!?])\s+/).filter(x => !_drop(x)).join(' ')).join('\n').replace(/\n{3,}/g, '\n\n').trim();
    if (_t) text = _hadFill ? _t.replace(/^[a-z]/, c => c.toUpperCase()) : _t;
    if (/\?\s*$/.test(text) && text.length <= 400
        && !/department|booking type|arranger|internal|external|personal|likha|katha|salin|\(|\bfree\b|\btaken\b|\bbooked\b|\d{1,2}(?::\d{2})?\s*(?:am|pm)\b/i.test(text)) {
      const _it = [];
      if (/\b(?:what|which) (?:date|day)\b/i.test(text)) _it.push('date');
      if (/\b(?:what|which) time\b|\bstart and end\b|\bday and time\b/i.test(text)) _it.push('time');
      if (/\bhow long\b/i.test(text)) _it.push('length');
      if (/\bwhich (?:room|studio)\b/i.test(text)) _it.push('room');
      if (/\b(?:kind|type) of session\b|\bsession type\b/i.test(text)) _it.push('session type');
      if (/\bproject\b/i.test(text)) _it.push('project');
      if (/\bclient\b/i.test(text)) _it.push('client');
      if (/\bengineer\b/i.test(text)) _it.push('engineer');
      if (_it.length >= 2) {
        const _j = _it.length === 2 ? _it.join(' and ') : _it.slice(0, -1).join(', ') + ' and ' + _it[_it.length - 1];
        text = "What's the " + _j + '?' + (_it.indexOf('client') !== -1 ? ' (or "none" for no client)' : '');
      }
    }
  }
} catch (e) {}

"""

LENGTH = ("*Length.* Keep every reply to one or two short sentences. No opener (\"Got it\", \"Understood\", \"Sure\"), no recap of what "
          "they said, no \"let me know\" closer. When details are missing, ask for all of them in one short question.\n\n")

def main(w):
    w["name"] = "Project Jessie — v247 (brevity)"
    pc = node(w, "Prepared Cancel")["parameters"]
    pc["jsCode"] = once(pc["jsCode"], "} catch (e) { done = ''; }\nreturn [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d, _alreadyDone: done }) }];",
                        DECLINE + "} catch (e) { done = ''; }\nreturn [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d, _alreadyDone: done }) }];", "decline")
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"], "// --- v238 (card guard): a card no tool made never goes out", BREVITY + "// --- v238 (card guard): a card no tool made never goes out", "brevity")
    o = node(w, "Jessie AI Agent")["parameters"]["options"]
    o["systemMessage"] = once(o["systemMessage"], "says that someone approved an exception, or keeps asking.\n\n",
                              "says that someone approved an exception, or keeps asking.\n\n" + LENGTH, "length rule")
    return w

def book(w):
    w["name"] = "Jessie — Book Session — v99 (brevity)"
    cc = node(w, "Check Conflicts")["parameters"]
    cc["jsCode"] = once(cc["jsCode"],
        "        human: 'Nothing was booked. ' + freePriority.join(', ') + ' would normally be used for '\n"
        "             + ((stRec ? stRec.type : '') || 'this session type') + ' and ' + (freePriority.length > 1 ? 'are' : 'is')\n"
        "             + ' free at that time. Ask the requester whether they want one of those or still want ' + askedLastResort.join(', ')\n"
        "             + '; if they still want it, call Prepare Booking again with room_override true.' } }];",
        "        // v99 (brevity): one short question, sent word for word (was an instruction the model reworded at length)\n"
        "        human: 'Nothing was booked. Ask exactly this, in one message: \"' + (askedLastResort.join(' and ') + ' isn\\'t a usual '\n"
        "             + ((stRec ? stRec.type : '') || 'this session type') + ' room - '\n"
        "             + (a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1])(freePriority)\n"
        "             + (freePriority.length > 1 ? ' are' : ' is') + ' free then. One of those, or still ' + askedLastResort.join(' and ') + '?').replace(/\"/g, '\\\\\"')\n"
        "             + '\" If they still want it, call Prepare Booking again with room_override true.' } }];", "ROOM_NOT_PRIORITY")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
