#!/usr/bin/env python3
"""Book Session v70 (for-person fix) + main v196 (client nickname search) - PENDING 65, live QA 30 Sep 09:30 PHT.
  scripts/build-for-person.py <book-live> <book-out> <main-live> <main-out>

"book orange studio 7 for anj" (Turn Log exec 18254 / 18257): the model put Anj - Angelo Villegas, a Music Arranger,
the colleague it is booked FOR - in the engineer slot, the client slot and the title (ORANGE / Angelo Villegas / AV), and
Jessie went on to "Angelo Villegas is down as the engineer". And "Anj" is two people: Angelo Villegas on staff (Bookers,
"Goes by ... Anj") and Angela Dela Calzada, an Advertising Producer and a client (Clients Notes "Goes by Anj"). Nothing
looked at the second: the Clients search only reads Name, so "is anj a producer" was answered "No" (exec 18250).

Book Session, prepare mode (Check Conflicts):
- A for-name that is both a staff nickname and a client's "Goes by" nickname is asked once: "Just to check - by Anj, do
  you mean Angelo Villegas (Music Arranger) or Angela Dela Calzada (Advertising Producer, a client)?" A reply naming one
  (a name, "producer" / "client", or the role) settles it; it is re-read every turn from what the requester typed.
- Picked the client: she becomes the client (the title's client segment, her Client Type as the booking type when it
  is the only one), "(for ...)" is dropped from Booked by, and the colleague is taken out of the engineer slot.
- The booked-for colleague in the engineer slot, never named as the engineer ("engineer anj", "with anj", "anj is
  engineering"), and not an engineer by role: taken out, and Jessie asks "Who is the engineer for this session?" (main's
  Booked For reads the bare answer to that question). An engineer booked for (their own session) stays.
- The booked-for colleague in the client slot, not a client on record (the in-house arrangers are, v54): dropped -
  "Client: None", and Guard Probe asks who the client is.
New node Client Aliases (Get Client -> Client Aliases -> Client Unmatched?): the clients whose Notes say "Goes by", read
only in prepare mode for an on-behalf booking; one small Airtable read, never fails the booking.

main v196: the Clients tool also finds a client by a "Goes by" nickname in Notes; Booked For reads the first "Goes by"
nickname of an Info that ends in a line break (the same fix as Check Conflicts).
"""
import json, sys, copy, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label, n=1):
    if s.count(old) != n: raise SystemExit(f"{label}: expected {n} match(es), found {s.count(old)}")
    return s.replace(old, new)

