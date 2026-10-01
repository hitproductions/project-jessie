#!/usr/bin/env python3
"""Cancel Booking v21 + main v204 (short cancel + series cards) - PENDING 69, 1 Oct.
  scripts/build-short-cards.py <cancel-live> <cancel-out> <main-live> <main-out>

Every card the requester sees is now the short form - title, date(s), time, room - with nothing printed for the system.
Cancel Booking v21: the cancel card drops its `_check` line (and "Booked by" when the requester is the booker). The
  check it did is kept by matching what the card shows: at the yes, main passes the card's Time and Room lines, and
  Cancel Booking cancels only the booking of that title, on that date, whose time and room are still exactly those -
  anything changed since the card was shown is refused (CHANGED), as the code did. Ownership is checked as before.
main v204: Prepared Cancel reads a card without a code (title, date, time, room) and Cancel Direct / the model's Cancel
  Booking call pass the time and room; the "_Next:" lines of a two-cancel card go above the confirmation (they were
  put after the code); Gate Context knows a cancel card without a code. Series summaries (model-written, PENDING 59)
  are cut by Guard Probe to the title, the Dates list, Time and Room - the model keeps its full version in memory for
  the yes, and Book Series / Book Session still fill and check every detail.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ------------------------------------------------------------------------------------------------ Cancel Booking v21
CX_ANCHOR = "let prepareMode = String(REQ.mode || '').toLowerCase() === 'prepare';"
CX_HELP = r"""// v21: the card's Time line, as rendered below - at the yes the booking must still show exactly this time and room.
const cxTime = e => { const s = (e.start && (e.start.dateTime || e.start.date)) || '', en = (e.end && (e.end.dateTime || e.end.date)) || '';
  if (!(e.start && e.start.dateTime)) return 'All day';
  const t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
  return t(s) + ' – ' + t(en); };
