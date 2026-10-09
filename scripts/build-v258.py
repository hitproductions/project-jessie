#!/usr/bin/env python3
"""main v258 - booking questions written in code (decided 9 Oct, after v255-v257 each closed one wording and the model found
another: 17:15 on v257, "I need a few details for Studio 6 tomorrow (Sunday, October 10): what kind of session is this, who's
the client, what's the project title, what time should it run, and is there a specific engineer or should I leave that for now?").

When the model's reply asks for booking details on a studio booking, the reply is replaced by code's question, built from what
the code already holds - never from the model's words:
  - the date (Gate Context) or time (Booked For) missing -> only that: "What date and time work?" / "What date works?" /
    "What time works?" (v252)
  - otherwise "🗓️ room · date · time", a blank line, and one question for what is still missing, in order: session type (a
    generic word only -> "Which kind of mixing - <every type>?"), project (Booked For), client (Booked For; "none" counts), the
    engineer only when nobody was named and the requester is not an engineer.
  - nothing missing by code's count -> the model's question stands, trimmed (v255).
Never on: a card, a code-written reply or relay (cards, Book Session's "Ask exactly this" questions, the heads-up layouts,
availability answers), internal rooms (M booths, conference rooms, the Lobby), series, cancels and moves. The heads-up
(early room check) still goes on top.

  scripts/build-v258.py <main-v257> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
ANCHOR = "// v250: the early room check's part-day heads-up goes on top of the shortened reply\nif (_erPre) text = _erPre"
BQ = r"""// --- v258 (decided 9 Oct): booking questions written in code ----------------------------------------------------------
// The model asked for details in a new way each time patches closed one (v255-v257). On a studio booking, a reply that asks
// for booking details is replaced by code's question, from what Gate Context, Booked For and Early Room Plan already hold.
let bookingQ = '';
try {
  const _bk = (($('Booked For').first() || {}).json) || {};
  const _rt = String(_bk.requesterText || '');
  const _pl = (((($('Early Room Plan').first() || {}).json) || {}).earlyPlan) || {};
  const _gc = (($('Gate Context').first() || {}).json) || {};
  // judged on the model's own reply: a question code already wrote (a card turned into a question, a relay) is not replaced
  const _raw = String((($input.first() || {}).json || {}).output || '');
  const _askDet = /\?\s*$/.test(text) && /\?/.test(_raw) && /\b(?:session|project|client|time|date|day|engineer|kind of|type of|details?)\b/i.test(_raw);
  const _internal = /\b(?:m[\s-]?booth|m[1-8]|salin|likha|katha|lobby|conference)\b/i.test(_rt + ' ' + String(_pl.knownRoom || ''));
  const _series = /\b(?:every|weekly|daily|biweekly|fortnightly|recurring|series|weekdays)\b/i.test(_rt);
  const _cm = /^(?:a yes|answering a cancel or move card|a cancel or move)$/.test(String(_pl.why || '')) || /\b(?:cancel|move|resched\w*)\b/i.test(_rt);
  const _card = /\*Date:\*|\*Dates|\*Moving to:\*|\*Now:\*|\*Client:\*|\*Session Type:\*|Book it\?|Cancel it\?|Move it\?|Confirm to|_check [0-9a-f]{8}_/i.test(text + '\n' + _raw);
  if (_askDet && !_prepared && !_codeCard && !_card && !_internal && !_series && !_cm && /\b(?:book|reserve|schedule)\b/i.test(_rt) && !/^\s*(?:❌|✅|🗓️|⚠️)/.test(text)) {
    const _ds = String(_gc.datesUnderDiscussion || '').split(',').map(x => x.trim()).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x));
    const _date = _ds.length === 1 ? new Date(_ds[0] + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' }) : '';
    const _f12 = x => (+x.slice(0, 2) % 12 || 12) + ':' + x.slice(3) + ' ' + (+x.slice(0, 2) < 12 ? 'AM' : 'PM');
    const _time = /^\d{2}:\d{2}$/.test(String(_bk.timeStart || '')) && /^\d{2}:\d{2}$/.test(String(_bk.timeEnd || '')) ? _f12(_bk.timeStart) + ' – ' + _f12(_bk.timeEnd) : '';
    if (!_date || !_time) {
      bookingQ = !_date && !_time ? 'What date and time work?' : !_date ? 'What date works?' : 'What time works?';
    } else {
      let _types = []; try { _types = [...new Set((JSON.parse(String((($('Room Table').first() || {}).json || {}).referenceData || '{}')).types || []).map(t => String(t.type || '').trim()).filter(Boolean))]; } catch (e) {}
      const _low = _rt.toLowerCase();
      const _named = _types.filter(t => _low.indexOf(t.toLowerCase()) !== -1);
      let _kind = '', _stMissing = false;
      if (!_named.length && _types.length) {
        const _g = ['mixing', 'recording', 'editing', 'dubbing'].find(w => new RegExp('\\b' + w + '\\b').test(_low));
        if (_g) { const _op = _types.filter(t => new RegExp('\\b' + _g + '\\b', 'i').test(t));
          const _nar = _op.filter(o => o.toLowerCase().split(/\s+/).filter(w => w !== _g).some(w => new RegExp('\\b' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b').test(_low)));
          if (_op.length >= 2 && _nar.length !== 1) _kind = 'Which kind of ' + _g + ' - ' + (_op.length === 2 ? _op.join(' or ') : _op.slice(0, -1).join(', ') + ' or ' + _op[_op.length - 1]) + '?'; }
        // nothing that names a session: asked only when the model asked too (shorthands like "isr" are read by Book Session)
        else _stMissing = /\b(?:kind|type) of session\b|\bsession type\b|\bwhat kind\b/i.test(text);
      }
      const _need = [];
      if (_stMissing) _need.push('session type');
      if (!String(_bk.project || _bk.projectCode || '').trim()) _need.push('project');
      const _noCl = String(_bk.clientAnswer || '') === 'none' || /\b(?:no|without(?: a| any)?|walang)\s+(?:a\s+)?clients?\b|\bclient\s*(?:is|:)?\s*(?:none|n\/?a|wala)\b/i.test(_rt);
      if (!String(_bk.client || _bk.forClient || '').trim() && !_noCl) _need.push('client');
      if (!_bk.engineerResolved && !String(_bk.engineer || '').trim() && /\bengineer\b/i.test(text)) _need.push('engineer');
      const _line = '🗓️ ' + [String(_pl.knownRoom || ''), _date, _time].filter(Boolean).join(' · ');
      if (_kind) bookingQ = _line + '\n\n' + _kind;
      else if (_need.length) bookingQ = _line + '\n\n' + (_need.length === 1
        ? ({ 'session type': "What's the session type?", project: "What's the project?", client: 'Who’s the client? (or "none")', engineer: 'Who’s the engineer?' })[_need[0]]
        : "What's the " + (_need.length === 2 ? _need.join(' and ') : _need.slice(0, -1).join(', ') + ' and ' + _need[_need.length - 1]) + '?' + (_need.indexOf('client') !== -1 ? ' (or "none" for no client)' : ''));
    }
    if (bookingQ) text = bookingQ;
  }
} catch (e) { bookingQ = ''; }

"""
SER_OLD = """    if (/\\?\\s*$/.test(text) && text.length <= 400
"""
SER_NEW = """    // v258: a series has its own flow (Prepare Series) - its questions are never rewritten into a single booking's
    let __ser = false; try { __ser = /\\b(?:every|weekly|daily|biweekly|fortnightly|recurring|series|weekdays)\\b/i.test(String(((($('Booked For').first() || {}).json) || {}).requesterText || '')); } catch (e) {}
    if (!__ser && /\\?\\s*$/.test(text) && text.length <= 400
"""
def main(w):
    w["name"] = "Project Jessie — v258 (booking questions in code)"
    gp = node(w, "Guard Probe")["parameters"]; c = once(gp["jsCode"], ANCHOR, BQ + ANCHOR, "booking questions"); gp["jsCode"] = once(c, SER_OLD, SER_NEW, "series"); return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
