#!/usr/bin/env python3
"""Book Session v81 (session type matching) - live 1 Oct 17:03: "mixing" fits four session types, and v80 asked the
same "What kind of session is this?" again; "celeb recording" or a typo ("mixng") would have too. Decided 1 Oct:
  1. Shortened words (5+ letters, e.g. "celeb") and near-misses (one letter for 5+, two for 8+: "mixng", "celebirty")
     match a type's words.
  2. An answer that fits several types gets the choices, the requester's department's first:
     "Which one - Post Mixing, Music Mixing, Localization Mixing or Localization Atmos Mixing?"
  3. Nothing matched, asked before: "What kind of session is this? (e.g. VO Recording, Post Mixing, Post Processing)".
  4. The requester's words name exactly one type in full and the model passed another -> the model is told that type
     (not shown to the requester).
  scripts/build-session-type-fuzzy.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
START = "// v80 (live 1 Oct 16:29, decided 1 Oct): a session type the requester's words do not name is asked, not guessed -"
END = "// v62 (live QA 29 Sep): a change right after a booking is a move of that booking."
NEW = r"""// v80 (live 1 Oct 16:29, decided 1 Oct): a session type the requester's words do not name is asked, not guessed -
// "he's recording himself" was booked as VO Recording. v81 (live 1 Oct 17:03): "mixing" fits four types and was asked
// the same question again - now the choices; shortened words and typos match ("celeb", "mixng").
if (__prep && String(REQ.session_type || '').trim() && String(REQ.requester_text || '').trim()) {
  let _RT = {}; try { _RT = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _types = (_RT.types || []).map(t => String(t.type || '').trim()).filter(Boolean);
  const _cur = _types.find(t => t.toLowerCase() === String(REQ.session_type).trim().toLowerCase());
  if (_cur) {
    const _GEN = new Set(['recording', 'session', 'sessions']);
    const _SYN = { voice: 'vo', voiceover: 'vo', vocals: 'vocal', loc: 'localization', localisation: 'localization', mixdown: 'mix', dub: 'dubbing', atmos: 'atmos', celeb: 'celebrity' };
    const _st = w => w.replace(/(?:ing|ed|es|s)$/, '').replace(/([b-df-hj-np-tv-z])\1$/, '$1');
    const _rtx = String(REQ.requester_text);
    const _ws = [...new Set(_rtx.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter(w => w.length >= 2).map(w => _SYN[w] || w))];
    const _tok = t => t.toLowerCase().split(/[^a-z0-9]+/).filter(w => w && !_GEN.has(w));
    const _ed = (a, b) => { if (Math.abs(a.length - b.length) > 2) return 9; const d = Array.from({ length: a.length + 1 }, (_, i) => [i].concat(Array(b.length).fill(0)));
      for (let j = 1; j <= b.length; j++) d[0][j] = j;
      for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) {
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1); }
      return d[a.length][b.length]; };
    const _EXACT = new Set(['meeting', 'event']);   // "let's meet the client" is not a Meeting session
    const _hit = x => _EXACT.has(x) ? _ws.some(w => w === x || w === x + 's') : _ws.some(w => w === x || _st(w) === _st(x)
      || (w.length >= 5 && x.length > w.length && x.startsWith(w))
      || (w.length >= 5 && x.length >= 5 && _ed(w, x) <= (Math.min(w.length, x.length) >= 8 ? 2 : 1)));
    const _all = _types.map(t => ({ t, k: _tok(t) }));
    const _uniq = x => _all.filter(o => o.k.indexOf(x) !== -1).length === 1;
    const _aka = T => { if (/^vo recording$/i.test(T) && /\b(?:isr|in[- ]studio recording)\b/i.test(_rtx)) return true;
      try { for (const t of (_RT.types || [])) if (String(t.type).toLowerCase() === T.toLowerCase()) for (const a of [].concat(t.aka || [])) if (a && new RegExp('\\b' + String(a).replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i').test(_rtx)) return true; } catch (e) {}
      return false; };
    const _full = o => (o.k.length && o.k.every(_hit)) || _aka(o.t);
    const _named = o => _full(o) || o.k.some(x => _hit(x) && _uniq(x));
    const _fulls = _all.filter(_full);
    const _DEPT = { 'audio post': ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording'],
      'music': ['Music Vocal Recording', 'Band Recording', 'Music Mixing'],
      'localization': ['Localization Dubbing', 'Localization Editing', 'Localization Mixing', 'Localization Atmos Mixing', 'QC'] };
    const _pref = [].concat(...(__reqDepts || []).map(d => _DEPT[d] || []));
    const _ord = a => a.slice().sort((x, y) => { const i = _pref.indexOf(x), j = _pref.indexOf(y); return (i < 0 ? 99 : i) - (j < 0 ? 99 : j); });
    const _list = a => a.length === 1 ? a[0] : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1];
    const _curO = _all.find(o => o.t === _cur);
    if (_fulls.length === 1 && _fulls[0].t !== _cur) {
      // the requester named one type in full; the model passed another
      return [{ json: { verdict:'REJECTED', reason:'SESSION_TYPE_IS', session_type: _fulls[0].t,
        human: 'Nothing was prepared. The requester named the session type: ' + _fulls[0].t + '. Call Prepare Booking again with session_type "' + _fulls[0].t + '" - do not ask them.' } }];
    }
    const _ok = _fulls.length ? (_fulls.length === 1 && _fulls[0].t === _cur) : _named(_curO);
    if (!_ok) {
      const _cand = _fulls.length > 1 ? _fulls.map(o => o.t) : _all.filter(o => o.k.some(_hit)).map(o => o.t);
      const _again = /^\s*(?:What kind of session is this\?|Which one - )/i.test(String(REQ.asked_text || ''));
      let _q;
      if (_cand.length >= 2) _q = 'Which one - ' + _list(_ord(_cand)) + '?';
      else if (_again) { const _ex = (_pref.length ? _pref : ['VO Recording', 'Music Vocal Recording', 'Post Mixing']).slice(0, 3);
        _q = 'What kind of session is this? (e.g. ' + _ex.join(', ') + ')'; }
      else _q = 'What kind of session is this?';
      return [{ json: { verdict:'REJECTED', reason:'NEED_SESSION_TYPE', guessed: _cur, options: _cand,
        human:'Nothing was prepared. Ask exactly this, in one message: "' + _q + '" Then prepare it again with the session type they name.' } }];
    }
  }
}
"""
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Book Session — v81 (session type matching)"
cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
i, j = s.index(START), s.index(END)
assert s.count(START) == 1 and i < j
cc["jsCode"] = s[:i] + NEW + s[j:]
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
