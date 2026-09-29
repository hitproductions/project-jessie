#!/usr/bin/env python3
"""main v193 (turn log + small fixes) + Book Session v67 (series booking type) - 29 Sep 2026, evening.
  scripts/build-turn-log-bundle.py <main-live> <main-out> <book-live> <book-out>

Turn log   From 29 Sep Claude cannot read n8n's executions, so every turn now appends one row to a new "Turn Log"
           tab of the Jessie Log spreadsheet: time (PHT), execution id, who, their message, which path answered
           (agent / book direct / cancel direct / already done / duplicate dropped), each tool with its key inputs and
           result, the reply, Guard Probe's claim check, seconds from message to reply, and the build. Read through the
           Google connector. Off Send Reply (and the dropped-duplicate branch); cannot fail a turn.
           Needs the tab created with the header row: Time, Exec, User, Message, Path, Tools, Reply, Claim, Seconds, Build
PENDING 61 A plain "no" to a move card offered the corrected move again (the earlier "3-6pm not 6-7" still counted as a
           change of the booking just made). Booked For: a "no" answering a move card ends the change - no move
           times, and the model is told nothing is moved.
PENDING 59 Series summaries lost their bold labels (" Time: ..."); Guard Probe puts them back on a series summary.
           Book Session v67: each date of a series now gets its booking type (Type: on the event) - from the client's
           one Client Type, the requester's own words, or External for Localization; never asked (it used to be
           worked out only in prepare mode).
Bug 10     "this week" answers did not say which dates were checked: when the reply names no date, Guard Probe adds
           "Dates checked: ..." from this turn's availability checks.
"""
import json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

SHEET_ID = "1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo"
TURN_ROW = r"""// Turn Log Row (main v193). From 29 Sep nobody's scripts read n8n's executions, so each turn leaves one row in the
// Jessie Log sheet's "Turn Log" tab for diagnosis. Reads only nodes on the main path (never a tool node - gotcha 11)
// and never throws: a failure here only means a missing log row.
const clip = (s, n) => { s = String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n) + '...' : s; };
const has = n => { try { $(n).first(); return true; } catch (e) { return false; } };
const row = { Time: '', Exec: '', User: '', Message: '', Path: '', Tools: '', Reply: '', Claim: '', Seconds: '', Build: '' };
try {
  const t = $('Slack Trigger').first().json || {};
  row.Time = new Date().toLocaleString('en-CA', { timeZone: 'Asia/Manila', hour12: false }).replace(',', '');
  row.Exec = String($execution.id || '');
  row.User = String(t.user || '');
  try { row.User = ((($('Get Booker').first() || {}).json || {}).fields || {}).Name || row.User; } catch (e) {}
  row.Message = clip(t.text, 1000);
  const inp = ($input.first() || {}).json || {};
  row.Path = inp._dup ? 'duplicate dropped' : has('Book Direct') ? 'book direct' : has('Cancel Direct') ? 'cancel direct'
    : has('Already Done Reply') ? 'already done' : 'agent';
  let steps = []; try { steps = ((($('Jessie AI Agent').first() || {}).json || {}).intermediateSteps) || []; } catch (e) {}
  const KEYS = ['title', 'booking_date', 'start', 'end', 'new_start', 'new_end', 'rooms', 'window_start', 'window_end', 'window_room', 'engineer', 'client', 'summary'];
  row.Tools = clip(steps.map(s => {
    const a = (s && s.action) || {}, ti = a.toolInput || {};
    const args = KEYS.filter(k => ti[k] !== undefined && ti[k] !== '').map(k => k + '=' + clip(ti[k], 60)).join(', ');
    let o = null; try { o = [].concat(JSON.parse(String(s.observation || '')))[0]; } catch (e) {}
    const res = o ? [o.status || o.verdict || '', o.reason || ''].filter(Boolean).join(' ') : clip(s.observation, 60);
    return (a.tool || '?') + '(' + args + ') -> ' + res;
  }).join(' | '), 6000);
  if (!steps.length && has('Book Direct')) { try { const r = $('Book Direct').first().json || {}; row.Tools = 'Book Direct -> ' + (r.status || r.verdict || '') + ' ' + (r.reason || ''); } catch (e) {} }
  if (!steps.length && has('Cancel Direct')) { try { const r = $('Cancel Direct').first().json || {}; row.Tools = 'Cancel Direct -> ' + (r.status || r.verdict || '') + ' ' + (r.reason || ''); } catch (e) {} }
  row.Reply = inp._dup ? '(nothing sent: a late copy of a message already answered)' : clip((inp.message && inp.message.text) || inp.text || '', 1500);
  try { row.Claim = String((($('Guard Probe').first() || {}).json || {}).claimProbe || ''); } catch (e) {}
  const ts = parseFloat(String(t.ts || '0')) || 0;
  if (ts) row.Seconds = ((Date.now() / 1000) - ts).toFixed(1);
  row.Build = String(($workflow && $workflow.name) || '');
} catch (e) { row.Reply = row.Reply || ('(log error: ' + e.message + ')'); }
return [{ json: row }];
"""

