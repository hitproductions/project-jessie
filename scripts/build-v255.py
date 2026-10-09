#!/usr/bin/env python3
"""main v255 + Book Session v104 - batch 1 (9 Oct): PENDING 107-112 and two small follow-ups.

main v255
  107 Gate Context: "next <day>" is that day of next week, except when today is later in the week (Mon-Sun) than the day
      named - then the coming one + 7 (decided 9 Oct: from Friday on, "next Thursday" is the Thursday after the coming one).
      "next next <day>", "<day> after next" and "the following <day>" are a week after that. Live 14:20: "next next thursday"
      matched the "next thursday" inside it, so the code used 14 Oct while the model offered 21 Oct.
  109 Guard Probe: a reply that ends in a question asking for booking details is only that question - the model's working
      notes before it ("The current request is ...", "Post Mixing is a Post Engineer session, so ...") and availability lines
      after it go; a bracket saying what is free goes too. Code then writes the restated line.
  108 The restated line: "🗓️ Studio 7 · Thursday, October 14 · 1:00 PM – 4:00 PM", a blank line, then the question.
  112 Prompt: 5.1 / Atmos questions are answered as rooms that can handle the format - never "record", never booth pairings.
  Under the heads-up, the model's "Free rooms that day: ..." is dropped like its other restatements.
Book Session v104
  110 Prepare: a session type the requester gave only as a generic word ("mixing", "recording", "editing", "dubbing") that
      several Session Types share is asked: "Which kind of mixing - Post Mixing, Music Mixing, ...?" (from reference data).
  111 A leading "project" / "proj" / "project title" is dropped from the title's first segment ("PROJECT BLUE BIRD").
  An M booth title with a nickname ("M4 - Howie") gets the staff member's first name ("M4 - Howard").

  scripts/build-v255.py <main-v254> <main-out> <book-v103> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---- Gate Context (107)
G_HELPER_OLD = "const dateLines = [];\nlet primaryDate = null;"
G_HELPER_NEW = r"""// v255 (decided 9 Oct, PENDING 107): "next <day>" is that day of next week - except when today is later in the week
// (Mon-Sun) than the day named: then it is the coming one + 7 (from Saturday, "next Thursday" is 21 Oct, not 14 Oct).
// more = 1 for "next next <day>", "<day> after next", "the following <day>".
const __nextOf = (name, more) => { const di = (dayIndex(name) + 6) % 7, ti = (today.getUTCDay() + 6) % 7;
  let d = addDays(weekMonday, 7 + di); if (ti > di) d = addDays(d, 7); return addDays(d, 7 * (more || 0)); };
""" + G_HELPER_OLD
G_MSG_OLD = r"""const reNext = new RegExp('\\bnext\\s+' + DAYRE + '\\b', 'gi');
while ((dm = reNext.exec(msgText)) !== null)
  note(dm[0], addDays(weekMonday, 7 + ((dayIndex(dm[1]) + 6) % 7)));"""
G_MSG_NEW = r"""// v255 (PENDING 107): "next next thursday", "thursday after next", "the following thursday" - a week after "next thursday"
const reNext2 = new RegExp('\\bnext\\s+next\\s+' + DAYRE + '\\b|\\b' + DAYRE + '\\s+after\\s+next\\b|\\bthe\\s+following\\s+' + DAYRE + '\\b', 'gi');
while ((dm = reNext2.exec(msgText)) !== null)
  note(dm[0], __nextOf(dm[1] || dm[2] || dm[3], 1));
const reNext = new RegExp('(?<!\\bnext\\s+)\\bnext\\s+' + DAYRE + '\\b', 'gi');
while ((dm = reNext.exec(msgText)) !== null)
  note(dm[0], __nextOf(dm[1], 0));"""
G_BARE_OLD = r"""const reBare = new RegExp('(?<!\\b(?:next|this|last|every|each)\\s)(?<!\\bnext\\s+week(?:\'s)?\\s+)\\b' + DAYRE + '\\b(?!\\s+(?:of\\s+)?next\\s+week)', 'gi');"""
G_BARE_NEW = r"""const reBare = new RegExp('(?<!\\b(?:next|this|last|every|each|following)\\s)(?<!\\bnext\\s+week(?:\'s)?\\s+)\\b' + DAYRE + '\\b(?!\\s+(?:of\\s+)?next\\s+week)(?!\\s+after\\s+next)', 'gi');   // v255: not "the following / after next\""""
G_NOTE_OLD = """  note(dm[0], target, '(the next one - if they meant the week after, that is "next ' + dm[1] + '")');"""
G_NOTE_NEW = """  note(dm[0], target, '(the coming one)');   // v255: "next <day>" is not always the week after (PENDING 107)"""
G_HIST_OLD = r"""  const nx = new RegExp('\\bnext\\s+' + DAYRE + '\\b', 'gi');
  while ((m = nx.exec(t)) !== null) add(m.index, addDays(weekMonday, 7 + ((dayIndex(m[1]) + 6) % 7)));"""
