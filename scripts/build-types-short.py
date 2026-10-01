#!/usr/bin/env python3
"""Book Session v73 (types + short summary) - PENDING 69, 70, 71 (Book Session half). For the DIGICON demo, 2 Oct.
  scripts/build-types-short.py <book-live> <book-out>

70 - four booking types: Advertising, Entertainment, Internal, Personal (were External / Personal), worked out in
     order: the requester's own words; the client's record (one Client Type), or a named producer -> Advertising; a
     Localization session -> Entertainment; an arranger with no client -> asked "Client work or your own project?";
     the requester's department (Audio Post, Music, Sales & Accounts -> Advertising; Localization -> Entertainment;
     Marketing, BD, P&C, IT, Management, Finance, Video Post -> Internal); else one short question. A conference room
     or the Lobby with no client is Internal. A legacy "External" (from the model or a client record not recoded yet)
     is worked out again. A series date is never asked (the same rules, minus the question).
     Advertising and Entertainment bookings with no client and no "none": "Who's the client? (or "none")".
69 - the summary shows the title, Date, Time and Room, short notes, and the confirmation - no other lines and no
     printed check code. Every detail is still checked and gathered: the full field set is stored in the reference-
     cache data table under prep-<fingerprint of requester + the four lines> (new nodes Store Prepared -> Prepared Out),
     and main reads it back at the yes. The length heads-up moves here from Guard Probe (it read the Session Type line).
71 - "me" / "myself" / "ako" as the engineer is the requester; after "for <colleague>" an engineer requester is put in
     instead of being asked; no "you're down as the engineer" note when they named themselves.
"""
import json, sys, copy, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
def between(s, start, end_after, new, label):
    i = s.find(start)
    if i < 0 or s.count(start) != 1: raise SystemExit(f"{label}: start not unique")
    j = s.find(end_after, i)
    if j < 0: raise SystemExit(f"{label}: end not found")
    return s[:i] + new + s[j + len(end_after):]

# ---------------------------------------------------------------------------------------------------- helpers
HELP_ANCHOR = "// v68 (live QA 30 Sep): studio shorthand"
HELPERS = r"""// v73 (PENDING 70, 1 Oct): four booking types - Advertising, Entertainment, Internal, Personal (were External / Personal).
// Worked out, never guessed by the model: what the requester typed, the client's record, the session, the requester's
// department. docs/design/booking-defaults.md.
const __TY = ['Advertising', 'Entertainment', 'Internal', 'Personal'];
const __tyNorm = v => { const x = String(v || '').trim().toLowerCase(); return __TY.find(t => t.toLowerCase() === x) || ''; };
const __tyWords = t => { t = String(t || '');
  if (/\b(personal|my own|own project|own session|side project|outside (?:of )?hit)\b/i.test(t)) return 'Personal';
  if (/\b(internal|hit project|company project|digicon|convention|in-?house event)\b/i.test(t)) return 'Internal';
  if (/\b(advertising|tvcs?|commercials?|ads?|radio spots?|jingles?)\b/i.test(t)) return 'Advertising';
  if (/\b(entertainment|dubbing|films?|movies?|netflix|disney|anime|documentar(?:y|ies))\b/i.test(t)) return 'Entertainment';
  return ''; };
const __reqStaff = (() => { const me = ((String(REQ.description || '').match(/booked by\s*:\s*([^|(]+)/i) || [])[1] || '').trim().toLowerCase();
  if (!me) return null;
  try { return $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).find(f => String(f.Name || '').trim().toLowerCase() === me) || null; } catch (e) { return null; } })();
const __reqDepts = __reqStaff ? [].concat(__reqStaff.Department || []).map(d => String((d && d.name) || d).trim().toLowerCase()) : [];
const __reqRole = __reqStaff ? String(__reqStaff.Info || '').split(/,|\bgoes by\b/i)[0].trim() : '';
const __tyDept = () => {
  if (__reqDepts.some(x => /^(audio post|music|sales & accounts|sales and accounts|s&a)$/.test(x))) return 'Advertising';
  if (__reqDepts.length && __reqDepts.every(x => x === 'localization')) return 'Entertainment';
  if (__reqDepts.some(x => /^(marketing|business development|people & culture|p&c|it|management|finance|video post)$/.test(x))) return 'Internal';
  return ''; };
const __decideType = ({ said, recTypes, producer, client, loc, ask, meeting }) => {
  const w = __tyWords(said); if (w) return { type: w };
  // a record not recoded yet: its old "External" means client work - this department's client type
  const _cw = () => { const d = __tyDept(); return d && d !== 'Internal' ? d : 'Advertising'; };
  const rt = [...new Set([].concat(recTypes || []).map(x => /^external$/i.test(String(x).trim()) ? _cw() : __tyNorm(x)).filter(Boolean))];
  if (rt.length === 1) return { type: rt[0] };
  if (rt.length > 1) return ask ? { ask: rt } : { type: rt[0] };
  if (producer) return { type: 'Advertising' };
  if (meeting) return { type: 'Internal' };   // a Meeting / Event session
  if (loc) return { type: 'Entertainment' };
  if (/\b(client work|for a client|client project|hit work|external)\b/i.test(String(said || ''))) return { type: _cw() };
  if (!client && ask && /arranger/i.test(__reqRole) && __reqDepts.indexOf('music') !== -1) return { ask: ['Client work', 'your own project'], arranger: true };
  const d = __tyDept(); if (d) return { type: d };
  return ask ? { ask: __TY } : {}; };
const __tyQuestion = d => { const a = d.ask.map((x, i) => i ? x.toLowerCase() : x);
  return a.length === 2 ? a[0] + ' or ' + a[1] + '?' : a.slice(0, -1).join(', ') + ' or ' + a[a.length - 1] + '?'; };
const __SAIDNONE = /\b(no|without(?: a| any)?|walang)\s+(?:a\s+)?(client|kliyente)\b|\bclient\s*(?:is|:|=)?\s*(?:none|n\/?a|wala)\b|(?:^|\n)\s*(?:none|no|wala)\s*[.!]?\s*(?:\n|$)/i;
"""