CC_ANCHOR = "// v62 (live QA 29 Sep): a change right after a booking is a move of that booking."
CC_BLOCK = r"""// v70 (PENDING 65, live QA 30 Sep 09:30): "book orange studio 7 for anj" - the colleague booked FOR (Angelo Villegas,
// a Music Arranger, "Anj") went into the engineer slot, the client slot and the title. And "Anj" is also a client,
// Angela Dela Calzada (Clients Notes "Goes by Anj"). Settled here from what the requester typed, every turn.
let __aliasClient = '';
if (__prep) {
  const _k = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
  const _esc = s => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const _forWho = ((String(REQ.description || '').match(/\(for\s+([^)]+)\)/i) || [])[1] || '').trim();
  const _rt = String(REQ.requester_text || ''), _rtk = ' ' + _k(_rt) + ' ';
  let _bk = []; try { _bk = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) {}
  const _staff = _bk.find(f => _k(f.Name) === _k(_forWho));
  if (_forWho && _staff) {
    const _info = String(_staff.Info || ''), _gb = _info.match(/goes by\s+([^\n]*)/i);
    const _role = _info.split(/,|\bgoes by\b/i)[0].trim();
    const _sKeys = [...new Set([_k(_staff.Name), _k(String(_staff.Name).split(/\s+/)[0])]
      .concat(_gb ? _gb[1].split(/,|\band\b/i).map(_k) : []).filter(a => a.length >= 2))];
    // the word(s) typed after "for" / "on behalf of" that name this colleague
    const _typedFor = [];
    { const re = /\b(?:on\s+behalf\s+of|for)\s+([a-z0-9ñ][\w.'’-]*(?:\s+[a-z0-9ñ][\w.'’-]*)?)/gi; let m;
      while ((m = re.exec(_rt))) { const w = m[1].split(/\s+/); for (const c of [w.join(' '), w[0]]) if (_sKeys.indexOf(_k(c)) !== -1) { _typedFor.push(_k(c)); break; } } }
    // --- the same nickname is also a client's -------------------------------------------------------------------
    let _al = []; try { _al = $('Client Aliases').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) {}
    const _amb = _al.map(f => { const g = String(f.Notes || '').match(/goes by\s+([^.\n]*)/i);
        return { f, keys: (g ? g[1].split(/,|\band\b|\bor\b/i).map(_k) : []).filter(a => a.length >= 2) }; })
      .find(c => _typedFor.some(w => c.keys.indexOf(w) !== -1) && _k(c.f.Name) !== _k(_staff.Name));
    let _pick = '';
    if (_amb) {
      const _alias = _typedFor.find(w => _amb.keys.indexOf(w) !== -1);
      const _cLabel = String((_amb.f['Booker Type'] && (_amb.f['Booker Type'].name || _amb.f['Booker Type'])) || '').trim();
      const _words = s => _k(s).split(' ').filter(t => t.length >= 4 && t !== _alias);
      const _has = t => _rtk.indexOf(' ' + t + ' ') !== -1;
      const _cSide = _words(_amb.f.Name).some(_has) || _words(_cLabel).slice(-1).some(_has) || /\bproducer\b/i.test(_rt)
        || /(?<!\bno\s)(?<!\bwithout\s)(?<!\bwithout\san\s)(?<!\bwithout\sa\s)\bclient\b(?!\s*(?:is\s+|:\s*)?(?:none|n\/?a|wala)\b)/i.test(_rt);
      const _sSide = _words(_staff.Name).some(_has) || _words(_role).slice(-1).some(_has) || /\b(colleague|staff|teammate)\b/i.test(_rt);
      if (_cSide && !_sSide) _pick = 'client';
      else if (_sSide && !_cSide) _pick = 'staff';
      else {
        const _say = s => s.replace(/^./, c => c.toUpperCase());
        return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_PERSON', typed: _alias, staff: _staff.Name, client: _amb.f.Name,
          human:'Nothing was prepared. Ask exactly this, in one message: "Just to check - by ' + _say(_alias) + ', do you mean ' + _staff.Name
            + (_role ? ' (' + _role + ')' : '') + ' or ' + _amb.f.Name + ' (' + (_cLabel ? _cLabel + ', a client' : 'a client') + ')?"' } }];
      }
    }
    const _t = String(REQ.summary || '').split(' / ').map(s => s.trim());
    const _isS = s => !!s && _sKeys.indexOf(_k(s)) !== -1;
    const _cNow = String(REQ.client || '').trim() || (_t.length >= 3 ? _t[1] : '');
    if (_pick === 'client') {
      // the requester meant the client: she is the client, and nobody is booked FOR
      __aliasClient = String(_amb.f.Name).trim();
      REQ.client = __aliasClient;
      if (_t.length >= 3) _t[1] = __aliasClient; else if (_t.length === 2) _t.splice(1, 0, __aliasClient);
      REQ.summary = _t.join(' / ');
      REQ.description = String(REQ.description || '').replace(/\s*\(for\s+[^)]+\)/i, '');
      const _ct = [].concat(_amb.f['Client Type'] || []).map(x => String((x && x.name) || x));
      if (!String(REQ.bookingType || '').trim() && _ct.length === 1) REQ.bookingType = _ct[0];
    } else if (_isS(_cNow)) {
      // the colleague is not the client - unless they are a client on record too (the in-house arrangers, v54)
      let _onRec = false; try { _onRec = $('Get Client').all().some(i => i.json && i.json.id && _k((i.json.fields || {}).Name) === _k(_staff.Name)); } catch (e) {}
      if (!_onRec && !new RegExp('\\b(?:client|produ[a-z]*)\\s*(?:is|:|=)?\\s*(?:' + _sKeys.map(_esc).join('|') + ')\\b', 'i').test(_k(_rt))) {
        REQ.client = '';
        if (_t.length >= 3 && _isS(_t[1])) REQ.summary = [_t[0], _t[_t.length - 1]].join(' / ');
      }
    }
    // --- the colleague in the engineer slot ------------------------------------------------------------------------
    const _segs = String(REQ.description || '').split('|');
    const _eI = _segs.findIndex(s => /^\s*engineer\s*:/i.test(s));
    const _eng = (String(REQ.engineer || '').trim() || (_eI !== -1 ? _segs[_eI].replace(/^\s*engineer\s*:\s*/i, '') : '')).replace(/\s*\([^)]*\)\s*$/, '').trim();
    const _engIsFor = !!_eng && (_isS(_eng) || _k(_eng) === _k(_staff.Name));
    const _kr = '(?:' + _sKeys.map(_esc).join('|') + ')';
    const _namedEng = new RegExp('\\bengineer(?:\\s+(?:is|will be|=))?\\s*[:=-]?\\s+' + _kr + '\\b|\\bengineered\\s+by\\s+' + _kr + '\\b|\\b' + _kr
      + '\\s+(?:is\\s+|will\\s+|as\\s+)?(?:the\\s+)?engineer(?:ing)?\\b|\\bwith\\s+' + _kr + '\\b', 'i').test(_k(_rt));
    if (_engIsFor && !_namedEng && (_pick === 'client' || !/engineer/i.test(_role))) {
      REQ.engineer = '';
      if (_eI !== -1) { _segs.splice(_eI, 1); REQ.description = _segs.join('|').replace(/^\s*\|\s*/, ''); }
      const _who = _pick === 'client' ? '' : ' (' + String(_staff.Name).split(/\s+/)[0] + ' is who it is booked for' + (_role ? ', a ' + _role : '') + ')';
      return [{ json: { verdict:'REJECTED', reason:'NEED_ENGINEER', booked_for: _pick === 'client' ? '' : _staff.Name, client: __aliasClient,
        human:'Nothing was prepared. ' + (_pick === 'client' ? 'The client is ' + __aliasClient + ' (not a colleague it is booked for), so leave booked_for empty and pass client "' + __aliasClient + '". ' : '')
          + 'Ask exactly this, in one message: "Who is the engineer for this session?' + _who + '"' } }];
    }
  }
}
"""

