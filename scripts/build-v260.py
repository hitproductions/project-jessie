#!/usr/bin/env python3
"""main v260 + Cancel Booking v26 + Move Booking v27 - PENDING 72 (two bookings with the same title on one day).

  1 Oct 11:07 (QASER at 10-12 and 3-5 on 2 Nov): Move Direct passed only the title and the date and got AMBIGUOUS_TITLE at
  the yes; Cancel / Move before the card answered "more than one booking ... Ask the requester which one they mean" - an
  instruction the model worded - and nothing carried the answer back, so the next call was refused the same way.
Cancel Booking v26 / Move Booking v27: a new input booking_time ("HH:MM", Manila start). Two or more bookings with the title
  -> the one starting at booking_time; still several -> a code question, word for word: 'There are two bookings named
  "QASER" on Tuesday, November 2: - 10:00 AM – 12:00 PM, Studio 7 - 3:00 PM – 5:00 PM, Studio 7  Which one should I cancel?'
main v260:
  - Booked For: whichTime - after Jessie's "Which one should I cancel / move?" (or "do you mean?"), the requester's answer read
    as a start time: a clock time ("the 3pm one", "3-5"), or an order ("the first", "the second", "the later one") against the
    times Jessie listed. approvedMove carries now_start (the card's Now: line).
  - Prepare Cancel, Cancel Booking, Move Booking pass booking_time = whichTime; Move Direct passes the card's now_start.
  - Guard Probe relays the quoted question of Prepare Cancel / Cancel Booking / Move Booking word for word, as Book Session's.

  scripts/build-v260.py <main-v259> <main-out> <cancel-v25> <cancel-out> <move-v26> <move-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

PICK = r"""// v26/v27 (PENDING 72): two or more bookings with this title - the one starting at booking_time (the requester's answer to
// "Which one ...?", or the card's Now: time at the yes); else one question, word for word
const __bt = (String(REQ.booking_time || '').match(/^(\d{1,2}):(\d{2})/) || []).slice(1).map(Number);
const __hm = e => { const s = e && e.start && e.start.dateTime; if (!s) return ''; const d = new Date(new Date(s).getTime() + 8 * 3600000); return String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0'); };
const __pickT = list => { if (__bt.length !== 2) return null; const k = String(__bt[0]).padStart(2, '0') + ':' + String(__bt[1]).padStart(2, '0'); const one = list.filter(e => __hm(e) === k); return one.length === 1 ? one[0] : null; };
const __numW2 = n => ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'][n] || String(n);
const __whichQ = (title, list, verb) => {
  const t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
  const s0 = list[0].start && (list[0].start.dateTime || list[0].start.date);
  const day = new Date(/^\d{4}-\d{2}-\d{2}$/.test(String(s0)) ? s0 + 'T12:00:00+08:00' : s0).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
  return 'There are ' + __numW2(list.length) + ' bookings named "' + title + '" on ' + day + ':\n'
    + list.slice().sort((a, b) => String(a.start.dateTime || a.start.date).localeCompare(String(b.start.dateTime || b.start.date)))
      .map(e => '- ' + (e.start && e.start.dateTime ? t(e.start.dateTime) + ' – ' + t(e.end.dateTime) : 'all day')).join('\n') + '\nWhich one should I ' + verb + '?'; };
"""

# ---- Cancel Booking v26
C_HELP_ANCHOR = "const when = e => {"
C_NODATE_OLD = "  else if (_ord.length > 1) {\n    const _q = __dupQ("
C_NODATE_NEW = "  else if (_ord.length > 1 && __pickT(_ord.map(o => o.x))) { ev = __pickT(_ord.map(o => o.x)); how = 'title + time'; }   // v26\n  else if (_ord.length > 1) {\n    const _q = __dupQ("
C_DATED_OLD = '  else if (hits.length > 1) {\n    return [{ json: { verdict:\'REJECTED\', reason:\'AMBIGUOUS_TITLE\',\n      human: \'Nothing was cancelled - more than one booking on that date is titled "\' + wantedTitle + \'":\\n\'\n        + hits.map(e => \'- \' + e.summary + \' \' + when(e)).join(\'\\n\')\n        + \'\\nAsk the requester which one they mean, then prepare the cancel again with that exact title.\' } }];\n  }'
C_DATED_NEW = '  else if (hits.length > 1 && __pickT(hits)) { ev = __pickT(hits); how = \'title + time\'; }   // v26 (PENDING 72)\n  else if (hits.length > 1) {\n    const _q = __whichQ(hits[0].summary, hits, \'cancel\');\n    return [{ json: { verdict:\'REJECTED\', reason:\'AMBIGUOUS_TITLE\', ask: _q,\n      human: \'Nothing was cancelled. Ask exactly this, in one message: "\' + _q.replace(/"/g, \'\\\\"\') + \'" Then prepare the cancel again with the same title and date.\' } }];\n  }'

# ---- Move Booking v27
M_HELP_ANCHOR = "const when = e => {"
M_OLD = """  else if (hits.length > 1) return bad('AMBIGUOUS_TITLE',
      'Nothing was moved - more than one booking on that date is titled "' + wantedTitle + '":\\n'
        + hits.map(e => '- ' + e.summary + ' ' + when(e)).join('\\n')
        + '\\nAsk the requester which one they mean, then call Move Booking again with that exact title.');"""
M_NEW = """  else if (hits.length > 1 && __pickT(hits)) { ev = __pickT(hits); how = 'title + time'; }   // v27 (PENDING 72)
  else if (hits.length > 1) { const _q = __whichQ(hits[0].summary, hits, 'move');
    return bad('AMBIGUOUS_TITLE', 'Nothing was moved. Ask exactly this, in one message: "' + _q.replace(/"/g, '\\\\"') + '" Then call Move Booking again with the same title, date and new time.'); }"""

# ---- main v260
BF_WT_ANCHOR = "  const said = [];\n"
BF_WT = r"""  // v260 (PENDING 72): the answer to Jessie's "Which one should I cancel / move?" as the booking's start time - a clock time
  // ("the 3pm one", "3-5") or an order ("the first", "the later one") against the times she listed
  out.whichTime = '';
  try {
    const _jq = String(theirs[0] || '');
    if (/\bWhich one (?:should I (?:cancel|move)|do you mean)\?\s*$/i.test(_jq) && mine.length) {
      const _ans = String(mine[0] || ''), _h24 = (h, m, ap) => { let x = +h % 12; if (/p/i.test(ap)) x += 12; return String(x).padStart(2, '0') + ':' + String(m || '00').padStart(2, '0'); };
      const _listed = [..._jq.matchAll(/^-\s*(?:[^\n]*?,\s*)?(\d{1,2}):(\d{2})\s*([AP]M)\s*[–-]/gim)].map(m => _h24(m[1], m[2], m[3]));
      const _r = allRanges(_ans), _c = _ans.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|nn|noon)\b/i);
      let _t = _r.length ? _r[0].s : _c ? hm(_c[1], _c[2], _c[3]) : '';
      if (!_t && _listed.length) {
        if (/\b(?:first|1st|earlier|earliest|morning|am one)\b/i.test(_ans)) _t = _listed[0];
        else if (/\b(?:second|2nd|later|latest|last|afternoon|evening|pm one)\b/i.test(_ans)) _t = _listed[/\b(?:second|2nd)\b/i.test(_ans) ? 1 : _listed.length - 1] || '';
        else { const _b = _ans.match(/^\s*(?:the\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:one)?\s*[.!]?\s*$/i);
          if (_b) { const _cand = _listed.filter(x => +x.slice(0, 2) % 12 === +_b[1] % 12 && (!_b[2] || x.slice(3) === _b[2])); if (_cand.length === 1) _t = _cand[0]; } }
      }
      if (_t) out.whichTime = _t;
    }
  } catch (e) {}
"""
BF_AM_OLD = "              to_line: String(_ml).trim(), date_label: String(_nl).trim().split(/,\\s*\\d{1,2}:\\d{2}/)[0],"
BF_AM_NEW = "              now_start: _h(_n3[4], _n3[5], _n3[6]),   // v260: the card's Now: start, to pick between same-titled bookings\n              to_line: String(_ml).trim(), date_label: String(_nl).trim().split(/,\\s*\\d{1,2}:\\d{2}/)[0],"
GP_RELAY_OLD = "    if (!/^(prepare booking|book session|prepare series)$/.test(_t9)) continue;   // v225: Prepare Series' questions too"
GP_RELAY_NEW = "    if (!/^(prepare booking|book session|prepare series|prepare cancel|cancel booking|move booking)$/.test(_t9)) continue;   // v225: Prepare Series; v260: cancel / move questions too"

def add_input(node_params, name, value):
    wi = node_params["workflowInputs"]
    if not any(s.get("id") == name for s in wi.get("schema", [])):
        wi.setdefault("schema", []).append({"canBeUsedToMatch": True, "defaultMatch": False, "display": True, "displayName": name, "id": name, "required": False, "type": "string"})
    wi["value"][name] = value

def main(w):
    w["name"] = "Project Jessie — v260 (same-title bookings)"
    bf = node(w, "Booked For")["parameters"]; c = bf["jsCode"]
    c = once(c, BF_WT_ANCHOR, BF_WT + BF_WT_ANCHOR, "whichTime"); c = once(c, BF_AM_OLD, BF_AM_NEW, "now_start"); bf["jsCode"] = c
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], GP_RELAY_OLD, GP_RELAY_NEW, "relay")
    for n in ("Prepare Cancel", "Cancel Booking", "Move Booking"):
        add_input(node(w, n)["parameters"], "booking_time", "={{ String((($('Booked For').first() || {}).json || {}).whichTime || '') }}")
    add_input(node(w, "Move Direct")["parameters"], "booking_time", "={{ String(((($('Booked For').first() || {}).json || {}).approvedMove || {}).now_start || (($('Booked For').first() || {}).json || {}).whichTime || '') }}")
    return w

def sub(w, name, node_name, edits, title):
    w["name"] = title
    n = node(w, node_name)["parameters"]; c = n["jsCode"]
    c = once(c, C_HELP_ANCHOR, PICK + C_HELP_ANCHOR, "helpers")
    for o, nn, k in edits: c = once(c, o, nn, k)
    n["jsCode"] = c
    trig = next(x for x in w["nodes"] if x["type"].endswith("executeWorkflowTrigger"))["parameters"]["workflowInputs"]["values"]
    if not any(v.get("name") == "booking_time" for v in trig): trig.append({"name": "booking_time"})
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 6: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(sub(json.load(open(a[2])), "cancel", "Check Ownership", [(C_NODATE_OLD, C_NODATE_NEW, "no date"), (C_DATED_OLD, C_DATED_NEW, "dated")], "Jessie — Cancel Booking — v26 (same-title bookings)"), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
    json.dump(sub(json.load(open(a[4])), "move", "Resolve Booking", [(M_OLD, M_NEW, "move dated")], "Jessie — Move Booking — v27 (same-title bookings)"), open(a[5], "w"), indent=2, ensure_ascii=False); print("wrote", a[5])