# ---------------------------------------------------------------------------------------------------- prepare mode
PREP_START = "  if (_studio && !String(REQ.bookingType || '').trim()) {"
PREP_END = "Personal (their own project), then prepare it again with that booking type.' } }];\n    }\n  }\n}\n"
PREP_NEW = r"""  // v73 (PENDING 70): the type is worked out here every time - the model's value (often a legacy "External") is not used.
  const _mtype = __tyNorm(REQ.bookingType) && __tyWords(REQ.requester_text) === __tyNorm(REQ.bookingType) ? __tyNorm(REQ.bookingType) : '';
  REQ.bookingType = _mtype;
  if (!_studio && !REQ.bookingType && !String(REQ.client || '').trim()) REQ.bookingType = 'Internal';   // a conference room / the Lobby
  const _said = String(REQ.requester_text || '');
  const _noCliSaid = __SAIDNONE.test(_said);
  const _cliAsked = /\bthe client\b/i.test(String(REQ.asked_text || ''));
  const _needCli = !_typed && !_code && !_loc3 && !_noCliSaid && !_cliAsked;
  if (_studio && !REQ.bookingType) {
    const _types = _rec ? [].concat((_rec.fields || {})['Client Type'] || []).map(x => String((x && x.name) || x)) : [];
    const _bt = _rec ? (((_rec.fields || {})['Booker Type'] || {}).name || (_rec.fields || {})['Booker Type'] || '') : '';
    const _d = __decideType({ said: _said, recTypes: _types, producer: /producer/i.test(String(_bt)), client: (_typed && !_code) ? _typed : '', loc: _loc3, ask: true, meeting: /^(meeting|event)$/i.test(String(REQ.session_type || '').trim()) });
    if (_d.type) REQ.bookingType = _d.type;
    else {
      const _q = __tyQuestion(_d);
      const _both = _needCli && !_d.arranger;
      return [{ json: { verdict:'REJECTED', reason:'NEED_BOOKING_TYPE', askClient: _both, options: _d.ask,
        human: 'Nothing was prepared. Ask exactly this, in one message: "' + (_both ? 'Who’s the client (or "none")? And ' + _q.charAt(0).toLowerCase() + _q.slice(1) : _q)
          + '" Then prepare it again with their answer.' } }];
    }
  }
  // v73: client work needs a client - asked once, in a few words; "none" is fine. Never for Internal or Personal.
  if (_studio && /^(Advertising|Entertainment)$/.test(REQ.bookingType) && _needCli) {
    return [{ json: { verdict:'REJECTED', reason:'NEED_CLIENT',
      human: 'Nothing was prepared. Ask exactly this, in one message: "Who’s the client? (or \\"none\\")" Then prepare it again with the name exactly as they type it, or with no client if they say none.' } }];
  }
}
"""