V50_OLD = "  if (_rt.trim() && _cl && !_code && !_found && !_err && (' ' + _nz(_rt) + ' ').indexOf(' ' + _nz(_cl) + ' ') === -1) {"
V50_NEW = "  if (_rt.trim() && _cl && !_code && !_found && !_err && _nz(_cl) !== _nz(typeof __aliasClient === 'undefined' ? '' : __aliasClient) && (' ' + _nz(_rt) + ' ').indexOf(' ' + _nz(_cl) + ' ') === -1) {   // v70: or a client picked by nickname"
OUT_OLD = "assumed_minutes: __assumedMins,"
OUT_NEW = "assumed_minutes: __assumedMins, client_known: typeof __aliasClient !== 'undefined' && !!__aliasClient,"

RS_OLD = "  && !clientRows.some(r => r.id) && !clientRows.some(r => r.error);"
RS_NEW = "  && !clientRows.some(r => r.id) && !clientRows.some(r => r.error) && !CC.client_known;   // v70: a client found by nickname"

ALIAS_FORMULA = r"""={{ (function(){
  // v70: only for an on-behalf booking being prepared - the clients whose Notes give a "Goes by" nickname, so a for-name
  // that is also a client's nickname ("Anj") can be asked about. A small read; never fails the booking.
  var R = $('When Executed by Another Workflow').first().json || {};
  if (String(R.mode || '').trim().toLowerCase() !== 'prepare' || !/\(for\s+[^)]+\)/i.test(String(R.description || ''))) { return 'FALSE()'; }
  return "SEARCH('goes by', LOWER({Notes} & ''))";
})() }}"""

MAIN_OLD = """  return "SEARCH('" + v + "', LOWER({Name}))";"""
MAIN_NEW = """  // v196: also a "Goes by" nickname in Notes - "is anj a producer" found no one (Angela Dela Calzada goes by Anj).
  var w = v.replace(/[^a-z0-9ñ ]/g, '');
  return "OR(SEARCH('" + v + "', LOWER({Name})), AND(SEARCH('goes by', LOWER({Notes} & '')), REGEX_MATCH(LOWER({Notes} & ''), '(^|[^a-z])" + w + "($|[^a-z])')))";"""

def book(w):
    w["name"] = "Jessie — Book Session — v70 (for-person fix)"
    c = node(w, "Check Conflicts")["parameters"]
    s = sub1(c["jsCode"], CC_ANCHOR, CC_BLOCK + CC_ANCHOR, "cc anchor")
    s = sub1(s, V50_OLD, V50_NEW, "v50")
    s = sub1(s, OUT_OLD, OUT_NEW, "outputs", 2)
    # Info that ends in a line break (Angelo Villegas, Rico Gonzales, Alec Elijah Gan, Cristel Cube) never matched
    # "goes by (.*)$" - the first nickname after "Goes by" was lost. Same reading otherwise.
    s = sub1(s, r"/goes by\s+(.*)$/i", r"/goes by\s+([^\n]*)/i", "cc goes-by", 2)
    s = sub1(s, r"/goes by.*$/i", r"/goes by[^\n]*/i", "cc role", 1)
    c["jsCode"] = s
    r = node(w, "Render Summary")["parameters"]; r["jsCode"] = sub1(r["jsCode"], RS_OLD, RS_NEW, "render")
    g = node(w, "Get Client")
    a = copy.deepcopy(g)
    a["id"] = str(uuid.uuid4()); a["name"] = "Client Aliases"; a["position"] = [g["position"][0] + 112, g["position"][1] + 176]
    a["parameters"]["filterByFormula"] = ALIAS_FORMULA
    a["parameters"]["options"] = {"fields": ["Name", "Notes", "Client Type", "Booker Type"]}
    w["nodes"].append(a)
    if w["connections"]["Get Client"] != {"main": [[{"node": "Client Unmatched?", "type": "main", "index": 0}]]}:
        raise SystemExit("Get Client wiring changed")
    w["connections"]["Get Client"] = {"main": [[{"node": "Client Aliases", "type": "main", "index": 0}]]}
    w["connections"]["Client Aliases"] = {"main": [[{"node": "Client Unmatched?", "type": "main", "index": 0}]]}
    return w

def main(w):
    w["name"] = "Project Jessie — v196 (client nickname search)"
    t = node(w, "Clients")["parameters"]; t["filterByFormula"] = sub1(t["filterByFormula"], MAIN_OLD, MAIN_NEW, "clients")
    bf = node(w, "Booked For")["parameters"]; bf["jsCode"] = sub1(bf["jsCode"], r"/goes by\s+(.*)$/i", r"/goes by\s+([^\n]*)/i", "booked-for goes-by", 2)
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
