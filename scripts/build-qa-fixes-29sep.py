#!/usr/bin/env python3
"""QA bugs from the 28-29 Sep live runs (docs/qa/qa-live-2026-09-28-night.md, docs/handoff-tara-2026-09-29.md), built
from fresh pulls:
  scripts/build-qa-fixes-29sep.py <main-pull> <main-out> <book-pull> <book-out> <cancel-pull> <cancel-out>

12  "Book 2pm to 4pm" then "actually make it 3pm instead" became 3-4 PM ("Assuming 1 hour"). A single new clock time
    after a range is a CHANGE: "make it 3pm" / "push it to 3pm" moves the start and keeps the length (3-5 PM); "until
    5pm" / "extend it to 5pm" moves the end. main: Booked For reads it (the earlier range from the requester's messages,
    else Jessie's last summary's Time line), the booking tools use those times while that message is the newest one
    (timeForced), and Gate Context no longer flags a start-time-only request when Jessie's last message has a range.
3   A tool's instruction reached the requester ("Suggest one of those instead of Studio 7. If they say to go ahead with
    what they asked for, book it."). Book Session v60's two refusals now say it as an instruction about "the
    requester" and name the tool; main's Guard Probe drops any sentence that mentions "the requester", a tool name or
    room_override - no real reply to a user contains them - so leaks nobody has seen yet are caught too.
A   Asked to cancel someone else's standing hold, the model wrote its own cancel card (from Find Booking), and the
    refusal came only at the yes. Cancel Booking v19: an unconfirmed call is treated as Prepare Cancel - ownership is
    checked first (NOT_YOURS at once), else the code-written card with its check code. main's Guard Probe shows a card
    from Cancel Booking exactly as it shows Prepare Cancel's.
B   That model-written card showed "Event ID: jmuq10se..." to the user. Guard Probe drops any "Event ID:" line.
19  A series summary labelled December Tuesdays "(Mon)" (dates written without a year). 14: series summaries had no
    "Booked by". Guard Probe replaces a series summary's date list with one written from Expand Series' own dates
    (weekday and year computed) and adds the Booked by line when missing.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ================================================================ main
GATE_OLD = "else if (timeHits.length === 1) { store[soKey] = { epoch: epoch, day: todayStamp }; }"
GATE_NEW = ("// 29 Sep (QA N2): \"actually make it 3pm instead\" after a 2-4 PM summary is a change to a booking that has a length,\n"
            "// not a start time on its own - flagging it made the model assume one hour (3-4 PM).\n"
            "else if (timeHits.length === 1 && /\\*?Time:\\*?\\s*\\d{1,2}:\\d{2}\\s*[AP]M\\s*[–-]\\s*\\d{1,2}:\\d{2}\\s*[AP]M/i.test(lastBotText)) { delete store[soKey]; }\n"
            "else if (timeHits.length === 1) { store[soKey] = { epoch: epoch, day: todayStamp }; }")

BF_OLD = """      if (s && e && s < e) { out.timeStart = s; out.timeEnd = e; out.timePhrase = m[0].trim(); }
    }
    break;
  }"""
BF_NEW = """      if (s && e && s < e) { out.timeStart = s; out.timeEnd = e; out.timePhrase = m[0].trim(); }
    } else {
      // 29 Sep (QA N2): one clock time after a range is a change. "make it 3pm" / "push it to 3pm" moves the start and
      // keeps the length; "until 5pm" / "extend it to 5pm" moves the end. The range is the requester's earlier one,
      // else the Time line of Jessie's last summary. A stated length ("for 3 hours") is left to the model.
      const _one = [...t.matchAll(/\\b(\\d{1,2})(?::(\\d{2}))?\\s*(am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b/gi)];
      const _len = /\\b\\d+(?:\\.\\d+)?\\s*(?:hours?|hrs?|mins?|minutes)\\b/i.test(t);
      if (_one.length === 1 && !_len) {
        let ps = '', pe = '';
        for (const o of mine.slice(mine.indexOf(t) + 1)) {
          const r = o.match(RANGE);
          if (r && (r[3] || r[6])) { let a = hm(r[1], r[2], r[3] || r[6]), b = hm(r[4], r[5], r[6] || r[3]);
            if (!r[3] && a && b && a >= b) a = hm(r[1], r[2], String(r[6]).toLowerCase().startsWith('p') ? 'am' : 'pm');
            if (a && b && a < b) { ps = a; pe = b; } break; }
        }
        if (!ps) { const bm = String(out.botText || '').match(/\\*?Time:\\*?\\s*(\\d{1,2}):(\\d{2})\\s*([AP]M)\\s*[–-]\\s*(\\d{1,2}):(\\d{2})\\s*([AP]M)/i);
          if (bm) { ps = hm(bm[1], bm[2], bm[3]); pe = hm(bm[4], bm[5], bm[6]); } }
        const v = hm(_one[0][1], _one[0][2], _one[0][3]);
        if (ps && pe && ps < pe && v) {
          const mins = x => +x.slice(0, 2) * 60 + +x.slice(3), fmt = x => String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0');
          const f12 = x => { const h = +x.slice(0, 2), mm = x.slice(3); return (h % 12 || 12) + ':' + mm + ' ' + (h < 12 ? 'AM' : 'PM'); };
          const endWord = /\\b(?:until|till|til|up to|to end|end(?:s|ing)?(?: at)?|finish(?:es|ing)?(?: at)?|extend(?:ed)?(?: it)?(?: to| until| till)?)\\b/i.test(t);
          if (endWord) { if (mins(v) > mins(ps)) { out.timeStart = ps; out.timeEnd = v; } }
          else { const e2 = mins(v) + (mins(pe) - mins(ps)); if (e2 <= 23 * 60 + 59) { out.timeStart = v; out.timeEnd = fmt(e2); } }
          if (out.timeStart) {
            out.timeChange = true; out.timeForced = (t === mine[0]);
            out.timePhrase = f12(out.timeStart) + ' to ' + f12(out.timeEnd) + (endWord ? ' (they changed the end)' : ' (they moved the start; same length as before)');
          }
        }
      }
    }
    break;
  }"""

FORCE = [("[].concat(b.timesMentioned || []).includes(m[2] + ':' + m[3]) ? v :",
          "(!b.timeForced && [].concat(b.timesMentioned || []).includes(m[2] + ':' + m[3])) ? v :"),
         ("[].concat(b.timesMentioned || []).includes(m[1].padStart(2, '0') + ':' + m[2]) ? v :",
          "(!b.timeForced && [].concat(b.timesMentioned || []).includes(m[1].padStart(2, '0') + ':' + m[2])) ? v :")]

GP_CARD_OLD = "    if (_t !== 'prepare cancel') continue;"
GP_CARD_NEW = "    if (_t !== 'prepare cancel' && _t !== 'cancel booking') continue;   // v183: Cancel Booking unconfirmed = Prepare Cancel"

GP_ANCHOR = "// 29 Sep: the confirmation goes out as one line"
GP_NEW = r"""// --- v183 (QA bugs 19, 14): a series summary's dates come from Expand Series, and it says who booked ----------------
// The model wrote the dates: December Tuesdays came out "(Mon)", and there was no Booked by line. When Expand Series
// answered this turn, its own dates replace the model's list (weekday and year computed here).
try {
  if (!_prepared && steps && /(Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i.test(text)) {
    let _occ = null;
    for (let i = steps.length - 1; i >= 0; i--) {
      const _t = String(((steps[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
      if (_t !== 'expand series') continue;
      let _o = null; try { _o = [].concat(JSON.parse(String((steps[i] || {}).observation || '')))[0]; } catch (e) {}
      if (_o && _o.status === 'OK' && Array.isArray(_o.occurrences) && _o.occurrences.length) _occ = _o.occurrences;
      break;
    }
    if (_occ) {
      const _M = ['January','February','March','April','May','June','July','August','September','October','November','December'];
      const _W = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
      const _line = o => { const d = String(o.start_iso || '').slice(0, 10); const dt = new Date(Date.parse(d + 'T00:00:00Z'));
        return '- ' + _W[dt.getUTCDay()] + ', ' + dt.getUTCDate() + ' ' + _M[dt.getUTCMonth()] + ' ' + dt.getUTCFullYear(); };
      const _DATE = /^\s*(?:[-•*]\s*)?(?:\*?(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\*?,?\s*)?(?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,?\s*\d{4})?\s*(?:\((?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\))?\s*$/i;
      const _HDR = /^\s*\*?(?:dates?|occurrences?|sessions?)\*?\s*:\*?\s*/i;
      const _out = []; let _at = -1;
      for (const l of text.split('\n')) {
        if (_DATE.test(l) || (_HDR.test(l) && (!l.replace(_HDR, '').trim() || /\d/.test(l)))) { if (_at === -1) _at = _out.length; continue; }
        _out.push(l);
      }
      if (_at === -1) { const ti = _out.findIndex(l => /^\*[^*]+\*\s*$/.test(l.trim())); _at = ti === -1 ? 0 : ti + 1; }
      _out.splice(_at, 0, '*Dates (' + _occ.length + '):*', ..._occ.map(_line));
      text = _out.join('\n');
      if (!/Booked by:/i.test(text)) {
        const _me = String(((($('Get Booker').first() || {}).json || {}).fields || {}).Name || '').trim();
        const _for = String(((($('Booked For').first() || {}).json) || {}).bookedFor || '').trim();
        if (_me) text = text.replace(/\n*(Reply only with "yes"[^\n]*\n\s*Confirm to book\.|Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i,
          m => '\n*Booked by:* ' + _me + (_for ? ' (for ' + _for + ')' : '') + '\n\n' + m.trim());
      }
    }
  }
} catch (e) {}

// --- v183 (QA bug 3): a tool's instruction never reaches the requester ------------------------------------------------
// "Suggest one of those instead of Studio 7. If they say to go ahead with what they asked for, book it." was pasted into
// a reply. Every instruction a tool gives the model names "the requester" or a tool; no real reply to a user does, so
// any such sentence is dropped. Prepared summaries and cards are written by code and left alone.
if (!_prepared) {
  const _RQ = /\bthe requester\b|\bIf they say to go ahead\b|\bSuggest (?:one of )?(?:those|these) instead of\b/i;
  const _TL = /\b(?:room_override|Prepare Booking|Prepare Cancel|Book Session|Cancel Booking|Move Booking|Room Availability|Find Booking|Expand Series|Book Series|Book Direct|Cancel Direct)\b|\b(?:Prepare|Book|Cancel|Move|Find|Expand)_[A-Z][a-z]+\b/;
  text = text.replace(/\bSuggest these instead:/g, 'The usual rooms for it are:')
    .split('\n').map(l => (_RQ.test(l) || _TL.test(l)) ? l.split(/(?<=[.!?])\s+/).filter(p => !_RQ.test(p) && !_TL.test(p)).join(' ') : l)
    .join('\n').replace(/\n{3,}/g, '\n\n').trim();
  // QA bug B: an "Event ID:" line reached the requester on a model-written cancel card.
  text = text.replace(/^[ \t]*[-•]?[ \t]*\*?Event ID:\*?[^\n]*(?:\n|$)/gim, '').trim();
}

"""

def main_fix(w):
    w["name"] = "Project Jessie — v183 (QA bug fixes)"
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GATE_OLD, GATE_NEW, "12 gate")
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF_OLD, BF_NEW, "12 booked for")
    for tool, fields in [("Prepare Booking", ["start_iso", "end_iso"]), ("Book Session", ["start_iso", "end_iso"]), ("Book Series", ["time_start", "time_end"])]:
        v = node(w, tool)["parameters"]["workflowInputs"]["value"]
        for f in fields:
            hit = 0
            for old, new in FORCE:
                if v[f].count(old) == 1: v[f] = v[f].replace(old, new); hit += 1
            if hit != 1: raise SystemExit(f"12 force {tool}.{f}: {hit} patterns matched")
    gp = node(w, "Guard Probe")["parameters"]
    c = sub1(gp["jsCode"], GP_CARD_OLD, GP_CARD_NEW, "A card")
    c = sub1(c, GP_ANCHOR, GP_NEW + GP_ANCHOR, "3/B/19/14 guard")
    gp["jsCode"] = c
    return w

# ================================================================ Book Session
BS = [
 (""" + '. Nothing was booked. Suggest these instead: '
             + priorityNames.join(', ')
             + '. If they say to go ahead with what they asked for, book it.' } }];""",
  """ + '. Nothing was booked. The usual rooms for it are: '
             + priorityNames.join(', ')
             + '. Ask the requester whether they want one of those or still want ' + notRun.join(', ')
             + '; if they still want it, call Prepare Booking again with room_override true.' } }];""", "3 unsuitable"),
 (""" + ' free at that time. Suggest one of those instead of ' + askedLastResort.join(', ')
             + '. If they say to go ahead with what they asked for, book it.' } }];""",
  """ + ' free at that time. Ask the requester whether they want one of those or still want ' + askedLastResort.join(', ')
             + '; if they still want it, call Prepare Booking again with room_override true.' } }];""", "3 not priority"),
]
def book_fix(w):
    w["name"] = "Jessie — Book Session — v60 (instruction leak)"
    n = node(w, "Check Conflicts")["parameters"]; c = n["jsCode"]
    for old, new, label in BS: c = sub1(c, old, new, label)
    n["jsCode"] = c
    return w

# ================================================================ Cancel Booking
CX = [
 ("const prepareMode = String(REQ.mode || '').toLowerCase() === 'prepare';",
  "let prepareMode = String(REQ.mode || '').toLowerCase() === 'prepare';", "A let"),
 ("""if (!confirmed && !prepareMode) {
  return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED',
    human:'Nothing was cancelled. Show the requester the booking you found, end that message with the line "Confirm to cancel. (yes/no)", and stop. Cancel it only after they reply yes.' } }];
}""",
  """// v19 (29 Sep QA): an unconfirmed call used to answer NOT_CONFIRMED and tell the model to show the booking itself - so it
// wrote its own card (with a raw Event ID) for a booking the requester could not cancel, and the refusal came only at
// the yes. Now it is Prepare Cancel: the booking is found, ownership is checked first, then the code-written card.
if (!confirmed && !prepareMode) prepareMode = true;""", "A prepare"),
]
def cancel_fix(w):
    w["name"] = "Jessie — Cancel Booking — v19 (cancel card fix)"
    n = node(w, "Check Ownership")["parameters"]; c = n["jsCode"]
    for old, new, label in CX: c = sub1(c, old, new, label)
    n["jsCode"] = c
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(book_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    json.dump(cancel_fix(json.load(open(a[4]))), open(a[5], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3], a[5])