# ---------------------------------------------------------------------------------------------------- series dates
SER_COND_OLD = "&& String(REQ.session_type || '').trim() && !String(REQ.bookingType || '').trim()) {"
SER_COND_NEW = "&& String(REQ.session_type || '').trim() && !__tyNorm(REQ.bookingType)) {   // v73: a legacy External is worked out again"
SER_OLD = ("    if (/^(localization|qc)\\b/i.test(String(REQ.session_type || '').trim())) REQ.bookingType = 'External';\n"
           "    else if (_types.length === 1) REQ.bookingType = _types[0];\n"
           "    else if (/\\b(personal|my own|own project|side project|outside (of )?hit)\\b/i.test(_said)) REQ.bookingType = 'Personal';\n"
           "    else if (/\\b(external|client work|hit work|for hit|for a client|company work)\\b/i.test(_said)) REQ.bookingType = 'External';\n")
SER_NEW = ("    // v73: the four types, the same rules as prepare mode - never asked on a series date\n"
           "    const _bt9 = _rec ? (((_rec.fields || {})['Booker Type'] || {}).name || (_rec.fields || {})['Booker Type'] || '') : '';\n"
           "    REQ.bookingType = __decideType({ said: _said, recTypes: _types, producer: /producer/i.test(String(_bt9)), client: _cl, loc: /^(localization|qc)\\b/i.test(String(REQ.session_type || '').trim()), ask: false, meeting: /^(meeting|event)$/i.test(String(REQ.session_type || '').trim()) }).type || '';\n")

# ---------------------------------------------------------------------------------------------------- "me" (71)
V70_OLD = """    if (_engIsFor && !_namedEng && (_pick === 'client' || !/engineer/i.test(_role))) {
      REQ.engineer = '';
      if (_eI !== -1) { _segs.splice(_eI, 1); REQ.description = _segs.join('|').replace(/^\\s*\\|\\s*/, ''); }"""
V70_NEW = """    if (_engIsFor && !_namedEng && (_pick === 'client' || !/engineer/i.test(_role))) {
      REQ.engineer = '';
      if (_eI !== -1) { _segs.splice(_eI, 1); REQ.description = _segs.join('|').replace(/^\\s*\\|\\s*/, ''); }
      // v73 (PENDING 71, 1 Oct DASHING): a requester who is an engineer engineers it - put in, not asked.
      if (__reqStaff && /engineer/i.test(__reqRole)) {
        REQ.engineer = String(__reqStaff.Name).trim(); REQ.__selfEng = true;
        const _s2 = String(REQ.description || '').split('|'); _s2.unshift('Engineer: ' + REQ.engineer + ' '); REQ.description = _s2.join('|');
      } else {"""
V70_RET_OLD = "      return [{ json: { verdict:'REJECTED', reason:'NEED_ENGINEER', booked_for: _pick === 'client' ? '' : _staff.Name, client: __aliasClient,"
V70_RET_NEW = "      return [{ json: { verdict:'REJECTED', reason:'NEED_ENGINEER', booked_for: _pick === 'client' ? '' : _staff.Name, client: __aliasClient,"
V70_Q_OLD = """          + 'Ask exactly this, in one message: "Who is the engineer for this session?' + _who + '"' } }];"""
V70_Q_NEW = """          + 'Ask exactly this, in one message: "Who\\u2019s engineering?"' } }];
      }"""

