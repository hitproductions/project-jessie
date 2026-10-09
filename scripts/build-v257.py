#!/usr/bin/env python3
"""main v257 (v256 fixed) - from the 9 Oct 17:08 Slack round on v256.

  "book studio 7 next thurs 1-4pm, mixing, project blue bird, client is jem" -> "I need the session type confirmed first: the
  request says "mixing", so is this Music Mixing, Post Mixing, or a Localization mix?" - model-written: v256 recognised only
  "which kind of mixing" / "mixing could be", and the quoted "mixing" stops v255's question-only rule.
main v257 (Guard Probe): a reply that asks which session type a generic word means - the word plus two or more of its
  session types named, or "session type" with the word - is code's question with every matching type, whatever the wording.

  scripts/build-v257.py <main-v256> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = r"""        const _kq = _qt.match(/\bwhich (?:kind|type) of (mixing|recording|editing|dubbing)\b|\b(mixing|recording|editing|dubbing) could be\b/i);
        let _kOpts = [];
        if (_kq) { try { const _RT = JSON.parse(String((($('Room Table').first() || {}).json || {}).referenceData || '{}'));
          const _g = String(_kq[1] || _kq[2]).toLowerCase();"""
NEW = r"""        // v257 (live 9 Oct 17:08: "the request says "mixing", so is this Music Mixing, Post Mixing, or a Localization mix?"):
        // any wording - the generic word with two or more of its types named, or with "session type" - is the kind question
        let _kq = _qt.match(/\bwhich (?:kind|type) of (mixing|recording|editing|dubbing)\b|\b(mixing|recording|editing|dubbing) could be\b/i);
        if (!_kq) { try { const _RT0 = JSON.parse(String((($('Room Table').first() || {}).json || {}).referenceData || '{}'));
          const _all = _qt.toLowerCase();   // the question itself, never a statement before it
          for (const _w of ['mixing', 'recording', 'editing', 'dubbing']) {
            if (!new RegExp('\\b' + _w + '\\b').test(_all)) continue;
            const _ty0 = (_RT0.types || []).map(t => String(t.type || '').trim()).filter(t => new RegExp('\\b' + _w + '\\b', 'i').test(t));
            const _named = _ty0.filter(t => _all.indexOf(t.toLowerCase()) !== -1).length;
            if (_ty0.length >= 2 && (_named >= 2 || /\bsession type\b/i.test(_qt))) { _kq = [null, _w]; break; }
          } } catch (e) {} }
        let _kOpts = [];
        if (_kq) { try { const _RT = JSON.parse(String((($('Room Table').first() || {}).json || {}).referenceData || '{}'));
          const _g = String(_kq[1] || _kq[2]).toLowerCase();"""
def main(w):
    w["name"] = "Project Jessie — v257 (v256 fixed)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], OLD, NEW, "kind question"); return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