const cxN = s => String(s || '').replace(/[*_]/g, '').replace(/\s+/g, ' ').replace(/\s*[–—-]\s*/g, ' – ').trim().toLowerCase();
const wantTime = String(REQ.card_time || '').trim(), wantRoom = String(REQ.card_room || '').trim();
"""
CX_MATCH_OLD = """if (wantCode) {
  // A yes to a prepared card: only the booking of that exact title whose current details still give the card's
  // code. The model's event id is not used on this path.
  const same = items.filter(e => norm(e.summary) && norm(e.summary) === norm(wantedTitle));
  ev = same.find(e => cxCode(e) === wantCode) || null; how = ev ? 'card' : '';"""
CX_MATCH_NEW = """if (wantCode || wantTime) {
  // A yes to a prepared card: only the booking of that exact title whose current details still give the card's
  // code - or (v21, the card prints no code) still show the card's time and room. The model's event id is not used.
  const same = items.filter(e => norm(e.summary) && norm(e.summary) === norm(wantedTitle));
  ev = same.find(e => wantCode ? cxCode(e) === wantCode : (cxN(cxTime(e)) === cxN(wantTime) && cxN(cxRoom(e) || '(no room on the booking)') === cxN(wantRoom))) || null; how = ev ? 'card' : '';"""
CX_CARD_OLD = """  const card = ['*' + title + '*', '*Date:* ' + date, '*Time:* ' + time, '*Room:* ' + room, '*Booked by:* ' + (who || 'unknown'),
    '_check ' + cxCode(ev) + '_', '', 'Reply only with "yes" to cancel, or "no" to keep it.', 'Confirm to cancel.'].join('\\n');   // as Guard Probe sends it"""
CX_CARD_NEW = """  // v21 (PENDING 69): the short card - no printed code; "Booked by" only when it is someone else's booking.
  const card = ['*' + title + '*', '*Date:* ' + date, '*Time:* ' + time, '*Room:* ' + room].concat(owner ? [] : ['*Booked by:* ' + (who || 'unknown')])
    .concat(['', 'Confirm to cancel.']).join('\\n');   // Guard Probe sends it with the one-line confirmation"""

def cancel(w):
    w["name"] = "Jessie — Cancel Booking — v21 (short cancel card)"
    c = node(w, "Check Ownership")["parameters"]; s = c["jsCode"]
    s = sub1(s, CX_ANCHOR, CX_HELP + CX_ANCHOR, "cx helpers")
    s = sub1(s, CX_MATCH_OLD, CX_MATCH_NEW, "cx match")
    s = sub1(s, CX_CARD_OLD, CX_CARD_NEW, "cx card")
    c["jsCode"] = s
    t = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    if not any(v["name"] == "card_time" for v in t): t += [{"name": "card_time"}, {"name": "card_room"}]
    return w

# ------------------------------------------------------------------------------------------------ main v204
PC_SHAPE = """
  // v204: a card without a code counts only in exactly Cancel Booking v21's shape - title, Date, Time, Room, Booked by,
  // queued _Next: lines, the confirmation. Anything else (a card the model wrote) -> the model handles it, as before.
  const ti = lines.findIndex(l => /^\\*[^*\\n]+\\*$/.test(l) && !/:\\*/.test(l));
  const shortShape = ti >= 0 && lines.slice(ti + 1).every(l => !l || /^\\*(Date|Time|Room|Booked by):\\*/.test(l) || /^_Next: .+_$/.test(l)
    || /^(Confirm to cancel\\.(\\s*\\(yes\\/no\\))?|Cancel it\\? Reply yes or no\\.)$/i.test(l));"""
PC_PARSE_OLD = "  const dl = ((lines.find(l => /^\\*Date:\\*/i.test(l)) || '').replace(/^\\*Date:\\*\\s*/i, '')).trim();"
PC_PARSE_NEW = PC_PARSE_OLD + """
  // v204: the short card prints no code - its Time and Room lines are what the yes must still match (Cancel Booking v21)
  const tl = ((lines.find(l => /^\\*Time:\\*/i.test(l)) || '').replace(/^\\*Time:\\*\\s*/i, '')).trim();
  const rl = ((lines.find(l => /^\\*Room:\\*/i.test(l)) || '').replace(/^\\*Room:\\*\\s*/i, '')).trim();""" + PC_SHAPE
PC_CODE_OLD = "  else if (!code) d.reason = 'the card has no check code - the model wrote it';"
PC_CODE_NEW = ("  else if (!code && !(tl && rl && shortShape)) d.reason = 'the card has no check code and is not the short card Cancel Booking writes';")
PC_D_OLD = "    d = { use: true, reason: '', title, booking_date: ymd, check_code: code, next };"
PC_D_NEW = "    d = { use: true, reason: '', title, booking_date: ymd, check_code: code || '', card_time: code ? '' : tl, card_room: code ? '' : rl, next };"
PC_CC_OLD = "  if (/(?:Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Cancel it\\? Reply yes or no\\.\\s*)$/i.test(t) && code) d.card_code = code;"
PC_CC_NEW = ("  if (/(?:Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Cancel it\\? Reply yes or no\\.\\s*)$/i.test(t) && code) d.card_code = code;\n"
             "  if (/(?:Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Cancel it\\? Reply yes or no\\.\\s*)$/i.test(t) && !code && tl && rl && shortShape) { d.card_time = tl; d.card_room = rl; }   // v204")
GATE_OLD = "const _cancelCard = /_check [0-9a-f]{8}_/.test(lastBotText);"
GATE_NEW = "const _cancelCard = /_check [0-9a-f]{8}_/.test(lastBotText) || (/\\*Date:\\*/.test(lastBotText) && /\\*Time:\\*/.test(lastBotText) && /Cancel it\\? Reply yes or no\\.\\s*$/i.test(lastBotText));   // v204: the short card"
GP_NEXT_OLD = "      if (_q.length) text = text.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + _q.join('\\n'));"
GP_NEXT_NEW = ("      if (_q.length) text = /_check [0-9a-f]{8}_/.test(text) ? text.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + _q.join('\\n'))\n"
               "        : text.replace(/\\n*(?:Reply only with \"yes\" to cancel[^\\n]*\\n)?\\s*Confirm to cancel\\.\\s*$/i, '\\n' + _q.join('\\n') + '\\n\\nConfirm to cancel.');   // v204: no code on the short card")
CDR_OLD = "      if (rest.length) card = card.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + rest.join('\\n'));"
CDR_NEW = ("      if (rest.length) card = /_check [0-9a-f]{8}_/.test(card) ? card.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + rest.join('\\n'))\n"
           "        : card.replace(/\\n*(?:Reply only with \"yes\" to cancel[^\\n]*\\n)?\\s*Confirm to cancel\\.\\s*$/i, '\\n' + rest.join('\\n') + '\\n\\nConfirm to cancel.');   // v204")
SER_ANCHOR = "// v201 (live QA 30 Sep 17:04): a series summary said \"*Engineer:* Howard\"."
SER_BLOCK = r"""// v204 (PENDING 69): a series summary is the short card too - the title, the Dates list, Time and Room. It is model-
// written (PENDING 59); the model keeps its full version in memory for the yes, and Book Series / Book Session fill and
// check every detail. Any line before the title ("Here is the recurring booking for QAMD:") goes too.
if (!_prepared && /\*Dates \(\d+\):\*/.test(text) && /(?:Book it\? Reply yes or no\.|Confirm to book\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i.test(text.trim())) {
  try {
    const _ls = text.split('\n'), _ti = _ls.findIndex(l => /^\s*\*[^*\n]+\*\s*$/.test(l) && !/:\*/.test(l));
    const _keep = (_ti > 0 ? _ls.slice(_ti) : _ls)
      .filter(l => !/^\s*[-•]?\s*\*?(Client|Project|Project Code|Session Type|Engineer|Arranger|Department|Booking Type|Type)\*?:/i.test(l))
      .filter(l => !/^\s*[-•]?\s*\*?Booked by\*?:/i.test(l) || /\(for /i.test(l));   // kept only when booked for someone else
    text = _keep.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  } catch (e) {}
}
"""

def main(w):
    w["name"] = "Project Jessie — v204 (short cancel + series cards)"
    pc = node(w, "Prepared Cancel")["parameters"]; s = pc["jsCode"]
    for o, n, l in [(PC_PARSE_OLD, PC_PARSE_NEW, "pc parse"), (PC_CODE_OLD, PC_CODE_NEW, "pc code"), (PC_D_OLD, PC_D_NEW, "pc d"), (PC_CC_OLD, PC_CC_NEW, "pc cc")]:
        s = sub1(s, o, n, l)
    pc["jsCode"] = s
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GATE_OLD, GATE_NEW, "gate")
    gp = node(w, "Guard Probe")["parameters"]; s = sub1(gp["jsCode"], GP_NEXT_OLD, GP_NEXT_NEW, "gp next")
    gp["jsCode"] = sub1(s, SER_ANCHOR, SER_BLOCK + SER_ANCHOR, "gp series")
    cdr = node(w, "Cancel Direct Reply")["parameters"]; cdr["jsCode"] = sub1(cdr["jsCode"], CDR_OLD, CDR_NEW, "cdr")
    cd = node(w, "Cancel Direct")["parameters"]["workflowInputs"]["value"]
    cd["card_time"] = "={{ ($('Prepared Cancel').first().json._cancelDirect || {}).card_time || '' }}"
    cd["card_room"] = "={{ ($('Prepared Cancel').first().json._cancelDirect || {}).card_room || '' }}"
    cb = node(w, "Cancel Booking")["parameters"]["workflowInputs"]
    cb["value"]["card_time"] = "={{ (($('Prepared Cancel').first().json || {})._cancelDirect || {}).card_time || '' }}"
    cb["value"]["card_room"] = "={{ (($('Prepared Cancel').first().json || {})._cancelDirect || {}).card_room || '' }}"
    if isinstance(cb.get("schema"), list) and cb["schema"]:
        for k in ("card_time", "card_room"):
            if not any(x.get("id") == k for x in cb["schema"]):
                cb["schema"].append({"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "canBeUsedToMatch": True, "type": "string"})
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(cancel(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