ME_ANCHOR = "// v71 (decided 30 Sep): no engineer named, not booked for a colleague"
ME_BLOCK = r"""// v73 (PENDING 71): "me" / "myself" / "ako" as the engineer is the requester; and when they named themselves, no note.
let __meNamed = false;
if (__prep && __reqStaff) {
  const _sgm = String(REQ.description || '').split('|'); const _eim = _sgm.findIndex(s => /^\s*engineer\s*:/i.test(s));
  const _em = (String(REQ.engineer || '').trim() || (_eim !== -1 ? _sgm[_eim].replace(/^\s*engineer\s*:\s*/i, '') : '')).trim();
  if (/^(me|myself|ako|i|i'?ll|i will|i am|i'?m)$/i.test(_em)) {
    REQ.engineer = String(__reqStaff.Name).trim(); __meNamed = true;
    if (_eim !== -1) _sgm[_eim] = ' Engineer: ' + REQ.engineer + ' '; else _sgm.unshift('Engineer: ' + REQ.engineer + ' ');
    REQ.description = _sgm.join('|').replace(/^\s+/, '');
  }
  if (/\bengineer(?:ed)?\s*(?:is|:|=|by)?\s*(?:me|myself)\b|\bi\s*(?:'m|’m| am|'ll be| will be)\s+(?:the\s+)?engineer|\bi\s*(?:'ll|’ll| will)\s+engineer\b|\bme\s+as\s+(?:the\s+)?engineer\b|\bako\s+(?:ang\s+|yung\s+)?(?:mag-?)?engineer\b|(?:^|\n)\s*(?:me|myself|ako)\s*[.!]?\s*(?:\n|$)/i.test(String(REQ.requester_text || ''))) __meNamed = true;
}

"""
V72_OLD = "      if (_isMe && !_named) __selfEngineer = String(_mf.Name).trim();"
V72_NEW = "      if (_isMe && !_named && !__meNamed) __selfEngineer = String(_mf.Name).trim();"
SELF_ANCHOR = "// --- engineer and arranger must be real people in Bookers ----------------"
SELF_ADD = ("// v73: the requester put in after \"for <colleague>\" (v70 block) gets the same note, unless they named themselves.\n"
            "if (__prep && REQ.__selfEng && !__selfEngineer && !__meNamed && __reqStaff) __selfEngineer = String(__reqStaff.Name).trim();\n\n")

# ---------------------------------------------------------------------------------------------------- shorter questions
ARR_OLD = """      human:'Nothing was prepared. Ask exactly this, in one message: "' + (_eng4 ? _eng4 + ' is down as the engineer. ' : '')
          + REQ.session_type + ' sessions usually have an arranger too - who is it, or is there none?" '"""
ARR_NEW = """      human:'Nothing was prepared. Ask exactly this, in one message: "Who\\u2019s the arranger? (or \\\\"none\\\\")" '   // v73: shorter"""
DATE_OLD = "human:'Nothing was prepared - the requester has not said which day this is for. Ask them for the date. Do not assume today or any other day.' } }];"
DATE_NEW = "human:'Nothing was prepared - the requester has not said which day. Ask exactly this: \"Which day?\" Do not assume today or any other day.' } }];"

