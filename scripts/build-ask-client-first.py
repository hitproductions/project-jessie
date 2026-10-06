#!/usr/bin/env python3
"""main v218 + Book Session v89 (client asked first, no leaked instruction) - live 6 Oct 13:32-13:33 PHT on main v217 /
Book Session v88:
  "book studio 8 next thu 3-5pm" -> "What kind of session is this? What's the project?" (no client) -> "mixing. for proj
  runway" -> "Which one - ...?" -> "post mixing" -> "Nothing was booked. If there is no client, leave it empty."
  - Book Session v89: the client rides on the first questions with the project, date and time: "What's the project, and
    who's the client? (or "none")". Asked at most twice; "none" / "no client" ends it. Not for a meeting, a conference
    room, an M booth, Localization / QC (a project code) or a booking the requester called internal or personal.
  - Book Session v89: in prepare mode a client the requester never typed (and not in Clients) is dropped and asked for,
    instead of refused as CLIENT_UNVERIFIED. The refusal told the model "Ask the requester who the client is ... If there
    is no client, leave it empty."; the model pasted it, Guard Probe's v183 filter dropped the sentences naming "the
    requester", and what was left reached Slack. CLIENT_UNVERIFIED (outside prepare mode) and MISSING_CLIENT now carry a
    quoted question, so Guard Probe's v203 relay sends the question itself.
  - main v218 Guard Probe: instruction sentences ("Ask exactly this", "Then prepare it again", "leave it empty", "present
    the summary again") are dropped like v183's, and a reply left as only "Nothing was booked." becomes the client
    question (after a client refusal) or a plain "send it again". The model's own booking questions get the client
    question too (beside v212/v214's project, day and time).
  scripts/build-ask-client-first.py <book-live> <book-out> <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- Book Session: Check Conflicts
TOP_OLD = "const __ccResult = (() => {\n"
TOP_NEW = "let __cliAsk = false;   // v89: the client is still to be asked (set in prepare mode below, read by the questions at the end)\nconst __ccResult = (() => {\n"

CLI_ANCHOR = "if (__prep && (String(REQ.session_type || '').trim() || __studioRoom) && String(REQ.requester_text || '').trim()) {\n  let _RT = __RT0;"
CLI_BLOCK = r"""// v89 (live 6 Oct 13:32-13:33): the client is asked with the first questions, and a client the requester never typed is
// dropped and asked for rather than refused. "book studio 8 next thu 3-5pm" was asked the session type and the project but
// not the client; after "post mixing" the model passed a client nobody named, CLIENT_UNVERIFIED refused it, and the model
// pasted the instruction: "Nothing was booked. If there is no client, leave it empty." __cliAsk tells the questions at the
// end to add "who's the client? (or "none")" - asked at most twice; a requester who passes it by twice has no client.
if (__prep && !__series && String(REQ.requester_text || '').trim()) {
  const _nz = s => String(s || '').toLowerCase().replace(/['’]s\b/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
  const _rt = String(REQ.requester_text || ''), _st = String(REQ.session_type || '').trim();
  const _t = String(REQ.summary || '').split(' / ').map(s => s.trim());
  const _loc = /^(localization|qc)\b/i.test(_st);
  const _cl = String(REQ.client || '').trim() || (_t.length >= 3 ? _t[1] : '');
  const _code = !!_cl && (_cl.toLowerCase() === String(_t[0] || '').toLowerCase() || /^[A-Z]{2,6}-[A-Z0-9-]+$/.test(_cl));
  if (_cl && !_code && !_loc) {
    let _rows = []; try { _rows = $('Get Client').all().map(i => (i && i.json) || {}); } catch (e) {}
    let _staff = []; try { _staff = $('All Bookers').all().map(i => _nz(((i && i.json && i.json.fields) || {}).Name)).filter(Boolean); } catch (e) {}
    const _found = _rows.some(r => r.id), _err = _rows.some(r => r.error);
    if (!_found && !_err && _nz(_cl) !== _nz(__aliasClient) && _staff.indexOf(_nz(_cl)) === -1
        && (' ' + _nz(_rt) + ' ').indexOf(' ' + _nz(_cl) + ' ') === -1) {
      REQ.client = '';
      if (_t.length >= 3 && _nz(_t[1]) === _nz(_cl)) REQ.summary = [_t[0], _t[_t.length - 1]].join(' / ');
    }
  }
  const _now = String(REQ.client || '').trim() || (String(REQ.summary || '').split(' / ').length >= 3 ? String(REQ.summary).split(' / ')[1].trim() : '');
  const _asked = (String(REQ.asked_text || '').match(/\bthe client\b/gi) || []).length;
  __cliAsk = !_now && !_loc && (!!_st || __studioRoom) && !/^(meeting|event)$/i.test(_st) && !__SAIDNONE.test(_rt)
    && !/^(Internal|Personal)$/.test(__tyWords(_rt)) && _asked < 2;
}
"""

UNV_OLD = """      human:'Nothing was booked. "' + _cl + '" is not in the Clients list and is not a name the requester gave. Ask the requester who the client is, use the name exactly as they type it, and present the summary again. If there is no client, leave it empty.' } }];"""
UNV_NEW = """      human:'Nothing was booked - "' + _cl + '" is not a client on record and not a name the requester gave. Ask exactly this, in one message: "Who’s the client? (or \\\\"none\\\\")" Then try again with the name exactly as they type it, or with no client.' } }];   // v89: a question, not an instruction to paste"""

