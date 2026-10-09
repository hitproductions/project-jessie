#!/usr/bin/env python3
"""main v253 + Book Session v103 + Cancel Booking v25 - from the 9 Oct 12:16-12:20 Slack round on v252, and PENDING 83.

  - "book 11-1 instead" (12:17): "I need the session type, project title, and client (if any)?" - v247 leaves alone a
    question with a bracket (it usually offers a choice), so "(if any)" stopped the rewrite and the booking was not said back.
  - "cancel M3 - Howard tomorrow" -> yes (12:19): "That booking has changed since I showed it to you" - the hold is stored
    as 12:00 AM - 12:00 AM; the card says "all day" and Check Ownership compared "12:00 AM – 12:00 AM" to it. Every M booth
    hold stored with times could not be cancelled through Jessie.
  - PENDING 83 (4 Oct): an M booth asked "What's the meeting title or what is M6 being booked for?" - an M booth hold is
    titled with the booker's first name (v84), so nothing should be asked.

main v253: "(if any)", "(optional)", "(if there is one)" are dropped from a question before v247 reads it.
Book Session v103: an M booth with no title is titled "M3 - <first name>" (the colleague it is for, else the requester)
  before the missing-details check.
Cancel Booking v25: a booking from midnight to midnight (Manila) reads as "All day", like a date-only one.

  scripts/build-v253.py <main-v252> <main-out> <book-v102> <book-out> <cancel-v24> <cancel-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
GP_OLD = "    text = text.replace(/\\s*\\((?:and\\s+)?(?:for\\s+)?how long(?: for)?\\)/gi, '');\n"
GP_NEW = GP_OLD + ("    // v253 (live 9 Oct 12:17): \"... and client (if any)?\" - a bracket that offers no choice does not stop the rewrite\n"
                   "    text = text.replace(/\\s*\\((?:if any|if there is one|if there's one|optional|if applicable)\\)/gi, '');\n")
BS_OLD = "const missing = [];\nif (!String(REQ.summary || '').trim())   missing.push('a title');"
BS_NEW = r"""// v103 (PENDING 83, 4 Oct): an M booth hold is titled with a first name (v84) - never asked for: the colleague it is for,
// else the requester
try {
  const _mb = String(REQ.rooms || '').trim().match(/^M[1-8]$/i);
  if (_mb && !String(REQ.summary || '').trim()) {
    const _fr = ((String(REQ.description || '').match(/\(for\s+([^)]+)\)/i) || [])[1] || (String(REQ.description || '').match(/booked by\s*:\s*([^|(]+)/i) || [])[1] || '').trim();
    if (_fr) REQ.summary = _mb[0].toUpperCase() + ' - ' + _fr.split(/\s+/)[0];
  }
} catch (e) {}
""" + BS_OLD
CB_OLD = "  if (!(e.start && e.start.dateTime)) return 'All day';\n"
CB_NEW = CB_OLD + ("  // v25 (live 9 Oct 12:19): a hold stored as 12:00 AM - 12:00 AM (Manila) is the \"all day\" the card showed\n"
                   "  { const _mid = x => { const d = new Date(new Date(x).getTime() + 8 * 3600000); return !isNaN(d) && d.getUTCHours() === 0 && d.getUTCMinutes() === 0; };\n"
                   "    if (_mid(s) && _mid(en) && new Date(en).getTime() > new Date(s).getTime()) return 'All day'; }\n")
def main(w):
    w["name"] = "Project Jessie — v253 (if-any question)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], GP_OLD, GP_NEW, "if any"); return w
def book(w):
    w["name"] = "Jessie — Book Session — v103 (M booth title)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = once(cc["jsCode"], BS_OLD, BS_NEW, "M booth title"); return w
def cancel(w):
    w["name"] = "Jessie — Cancel Booking — v25 (all-day holds)"
    co = node(w, "Check Ownership")["parameters"]; co["jsCode"] = once(co["jsCode"], CB_OLD, CB_NEW, "all day"); return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 6: print(__doc__.strip()); sys.exit(2)
    for f, (i, o) in zip((main, book, cancel), ((a[0], a[1]), (a[2], a[3]), (a[4], a[5]))):
        json.dump(f(json.load(open(i))), open(o, "w"), indent=2, ensure_ascii=False); print("wrote", o)