# ---------------------------------------------------------------------------------------------------- Render Summary
RS_SHOW_OLD = """const L = ['*' + F['Title'] + '*'];
for (const k of ['Client', 'Project', 'Session Type', 'Date', 'Time', 'Room', 'Engineer', 'Arranger', 'Department', 'Booking Type', 'Booked by']) {
  if (F[k]) L.push('*' + (k === 'Project' && loc ? 'Project Code' : k) + ':* ' + F[k]);
}"""
RS_SHOW_NEW = """// v73 (PENDING 69, 1 Oct - DIGICON demo): the requester sees the title, Date, Time and Room. Every other field is still
// worked out, checked and booked - it is stored below (Store Prepared) and read back by main at the yes.
const L = ['*' + F['Title'] + '*'];
for (const k of ['Date', 'Time', 'Room']) if (F[k]) L.push('*' + k + ':* ' + F[k]);"""
RS_TYPE_OLD = "  'Booking Type': internal ? '' : String(CC.final_booking_type || REQ.bookingType || '').trim(),   // v64: what Check Conflicts settled on"
RS_TYPE_NEW = "  'Booking Type': String(CC.final_booking_type || REQ.bookingType || '').trim(),   // v64: what Check Conflicts settled on; v73: internal rooms too"
NOTES_START = "const notes = [];"
NOTES_END = "if (override) notes.push(rooms + \" isn't a usual \" + (st ? st + ' room' : 'room for this') + ' - booking it as asked.');\n"
NOTES_NEW = r"""const notes = [];
// v73: short notes - only what the requester may want to answer or should know.
const _am = Number(CC.assumed_minutes) || 0;
const _durTxt = m => { const h = Math.floor(m / 60), mm = m % 60; return (h ? h + ' hour' + (h === 1 ? '' : 's') : '') + (h && mm ? ' ' : '') + (mm ? mm + ' minutes' : ''); };
if (CC.time_proposed && F['Time'] && !allDay) notes.push('No time given, so I picked ' + F['Time'] + '. Tell me if you’d like another.');
else if (_am > 0) notes.push(_durTxt(_am) + ' - the usual for ' + (st || 'this') + '.');
if (CC.room_suggested) notes.push('I picked ' + CC.room_suggested + '. Tell me if you’d like another room.');
if (CC.self_engineer) notes.push('You’re down as the engineer.');
if (override) notes.push('Not a usual ' + (st ? st + ' ' : '') + 'room - booking it as asked.');
// the length heads-up (was Guard Probe, which read the Session Type line the summary no longer shows)
try {
  let _R3 = {}; try { _R3 = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _ty3 = (_R3.types || []).find(x => String(x.type || '').toLowerCase() === st.toLowerCase());
  const _len = start && end && !allDay ? Math.round((Date.parse(end) - Date.parse(start)) / 60000) : 0;
  if (_ty3 && _len > 0 && !_am && ((+_ty3.max && _len > +_ty3.max) || (+_ty3.min && _len < +_ty3.min)))
    notes.push('Heads up: ' + _durTxt(_len) + ' is ' + (_len > +_ty3.max ? 'longer' : 'shorter') + ' than ' + st + ' usually runs (' + _durTxt(+_ty3.min) + ' – ' + _durTxt(+_ty3.max) + ').');
} catch (e) {}
"""
HOLD_OLD = "    notes.push(st + ' usually pairs with a conference room as a holding area - if you want one, say which (Likha, Katha or Salin) before you confirm.');"
HOLD_NEW = "    notes.push('Want a holding room? (Likha, Katha or Salin)');"
OUT_OLD = """const out = L.join('\\n') + (notes.length ? '\\n\\n' + notes.map(n => '*Note:* ' + n).join('\\n') : '')
  + '\\n\\n_check ' + pbCode(F) + '_'
  + '\\n\\nReply only with "yes" to book, or "no" to change anything.\\nConfirm to book.';
return [{ json: { status: 'PREPARED', summary_text: out, title: F['Title'], needs_consent: needsConsent, new_client: newClient,"""
OUT_NEW = """// v73: no printed check code. The fingerprint is over the requester and the four lines they see; main recomputes it from
// the message at the yes and reads the full field set stored under it (Store Prepared). Keep pbKey identical in main.
const _ref = seg(/^ref\\s*:\\s*/i);
const pbKey = (ref, f) => { let h = 0x811c9dc5; const s = PB_SALT + '|key|' + String(ref || '').trim() + '|' + ['Title', 'Date', 'Time', 'Room'].map(k => pbNorm(f[k])).join('|');
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
const prepKey = _ref ? 'prep-' + pbKey(_ref, F) : '';
const out = L.join('\\n') + (notes.length ? '\\n\\n' + notes.join('\\n') : '') + '\\n\\nConfirm to book.';
return [{ json: { status: 'PREPARED', summary_text: out, title: F['Title'], needs_consent: needsConsent, new_client: newClient,
  prep_key: prepKey, prep_payload: JSON.stringify({ v: 2, ref: _ref, code: pbCode(F), F, at: new Date().toISOString() }),"""