G_HIST_NEW = r"""  const nx2 = new RegExp('\\bnext\\s+next\\s+' + DAYRE + '\\b|\\b' + DAYRE + '\\s+after\\s+next\\b|\\bthe\\s+following\\s+' + DAYRE + '\\b', 'gi');   // v255
  while ((m = nx2.exec(t)) !== null) add(m.index, __nextOf(m[1] || m[2] || m[3], 1));
  const nx = new RegExp('(?<!\\bnext\\s+)\\bnext\\s+' + DAYRE + '\\b', 'gi');
  while ((m = nx.exec(t)) !== null) add(m.index, __nextOf(m[1], 0));"""
G_HBARE_OLD = r"""  const bare = new RegExp('(?<!\\b(?:next|this|last|every|each)\\s)(?<!\\bnext\\s+week(?:\'s)?\\s+)\\b' + DAYRE + '\\b(?!\\s+(?:of\\s+)?next\\s+week)', 'gi');"""
G_HBARE_NEW = r"""  const bare = new RegExp('(?<!\\b(?:next|this|last|every|each|following)\\s)(?<!\\bnext\\s+week(?:\'s)?\\s+)\\b' + DAYRE + '\\b(?!\\s+(?:of\\s+)?next\\s+week)(?!\\s+after\\s+next)', 'gi');   // v255"""

# ---- Guard Probe (109, 108, repeated free list)
GP_ER_OLD = r"""\bfree (?:all day|the rest)\b/i.test(x)"""
GP_ER_NEW = r"""\bfree (?:all day|the rest)\b|\bfree rooms?\b|\b(?:also )?free that day\b/i.test(x)"""   # v255
GP_Q_ANCHOR = r"""    if (/\?\s*$/.test(text) && text.length <= 400
"""
GP_Q = r"""    // v255 (PENDING 109, live 9 Oct 15:02 / 15:09): a reply asking for booking details is only that question. The model's
    // working notes before it ("The current request is ...", "Post Mixing is a Post Engineer session, so the department is
    // ...", "I still need ... so I'll ask") and the availability lines after it go; code says the booking back (108).
    if (!/\*(?:Client|Session Type|Date|Time|Room|Booked by|Engineer):\*/.test(text)) { const _ss = text.replace(/\s*\((?=[^)]*\b(?:free|booked|taken|available)\b)[^)]*\)/gi, '').replace(/\s*\(or ["“]none["”][^)]*\)/gi, '').replace(/\n+/g, ' ').split(/(?<=[.!?])\s+/).map(x => x.trim()).filter(Boolean);
      let _q1 = -1; for (let i = _ss.length - 1; i >= 0; i--) if (/\?$/.test(_ss[i])) { _q1 = i; break; }
      if (_q1 >= 0) {
        let _q0 = _q1; while (_q0 > 0 && /\?$/.test(_ss[_q0 - 1])) _q0--;
        const _qt = _ss.slice(_q0, _q1 + 1).join(' ');
        const _ni = [/\b(?:what|which) (?:date|day)\b|\bthe date\b/i, /\b(?:what|which) time\b|\bthe time\b|\bstart and end\b|\bwhat time\b|\btime should\b/i, /\b(?:kind|type) of session\b|\bsession type\b/i, /\bproject\b/i, /\bclient\b/i].filter(r => r.test(_qt)).length;
        const _rest = _ss.slice(0, _q0).concat(_ss.slice(_q1 + 1));
        if (_ni >= 1 && !/["“]|❌|✅|⚠️|\bnot (?:a )?usual\b|\bisn['’]t (?:a )?usual\b|\bdid you mean\b/i.test(_rest.join(' ')))
          text = _qt;
      } }
"""
GP_PRE_OLD = r"""        const _pre = _kn.time ? [_kn.room && _freeSaid === _kn.room ? '✅ ' + _kn.room + ' is free' : _kn.room, _kn.date, _kn.time].filter(Boolean).join(' · ') : '';
        text = (_pre ? _pre + '\n' : '') + "What's the " """
GP_PRE_NEW = r"""        const _pre = _kn.time ? [_kn.room, _kn.date, _kn.time].filter(Boolean).join(' · ') : '';   // v255 (108): one form
        if (_pre) _freeSaid = '';   // the 🗓️ line says it
        text = (_pre ? '🗓️ ' + _pre + '\n\n' : '') + "What's the " """
PR_51_OLD = "- *Formats come from Recording Format, not Room Type.* A question about 5.1, Atmos or stereo goes to Rooms and Studios as a recording_format."
PR_51_NEW = PR_51_OLD + (" Answer it as the rooms that can handle that format - \"Rooms that can handle 5.1: Studio 3, Studio 4, ...\" - 5.1 and Atmos are for "
                         "mixing: never say \"record\", and never mention which booths a room is paired with.")

