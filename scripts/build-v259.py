#!/usr/bin/env python3
"""main v259 - from the 12 Oct 10:56-10:58 Slack round on v258 (the long exchange).

  "book studio 6 tomorrow" -> "What time works?" -> "2-4pm" -> 🗓️ line + session type, project, client -> "vo recording,
  project QATEST2" -> client only -> "actually make it 3-5pm" -> "Studio 6 isn't a usual VO Recording room ... or still
  Studio 6?" -> "still studio 6" -> 🗓️ 3-5 PM + client -> "no client" -> the same room question again. The model has to
  pass room_override on every Prepare Booking call after the requester said "still Studio 6"; it did once, then dropped it.
main v259: Booked For reads the answer - after Jessie's "isn't a usual ... room ... or still <room>?", a requester message
  "still <room>" / "keep <room>" / "yes <room>" / "still" sets roomOverride for the rest of this booking - and Prepare
  Booking's room_override is true when it is set, whatever the model passes.

  scripts/build-v259.py <main-v258> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
BF_ANCHOR = "  const said = [];\n"
BF = r"""  // v259 (live 12 Oct 10:58): "still studio 6" after Jessie's not-usual-room question holds for the rest of this booking -
  // the model passed room_override once and dropped it on the next call, and the question came back
  out.roomOverride = '';
  try {
    const _ask = theirs.map(x => (String(x).match(/isn['’]t a usual [^\n?]*?\bor still ((?:Studio|Booth) [0-9A-Za-z]+|M[1-8]|[A-Z][a-z]+)\?/) || [])[1]).filter(Boolean);
    if (_ask.length) {
      const _r = _ask[0], _rx = _r.replace(/\s+/g, '\\s*');
      if (mine.some(t => new RegExp('\\b(?:still|keep|stick with|go with|yes,?|just)\\s+(?:the\\s+)?' + _rx + '\\b', 'i').test(t) || /^\s*(?:still|yes,?\s+still|keep it|that'?s fine|it'?s fine)\b/i.test(t)))
        out.roomOverride = _r;
    }
  } catch (e) {}
"""
PB_OLD = "={{ $fromAI('room_override', 'True only when a previous call was refused with ROOM_UNSUITABLE or ROOM_NOT_PRIORITY and the requester has since said, in their own message, to book that room anyway. False on a first attempt and in every other case.', 'boolean', false) }}"
PB_NEW = "={{ $fromAI('room_override', 'True only when a previous call was refused with ROOM_UNSUITABLE or ROOM_NOT_PRIORITY and the requester has since said, in their own message, to book that room anyway. False on a first attempt and in every other case.', 'boolean', false) === true || !!String((($('Booked For').first() || {}).json || {}).roomOverride || '') }}"
def main(w):
    w["name"] = "Project Jessie — v259 (room answer kept)"
    bf = node(w, "Booked For")["parameters"]; bf["jsCode"] = once(bf["jsCode"], BF_ANCHOR, BF + BF_ANCHOR, "booked for")
    v = node(w, "Prepare Booking")["parameters"]["workflowInputs"]["value"]
    assert v["room_override"] == PB_OLD, "prepare input changed"
    v["room_override"] = PB_NEW
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
