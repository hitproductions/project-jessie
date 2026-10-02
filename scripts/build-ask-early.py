#!/usr/bin/env python3
"""main v212 + Book Session v85 (ask date/time early, no type examples) - live 2 Oct 12:29 / decided 2 Oct:
  - The model asked "What session type is this? (e.g. Celebrity Recording, Post Mixing, VO Recording, etc.)" itself,
    so the time was not asked with it (Book Session v84 only adds it to its own questions - PENDING 77). Guard Probe now
    adds what is missing to the model's booking questions too: "And which day and time?" / "And which day?" / "And
    what time?" (was day only, v164).
  - No examples on the session-type question: the prompt no longer tells the model to offer them (it keeps the full
    list, never shown unless asked), Guard Probe words the question one way ("What kind of session is this?") and drops
    an "(e.g. ...)", and Book Session's second ask has no examples. Shorthand still registers (dubbing, vo, isr, celeb,
    atmos, loc mixing ... - Book Session v81's matcher).
  scripts/build-ask-early.py <book-live> <book-out> <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

SM_OLD = """Offer session-type examples, using exactly these — this requester's own department ({{ $('Get Booker').first().json.fields.Department }}):

{{ $('Room Table').first().json.sessionTypeHint }}

Present them as examples, not the only options. If that list is empty, or none fit, or they ask what else there is, give the full list:

{{ $('Room Table').first().json.sessionTypes }}

Use only types on the full list, spelled exactly — map informal names ("Loc Dubbing") to the exact value yourself."""
SM_NEW = """The session types - use only these, spelled exactly, and map informal names ("dubbing", "Loc Dubbing", "vo") to the exact value yourself. Ask "What kind of session is this?" with no examples; list them only if the requester asks what types there are:

{{ $('Room Table').first().json.sessionTypes }}

Pick from that list."""

GP_OLD = "  if (_asks && _booking && _noDate && _aboutBooking && !_series && !/\\b(date|day|when|which day)\\b/i.test(text)) text = text.trim() + '\\nAnd which day is it for?';"
GP_NEW = """  // v212 (live 2 Oct 12:29, PENDING 77): the time too - "And which day and time?" / "And which day?" / "And what time?"
  const _noTime = !/\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b|\\b\\d{1,2}:\\d{2}\\b|\\b(?:noon|midnight|morning|afternoon|evening|tonight|lunch|all day|whole day|half day)\\b|\\bat\\s+\\d{1,2}\\b|\\b\\d{1,2}\\s*(?:-|\\u2013|to|until|till)\\s*\\d{1,2}\\b/i.test(_rt)
    && !/\\bM[1-8]\\b/i.test(_rt);
  const _askDay = _noDate && !/\\b(date|day|when)\\b/i.test(text), _askTime = _noTime && !/\\b(time|when|hours?)\\b/i.test(text);
  if (_asks && _booking && _aboutBooking && !_series && (_askDay || _askTime))
    text = text.trim() + '\\n' + (_askDay && _askTime ? 'And which day and time?' : _askDay ? 'And which day?' : 'And what time?');"""
GP_ANCHOR = "// v164 (QA E1): \"Book Studio 7 from 2pm to 5pm\" was answered with questions about everything but the date, 3 of 3."
GP_TYPEQ = r"""// v212 (decided 2 Oct): the session-type question in one wording, with no examples - "What session type is this? (e.g.
// Celebrity Recording, Post Mixing, VO Recording, etc.)" -> "What kind of session is this?"
try {
  text = text.replace(/\bWhat(?:'s|’s| is)?\s+(?:the\s+)?(?:session type|kind of session|type of session|session)(?:\s+(?:is\s+this|for\s+this(?:\s+(?:session|booking))?))?\s*\?(?:\s*\((?:e\.g\.?|eg|for example|like|such as|ex\.?)[^)]*\))?/gi, 'What kind of session is this?')
             .replace(/(What kind of session is this\?)\s*\((?:e\.g\.?|eg|for example|like|such as|ex\.?)[^)]*\)/gi, '$1');
} catch (e) {}

""" + GP_ANCHOR

BS_OLD = """      else if (_again) { const _ex = (_pref.length ? _pref : ['VO Recording', 'Music Vocal Recording', 'Post Mixing']).slice(0, 3);
        _q = 'What kind of session is this? (e.g. ' + _ex.join(', ') + ')'; }"""
BS_NEW = """      else if (_again) _q = 'What kind of session is this?';   // v85 (decided 2 Oct): no examples"""

def book(w):
    w["name"] = "Jessie — Book Session — v85 (no type examples)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = sub1(cc["jsCode"], BS_OLD, BS_NEW, "bs examples")
    return w
ASKS_OLD = "  const _asks = /\\?\\s*$/.test(text.trim()) && !/Confirm to (book|cancel|move)\\./i.test(text);"
ASKS_NEW = "  const _asks = /\\?\\s*(?:\\(or \"none\"\\)\\s*)?$/.test(text.trim()) && !/Confirm to (book|cancel|move)\\./i.test(text);   // v212: the client question ends (or \"none\")"

def main(w):
    w["name"] = "Project Jessie — v212 (ask date/time early)"
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]; ag["systemMessage"] = sub1(ag["systemMessage"], SM_OLD, SM_NEW, "prompt")
    ag["systemMessage"] = sub1(ag["systemMessage"], 'Good: "What session type is this, who\'s the client', 'Good: "What kind of session is this, who\'s the client', "prompt good")
    gp = node(w, "Guard Probe")["parameters"]; s = gp["jsCode"]
    s = sub1(s, GP_OLD, GP_NEW, "gp day/time"); s = sub1(s, ASKS_OLD, ASKS_NEW, "gp asks"); s = sub1(s, GP_ANCHOR, GP_TYPEQ, "gp typeq"); gp["jsCode"] = s
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
