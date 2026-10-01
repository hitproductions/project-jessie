#!/usr/bin/env python3
"""Book Session v80 (on-behalf + session type) - live 1 Oct 16:29: "book studio 7 for joaquin, he's recording himself
for jem lim's project YELLOW" was booked YELLOW / Jem Lim / HL as VO Recording - the requester put in as the engineer,
a session type nobody said, and the on-behalf part invisible on the card. Decided 1 Oct:
  1. The card shows "For: <colleague>" on an on-behalf booking (only then - "for <name>" is on-behalf only when the name
     is in Bookers; a producer or a project never shows it).
  2. A colleague who is also a client on record (the in-house arrangers) with no other client named: asked once,
     "Booking this on behalf of Joaquin Santos, or is it Joaquin's own project?"
  3. On an on-behalf booking the requester is never the engineer by default: "himself / herself / themselves" makes
     the colleague the engineer, otherwise "Who's the engineer?" (v73's default there is gone).
  4. A session type the requester's words do not name is asked: "What kind of session is this?" A type counts as named
     when all its distinctive words appear, or one that no other type has ("vo", "vocal", "band", "dubbing",
     "meeting"); "a mix" alone is asked (several types mix).
  5. "for anj's project": the possessive hid the name from the "which Anj?" check (main's Booked For already read it
     as Angelo Villegas), so the arranger / client question was never asked (16:40).
  6. The heads-up said "longer" for a 2-hour Localization Editing (usually 4+ hours) and printed "(4 hours - )".
  scripts/build-on-behalf.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# 2 + 3a: in the v70 block, after the client pick, before "the colleague in the engineer slot"
V70_ANCHOR = "    // --- the colleague in the engineer slot ------------------------------------------------------------------------"
V70_NEW = r"""    // v80 (decided 1 Oct): a colleague who is also a client on record (the in-house arrangers) with no other client
    // named - on their behalf, or their own project? Asked once; the answer settles it.
    if (_pick !== 'client' && /arranger/i.test(_role)) {
      const _cN = String(REQ.client || '').trim() || (_t.length >= 3 ? _t[1] : '');
      const _otherClient = !!_cN && !_isS(_cN) && _k(_cN) !== _k(_staff.Name);
      const _own = /\b(?:(?:his|her|their|my)\s+own|own\s+(?:project|session|thing|track|song|album))\b/i.test(_rt);
      const _behalf = /\bon\s+(?:his|her|their)?\s*behalf\b|\bbehalf\b|\bfor\s+(?:a|the)\s+client\b/i.test(_rt);
      if (!_otherClient && _own && !_behalf) {
        REQ.client = String(_staff.Name).trim();
        if (_t.length >= 3) _t[1] = REQ.client; else if (_t.length === 2) _t.splice(1, 0, REQ.client);
        REQ.summary = _t.join(' / ');
      } else if (!_otherClient && _behalf && !_own) {
        if (_isS(_cN) || _k(_cN) === _k(_staff.Name)) { REQ.client = ''; if (_t.length >= 3) REQ.summary = [_t[0], _t[_t.length - 1]].join(' / '); }
      } else if (!_otherClient) {
        const _first = String(_staff.Name).split(/\s+/)[0];
        return [{ json: { verdict:'REJECTED', reason:'ON_BEHALF_OR_OWN', booked_for: _staff.Name,
          human:'Nothing was prepared. Ask exactly this, in one message: "Booking this on behalf of ' + _staff.Name + ', or is it ' + _first + '’s own project?"' } }];
      }
    }
    // v80 (live 1 Oct 16:29, "he's recording himself"): the colleague records / engineers it themselves.
    if (/\b(?:him|her|them)sel(?:f|ves)\b|\bthemself\b/i.test(_rt) && !/\bengineer(?:ed)?\s*(?:is|:|=|by)\s+[a-z]/i.test(_rt)) {
      REQ.engineer = String(_staff.Name).trim();
      const _s3 = String(REQ.description || '').split('|'), _i3 = _s3.findIndex(s => /^\s*engineer\s*:/i.test(s));
      if (_i3 !== -1) _s3[_i3] = ' Engineer: ' + REQ.engineer + ' '; else _s3.unshift('Engineer: ' + REQ.engineer + ' ');
      REQ.description = _s3.join('|').replace(/^\s+/, '');
      REQ.__forSelfEng = true;
    }
