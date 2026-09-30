#!/usr/bin/env python3
"""Book Session v72 (v71 fixed) - live QA 30 Sep 15:29 PHT.
  scripts/build-self-engineer-note.py <book-live> <book-out>

"book qaself studio 7 tomorrow 2pm to 4pm, vo recording, no client, external" -> Engineer: Howard Luistro (Post
Engineer), right, but without v71's note. v71 only stepped in when the engineer slot arrived empty; the model had
already put the requester there itself (as in the QAANJ test), so the note never showed. Now the requester in the
engineer slot, when the requester never named an engineer - no name of theirs typed, no "I'll engineer", "engineer me" -
counts as the same default and gets the note.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label, n=1):
    if s.count(old) != n: raise SystemExit(f"{label}: expected {n} match(es), found {s.count(old)}")
    return s.replace(old, new)

OLD = "  if (!_e0 && !_forP && !_noEng && _me) {"
NEW = r"""  // v72 (v71 fixed, live QA 30 Sep 15:29): the model often puts the requester in itself - the same default, so the same note,
  // when the requester never named an engineer (no name of theirs typed, no "I'll engineer" / "engineer me").
  if (_e0 && !_forP && _me) {
    const _kk = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
    let _mf = null;
    try { _mf = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).find(x => _kk(x.Name) === _kk(_me)); } catch (e) {}
    if (_mf && /engineer/i.test(String(_mf.Info || '').split(/goes by/i)[0])) {
      const _gb = String(_mf.Info || '').match(/goes by\s+([^\n]*)/i);
      const _keys = [...new Set([_kk(_mf.Name), _kk(String(_mf.Name).split(/\s+/)[0]), _kk(_mf.Initials)]
        .concat(_gb ? _gb[1].split(/,|\band\b/i).map(_kk) : []).filter(a => a.length >= 2))];
      const _said = ' ' + _kk(REQ.requester_text) + ' ';
      const _isMe = _keys.indexOf(_kk(String(_e0).replace(/\s*\([^)]*\)\s*$/, ''))) !== -1;
      const _named = _keys.some(k => _said.indexOf(' ' + k + ' ') !== -1)
        || /\bengineer(?:ed)?\s*(?:is|:|=|by)?\s*me\b|\bi\s*(?:'ll|will|am|'m)\s+(?:be\s+)?(?:the\s+)?engineer(?:ing)?\b|\bme\s+as\s+(?:the\s+)?engineer\b|\bi(?:'ll| will)?\s+engineer\b/i.test(String(REQ.requester_text || ''));
      if (_isMe && !_named) __selfEngineer = String(_mf.Name).trim();
    }
  }
  if (!_e0 && !_forP && !_noEng && _me) {"""

def fix(w):
    w["name"] = "Jessie — Book Session — v72 (v71 fixed)"
    c = node(w, "Check Conflicts")["parameters"]; c["jsCode"] = sub1(c["jsCode"], OLD, NEW, "v71 block")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