# ---- Book Session (110, 111, nickname)
BS_ST_ANCHOR = "// --- required fields ----------------------------------------------------"
BS_ST = r"""// v104 (PENDING 110, live 9 Oct 15:09 on Haiku): "mixing" was taken as Post Mixing. A session type the requester gave only as
// a generic word that several Session Types share is asked, with the types from reference data - never picked.
if (__prep && String(REQ.requester_text || '').trim() && String(REQ.session_type || '').trim()) {
  try {
    let _R3 = {}; try { _R3 = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
    const _ty3 = [...new Set((_R3.types || []).map(t => String(t.type || '').trim()).filter(Boolean))];
    const _rt3 = String(REQ.requester_text).toLowerCase(), _st3 = String(REQ.session_type).trim().toLowerCase();
    const _and3 = a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1];
    if (_ty3.length && !_ty3.some(t => _rt3.indexOf(t.toLowerCase()) !== -1)) {
      for (const g of ['mixing', 'recording', 'editing', 'dubbing']) {
        if (!new RegExp('\\b' + g + '\\b').test(_rt3)) continue;
        const _op = _ty3.filter(t => new RegExp('\\b' + g + '\\b', 'i').test(t));
        if (_op.length >= 2 && _op.some(o => o.toLowerCase() === _st3))
          return [{ json: { verdict:'REJECTED', reason:'SESSION_TYPE_CHECK', options: _op,
            human:'Nothing was prepared. Ask exactly this, in one message: "Which kind of ' + g + ' - ' + _and3(_op) + '?" Then prepare it again with the type they pick.' } }];
      }
    }
  } catch (e) {}
}

"""
BS_NICK_OLD = "    if (_f) finalSummary = _mm[1].toUpperCase() + ' - ' + String(_f.Name).trim().split(/\\s+/)[0]; }"
BS_NICK_NEW = BS_NICK_OLD + r"""
  // v104 (live 9 Oct 12:57: "M4 - Howie"): a first name or "Goes by" alias of one staff member is written as their first name
  if (_mm && finalSummary === _mm[0]) { let _bk2 = []; try { _bk2 = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) {}
    const _k = _mm[2].trim().toLowerCase();
    const _al = _bk2.filter(f => String(f.Name).trim().split(/\s+/)[0].toLowerCase() === _k
      || ((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1] || '').split(/,|\bor\b/).map(x => x.trim().toLowerCase().replace(/\.$/, '')).indexOf(_k) !== -1);
    if (_al.length === 1) finalSummary = _mm[1].toUpperCase() + ' - ' + String(_al[0].Name).trim().split(/\s+/)[0]; }"""
BS_PROJ_ANCHOR = "// v51: the project segment of a studio title is in capitals (the title convention)"
BS_PROJ = r"""// v104 (PENDING 111, live 9 Oct 15:28: "PROJECT BLUE BIRD / Jem Lim / HL"): "project" is the requester's label, not the name
if (/ \/ /.test(finalSummary)) finalSummary = finalSummary.replace(/^\s*(?:project\s+title|project|proj\.?)\s*[:\-]?\s+(?=\S)/i, '');
"""

def main(w):
    w["name"] = "Project Jessie — v255 (next-day rule, leaks, restated line)"
    g = node(w, "Gate Context")["parameters"]; c = g["jsCode"]
    for o, n, k in [(G_HELPER_OLD, G_HELPER_NEW, "gate helper"), (G_MSG_OLD, G_MSG_NEW, "gate next"), (G_BARE_OLD, G_BARE_NEW, "gate bare"),
                    (G_NOTE_OLD, G_NOTE_NEW, "gate note"), (G_HIST_OLD, G_HIST_NEW, "gate history next"), (G_HBARE_OLD, G_HBARE_NEW, "gate history bare")]:
        c = once(c, o, n, k)
    g["jsCode"] = c
    gp = node(w, "Guard Probe")["parameters"]; c = gp["jsCode"]
    c = once(c, GP_ER_OLD, GP_ER_NEW, "free list"); c = once(c, GP_Q_ANCHOR, GP_Q + GP_Q_ANCHOR, "question only"); c = once(c, GP_PRE_OLD, GP_PRE_NEW, "restated line")
    gp["jsCode"] = c
    ag = next(x for x in w["nodes"] if x["type"].endswith(".agent")); o = ag["parameters"]["options"]
    o["systemMessage"] = once(o["systemMessage"], PR_51_OLD, PR_51_NEW, "prompt 5.1")
    return w

def book(w):
    w["name"] = "Jessie — Book Session — v104 (session kind, project label, booth names)"
    cc = node(w, "Check Conflicts")["parameters"]; c = cc["jsCode"]
    c = once(c, BS_ST_ANCHOR, BS_ST + BS_ST_ANCHOR, "session kind"); c = once(c, BS_NICK_OLD, BS_NICK_NEW, "nickname"); c = once(c, BS_PROJ_ANCHOR, BS_PROJ + BS_PROJ_ANCHOR, "project label")
    cc["jsCode"] = c
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
