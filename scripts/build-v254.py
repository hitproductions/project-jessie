#!/usr/bin/env python3
"""main v254 - from the 9 Oct 12:24-12:26 Slack round on v253 / Book Session v103 / Cancel v25.

  - "book 11-1 instead" (12:25): "Got the new time: 11:00 AM – 1:00 PM on Monday, October 11 in Studio 8. What's the
    session type, project title, and client?" - right, but model-written: v247 leaves a reply with a clock time alone.
  - "book m6 on tuesday" (12:26): the heads-up said "M6 is already booked 12:00 AM – 12:00 AM" for an all-day hold stored
    with times (Early Room Result; Cancel v25 had the same mismatch).
  - "m4 then" (12:26): "M4 is free that day (checked), and M Booths are booked straight away once I have the owner. The owner
    name is still missing, so I need to ask for it. Who is the booking owner ...?" - internal reasoning, and the owner asked:
    the prompt listed "Booking Owner" as needed (Book Session v103 already titles an M booth with the requester's name).
main v254:
  1. Guard Probe: a sentence restating the time Booked For has ("Got the new time: 11:00 AM – 1:00 PM ...") is dropped
     before the details question is read, so code says the booking back.
  2. Early Room Result: an event from midnight to midnight (Manila) is "all day".
  3. Prompt (M Booths): the Booking Owner is the requester unless they name someone else - never asked.
  4. Guard Probe leak filter: "booked straight away", "is still missing", "so I need to ask", "once I have the ...".

  scripts/build-v254.py <main-v253> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
RS_ANCHOR = "    // v250 (live 9 Oct 11:39): \"... and who's the client? The engineer is Howard Luistro, so I'll use that.\""
RS = r"""    // v254 (live 9 Oct 12:25): "Got the new time: 11:00 AM – 1:00 PM on Monday, October 11 in Studio 8. What's ...?" - the
    // model's own statement of the time Booked For has goes, so the question is read and code says the booking back
    try { const _bt = (($('Booked For').first() || {}).json) || {};
      if (/^\d{2}:\d{2}$/.test(String(_bt.timeStart || '')) && /\?\s*$/.test(text)) {
        const _hp = x => { const h = +x.slice(0, 2), m = x.slice(3); return new RegExp('\\b' + (h % 12 || 12) + (m === '00' ? '(?::00)?' : ':' + m) + '\\s*' + (h < 12 ? 'a\\.?m\\b' : 'p\\.?m\\b|' + (h % 12 || 12) + '(?::00)?\\s*nn\\b'), 'i'); };
        const _sp = _hp(_bt.timeStart);
        const _ss = text.split(/(?<=[.!])\s+/);
        if (_ss.length > 1) text = _ss.filter((x, i) => i === _ss.length - 1 || /\?\s*$/.test(x) || !_sp.test(x)).join(' ').trim();
      } } catch (e) {}
"""
LEAK_OLD = "|\\bwhich is expected for\\b/i;"
LEAK_NEW = "|\\bwhich is expected for\\b|\\bbooked straight away\\b|\\bis still missing\\b|\\bso I need to ask\\b|\\bonce I have the (?:owner|details|date|time)\\b/i;   // v254: + 12:26"
ER_OLD = "      const evs = [].concat(a0.events || []);\n"
ER_NEW = ER_OLD + ("      // v254 (live 9 Oct 12:26): \"M6 is already booked 12:00 AM – 12:00 AM\" - a hold from midnight to midnight is all day\n"
                   "      { const _mid = x => { const d = new Date(Date.parse(x) + 8 * 3600000); return !isNaN(d) && d.getUTCHours() === 0 && d.getUTCMinutes() === 0; };\n"
                   "        evs.forEach(e => { if (!e.allDay && _mid(e.start) && _mid(e.end) && Date.parse(e.end) > Date.parse(e.start)) e.allDay = true; }); }\n")
PR_OLD = "Need: Booking Owner and the date; time optional. Title: `M5 - <Owner>`."
PR_NEW = "Need: the date; time optional. The Booking Owner is the requester unless they name someone else - never ask for it. Title: `M5 - <Owner's first name>`."
def main(w):
    w["name"] = "Project Jessie — v254 (restated time, all-day holds, M booth owner)"
    gp = node(w, "Guard Probe")["parameters"]; c = gp["jsCode"]
    c = once(c, RS_ANCHOR, RS + RS_ANCHOR, "restated time"); c = once(c, LEAK_OLD, LEAK_NEW, "leak"); gp["jsCode"] = c
    er = node(w, "Early Room Result")["parameters"]; er["jsCode"] = once(er["jsCode"], ER_OLD, ER_NEW, "all day")
    ag = next(x for x in w["nodes"] if x["type"].endswith(".agent")); o = ag["parameters"]["options"]
    o["systemMessage"] = once(o["systemMessage"], PR_OLD, PR_NEW, "prompt owner")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
