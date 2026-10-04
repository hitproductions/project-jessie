#!/usr/bin/env python3
"""main v217 + Book Session v88 + Room Availability v16 (schedule fixes) - live 4 Oct 21:14-21:48 PHT:
  1. main v217 - "sun" in a project name is not Sunday. "book vo recording for me tomorrow studio f" then "project wheat
     sun. 3-5pm" was prepared and booked for Sunday 10 Oct (exec 25540: start 2027-10-10), and the project cut to WHEAT.
     Since v215 the short day names count as days anywhere. Now a short form (mon, tue, wed, thu, thurs, fri, sat, sun
     ...) is a day only with a cue - a time after it ("thurs 11am"), or "on / this / next / by / until / for / every"
     or a number before it ("studio 8 thurs"), or at the end of a message ("can we do sat?") - and no day name inside a
     project or title ("project wheat sun.") counts unless a time follows it. Gate Context (the message and the history
     fallback) and Booked For's project reader use the same rule.
  2. Book Session v88 - the room is checked before the questions. "book celeb recording 3-4pm tomorrow studio f" was
     asked the client, the project and the arranger before the card said Studio F was booked (exec 25472). When Book
     Session asks a question and the named room is booked in that window, the question opens with it: 'Heads up:
     Studio F is booked 3:00 PM – 4:00 PM ("SMILE / Jem Lim / AEG").' Not for M booths (their standing holds go to
     consent), not without a time, and not again once said.
  3. Room Availability v16 - the layout decided 4 Oct: no blank line after "Free all day:" / "Free studios:", and
     "Studio 5 (except 12:00 PM – 3:00 PM)." (was "free except for").
  scripts/build-sched-fixes.py <main-live> <main-out> <book-live> <book-out> <ra-live> <ra-out>
"""
import json, re, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# --- main: Gate Context -----------------------------------------------------------------------------------------------
DAY_ANCHOR = "let dm;\n"
DAY_HELPER = r"""let dm;
// v217 (live 4 Oct 21:46, "project wheat sun." booked for Sunday): a short day name is a day only with a cue around it,
// and no day name inside a project or title counts unless a time follows it.
const __SHORTD = /^(?:thurs|thur|thu|tues|tue|weds|wed|mon|fri|sat|sun)$/i;
const __TIMEN = /^[\s,]*(?:\d|at\b|from\b|morning|afternoon|evening|night|noon|lunch|am\b|pm\b|all\s+day|whole\s+day)/i;
function __dayOk(text, idx, word) {
  const s = String(text || ''), before = s.slice(0, idx), after = s.slice(idx + String(word).length);
  const timeNext = __TIMEN.test(after);
  // inside "project ..." / "title is ..." up to the end of that clause
  const _sp = /\b(?:project|title)(?:\s+(?:title|name))?\s*(?:is|:|=|-)?\s+[^.,;!?\n]*$/i;
  if (_sp.test(before) && !timeNext) return false;
  if (!__SHORTD.test(String(word).trim())) return true;
  if (timeNext) return true;
  if (/(?:^|\b(?:on|this|next|by|until|till|til|for|every|each|to|or|and|do|make|move|book)|\d|,)\s*$/i.test(before)) return true;
  return /^\s*[?!.]*\s*$/.test(after);
}
"""
BARE1_OLD = "while ((dm = reBare.exec(msgText)) !== null) {\n"
BARE1_NEW = "while ((dm = reBare.exec(msgText)) !== null) {\n  if (!__dayOk(msgText, dm.index, dm[0])) continue;   // v217\n"
BARE2_OLD = "  while ((m = bare.exec(t)) !== null) {\n"
BARE2_NEW = "  while ((m = bare.exec(t)) !== null) {\n    if (!__dayOk(t, m.index, m[0])) continue;   // v217\n"

# --- main: Booked For's project reader --------------------------------------------------------------------------------
TN_OLD = "    for (const t0 of toks) {\n      const t = t0.replace(/['’]s$/i, '').replace(/[.'’-]+$/, '');"
TN_NEW = ("    for (let __i = 0; __i < toks.length; __i++) { const t0 = toks[__i];\n"
          "      if (__i > 0 && keep.length && /[.;!?]$/.test(toks[__i - 1])) break;   // v217: a full stop ends the project\n"
          "      const t = t0.replace(/['’]s$/i, '').replace(/[.'’-]+$/, '');\n"
          "      // v217 (live 4 Oct, \"project wheat sun.\" -> WHEAT): a short day name ends the project only when a time follows it\n"
          "      const __dayIn = /^(?:mon|tue|tues|wed|weds|thu|thur|thurs|fri|sat|sun)$/i.test(t) && (/[.,;!?]$/.test(t0) || !toks[__i + 1]\n"
          "        || !/^(?:\\d|at$|from$|morning|afternoon|evening|night|noon|am$|pm$)/i.test(toks[__i + 1]));")
PS_OLD = "!STOPW.test(t) && !OKNEXT.test(t) && !PSTOP.test(t)) { keep.push(t); continue; }"
PS_NEW = "!STOPW.test(t) && !OKNEXT.test(t) && (__dayIn || !PSTOP.test(t))) { keep.push(t); continue; }"

