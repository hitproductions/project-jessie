#!/usr/bin/env python3
"""main v256 + Book Session v105 - from the 9 Oct 16:56-16:59 Slack round on v255 / Book Session v104.

  - "mixing, project blue bird, client is jem" (16:56): "Mixing could be Post Mixing or Music Mixing, and the client matches
    Jem Lim exactly. Which kind of mixing is this, Post or Music? And is the engineer Howard Luistro?" - a working note, the
    model's own (incomplete) list, and the engineer asked of an engineer requester. v255's question-only rule did not see
    "which kind of mixing" or an engineer question as a details question.
  - "post" (16:57): Book Session v104 asked again ("Which kind of mixing - Post Mixing, Localization Mixing, ...?") - it only
    accepted the full type name.
main v256 (Guard Probe): a question asking which kind of mixing / recording / editing / dubbing is the code's question,
  with the options from the session types (Room Table's reference data) - nothing else in the reply; a question about the
  engineer is dropped when Booked For knows the engineer; v255's question-only rule also counts the engineer.
Book Session v105: a word that narrows the generic one to a single type ("post" -> Post Mixing, "atmos" -> Localization Atmos
  Mixing) is that type - not asked again.

  scripts/build-v256.py <main-v255> <main-out> <book-v104> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
GP_OLD = r"""        const _rest = _ss.slice(0, _q0).concat(_ss.slice(_q1 + 1));"""
GP_NEW = r"""        const _rest = _ss.slice(0, _q0).concat(_ss.slice(_q1 + 1));
        // v256 (live 9 Oct 16:56): "Which kind of mixing is this, Post or Music? And is the engineer Howard Luistro?" - the
        // kind question is code's, with every type from the session types; an engineer Booked For knows is never asked
        const _kq = _qt.match(/\bwhich (?:kind|type) of (mixing|recording|editing|dubbing)\b|\b(mixing|recording|editing|dubbing) could be\b/i);
        let _kOpts = [];
        if (_kq) { try { const _RT = JSON.parse(String((($('Room Table').first() || {}).json || {}).referenceData || '{}'));
          const _g = String(_kq[1] || _kq[2]).toLowerCase();
          _kOpts = [...new Set((_RT.types || []).map(t => String(t.type || '').trim()).filter(t => new RegExp('\\b' + _g + '\\b', 'i').test(t)))];
          if (_kOpts.length >= 2) { const _a = _kOpts.length === 2 ? _kOpts.join(' or ') : _kOpts.slice(0, -1).join(', ') + ' or ' + _kOpts[_kOpts.length - 1];
            text = 'Which kind of ' + _g + ' - ' + _a + '?'; } } catch (e) {} }"""
GP_COND_OLD = r"""        if (_ni >= 1 && !/"""
GP_COND_NEW = r"""        let _qt2 = _qt;
        try { const _be2 = (($('Booked For').first() || {}).json) || {};
          if (_be2.engineerResolved && String(_be2.engineer || '').trim()) _qt2 = _qt.split(/(?<=\?)\s+/).filter(x => !/\bengineer\b/i.test(x)).join(' ').trim() || _qt; } catch (e) {}
        if (_kOpts.length >= 2) {}
        else if ((_ni >= 1 || /\bengineer\b/i.test(_qt)) && !/"""
GP_SET_OLD = r"""          text = _qt;
      } }"""
GP_SET_NEW = r"""          text = _qt2;
      } }"""
BS_OLD = r"""        if (_op.length >= 2 && _op.some(o => o.toLowerCase() === _st3))"""
BS_NEW = r"""        // v105 (live 9 Oct 16:57): a word that narrows it to one type ("post" -> Post Mixing) is that type
        const _nar = _op.filter(o => o.toLowerCase().split(/\s+/).filter(w => w !== g).some(w => new RegExp('\\b' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b').test(_rt3)));
        if (_nar.length === 1 && _nar[0].toLowerCase() === _st3) break;
        if (_op.length >= 2 && _op.some(o => o.toLowerCase() === _st3))"""
def main(w):
    w["name"] = "Project Jessie — v256 (v255 fixed)"
    gp = node(w, "Guard Probe")["parameters"]; c = gp["jsCode"]
    c = once(c, GP_OLD, GP_NEW, "kind q"); c = once(c, GP_COND_OLD, GP_COND_NEW, "cond"); c = once(c, GP_SET_OLD, GP_SET_NEW, "set")
    gp["jsCode"] = c; return w
def book(w):
    w["name"] = "Jessie — Book Session — v105 (v104 fixed)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = once(cc["jsCode"], BS_OLD, BS_NEW, "narrow"); return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