MC_OLD = """      human:'Nothing was booked. ' + bookedFor + ' is who this session is booked FOR, not the client - so ' + bookedFor + ' must not be the client and must not appear in the calendar title. Ask the requester who the client is. If there is none, leave the client empty and use PROJECT / initials as the title. Present the summary again.' } }];"""
MC_NEW = """      human:'Nothing was booked - ' + bookedFor + ' is who this session is booked for, not the client, so not the client or in the title. Ask exactly this, in one message: "Who’s the client? (or \\\\"none\\\\")" Then try again with the client they name, or with none (title PROJECT / initials).' } }];   // v89"""

ASKED_OLD = "  const _cliAsked = /\\bthe client\\b/i.test(String(REQ.asked_text || ''));"
ASKED_NEW = "  const _cliAsked = (String(REQ.asked_text || '').match(/\\bthe client\\b/gi) || []).length >= 2;   // v89: asked at most twice (the first time with the first questions)"

TAIL_OLD = """    const _dt = _noDate && _noTime ? 'which day and time?' : _noDate ? 'which day?' : _noTime ? 'what time?' : '';
    const _add = [_noProj && __j.reason !== 'ON_BEHALF_OR_OWN' ? 'What’s the project?' : '', _dt ? 'And ' + _dt : ''].filter(Boolean).join(' ');   // the on-behalf question already says "project\""""
TAIL_NEW = """    const _dt = _noDate && _noTime ? 'which day and time?' : _noDate ? 'which day?' : _noTime ? 'what time?' : '';
    // v89: the client rides on the first questions too, unless the question already asks about a client
    const _q0 = (String((__j && __j.human) || '').match(/Ask exactly this[^"]*"((?:[^"\\\\]|\\\\.)+)"/) || [])[1] || '';
    const _cli = __cliAsk && __j && __j.reason !== 'ON_BEHALF_OR_OWN' && !/\\bclient\\b/i.test(_q0);
    const _pj = _noProj && __j.reason !== 'ON_BEHALF_OR_OWN';
    const _pc = _pj && _cli ? 'What’s the project, and who’s the client? (or \\\\"none\\\\")' : _pj ? 'What’s the project?' : _cli ? 'Who’s the client? (or \\\\"none\\\\")' : '';
    const _add = [_pc, _dt ? 'And ' + _dt : ''].filter(Boolean).join(' ');   // the on-behalf question already says "project\""""

MD_OLD = """    if (__j.verdict === 'REJECTED' && __j.reason === 'MISSING_DATE' && (_noTime || _noProj))
      __j.human = String(__j.human).replace('Ask exactly this: "Which day?"', 'Ask exactly this: "' + (_noProj ? 'What’s the project? And ' : '') + (_noTime ? (_noProj ? 'which day and time?' : 'Which day and time?') : (_noProj ? 'which day?' : 'Which day?')) + '"');"""
MD_NEW = """    if (__j.verdict === 'REJECTED' && __j.reason === 'MISSING_DATE' && (_noTime || _pc))
      __j.human = String(__j.human).replace('Ask exactly this: "Which day?"', 'Ask exactly this: "' + (_pc ? _pc + ' And ' : '') + (_noTime ? (_pc ? 'which day and time?' : 'Which day and time?') : (_pc ? 'which day?' : 'Which day?')) + '"');   // v89: + the client"""

