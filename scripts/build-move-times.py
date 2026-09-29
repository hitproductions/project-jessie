#!/usr/bin/env python3
"""Live QA 29 Sep 13:53 PHT (v184): the change after "Booked." became a move, but to 3-4 PM, not 3-5. Two "make it 3pm
instead" messages were read together (two times -> no new times worked out), and the model guessed an hour.
  scripts/build-move-times.py <main-pull> <main-out>
- Booked For takes the time from the NEWEST requester message that has one.
- The Move Booking tool's new start / end use Booked For's times whenever it is a change to the booking just made
  (the model's date is kept, so "move it to tomorrow 3pm" still moves the day).
- Guard Probe: a move confirmation for that change shows exactly those times.
"""
import json, re, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF = [("          const one = [...said2.matchAll(",
       "          // v185: the newest message that has a time decides - two \"make it 3pm\" messages read together gave none\n"
       "          const _tmsg = mine.find(x => /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b/i.test(x)) || '';\n"
       "          const one = [..._tmsg.matchAll(", "tmsg"),
      ("if (tm && one.length === 1 && !/\\b\\d+(?:\\.\\d+)?\\s*(?:hours?|hrs?|mins?|minutes)\\b/i.test(said2)) {",
       "if (tm && one.length === 1 && !/\\b\\d+(?:\\.\\d+)?\\s*(?:hours?|hrs?|mins?|minutes)\\b/i.test(_tmsg)) {", "len"),
      ("extend(?:ed)?(?: it)?(?: to| until| till)?)\\b/i.test(said2);\n            if (ps && pe && v) {",
       "extend(?:ed)?(?: it)?(?: to| until| till)?)\\b/i.test(_tmsg);\n            if (ps && pe && v) {", "endword")]

BFX = "($('Booked For').first().json || {})"
MOVEWRAP = ("((b, v, isEnd) => { const t = isEnd ? b.moveEnd : b.moveStart; const d = (b.justBooked || {}).iso; "
            "if (!b.changeJustBooked || !t || !d) return v; const s = String(v || ''); "
            "const day = /^\\d{4}-\\d{2}-\\d{2}/.test(s) ? s.slice(0, 10) : d; return day + 'T' + t + ':00+08:00'; })(" + BFX + ", {CALL}, {END})")

GP_ANCHOR = "// --- v183 (QA bug 3): a tool's instruction never reaches the requester"
GP_NEW = r"""// --- v185: a move of the booking just made shows the times that will be used --------------------------------------
// The Move Booking inputs come from Booked For's times for that change; the model's confirmation text is made to match.
try {
  const _bf = (($('Booked For').first() || {}).json) || {};
  if (_bf.changeJustBooked && _bf.moveStart && _bf.moveEnd && /Move it\? Reply yes or no\.|Confirm to move\./i.test(text)) {
    const _f = x => { const h = +x.slice(0, 2); return (h % 12 || 12) + ':' + x.slice(3) + ' ' + (h < 12 ? 'AM' : 'PM'); };
    const _R = /\d{1,2}:\d{2}\s*[AP]M\s*(?:–|-|—|to)\s*\d{1,2}:\d{2}\s*[AP]M/gi;
    const _all = text.match(_R) || [];
    const _want = _f(_bf.moveStart) + ' – ' + _f(_bf.moveEnd);
    if (_all.length) { const _last = _all[_all.length - 1]; const _i = text.lastIndexOf(_last); text = text.slice(0, _i) + _want + text.slice(_i + _last.length); }
  }
} catch (e) {}

"""

def fix(w):
    w["name"] = "Project Jessie — v185 (move times)"
    b = node(w, "Booked For")["parameters"]; c = b["jsCode"]
    for old, new, label in BF: c = sub1(c, old, new, label)
    b["jsCode"] = c
    v = node(w, "Move Booking")["parameters"]["workflowInputs"]["value"]
    for k, key, isEnd in [("new_start_iso", "new_start", "false"), ("new_end_iso", "new_end", "true")]:
        e = v[k]; m = re.match(r"^=\{\{ (\$fromAI\('" + key + r"',.*'string'\)) \}\}$", e, re.S)
        if not m: raise SystemExit("move input shape " + k)
        v[k] = "={{ " + MOVEWRAP.replace("{CALL}", m.group(1)).replace("{END}", isEnd) + " }}"
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_NEW + GP_ANCHOR, "guard")
    return w

if __name__ == "__main__":
    json.dump(fix(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    print("wrote", sys.argv[2])
