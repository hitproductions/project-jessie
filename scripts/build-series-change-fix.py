#!/usr/bin/env python3
"""main v199 (v198 fixed) - live QA 30 Sep 16:38 PHT.
  scripts/build-series-change-fix.py <main-live> <main-out>

v198: "make it 3pm instead" after the QASER series (2 + 9 Nov) asked which date - right. Then "all": Booked For picked
2 Nov, but the model called Move Booking for 9 Nov, and Guard Probe put "_Next: ... November 9" on a 9 Nov card. At the
yes the model moved BOTH dates in one turn ("all" was in the conversation) - no second card, no second yes.
Both events ended at 3-5 PM, one copy each, so nothing was lost - but the requester approved one card and got two moves.

Now:
- The first series card is written by code for the date Booked For picked (the same format as Move Booking's card;
  Move Booking still checks ownership and clashes at the yes), with the "_Next:" lines; the model's card is replaced.
- At the yes to a series card, the model is told to move that date only, once; the next date gets its own card.
- "_Next:" lines go onto a model card only if its date is the one picked.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# Booked For: mark the date the first card is for; at a yes to a series card, say "that one only"
BF1_OLD = "            __serPick = true;"
BF1_NEW = """            __serPick = true;
            // v199: no card shown yet -> Guard Probe writes this date's card itself (the model picked another date, 30 Sep)
            if (!_card) out.seriesCardDate = _long(_now);
            // v199: a yes to a series card moves that date only - the model moved both dates on one yes (30 Sep 16:39)
            if (_card && _cur && YES_RE.test(String(mine[0] || ''))) notes.push('THE MOVE THEY JUST APPROVED IS THE CARD IN YOUR LAST MESSAGE ONLY: "'
              + _ser.title + '" on ' + _long(_cur) + '. Call Move Booking ONCE, for that date only. Do not move any other date of the series now - '
              + 'each other date gets its own card and its own yes after this one.');"""
# Guard Probe: build the first card; Next lines only on a card for the picked date
GP_OLD = """    if (Array.isArray(_bf8.seriesQueueNext) && _bf8.seriesQueueNext.length && !_moved8 && /\\*Moving to:\\*/.test(text) && /Move it\\? Reply yes or no\\.\\s*$/i.test(text) && !/_Next: /.test(text))
      text = text.replace(/\\s*Move it\\? Reply yes or no\\.\\s*$/i, '\\n' + _bf8.seriesQueueNext.join('\\n') + '\\n\\nMove it? Reply yes or no.');"""
GP_NEW = """    // v199: the first card of a series change is written here, for the date Booked For picked - the model's own card
    // was for another date (30 Sep). Same format as Move Booking's card; Move Booking checks the booking at the yes.
    const _jb8 = _bf8.justBooked || {};
    const _f12 = x => { const h = +String(x).slice(0, 2); return (h % 12 || 12) + ':' + String(x).slice(3, 5) + ' ' + (h < 12 ? 'AM' : 'PM'); };
    const _nx8 = Array.isArray(_bf8.seriesQueueNext) ? _bf8.seriesQueueNext : [];
    if (_bf8.seriesCardDate && !_moved8 && _jb8.title && _jb8.time && /^\\d{2}:\\d{2}$/.test(String(_bf8.moveStart || '')) && /^\\d{2}:\\d{2}$/.test(String(_bf8.moveEnd || ''))) {
      text = '*' + _jb8.title + '*\\n*Now:* ' + _bf8.seriesCardDate + ', ' + _jb8.time + (_jb8.room ? ', ' + _jb8.room : '')
        + '\\n*Moving to:* ' + _bf8.seriesCardDate + ', ' + _f12(_bf8.moveStart) + ' – ' + _f12(_bf8.moveEnd) + (_jb8.room ? ', ' + _jb8.room : '')
        + (_nx8.length ? '\\n' + _nx8.join('\\n') : '') + '\\n\\nMove it? Reply yes or no.';
    } else if (_nx8.length && !_moved8 && /\\*Moving to:\\*/.test(text) && /Move it\\? Reply yes or no\\.\\s*$/i.test(text) && !/_Next: /.test(text)
      && (!_bf8.seriesCardDate || String((text.match(/\\*Now:\\*\\s*([^\\n]+)/) || [])[1] || '').indexOf(_bf8.seriesCardDate) === 0))
      text = text.replace(/\\s*Move it\\? Reply yes or no\\.\\s*$/i, '\\n' + _nx8.join('\\n') + '\\n\\nMove it? Reply yes or no.');"""

def fix(w):
    w["name"] = "Project Jessie — v199 (v198 fixed)"
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF1_OLD, BF1_NEW, "bf")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_OLD, GP_NEW, "gp")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
