#!/usr/bin/env python3
"""main v241: length changes after "Booked." + prompt tidy (Tara's Slack tests on Haiku, 8 Oct; PENDING 98).

  scripts/build-v241.py <main-v240.json> <main-v241.json>

Code (Booked For)
  A length with no clock time right after "Booked." / "Moved" - "actually make it 2 hours", "1.5 hrs", "an hour
  longer" - now gives the new times (start kept; "longer / more / extra / extend by" adds to the end). Before, only
  a clock time did: on 8 Oct (Haiku) "actually make it 2 hours" got "Reply yes to book it." and then "I haven't
  booked anything yet" with the booking on the calendar. With the times worked out, Guard Probe (v185) writes them
  into the move card and Move Direct carries out the yes, as for "make it 3pm".

Prompt
  1. A change before the yes means a new card from Prepare Booking - never "the summary above still stands" (8 Oct:
     "no wait, keep 7" after a Studio 8 card got exactly that, with no card for Studio 7).
  2. Rescheduling: a change right after "Booked." / "Moved" is a move of that booking - never "not booked yet".
  3. "Look up before booking" renamed "What Prepare Booking checks"; Rooms & Studios only for questions (it
     contradicted "Nothing needs looking up first" and invited extra Airtable calls).
  4. The broken `Avoid:```` line in Tone removed.
  5. "Book Session refuses it" dropped (not true with room_override); the hardcoded "Studio 1-6 / Studio 7" for
     Localization Dubbing replaced by the ranking.
  Rescheduling step 4 ("On yes, call Move Booking") stays: it is the fallback when Move Direct cannot read the card.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_ANCHOR = "          const f12 = x => { const h = +x.slice(0, 2); return (h % 12 || 12) + ':' + x.slice(3) + ' ' + (h < 12 ? 'AM' : 'PM'); };\n          out.moveStart = ns; out.moveEnd = ne;\n"
BF_NEW = r"""          // v241 length (8 Oct, Haiku): a new length with no clock time - "actually make it 2 hours", "1.5 hrs",
          // "an hour longer" - keeps the start ("longer / more / extra / extend by / add" adds to the end). Only the newest
          // message counts. Before, only a clock time gave times, and "make it 2 hours" was answered "Reply yes to book it",
          // then "I haven't booked anything yet" with the booking on the calendar.
          if (!ns && tm) {
            const _lm = String(mine[0] || '').toLowerCase();
            if (!/\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.|nn|noon)\b/.test(_lm)) {
              const _W = { a: 1, an: 1, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8 };
              let _len = null;
              if (/\b(?:an?|one) hour and a half\b|\b1\.5\s*(?:hours?|hrs?|h)\b|\b90\s*(?:minutes?|mins?)\b/.test(_lm)) _len = 90;
              else if (/\bhalf an hour\b/.test(_lm)) _len = 30;
              else {
                const _d = _lm.match(/\b(\d+(?:\.\d+)?|an?|one|two|three|four|five|six|seven|eight)\s*-?\s*(hours?|hrs?|h|minutes?|mins?)\b/);
                if (_d) { const _n = _W[_d[1]] !== undefined ? _W[_d[1]] : parseFloat(_d[1]); _len = /^h/.test(_d[2]) ? Math.round(_n * 60) : Math.round(_n); }
              }
              const _ps = hm(tm[1], tm[2], tm[3]), _pe = hm(tm[4], tm[5], tm[6]);
              const _mins = x => +x.slice(0, 2) * 60 + +x.slice(3), _fmt = x => String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0');
              if (_len && _len >= 15 && _len <= 12 * 60 && _ps && _pe) {
                const _add = /\b(?:longer|more|extra|another|add(?:ed)?|extend(?:ed)?(?: it)? by)\b/.test(_lm);
                const _e = _add ? _mins(_pe) + _len : _mins(_ps) + _len;
                if (_e <= 23 * 60 + 59 && _e > _mins(_ps)) { ns = _ps; ne = _fmt(_e); }
              }
            }
          }
"""

P = [
    ("*A clarifying answer is not approval.*",
     "*A change before the yes means a new card.* When they change any detail of a summary they have not approved yet - "
     "including changing it back to what it was - call Prepare Booking again with the full corrected details and send "
     "only its card. Never say an earlier summary \"still stands\": their yes approves the last card on screen.\n\n"
     "*A clarifying answer is not approval.*", "1 change before yes"),
    ("*Move Booking does the whole move in one call* — you don't delete or book anything.\n",
     "*Move Booking does the whole move in one call* — you don't delete or book anything.\n\n"
     "*A change right after \"Booked.\" or \"Moved\" is a move of that booking* - a new time, a new length (\"make it 2 "
     "hours\") or a new room. A notice above says so: follow it. Never say it has not been booked, never ask them to book "
     "it again, and never call Prepare Booking or Book Session for it.\n", "2 change after booked"),
    ("## Look up before booking\n", "## What Prepare Booking checks\n", "3 heading"),
    ("see *Client* under *Look up before booking*", "see *Client* under *What Prepare Booking checks*", "3 cross-ref"),
    ("*Rooms & Studios* — only once the requester names a room: confirm its Size Category, vocal-booth flag and Equipment from the tool, never from this prompt. Don't call it just to get an example room name.",
     "*Rooms & Studios* — Prepare Booking checks a named room itself. Call the Rooms and Studios tool only to answer a "
     "question about a room (its size, booth, equipment or formats), never just to get an example room name.", "3 rooms"),
    ("Avoid:```\n\nAvoid: ", "Avoid: ", "4 tone"),
    ("Never offer a room in neither list — Book Session refuses it.", "Never offer a room in neither list.", "5 refuses"),
    ("The studio is normally one of Studio 1–6, with Studio 7 as a last resort (the booth still applies).",
     "Take the studio from the ranking above (the booth still applies).", "5 rooms"),
]

def apply(w):
    w["name"] = "Project Jessie — v241 (length change + prompt tidy)"
    bf = node(w, "Booked For"); bf["parameters"]["jsCode"] = sub1(bf["parameters"]["jsCode"], BF_ANCHOR, BF_NEW + BF_ANCHOR, "booked for")
    a = node(w, "Jessie AI Agent")["parameters"]["options"]; s = a["systemMessage"]
    for old, new, label in P: s = sub1(s, old, new, label)
    a["systemMessage"] = s
    return w

if __name__ == "__main__":
    w = apply(json.load(open(sys.argv[1]))); json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    print("wrote", sys.argv[2], len(w["nodes"]), "nodes")
