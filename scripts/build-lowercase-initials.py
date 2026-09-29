#!/usr/bin/env python3
"""main v188 (lowercase initials fix) - live QA 29 Sep 15:45 PHT (execs 16886-16897), decided the same day: "capitals
will definitely be typed in lowercase, so let's accept".
  scripts/build-lowercase-initials.py <main-pull> <main-out>

Asked "Who is the arranger?", the requester answered "bp" (BP Valenzuela). Booked For only read initials typed in
capitals, and only after a role word ("arranger BP"), so a bare lowercase answer resolved to no one. On the next turn
the model answered '"bp" is not on the Hit Productions staff list' without calling anything - a refusal copied from
the turn before - and only the third "bp" went through.

Booked For  - initials in any case count, in a role slot ("engineer rg", "arranger bp"); a word on the stop list
              ("na", "tbd", "me" ...) never does.
            - a bare answer (up to three words) to Jessie's "Who is the arranger / engineer?" is read as that person:
              "bp", "Drey", "Brian Cua". One person = the canonical name, as for every other name.
Guard Probe - a reply saying a name "is not on the staff list" that no staff check backed this turn (no
              ENGINEER_UNKNOWN / ENGINEER_UNVERIFIED from Prepare Booking, Book Session or Book Series) is replaced
              with an honest "I didn't check that name properly - could you send it once more?".
Book Session already matches initials in any case; unchanged.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_CAPS_OLD = """      // a two- or three-letter key counts as initials only when typed in capitals ("RG"), unless it is a first name ("Tel")
      if (k === 1 && key.length <= 3 && !/^[A-Z]{2,3}$/.test(seg[0]) && ![...set].some(nm => firstOf(nm) === key)) continue;"""
BF_CAPS_NEW = """      // v188: initials count in any case ("RG", "rg") - people type them in lowercase. A stop word never does.
      if (k === 1 && key.length <= 3 && (RAWSTOP.test(seg[0]) || INISTOP.test(seg[0]))) continue;"""
BF_STOP_OLD = "  const RAWSTOP = /"
BF_STOP_NEW = "  const INISTOP = /^(me|my|us|it|you|tbc|any|all|ok|oh|so|na|nil|idk)$/i;   // v188: never read as initials\n  const RAWSTOP = /"

BF_BARE_ANCHOR = "  for (const t of mine) { const r = findRole(t, 'arranger'); if (r) { out.arranger = r.who || r.raw; out.arrangerResolved = !!r.who; out.arrangerPhrase = r.phrase; break; } }\n"
BF_BARE_NEW = BF_BARE_ANCHOR + r"""  // v188 (live QA 29 Sep): a bare answer to "Who is the arranger?" - "bp" - named no one, because nothing in it says
  // "arranger". Read the newest message as that person when Jessie's message just before it asked for one.
  try {
    const _last = String(theirs[0] || ''), _ans = String(mine[0] || '').trim().replace(/[.!?]+$/, '');
    const _q = /\bwho(?:'s|\s+is|\s+will\s+be)?\s+(?:the\s+|your\s+)?(arranger|engineer)\b/i.exec(_last);
    if (_q && _ans && _ans.split(/\s+/).length <= 3 && !/\b(no|none|wala|n\/a|tbd|tba)\b/i.test(_ans)) {
      const role = _q[1].toLowerCase();
      const r = resolveWords(_ans.split(/\s+/));
      if (r && r.who && !out[role + 'Resolved']) { out[role] = r.who; out[role + 'Resolved'] = true; out[role + 'Phrase'] = _ans; }
    }
  } catch (e) {}
"""

GP_ANCHOR = "// 29 Sep: the confirmation goes out as one line"
GP_NEW = r"""// --- v188 (live QA 29 Sep): "not on the staff list" with nothing behind it ------------------------------------------
// Answered "bp" to "Who is the arranger?", the model replied '"bp" is not on the Hit Productions staff list' without
// calling anything - copied from the turn before. Only Book Session's staff check can say that; without its refusal
// this turn, the claim is replaced.
try {
  if (!_prepared && /\bnot on (?:the |our )?(?:Hit Productions )?staff list\b/i.test(text)) {
    const _sx = (($input.first().json || {}).intermediateSteps) || [];
    const _backed = _sx.some(s => {
      const _t = String(((s || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
      if (!/^(prepare booking|book session|book series)$/.test(_t)) return false;
      let _o = null; try { _o = [].concat(JSON.parse(String((s || {}).observation || '')))[0]; } catch (e) {}
      return !!_o && /^ENGINEER_(UNKNOWN|UNVERIFIED)$/.test(String(_o.reason || ''));
    });
    if (!_backed) text = "Sorry - I didn't check that name properly. Could you send it once more?";
  }
} catch (e) {}

"""

def main_fix(w):
    w["name"] = "Project Jessie — v188 (lowercase initials fix)"
    b = node(w, "Booked For")["parameters"]
    c = sub1(b["jsCode"], BF_CAPS_OLD, BF_CAPS_NEW, "caps")
    c = sub1(c, BF_STOP_OLD, BF_STOP_NEW, "stop")
    c = sub1(c, BF_BARE_ANCHOR, BF_BARE_NEW, "bare")
    b["jsCode"] = c
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_NEW + GP_ANCHOR, "guard")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
