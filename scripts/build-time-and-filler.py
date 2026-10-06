#!/usr/bin/env python3
"""main v222 + Book Session v92 (time not in project, filler not a client) - live 6 Oct 14:35-14:37 PHT on main v221 /
Book Session v91:
  "book studio 7 for oct 8" -> "mixing session. project dinos 10-12pm" -> "post mix" -> "Who's the client?" -> "that will be
  all" -> card "DINOS 10-12PM / That Will Be All / HL".
  1. Booked For's project reader (takeName) keeps a token that starts with a capital or a DIGIT ("SEASON 2"), so "10-12pm"
     ran on into the project. A time is now where a name stops: "2pm", "10-12pm", "10:30", "10 - 12pm", "10 to 12pm",
     "noon"; and a date like "10/8". A bare number on its own still counts ("TOP 10", "SEASON 2").
  2. A reply to the client question made only of filler words ("that will be all", "ok thanks", "nothing else", "idk") was
     read as the client (main v219's bare answer), and Book Session keeps a client the requester typed. Neither takes one
     now: the client is asked again.
  Book Session v92 also strips a time left on the end of the title's project ("DINOS 10-12PM" -> "DINOS") as a backstop.
  scripts/build-time-and-filler.py <book-v91> <book-out> <main-v221> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# words that never make a client name on their own (English + Taglish fillers)
FILL = r"/^(?:that|thats|that's|that'll|thatll|this|it|its|it's|will|would|could|should|be|is|are|was|all|ok|okay|okey|k|kk|thanks|thank|thx|ty|you|nothing|else|done|good|fine|great|cool|yes|yeah|yep|yup|no|nope|nah|skip|none|na|n\/a|idk|dunno|not|sure|maybe|later|tbd|tba|the|a|an|for|now|just|only|i|me|we|us|don't|dont|do|know|have|has|any|there|so|wait|hmm|of|course|go|ahead|po|lang|lng|yun|yan|ito|wala|sige|oo|opo|ewan|ko|pa|muna|basta|anything|whatever|nevermind|never|mind|everything|set|ready|same|as|before)$/i"

# ---------------------------------------------------------------- main: Booked For
TN_OLD = """      if (__i > 0 && keep.length && /[.;!?]$/.test(toks[__i - 1])) break;   // v217: a full stop ends the project
"""
TN_NEW = """      if (__i > 0 && keep.length && /[.;!?]$/.test(toks[__i - 1])) break;   // v217: a full stop ends the project
      // v222 (live 6 Oct 14:36, "project dinos 10-12pm" -> DINOS 10-12PM): a time or a date ends a name. A bare number
      // still counts ("SEASON 2", "TOP 10") unless a range or am/pm follows it ("10 - 12pm", "10 to 12pm", "10 pm").
      { const _tc = t0.replace(/[.,;!?]+$/, ''), _nx = String(toks[__i + 1] || '');
        const _TIME = /^@?(?:\\d{1,2}(?::\\d{2})?(?:am|pm|nn|a\\.m|p\\.m)|\\d{1,2}(?::\\d{2})?(?:am|pm|nn)?[-–—]\\d{0,2}(?::\\d{2})?(?:am|pm|nn)?|\\d{1,2}:\\d{2}|\\d{1,2}\\/\\d{1,2}(?:\\/\\d{2,4})?|noon|midnight)$/i;
        if (_TIME.test(_tc) || (/^\\d{1,2}(?::\\d{2})?$/.test(_tc) && /^(?:[-–—]|to|till|til|until|am|pm|nn|a\\.m\\.?|p\\.m\\.?)$|^[-–—]\\d/i.test(_nx))) break; }