def main(w):
    w["name"] = "Project Jessie — v217 (day names in projects)"
    g = node(w, "Gate Context")["parameters"]; s = g["jsCode"]
    s = sub1(s, DAY_ANCHOR, DAY_HELPER, "gate helper"); s = sub1(s, BARE1_OLD, BARE1_NEW, "gate bare msg"); s = sub1(s, BARE2_OLD, BARE2_NEW, "gate bare hist")
    g["jsCode"] = s
    b = node(w, "Booked For")["parameters"]; s = b["jsCode"]
    s = sub1(s, TN_OLD, TN_NEW, "takeName loop"); s = sub1(s, PS_OLD, PS_NEW, "takeName pstop"); b["jsCode"] = s
    return w

# --- Book Session: the room's clash rides on the first question --------------------------------------------------------
BS_TAIL_ANCHOR = "    const _ASKS = ['NEED_SESSION_TYPE', 'NEED_DEPARTMENT', 'NEED_BOOKING_TYPE', 'NEED_CLIENT', 'NEED_ARRANGER', 'NEED_ENGINEER', 'ON_BEHALF_OR_OWN', 'CLIENT_CHECK'];\n"
def book(w):
    w["name"] = "Jessie — Book Session — v88 (room checked first)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    rooms = re.search(r"const ROOMS = \{.*?\n\};", s, re.S)
    if not rooms: raise SystemExit("ROOMS map not found")
    rmap = rooms.group(0).replace("const ROOMS = ", "const __R88 = ", 1)
    BUSY = BS_TAIL_ANCHOR + r"""    // v88 (live 4 Oct 21:31, exec 25472): the named room is checked before the questions - a clash rides on the first one.
    let _busy = '';
    try {
      if (_ASKS.indexOf(__j.reason) !== -1 && !_noDate && !_noTime && !/Heads up: \S.* is booked/.test(String(_R.asked_text || ''))) {
""" + "        " + rmap.replace("\n", "\n        ") + r"""
        const _rs = Date.parse(String(_R.start_iso || '')), _re = Date.parse(String(_R.end_iso || ''));
        const _want = _rooms.filter(r => !/^M[1-8]$/i.test(r)).map(r => Object.keys(__R88).find(k => k.toLowerCase() === r.toLowerCase())).filter(Boolean);
        if (_want.length && _rs && _re && _re > _rs) {
          const _seen = {}, _hits = [];
          for (const it of $input.all()) { const jj = (it && it.json) || {};
            for (const ev of (Array.isArray(jj.items) ? jj.items : (jj && jj.id ? [jj] : []))) {
              if (!ev || !ev.id || _seen[ev.id]) continue; _seen[ev.id] = 1;
              const _es = Date.parse((ev.start || {}).dateTime || (ev.start || {}).date || ''), _ee = Date.parse((ev.end || {}).dateTime || (ev.end || {}).date || '');
              if (!(_es < _re && _ee > _rs) || ev.transparency === 'transparent') continue;
              const _em = (ev.attendees || []).map(a => String(a.email || '').toLowerCase()), _loc = String(ev.location || '').toLowerCase();
              const _fs = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
              for (const k of _want) if (_em.indexOf(__R88[k].toLowerCase()) !== -1 || (_loc && _loc.indexOf(k.toLowerCase()) !== -1) || _fs === k.toLowerCase())
                _hits.push({ k, s: ev.summary || '(no title)', a: _es, b: _ee, all: !((ev.start || {}).dateTime) });
            } }
          if (_hits.length) {
            const _t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
            const _h = _hits[0];
            _busy = 'Heads up: ' + _h.k + ' is booked ' + (_h.all ? 'all day' : _t(_h.a) + ' – ' + _t(_h.b)) + ' (\\"' + _h.s.replace(/"/g, '') + '\\").';
          }
        }
      }
    } catch (e) {}
"""
    s = sub1(s, BS_TAIL_ANCHOR, BUSY, "book busy")
    # after every rewrite of the question, the heads-up goes in front of it
    TAIL_OLD = "    }\n  }\n} catch (e) {}\nreturn __ccResult;"
    TAIL_NEW = ("    }\n    if (_busy && __j.verdict === 'REJECTED')\n"
                "      __j.human = String(__j.human).replace(/(Ask exactly this[^\"]*\")/, (m, a) => a + _busy + ' ');   // v88\n"
                "  }\n} catch (e) {}\nreturn __ccResult;")
    s = sub1(s, TAIL_OLD, TAIL_NEW, "book tail")
    cc["jsCode"] = s
    return w

# --- Room Availability: layout ----------------------------------------------------------------------------------------
def ra(w):
    w["name"] = "Jessie — Room Availability — v16 (tighter layout)"
    ca = node(w, "Compute Availability")["parameters"]; s = ca["jsCode"]
    s = sub1(s, "if (L.length) lines.push('Free all day:', '', ...L);   // v15: a blank line after the heading",
                "if (L.length) lines.push('Free all day:', ...L);   // v16 (decided 4 Oct): no blank line after the heading", "ra heading")
    s = sub1(s, "lines.push(n + ' (free except for ' + m.map(", "lines.push(n + ' (except ' + m.map(", "ra except")   # v16: "(except ...)"
    s = sub1(s, "(_sOnly ? 'Free studios:' : 'Free rooms:') + '\\n\\n' + _lines.join('\\n')",
                "(_sOnly ? 'Free studios:' : 'Free rooms:') + '\\n' + _lines.join('\\n')", "ra studios")   # v16
    ca["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    for f, i, o in ((main, 0, 1), (book, 2, 3), (ra, 4, 5)):
        json.dump(f(json.load(open(a[i]))), open(a[o], "w"), indent=2, ensure_ascii=False); print("wrote", a[o])