BF_ANCHOR = "  out.justBooked = null; out.changeJustBooked = false;\n  try {\n    if (__bookedAt > 0 && mine.length) {"
BF_NEW = """  out.justBooked = null; out.changeJustBooked = false;
  // v193 (PENDING 61): a plain "no" to a move card ends the change. It used to count the earlier change message again
  // and offer the (corrected) move once more; the second "no" was needed to stop it.
  const __movedNo = /^\\s*(no|nope|nah|hindi|huwag|wag|ayaw|cancel(?: it| that)?|never ?mind|forget it|don'?t|stop)\\s*[.!]*\\s*$/i.test(String(mine[0] || ''))
    && /Move it\\? Reply yes or no\\.|Confirm to move\\./i.test(String(theirs[0] || ''));
  if (__movedNo) notes.push('THEY SAID NO TO THE MOVE: nothing is moved. Say so in one line and ask what they would like instead. Do not show a move again unless they ask for one.');
  try {
    if (!__movedNo && __bookedAt > 0 && mine.length) {"""

GP_ANCHOR = "// 29 Sep: the confirmation goes out as one line"
GP_NEW = r"""// --- v193 (PENDING 59): a series summary's detail lines keep their bold labels --------------------------------------
// The dates list is rebuilt in code; the model's other lines came out as " Time: 10:00 AM - 12:00 PM".
if (!_prepared && /\*Dates \(\d+\):\*/.test(text))
  text = text.replace(/^[ \t]*\*?(Time|Rooms?|Session Type|Client|Project|Engineer|Arranger|Department|Booking Type)\*?:\*?[ \t]*/gim, '*$1:* ');

// --- v193 (QA bug 10): "this week" / "next week" - say which dates were checked ------------------------------------------
try {
  const _said = String(($('Slack Trigger').first().json || {}).text || '');
  const _hasDate = /\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/i;
  if (!_prepared && /\b(?:this|next)\s+week\b/i.test(_said) && !_hasDate.test(text)) {
    const _st = (($input.first().json || {}).intermediateSteps) || [], _ds = new Set();
    for (const s of _st) { const ti = ((s || {}).action || {}).toolInput || {}; for (const k of ['window_start', 'booking_date', 'start']) { const m = String(ti[k] || '').match(/\d{4}-\d{2}-\d{2}/); if (m) _ds.add(m[0]); } }
    const _d = [..._ds].sort();
    if (_d.length) {
      const _f = iso => new Date(iso + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
      const _y = _d[_d.length - 1].slice(0, 4);
      const _run = _d.length > 2 && _d.every((x, i) => !i || (new Date(x) - new Date(_d[i - 1])) === 86400000);
      text = text.trim() + '\n\nDates checked: ' + (_run ? _f(_d[0]) + ' to ' + _f(_d[_d.length - 1]) : _d.map(_f).join('; ')) + ', ' + _y + '.';
    }
  }
} catch (e) {}

"""

