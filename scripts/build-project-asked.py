#!/usr/bin/env python3
"""Book Session v86 + main v214 (project asked) - live 2 Oct 13:02: "can you book studio 7 for me - client is vic icasas"
-> "VO RECORDING / Vic Icasas / HL": no project was asked, and the model used the session type as the title's project
(the requester typed "vo recording", so nothing caught it). Decided 2 Oct: the project is required.
  Book Session v86: the title's project must be something the requester typed and not the session type, the client or a
  room; otherwise "What's the project?" is asked - with whatever else is being asked, in one message ("What kind of
  session is this? What's the project? And what time?"), or on its own before the card.
  main v214: Guard Probe adds "What's the project?" to the model's own booking questions when the requester named none
  (no "project ..." and no name in capitals), and everything it adds now goes on the same line (was a line break).
  scripts/build-project-asked.py <book-live> <book-out> <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BS_OLD = """    const _add = _noDate && _noTime ? 'And which day and time?' : _noDate ? 'And which day?' : _noTime ? 'And what time?' : '';
    const _ASKS = ['NEED_SESSION_TYPE', 'NEED_DEPARTMENT', 'NEED_BOOKING_TYPE', 'NEED_CLIENT', 'NEED_ARRANGER', 'NEED_ENGINEER', 'ON_BEHALF_OR_OWN', 'CLIENT_CHECK'];
    if (__j.verdict === 'REJECTED' && __j.reason === 'MISSING_DATE' && _noTime)
      __j.human = String(__j.human).replace('Ask exactly this: "Which day?"', 'Ask exactly this: "Which day and time?"');
    else if (__j.verdict === 'REJECTED' && _ASKS.indexOf(__j.reason) !== -1 && _add)
      __j.human = String(__j.human).replace(/(Ask exactly this[^"]*")((?:[^"\\\\]|\\\\.)+)(")/, (m, a, q, c) => a + q + ' ' + _add + c);
    else if (__j.verdict === 'CLEAR' && __j.time_proposed) {
      return [{ json: { verdict:'REJECTED', reason:'NEED_TIME',
        human:'Nothing was prepared. Ask exactly this, in one message: "What time?" Then prepare it again with the time they give.' } }];
    }"""
BS_NEW = r"""    // v86 (live 2 Oct 13:02, decided 2 Oct): the project is required - the title's project must be something the requester
    // typed, and not the session type, the client or a room ("VO RECORDING / Vic Icasas / HL").
    let _noProj = false;
    try {
      const _st0 = String(_R.session_type || '').trim(), _sum = String(_R.summary || '');
      const _studioB = !!_st0 || _rooms.some(r => /^Studio\s/i.test(r));
      if (_studioB && _sum.indexOf(' / ') !== -1) {
        const _nz = x => String(x || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
        const _p = _nz(_sum.split(' / ')[0]);
        let _RF = {}; try { _RF = JSON.parse(String(_R.reference_data || '{}')); } catch (e) {}
        const _isType = (_RF.types || []).some(t => _nz(t.type) === _p) || /^(?:vo|recording|vo recording|mix|mixing|session|booking|editing|dubbing|qc|meeting|event)$/.test(_p);
        const _isRoom = (_RF.rooms || []).some(r => _nz(r.name) === _p) || /^studio [a-z0-9]$/.test(_p);
        const _isClient = !!_p && _p === _nz(_R.client || (_sum.split(' / ').length >= 3 ? _sum.split(' / ')[1] : ''));
        const _typed = !!_p && (' ' + _nz(_rt) + ' ').indexOf(' ' + _p + ' ') !== -1;
        _noProj = !_p || !_typed || _isType || _isRoom || _isClient;
      }
    } catch (e) {}
    const _dt = _noDate && _noTime ? 'which day and time?' : _noDate ? 'which day?' : _noTime ? 'what time?' : '';
    const _add = [_noProj && __j.reason !== 'ON_BEHALF_OR_OWN' ? 'What’s the project?' : '', _dt ? 'And ' + _dt : ''].filter(Boolean).join(' ');   // the on-behalf question already says "project"
    const _ASKS = ['NEED_SESSION_TYPE', 'NEED_DEPARTMENT', 'NEED_BOOKING_TYPE', 'NEED_CLIENT', 'NEED_ARRANGER', 'NEED_ENGINEER', 'ON_BEHALF_OR_OWN', 'CLIENT_CHECK'];
    if (__j.verdict === 'REJECTED' && __j.reason === 'MISSING_DATE' && (_noTime || _noProj))
      __j.human = String(__j.human).replace('Ask exactly this: "Which day?"', 'Ask exactly this: "' + (_noProj ? 'What’s the project? And ' : '') + (_noTime ? (_noProj ? 'which day and time?' : 'Which day and time?') : (_noProj ? 'which day?' : 'Which day?')) + '"');
    else if (__j.verdict === 'REJECTED' && _ASKS.indexOf(__j.reason) !== -1 && _add)
      __j.human = String(__j.human).replace(/(Ask exactly this[^"]*")((?:[^"\\]|\\.)+)(")/, (m, a, q, c) => a + q + ' ' + _add + c);
    else if (__j.verdict === 'CLEAR' && (__j.time_proposed || _noProj)) {
      const _q = _noProj ? 'What’s the project?' + (__j.time_proposed ? ' And what time?' : '') : 'What time?';
      return [{ json: { verdict:'REJECTED', reason: _noProj ? 'NEED_PROJECT' : 'NEED_TIME',
        human:'Nothing was prepared. Ask exactly this, in one message: "' + _q + '" Then prepare it again with what they give.' } }];
    }"""

GP_OLD = """  const _askDay = _noDate && !/\\b(date|day|when)\\b/i.test(text), _askTime = _noTime && !/\\b(time|when|hours?)\\b/i.test(text);
  if (_asks && _booking && _aboutBooking && !_series && (_askDay || _askTime))
    text = text.trim() + '\\n' + (_askDay && _askTime ? 'And which day and time?' : _askDay ? 'And which day?' : 'And what time?');"""
GP_NEW = """  const _askDay = _noDate && !/\\b(date|day|when)\\b/i.test(text), _askTime = _noTime && !/\\b(time|when|hours?)\\b/i.test(text);
  // v214 (live 2 Oct 13:02): the project too, when the requester named none ("project ...", or a name in capitals)
  const _bfp = String(((($('Booked For').first() || {}).json) || {}).project || '').trim();
  const _askProj = !_bfp && !/\\b(project|title)\\b/i.test(text) && !/\\bproject\\b/i.test(_rt) && !/\\b(?!AM\\b|PM\\b|VO\\b|ISR\\b|QC\\b|HL\\b)[A-Z][A-Z0-9&-]{2,}\\b/.test(_rt.replace(/\\bStudio\\s+[A-Z0-9]\\b|\\bM[1-8]\\b/g, '')) && /\\b(?:studio|booth)\\b/i.test(_rt);
  if (_asks && _booking && _aboutBooking && !_series && (_askDay || _askTime || _askProj))
    text = text.trim() + ' ' + [_askProj ? 'What\\u2019s the project?' : '', (_askDay || _askTime) ? (_askDay && _askTime ? 'And which day and time?' : _askDay ? 'And which day?' : 'And what time?') : ''].filter(Boolean).join(' ');   // v214: one line"""

def book(w):
    w["name"] = "Jessie — Book Session — v86 (project asked)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = sub1(cc["jsCode"], BS_OLD, BS_NEW, "bs wrapper")
    return w
def main(w):
    w["name"] = "Project Jessie — v214 (project asked)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_OLD, GP_NEW, "gp")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