""" + V70_ANCHOR

# 3b: the requester default on an on-behalf booking is gone - ask instead
V73_OLD = """      // v73 (PENDING 71, 1 Oct DASHING): a requester who is an engineer engineers it - put in, not asked.
      if (__reqStaff && /engineer/i.test(__reqRole)) {
        REQ.engineer = String(__reqStaff.Name).trim(); REQ.__selfEng = true;
        const _s2 = String(REQ.description || '').split('|'); _s2.unshift('Engineer: ' + REQ.engineer + ' '); REQ.description = _s2.join('|');
      } else {"""
V73_NEW = """      // v73 (PENDING 71): a requester who is an engineer engineers it - put in, not asked. v80 (decided 1 Oct): only when
      // the name turned out to be the client (_pick 'client'); booking FOR a colleague, the engineer is asked.
      if (_pick === 'client' && __reqStaff && /engineer/i.test(__reqRole)) {
        REQ.engineer = String(__reqStaff.Name).trim(); REQ.__selfEng = true;
        const _s2 = String(REQ.description || '').split('|'); _s2.unshift('Engineer: ' + REQ.engineer + ' '); REQ.description = _s2.join('|');
      } else {"""
ENG_COND_OLD = "    if (_engIsFor && !_namedEng && (_pick === 'client' || !/engineer/i.test(_role))) {"
ENG_COND_NEW = "    if (_engIsFor && !_namedEng && !REQ.__forSelfEng && (_pick === 'client' || !/engineer/i.test(_role))) {"

# 3c: the model put the requester in itself on an on-behalf booking
AFTER517 = "if (__prep && REQ.__selfEng && !__selfEngineer && !__meNamed && __reqStaff) __selfEngineer = String(__reqStaff.Name).trim();"
AFTER517_NEW = AFTER517 + r"""
// v80: on an on-behalf booking the model's own choice of the requester as engineer is not used either - asked.
if (__prep && /\(for\s+[^)]+\)/i.test(String(REQ.description || '')) && __reqStaff && !__meNamed && !REQ.__forSelfEng) {
  const _kq = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
  const _eq = (String(REQ.engineer || '').trim() || ((String(REQ.description || '').match(/engineer\s*:\s*([^|]+)/i) || [])[1] || '')).replace(/\s*\([^)]*\)\s*$/, '').trim();
  const _gq = String(__reqStaff.Info || '').match(/goes by\s+([^\n]*)/i);
  const _mk = [...new Set([_kq(__reqStaff.Name), _kq(String(__reqStaff.Name).split(/\s+/)[0]), _kq(__reqStaff.Initials)].concat(_gq ? _gq[1].split(/,|\band\b/i).map(_kq) : []).filter(a => a.length >= 2))];
  const _sq = ' ' + _kq(REQ.requester_text) + ' ';
  const _typedMe = _mk.some(k => _sq.indexOf(' engineer ' + k + ' ') !== -1 || _sq.indexOf(' ' + k + ' engineer') !== -1);
  if (_eq && _kq(_eq) === _kq(__reqStaff.Name) && !_typedMe)
    return [{ json: { verdict:'REJECTED', reason:'NEED_ENGINEER', human:'Nothing was prepared. Ask exactly this, in one message: "Who’s the engineer?"' } }];
}"""

# 4: the session type must be one the requester named
ST_ANCHOR = "// v62 (live QA 29 Sep): a change right after a booking is a move of that booking."
ST_NEW = r"""// v80 (live 1 Oct 16:29, decided 1 Oct): a session type the requester's words do not name is asked, not guessed -
// "he's recording himself" was booked as VO Recording. Named = all its distinctive words appear, or one no other type
// has ("vo", "vocal", "band", "dubbing", "meeting"); "a mix" alone is asked (several types mix). Shorthand (ISR) counts.
if (__prep && String(REQ.session_type || '').trim() && String(REQ.requester_text || '').trim()) {
  let _RT = {}; try { _RT = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _types = (_RT.types || []).map(t => String(t.type || '').trim()).filter(Boolean);
  const _cur = _types.find(t => t.toLowerCase() === String(REQ.session_type).trim().toLowerCase());
  if (_cur) {
    const _GEN = new Set(['recording', 'session', 'sessions']);
    const _st = w => w.replace(/(?:ing|es|s)$/, '').replace(/([b-df-hj-np-tv-z])\1$/, '$1');
    const _SYN = { voice: 'vo', voiceover: 'vo', vocals: 'vocal', loc: 'localization', localisation: 'localization', mixdown: 'mix', dub: 'dubb', atmos: 'atmo' };
    const _said = new Set(String(REQ.requester_text).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter(Boolean)
      .map(w => _SYN[w] || w).map(_st));
    const _tok = t => t.toLowerCase().split(/[^a-z0-9]+/).filter(w => w && !_GEN.has(w)).map(w => _SYN[w] || w).map(_st);
    const _all = _types.map(t => ({ t, k: _tok(t) }));
    const _named = T => { const k = _tok(T); if (!k.length) return false;
      if (k.every(x => _said.has(x))) return true;
      return k.some(x => _said.has(x) && _all.filter(o => o.k.indexOf(x) !== -1).length === 1); };
    let _aka = false;
    try { for (const t of (_RT.types || [])) if (String(t.type).toLowerCase() === _cur.toLowerCase()) for (const a of [].concat(t.aka || [])) if (a && new RegExp('\\b' + String(a).replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i').test(String(REQ.requester_text))) _aka = true; } catch (e) {}
    if (/^vo recording$/i.test(_cur) && /\b(?:isr|in[- ]studio recording)\b/i.test(String(REQ.requester_text))) _aka = true;
    if (!_named(_cur) && !_aka)
      return [{ json: { verdict:'REJECTED', reason:'NEED_SESSION_TYPE', guessed: _cur,
        human:'Nothing was prepared. Ask exactly this, in one message: "What kind of session is this?" Then prepare it again with the session type they name.' } }];
  }
}
""" + ST_ANCHOR

RS_OLD = "for (const k of ['Date', 'Time', 'Room']) if (F[k]) L.push('*' + k + ':* ' + F[k]);"
RS_NEW = RS_OLD + """
// v80 (decided 1 Oct): an on-behalf booking says who it is for - only then (a Bookers colleague; never a client or a project).
{ const _forN = (String(F['Booked by'] || '').match(/\\(for\\s+([^)]+)\\)/i) || [])[1]; if (_forN) L.push('*For:* ' + _forN.trim()); }"""

# 5: "for anj's project" - the possessive hid the name (live 1 Oct 16:40)
TF_OLD = "while ((m = re.exec(_rt))) { const w = m[1].split(/\\s+/); for (const c of [w.join(' '), w[0]])"
TF_NEW = "while ((m = re.exec(_rt))) { const w = m[1].split(/\\s+/).map(x => x.replace(/['\u2019]s$/i, '')); for (const c of [w.join(' '), w[0]])"
# 6: the heads-up line: "longer" for a shorter session, and a blank range when the type has no maximum (16:40)
HU_OLD = "    notes.push('Heads up: ' + _durTxt(_len) + ' is ' + (_len > +_ty3.max ? 'longer' : 'shorter') + ' than ' + st + ' usually runs (' + _durTxt(+_ty3.min) + ' \u2013 ' + _durTxt(+_ty3.max) + ').');"
HU_OLD2 = HU_OLD.replace('\\u2013', '\u2013')
HU_NEW = "    notes.push('Heads up: ' + _durTxt(_len) + ' is ' + ((+_ty3.max && _len > +_ty3.max) ? 'longer' : 'shorter') + ' than ' + st + ' usually runs (' + (+_ty3.min && +_ty3.max ? _durTxt(+_ty3.min) + ' \u2013 ' + _durTxt(+_ty3.max) : +_ty3.max ? 'up to ' + _durTxt(+_ty3.max) : 'at least ' + _durTxt(+_ty3.min)) + ').');   // v80: right word, no blank range"

def build(w):
    w["name"] = "Jessie — Book Session — v80 (on-behalf + session type)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, V70_ANCHOR, V70_NEW, "v70 block")
    s = sub1(s, V73_OLD, V73_NEW, "v73 default")
    s = sub1(s, ENG_COND_OLD, ENG_COND_NEW, "eng cond")
    s = sub1(s, AFTER517, AFTER517_NEW, "after 517")
    s = sub1(s, ST_ANCHOR, ST_NEW, "session type")
    s = sub1(s, TF_OLD, TF_NEW, "possessive")
    cc["jsCode"] = s
    rs = node(w, "Render Summary")["parameters"]; t = sub1(rs["jsCode"], RS_OLD, RS_NEW, "render for line")
    hu = HU_OLD if HU_OLD in t else HU_OLD2
    rs["jsCode"] = sub1(t, hu, HU_NEW, "heads-up")
    return w

if __name__ == "__main__":
    json.dump(build(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