BS_ANCHOR = "// v54 - PENDING 29 (Howard, 2026-09-28): a Music session whose type lists a Music Arranger always gets asked for"
BS_NEW = r"""// v67 (PENDING 59): a series books each date outside prepare mode, and the model sends no booking type, so the events
// had no "Type:". Worked out the same way as in prepare mode - never asked: the client's one Client Type, the
// requester's own words, or External for Localization.
if (!__prep && (REQ.series === true || String(REQ.series).toLowerCase() === 'true') && String(REQ.session_type || '').trim() && !String(REQ.bookingType || '').trim()) {
  try {
    const _nz = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9&]+/g, ' ').trim();
    const _t = String(REQ.summary || '').split(' / ').map(s => s.trim());
    const _cl = String(REQ.client || '').trim() || (_t.length >= 3 ? _t[1] : '');
    let _rows = []; try { _rows = $('Get Client').all().map(i => (i && i.json) || {}).filter(r => r && r.id); } catch (e) {}
    const _rec = _cl ? _rows.find(r => _nz((r.fields || {}).Name) === _nz(_cl)) : null;
    const _types = _rec ? [].concat((_rec.fields || {})['Client Type'] || []).map(x => String((x && x.name) || x)) : [];
    const _said = String(REQ.requester_text || '');
    if (/^(localization|qc)\b/i.test(String(REQ.session_type || '').trim())) REQ.bookingType = 'External';
    else if (_types.length === 1) REQ.bookingType = _types[0];
    else if (/\b(personal|my own|own project|side project|outside (of )?hit)\b/i.test(_said)) REQ.bookingType = 'Personal';
    else if (/\b(external|client work|hit work|for hit|for a client|company work)\b/i.test(_said)) REQ.bookingType = 'External';
  } catch (e) {}
}

"""

def main_fix(w):
    w["name"] = "Project Jessie — v193 (turn log + small fixes)"
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF_ANCHOR, BF_NEW, "bf")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_NEW + GP_ANCHOR, "gp")
    sr = node(w, "Send Reply"); x, y = sr["position"]
    code = {"parameters": {"jsCode": TURN_ROW}, "id": str(uuid.uuid4()), "name": "Turn Log Row", "type": "n8n-nodes-base.code",
            "typeVersion": 2, "position": [x + 160, y + 176], "onError": "continueRegularOutput"}
    rp = node(w, "Read Pending Consent")
    sheet = {"parameters": {"authentication": "serviceAccount", "operation": "append",
                            "documentId": {"__rl": True, "mode": "id", "value": SHEET_ID},
                            "sheetName": {"__rl": True, "mode": "name", "value": "Turn Log"},
                            "columns": {"mappingMode": "autoMapInputData", "matchingColumns": [], "schema": [], "value": {}}, "options": {}},
             "id": str(uuid.uuid4()), "name": "Log Turn", "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5,
             "position": [x + 336, y + 176], "credentials": rp["credentials"], "onError": "continueRegularOutput", "alwaysOutputData": True}
    w["nodes"] += [code, sheet]
    C = w["connections"]
    if [t["node"] for t in C["Send Reply"]["main"][0]] != ["Clear Ack"]: raise SystemExit("Send Reply wiring changed")
    C["Send Reply"]["main"][0].append({"node": "Turn Log Row", "type": "main", "index": 0})
    if [t["node"] for t in C["Duplicate?"]["main"][0]] != ["Clear Ack"]: raise SystemExit("Duplicate? wiring changed")
    C["Duplicate?"]["main"][0].append({"node": "Turn Log Row", "type": "main", "index": 0})
    C["Turn Log Row"] = {"main": [[{"node": "Log Turn", "type": "main", "index": 0}]]}
    return w

def book_fix(w):
    w["name"] = "Jessie — Book Session — v67 (series booking type)"
    c = node(w, "Check Conflicts")["parameters"]; c["jsCode"] = sub1(c["jsCode"], BS_ANCHOR, BS_NEW + BS_ANCHOR, "bs")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(book_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