PREP_OUT = r"""// Prepared Out (Book Session v73): hands Render Summary's result back to main unchanged - Store Prepared only saved it.
// If the save failed, the summary still goes out; at the yes main finds nothing stored and Book Session refuses
// NOT_PREPARED, so the summary is prepared again (never a booking with missing details).
return $('Render Summary').all().map(i => ({ json: Object.assign({}, i.json, { prep_stored: (function () { try { const s = $('Store Prepared').first().json || {}; return !s.error; } catch (e) { return false; } })() }) }));
"""

def fix(w):
    w["name"] = "Jessie — Book Session — v73 (types + short summary)"
    c = node(w, "Check Conflicts")["parameters"]; s = c["jsCode"]
    s = sub1(s, HELP_ANCHOR, HELPERS + HELP_ANCHOR, "helpers")
    s = between(s, PREP_START, PREP_END, PREP_NEW, "prepare type block")
    s = sub1(s, SER_COND_OLD, SER_COND_NEW, "series cond")
    s = sub1(s, SER_OLD, SER_NEW, "series type")
    s = sub1(s, V70_OLD, V70_NEW, "v70")
    s = sub1(s, V70_Q_OLD, V70_Q_NEW, "v70 question")
    s = sub1(s, ME_ANCHOR, ME_BLOCK + ME_ANCHOR, "me")
    s = sub1(s, V72_OLD, V72_NEW, "v72")
    s = sub1(s, SELF_ANCHOR, SELF_ADD + SELF_ANCHOR, "self")
    s = sub1(s, ARR_OLD, ARR_NEW, "arranger")
    s = sub1(s, DATE_OLD, DATE_NEW, "date")
    c["jsCode"] = s
    r = node(w, "Render Summary")["parameters"]; t = r["jsCode"]
    t = sub1(t, RS_TYPE_OLD, RS_TYPE_NEW, "rs type")
    t = sub1(t, RS_SHOW_OLD, RS_SHOW_NEW, "rs show")
    t = between(t, NOTES_START, NOTES_END, NOTES_NEW, "rs notes")
    t = sub1(t, HOLD_OLD, HOLD_NEW, "rs hold")
    t = sub1(t, OUT_OLD, OUT_NEW, "rs out")
    r["jsCode"] = t
    # Store Prepared (data table upsert, as Refresh Reference Cache's Save) -> Prepared Out
    rsn = node(w, "Render Summary"); x, y = rsn["position"]
    store = {"parameters": {"operation": "upsert", "dataTableId": {"__rl": True, "value": "CsdJhgDxCsqq9K9j", "mode": "list", "cachedResultName": "Jessie Reference Cache", "cachedResultUrl": "/projects/518sXYqvqTl1cuns/datatables/CsdJhgDxCsqq9K9j"},
                              "matchType": "allConditions", "filters": {"conditions": [{"keyName": "cache_key", "keyValue": "={{ $('Render Summary').first().json.prep_key || 'prep-none' }}"}]},
                              "columns": {"mappingMode": "defineBelow", "value": {"cache_key": "={{ $('Render Summary').first().json.prep_key || 'prep-none' }}", "payload": "={{ $('Render Summary').first().json.prep_payload }}", "refreshed_at": "={{ new Date().toISOString() }}"},
                                          "matchingColumns": [], "schema": [{"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "type": "string", "readOnly": False, "removed": False} for k in ("cache_key", "payload", "refreshed_at")],
                                          "attemptToConvertTypes": False, "convertFieldsToString": False}, "options": {}},
             "id": str(uuid.uuid4()), "name": "Store Prepared", "type": "n8n-nodes-base.dataTable", "typeVersion": 1, "position": [x + 224, y],
             "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput"}
    pout = copy.deepcopy(rsn); pout["id"] = str(uuid.uuid4()); pout["name"] = "Prepared Out"; pout["position"] = [x + 448, y]
    pout["parameters"] = {"jsCode": PREP_OUT}
    for k in ("executeOnce", "alwaysOutputData", "onError"): pout.pop(k, None)
    w["nodes"] += [store, pout]
    cn = w["connections"]
    if cn.get("Render Summary"): raise SystemExit("Render Summary already has outputs")
    cn["Render Summary"] = {"main": [[{"node": "Store Prepared", "type": "main", "index": 0}]]}
    cn["Store Prepared"] = {"main": [[{"node": "Prepared Out", "type": "main", "index": 0}]]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