"""
BA_OLD = """    if (!out.client && /^Who[’']s the client\\? \\(or "none"\\)$/.test(_lastQ) && _ans && _ans.split(/\\s+/).length <= 5 && !NOCLIENT.test(_ans)"""
BA_NEW = """    const _FILL = """ + FILL + """;   // v222 (live 6 Oct 14:37): "that will be all" is not a client
    const _filler = _ans.toLowerCase().replace(/[^a-z0-9'’\\/ ]+/g, ' ').split(/\\s+/).filter(Boolean).every(w => _FILL.test(w.replace(/’/g, "'")));
    if (!out.client && /^Who[’']s the client\\? \\(or "none"\\)$/.test(_lastQ) && _ans && _ans.split(/\\s+/).length <= 5 && !NOCLIENT.test(_ans) && !_filler"""

PL_OLD = """    const p = m ? takeName(m[1].replace(/["”]+$/, ''), true) : '';"""
PL_NEW = """    // v222: the pattern stops at ":", "/" or " - ", so "dinos 10:30-12" / "dinos 10 - 12pm" / "dinos 10/8" arrive as "dinos 10" -
    // a bare number there is the start of a time or date, not part of the name
    let _m1 = m ? m[1].replace(/["”]+$/, '') : '';
    if (m && /(?:^|\\s)\\d{1,2}$/.test(_m1) && /^(?::\\d{2}|\\/\\d|\\s*[-–—]\\s*\\d|\\s+(?:to|till|til|until)\\s+\\d|\\s*(?:am|pm|nn)\\b)/i.test(t.slice(m.index + m[0].length)))
      _m1 = _m1.replace(/\\s*\\d{1,2}$/, '');
    const p = m ? takeName(_m1, true) : '';"""
def main(w):
    w["name"] = "Project Jessie — v222 (time not in project)"
    bf = node(w, "Booked For")["parameters"]; s = bf["jsCode"]
    s = sub1(s, PL_OLD, PL_NEW, "project loop")
    s = sub1(s, TN_OLD, TN_NEW, "takeName"); s = sub1(s, BA_OLD, BA_NEW, "bare answer"); bf["jsCode"] = s
    return w

# ---------------------------------------------------------------- Book Session: Check Conflicts
BS_ANCHOR = "// v89 (live 6 Oct 13:32-13:33): the client is asked with the first questions"
BS_BLOCK = r"""// v92 (live 6 Oct 14:36-14:37): "DINOS 10-12PM / That Will Be All / HL". A time left on the end of the title's project is
// taken off (Booked For v222 stops the project at a time; this is the backstop), and a client made only of filler words
// ("that will be all", "ok thanks", "idk") is not a client - it is asked again.
if (__prep) {
  const _sg = String(REQ.summary || '').split(' / ');
  if (_sg.length >= 2) {
    const _p0 = _sg[0];
    const _p1 = _p0.replace(/(?:\s+(?:@|at|from)?\s*\d{1,2}(?::\d{2})?\s*(?:am|pm|nn)?\s*(?:-|–|—|to)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm|nn)|\s+(?:@|at|from)?\s*\d{1,2}(?::\d{2})?\s*(?:am|pm|nn))+\s*$/i, '').trim();
    if (_p1 && _p1 !== _p0.trim()) { _sg[0] = _p1; REQ.summary = _sg.join(' / '); }
  }
  const _FILL = """ + FILL + r""";
  const _t3 = String(REQ.summary || '').split(' / ').map(s => s.trim());
  const _c3 = String(REQ.client || '').trim() || (_t3.length >= 3 ? _t3[1] : '');
  const _w3 = _c3.toLowerCase().replace(/[^a-z0-9'’\/ ]+/g, ' ').split(/\s+/).filter(Boolean);
  if (_w3.length && _w3.every(x => _FILL.test(x.replace(/’/g, "'")))) {
    REQ.client = '';
    if (_t3.length >= 3 && _t3[1].toLowerCase() === _c3.toLowerCase()) REQ.summary = [_t3[0], _t3[_t3.length - 1]].join(' / ');
  }
}
"""

def book(w):
    w["name"] = "Jessie — Book Session — v92 (time not in project)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = sub1(cc["jsCode"], BS_ANCHOR, BS_BLOCK + BS_ANCHOR, "bs block")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
