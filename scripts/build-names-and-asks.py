#!/usr/bin/env python3
"""Book Session v84 (names + ask once) - live 2 Oct (Oct 3 test bookings "THANK / ruff lopez / HL x BPV", "DIGICON /
Sir Vic / HL", "M3 - Howard Luistro") and decided 2 Oct:
  1. Client names: a leading title is dropped ("sir vic"); a client on record is written as on record (full name, or a
     first name only one client has -> "Vic Icasas"); a new client typed all in lowercase gets capitals ("Ruff Lopez").
     Get Client searches without the title too.
  2. The event description says "Engineer: Howard Luistro" - no "(Post Engineer)".
  3. An M booth hold is titled with the first name: "M3 - Howard".
  4. Missing details are asked in one message: a missing date / time is added to whatever is being asked ("What kind
     of session is this? And which day and time?"); with nothing else to ask, "Which day and time?" / "What time?" -
     no time is picked for the requester any more ("No time given, so I picked ...").
  scripts/build-names-and-asks.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

HON = r"(?:sir|ma['\u2019]?am|mam|madam|miss|ms\.?|mr\.?|mrs\.?|dr\.?|direk|kuya|ate|tito|tita|engr\.?|atty\.?)"

ANCHOR = "const __series = REQ.series === true || String(REQ.series).toLowerCase() === 'true';"
CLIENT = ANCHOR + r"""
// v84 (live 2 Oct, "DIGICON / Sir Vic / HL", "THANK / ruff lopez / ..."): client names - a leading title is dropped, a
// client on record is written as on record (full name, or a first name only one client has), and a new client typed all
// in lowercase gets capitals. A Localization Project Code / the project itself in the client slot is left alone.
try {
  const _HON = /^""" + HON + r"""\s+/i;
  const _tp = String(REQ.summary || '').split(' / ');
  const _c0 = String(REQ.client || '').trim() || (_tp.length >= 3 ? _tp[1].trim() : '');
  const _lc = x => String(x || '').toLowerCase().replace(/\s+/g, ' ').trim();
  if (_c0 && _lc(_c0) !== _lc(_tp[0]) && !/^[A-Z]{2,6}-[A-Z0-9]/.test(_c0)) {
    let _c = _c0.replace(_HON, '').trim() || _c0;
    let _rows = []; try { _rows = $('Get Client').all().map(i => (i && i.json) || {}); } catch (e) {}
    const _recs = _rows.filter(r => r.id && r.fields && r.fields.Name);
    let _hit = _recs.find(r => _lc(r.fields.Name) === _lc(_c));
    if (!_hit) { const _f = _recs.filter(r => _lc(String(r.fields.Name).split(/\s+/)[0]) === _lc(_c)); if (_f.length === 1) _hit = _f[0]; }
    if (_hit) _c = String(_hit.fields.Name).trim();
    else if (_c === _c.toLowerCase() && /[a-z]/.test(_c) && !_rows.some(r => r.error)) _c = _c.replace(/(^|[\s'\u2019-])([a-z\u00f1])/g, (m, a, b) => a + b.toUpperCase());
    if (_c !== _c0) {
      if (String(REQ.client || '').trim()) REQ.client = _c;
      if (_tp.length >= 3 && _lc(_tp[1]) === _lc(_c0)) { _tp[1] = _c; REQ.summary = _tp.join(' / '); }
      REQ.__clientFrom = _c0;
    }
  }
} catch (e) {}"""

GC_OLD = "  if (!v) { return 'FALSE()'; }\n  return \"SEARCH(LOWER('\""
GC_NEW = "  v = v.replace(/^" + HON.replace("\\u2019", "\u2019") + "\\s+/i, '').trim() || v;   // v84: no title (\"sir vic\")\n  if (!v) { return 'FALSE()'; }\n  return \"SEARCH(LOWER('\""

DESC_OLD = "const finalDescription = segs.join(' | ');"
DESC_NEW = "const finalDescription = segs.join(' | ').replace(/((?:Engineer|Arranger):\\s*[^|()]+?)\\s*\\([^)|]*\\)/g, '$1');   // v84: no \"(Post Engineer)\""

MB_ANCHOR = "// v51: the project segment of a studio title is in capitals (the title convention), whatever the model typed -"
MB_NEW = r"""// v84 (decided 2 Oct): an M booth hold is titled with the first name - "M3 - Howard", not "M3 - Howard Luistro".
try {
  const _mm = finalSummary.match(/^(M[1-8])\s*-\s*(.+)$/i);
  if (_mm) { let _bk = []; try { _bk = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}); } catch (e) {}
    const _f = _bk.find(f => String(f.Name || '').trim().toLowerCase() === _mm[2].trim().toLowerCase());
    if (_f) finalSummary = _mm[1].toUpperCase() + ' - ' + String(_f.Name).trim().split(/\s+/)[0]; }
} catch (e) {}
""" + MB_ANCHOR

WRAP_HEAD = "const __ccResult = (() => {\n"
WRAP_TAIL = r"""
})();
// v84 (decided 2 Oct): ask for everything missing in one message - a missing date / time rides on whatever is asked, and
// with nothing else to ask Jessie asks for them instead of picking a time.
try {
  const __j = (__ccResult && __ccResult[0] && __ccResult[0].json) || null;
  const _R = $('When Executed by Another Workflow').first().json || {};
  const _prep = String(_R.mode || '').trim().toLowerCase() === 'prepare';
  const _ser = _R.series === true || String(_R.series).toLowerCase() === 'true';
  const _rt = String(_R.requester_text || '');
  const _rooms = String(_R.rooms || '').split(',').map(r => r.trim()).filter(Boolean);
  const _mb = _rooms.length > 0 && _rooms.every(r => /^M[1-8]$/i.test(r));
  const _allDay = _R.all_day === true || String(_R.all_day).toLowerCase() === 'true';
  if (__j && _prep && !_ser && _rt.trim()) {
    const _noDate = !String(_R.expected_date || '').split(',').some(s => /^\d{4}-\d{2}-\d{2}$/.test(s.trim())) && !_mb;
    const _noTime = !_mb && !_allDay && !/\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.|nn|noon)\b|\b\d{1,2}:\d{2}\b|\b(?:noon|midnight|morning|afternoon|evening|tonight|lunch|all day|whole day|half day)\b|\bat\s+\d{1,2}\b|\b\d{1,2}\s*(?:-|\u2013|to|until|till)\s*\d{1,2}\b/i.test(_rt);
    const _add = _noDate && _noTime ? 'And which day and time?' : _noDate ? 'And which day?' : _noTime ? 'And what time?' : '';
    const _ASKS = ['NEED_SESSION_TYPE', 'NEED_DEPARTMENT', 'NEED_BOOKING_TYPE', 'NEED_CLIENT', 'NEED_ARRANGER', 'NEED_ENGINEER', 'ON_BEHALF_OR_OWN', 'CLIENT_CHECK'];
    if (__j.verdict === 'REJECTED' && __j.reason === 'MISSING_DATE' && _noTime)
      __j.human = String(__j.human).replace('Ask exactly this: "Which day?"', 'Ask exactly this: "Which day and time?"');
    else if (__j.verdict === 'REJECTED' && _ASKS.indexOf(__j.reason) !== -1 && _add)
      __j.human = String(__j.human).replace(/(Ask exactly this[^"]*")((?:[^"\\]|\\.)+)(")/, (m, a, q, c) => a + q + ' ' + _add + c);
    else if (__j.verdict === 'CLEAR' && __j.time_proposed) {
      return [{ json: { verdict:'REJECTED', reason:'NEED_TIME',
        human:'Nothing was prepared. Ask exactly this, in one message: "What time?" Then prepare it again with the time they give.' } }];
    }
  }
} catch (e) {}
return __ccResult;"""

def build(w):
    w["name"] = "Jessie — Book Session — v84 (names + ask once)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, ANCHOR, CLIENT, "client")
    s = sub1(s, DESC_OLD, DESC_NEW, "description")
    s = sub1(s, MB_ANCHOR, MB_NEW, "m booth")
    cc["jsCode"] = WRAP_HEAD + s + WRAP_TAIL
    gc = node(w, "Get Client")["parameters"]; gc["filterByFormula"] = sub1(gc["filterByFormula"], GC_OLD, GC_NEW, "get client")
    return w

if __name__ == "__main__":
    json.dump(build(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