def book(w):
    w["name"] = "Jessie — Book Session — v89 (client asked first)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, TOP_OLD, TOP_NEW, "top")
    s = sub1(s, CLI_ANCHOR, CLI_BLOCK + CLI_ANCHOR, "client block")
    s = sub1(s, UNV_OLD, UNV_NEW, "unverified")
    s = sub1(s, MC_OLD, MC_NEW, "missing client")
    s = sub1(s, ASKED_OLD, ASKED_NEW, "asked twice")
    s = sub1(s, TAIL_OLD, TAIL_NEW, "tail add")
    s = sub1(s, MD_OLD, MD_NEW, "missing date")
    cc["jsCode"] = s
    return w

# ---------------------------------------------------------------- main: Guard Probe
RQ_OLD = """  const _RQ = /\\bthe requester\\b|\\bIf they say to go ahead\\b|\\bSuggest (?:one of )?(?:those|these) instead of\\b/i;"""
RQ_NEW = """  // v218 (live 6 Oct 13:33): "Nothing was booked. If there is no client, leave it empty." - the rest of the instruction was
  // dropped here, those two sentences were not. Instruction wording is dropped too, and a reply left as only "Nothing was
  // booked." gets a question it can be answered with.
  const _RQ = /\\bthe requester\\b|\\bIf they say to go ahead\\b|\\bSuggest (?:one of )?(?:those|these) instead of\\b|\\bAsk exactly this\\b|\\bThen (?:prepare|try|present|call)\\b|\\bleave (?:it|the client|booked_for) empty\\b|\\bpresent the summary again\\b|\\bIf there is (?:none|no client)\\b/i;
  const _before = text;"""
EV_OLD = """  // QA bug B: an "Event ID:" line reached the requester on a model-written cancel card."""
EV_NEW = """  if (text !== _before && /^\\s*(?:Nothing was (?:booked|prepared)[.!]?\\s*)?$/i.test(text)) {
    let _why = '';
    try { const _sN = (($input.first().json || {}).intermediateSteps) || [];
      for (let i = _sN.length - 1; i >= 0 && !_why; i--) {
        if (!/^(prepare booking|book session|book series)$/.test(String(((_sN[i] || {}).action || {}).tool || '').replace(/[_\\s]+/g, ' ').toLowerCase())) continue;
        let _oN = null; try { _oN = [].concat(JSON.parse(String((_sN[i] || {}).observation || '')))[0]; } catch (e) {}
        _why = String((_oN && _oN.reason) || '-');
      } } catch (e) {}
    text = /CLIENT/.test(_why) ? 'Who’s the client? (or "none")' : 'Sorry - I couldn’t get that ready. Could you send the booking details again?';
  }
  // QA bug B: an "Event ID:" line reached the requester on a model-written cancel card."""

PROJ_OLD = """  if (_asks && _booking && _aboutBooking && !_series && (_askDay || _askTime || _askProj))
    text = text.trim() + ' ' + [_askProj ? 'What\\u2019s the project?' : '', (_askDay || _askTime) ? (_askDay && _askTime ? 'And which day and time?' : _askDay ? 'And which day?' : 'And what time?') : ''].filter(Boolean).join(' ');   // v214: one line"""
PROJ_NEW = """  // v218 (live 6 Oct 13:32): the client too, when none was named or declined - asked with the first questions
  const _bfc = (($('Booked For').first() || {}).json) || {};
  const _askCli = !String(_bfc.client || _bfc.forClient || '').trim() && !/\\bclients?\\b/i.test(text) && !/\\bclients?\\b|\\bprodu(?:cer)?\\b|\\b(?:none|wala)\\b/i.test(_rt)
    && !/\\b(?:personal|my own|own project|internal|meeting|event)\\b/i.test(_rt) && /\\b(?:studio\\s+[a-z0-9]|booth)\\b/i.test(_rt);
  if (_asks && _booking && _aboutBooking && !_series && (_askDay || _askTime || _askProj || _askCli))
    text = text.trim() + ' ' + [_askProj && _askCli ? 'What\\u2019s the project, and who\\u2019s the client? (or "none")' : _askProj ? 'What\\u2019s the project?' : _askCli ? 'Who\\u2019s the client? (or "none")' : '',
      (_askDay || _askTime) ? (_askDay && _askTime ? 'And which day and time?' : _askDay ? 'And which day?' : 'And what time?') : ''].filter(Boolean).join(' ');   // v214: one line; v218: + the client"""

def main(w):
    w["name"] = "Project Jessie — v218 (client asked first)"
    gp = node(w, "Guard Probe")["parameters"]; s = gp["jsCode"]
    s = sub1(s, RQ_OLD, RQ_NEW, "gp rq"); s = sub1(s, EV_OLD, EV_NEW, "gp nothing-left"); s = sub1(s, PROJ_OLD, PROJ_NEW, "gp client ask")
    gp["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
