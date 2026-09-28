#!/usr/bin/env python3
"""Prepare Cancel (29 Sep): code writes the cancel card, and a yes to it cancels without the AI.

  scripts/build-prepare-cancel.py <cancel-pull.json> <main-pull.json> <cancel-out.json> <main-out.json>

Cancel Booking v18
  mode 'prepare'  resolves the booking (same resolution and ownership checks as a cancel), deletes nothing, and
                  returns PREPARED with a card: title, date, time, room, booked by, a check code over the event
                  (id, title, start, end, room) and "Confirm to cancel. (yes/no)".
  check_code      the yes: only the booking on that date with that exact title whose CURRENT details still give
                  that code is cancelled. Anything changed -> CHANGED, nothing cancelled.
main v177
  Prepare Cancel  a tool (Cancel Booking in prepare mode); Guard Probe sends its card as the whole reply.
  Prepared Cancel reads the card Jessie just sent; a yes to a fresh (< 4 h) prepared card goes Cancel Direct ->
                  Cancel Booking with the card's title, date and code -> Cancel Direct Reply. No AI call.
Stateless like Prepare Booking: the card in Slack is the pending action; nothing else is stored.
"""
import copy, json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def uid(): return str(uuid.uuid4())
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
def link(C, a, b, br=0):
    arr = C.setdefault(a, {}).setdefault("main", [])
    while len(arr) <= br: arr.append([])
    arr[br].append({"node": b, "type": "main", "index": 0})

CX = r"""
// --- v18 Prepare Cancel: the card IS the pending cancellation (29 Sep) ----------------------------------------
// The check code covers the event itself - id, title, start, end and room - so a yes can only cancel the booking
// the requester saw, unchanged. Keep CX_SALT and cxCode as they are: main reads the code off the card, this checks it.
const CX_SALT = 'c4nc3l-7e1d0b2a';
const cxRoom = e => { const r = (e.attendees || []).filter(a => a.resource || /@resource\.calendar\.google\.com$/i.test(String(a.email || '')))
  .map(a => String(a.displayName || a.email || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\s*\(\d+\)\s*$/, '').trim()); return (r.length ? r.join(', ') : String(e.location || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\s*\(\d+\)\s*$/, '').trim()); };
const cxCode = e => { let h = 0x811c9dc5; const s = [CX_SALT, e.id, e.summary || '', (e.start && (e.start.dateTime || e.start.date)) || '', (e.end && (e.end.dateTime || e.end.date)) || '', cxRoom(e)].join('|');
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
const prepareMode = String(REQ.mode || '').toLowerCase() === 'prepare';
const wantCode = String(REQ.check_code || '').trim().toLowerCase();
"""

CARD = r"""if (prepareMode) {
  // Nothing is deleted in prepare mode: the requester sees exactly this card, and their yes cancels exactly it.
  const s = (ev.start && (ev.start.dateTime || ev.start.date)) || '', en = (ev.end && (ev.end.dateTime || ev.end.date)) || '';
  const allDay = !(ev.start && ev.start.dateTime);
  const D = allDay ? new Date(s + 'T00:00:00+08:00') : new Date(s);
  const date = D.toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
  const time = allDay ? 'All day' : (t(s) + ' – ' + t(en));
  const room = cxRoom(ev) || '(no room on the booking)';
  const card = ['*' + title + '*', '*Date:* ' + date, '*Time:* ' + time, '*Room:* ' + room, '*Booked by:* ' + (who || 'unknown'),
    '_check ' + cxCode(ev) + '_', '', 'Reply only with "yes" to cancel, or "no" to keep it.', 'Confirm to cancel.'].join('\n');   // as Guard Probe sends it
  return [{ json: { verdict:'PREPARED', status:'PREPARED', event_id: ev.id, title, card_text: card,
    human:'Send the requester this card as your whole reply, exactly as it is, and stop. Their yes cancels it.' } }];
}
"""

RETURN_PREPARED = r"""const c = $input.first().json || {};
return [{ json: { status: 'PREPARED', event_id: c.event_id, title: c.title, card_text: c.card_text, human: c.human } }];"""

def build_cancel(w):
    w["name"] = "Jessie — Cancel Booking — v18 (v17 fixed)"
    trig = node(w, "When Executed by Another Workflow")
    trig["parameters"]["workflowInputs"]["values"] += [{"name": "mode"}, {"name": "check_code"}]
    n = node(w, "Check Ownership"); c = n["parameters"]["jsCode"]
    c = sub1(c, "const norm = s => String(s || '').toLowerCase().replace(/\\s+/g, ' ').trim();\n",
             "const norm = s => String(s || '').toLowerCase().replace(/\\s+/g, ' ').trim();\n" + CX, "cx helpers")
    c = sub1(c, "if (!confirmed) {\n", "if (!confirmed && !prepareMode) {\n", "confirm")
    c = sub1(c, "let ev = wantedId ? items.find(e => String(e.id) === wantedId) : null;\nlet how = ev ? 'id' : '';\n",
             "let ev = wantedId ? items.find(e => String(e.id) === wantedId) : null;\nlet how = ev ? 'id' : '';\n"
             "if (wantCode) {\n"
             "  // A yes to a prepared card: only the booking of that exact title whose current details still give the card's\n"
             "  // code. The model's event id is not used on this path.\n"
             "  const same = items.filter(e => norm(e.summary) && norm(e.summary) === norm(wantedTitle));\n"
             "  ev = same.find(e => cxCode(e) === wantCode) || null; how = ev ? 'card' : '';\n"
             "  if (!ev) return [{ json: { verdict:'REJECTED', reason: same.length ? 'CHANGED' : 'NOT_ON_CALENDAR', title: wantedTitle,\n"
             "    human: same.length ? 'Nothing was cancelled - that booking has changed since the card was shown. Show the current details and ask again.'\n"
             "                       : 'Nothing was cancelled - that booking is no longer on the calendar.' } }];\n"
             "}\n", "card resolution")
    c = sub1(c, "const notify = !owner && (coordInDept || isHaistDev);\n", CARD + "const notify = !owner && (coordInDept || isHaistDev);\n", "card")
    n["parameters"]["jsCode"] = c
    # Check Ownership -> Prepared? -> [PREPARED] Return Prepared | [else] Allowed?
    allowed = node(w, "Allowed?")
    prep = copy.deepcopy(allowed); prep["id"] = uid(); prep["name"] = "Prepared?"
    prep["position"] = [allowed["position"][0], allowed["position"][1] - 176]
    prep["parameters"]["conditions"]["conditions"][0].update({"id": uid(), "rightValue": "PREPARED"})
    rp = {"parameters": {"mode": "runOnceForAllItems", "jsCode": RETURN_PREPARED}, "id": uid(), "name": "Return Prepared",
          "position": [allowed["position"][0] + 224, allowed["position"][1] - 176], "type": "n8n-nodes-base.code", "typeVersion": 2}
    w["nodes"] += [prep, rp]
    C = w["connections"]
    C["Check Ownership"] = {"main": [[{"node": "Prepared?", "type": "main", "index": 0}]]}
    link(C, "Prepared?", "Return Prepared", 0); link(C, "Prepared?", "Allowed?", 1)
    return w

# ---------------------------------------------------------------- main
PREPARED_CANCEL = r"""// Prepared Cancel (main v177). A yes to a cancel card that Cancel Booking wrote (prepare mode) is carried out in
// code - Cancel Direct - without the model: 28 Sep QA, the model wrote cancel cards itself (once with an invented
// room and time), called Cancel Booking before showing the booking, and a Gemini 503 on the yes left a booking
// uncancelled. Reads the newest Jessie message (the card the yes answers); needs the gate's confirmedCancel, the
// card's check code, and a card under 4 hours old. Anything else -> the model handles the turn as before.
// Passes its input through, so the agent sees what it always did.
let d = { use: false, reason: '' };
try {
  const gate = ($('Gate Context').first() || {}).json || {};
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const bot = msgs.find(isBot);
  // Slack escapes &, < and > in message text; the title must match the calendar exactly.
  const t = bot ? String(bot.text || (bot.message && bot.message.text) || '').replace(/\r/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim() : '';
  const code = (t.match(/_check ([0-9a-f]{8})_/) || [])[1];
  const lines = t.split('\n').map(l => l.trim());
  const title = ((lines.find(l => /^\*[^*\n]+\*$/.test(l) && !/:\*/.test(l)) || '').replace(/^\*|\*$/g, '')).trim();
  const dl = ((lines.find(l => /^\*Date:\*/i.test(l)) || '').replace(/^\*Date:\*\s*/i, '')).trim();
  const M = ['january','february','march','april','may','june','july','august','september','october','november','december'];
  const dm = dl.match(/([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})/); const mo = dm ? M.indexOf(dm[1].toLowerCase()) : -1;
  const ymd = mo >= 0 ? dm[3] + '-' + String(mo + 1).padStart(2, '0') + '-' + String(+dm[2]).padStart(2, '0') : '';
  const ageH = bot && bot.ts ? (Date.now() / 1000 - parseFloat(bot.ts)) / 3600 : 99;
  if (gate.confirmedCancel !== true) d.reason = 'not a confirmed cancel';
  else if (!/Confirm to cancel\.\s*(?:\(yes\/no\)\s*)?$/i.test(t)) d.reason = 'the last message is not a cancel card';
  else if (!code) d.reason = 'the card has no check code - the model wrote it';
  else if (!title || !ymd) d.reason = 'the card has no title or date';
  else if (ageH > 4) d.reason = 'the card is more than 4 hours old';
  else d = { use: true, reason: '', title, booking_date: ymd, check_code: code };
  // The model's own Cancel Booking call (when the direct path declines) is held to the card too.
  if (/Confirm to cancel\.\s*(?:\(yes\/no\)\s*)?$/i.test(t) && code) d.card_code = code;
} catch (e) { d = { use: false, reason: 'error: ' + e.message }; }
return [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d }) }];"""

CANCEL_DIRECT_REPLY = r"""// Cancel Direct Reply (main v177): the requester's answer, from Cancel Booking's result - never its model-facing
// instructions. "Cancelled" only on CANCELLED.
const r = (() => { try { const j = $input.first().json || {}; return Array.isArray(j) ? (j[0] || {}) : j; } catch (e) { return {}; } })();
const st = String(r.status || '').toUpperCase(), why = String(r.reason || '').toUpperCase();
const T = {
  NOT_ON_CALENDAR: "I can't find that booking any more - it may already have been cancelled. Nothing else was changed.",
  CHANGED: "That booking has changed since I showed it to you, so nothing was cancelled. Ask me again and I'll show you the current details.",
  NOT_YOURS: "That booking was made by someone else, and you don't have authority to cancel it. Nothing was cancelled.",
  NO_REFERENCE: "That booking has no booker on record, so I can't cancel it. Nothing was cancelled - please ask the studio team.",
  LOOKUP_FAILED: "I couldn't read the calendar just now, so nothing was cancelled. Please try again in a moment.",
};
let text;
if (st === 'CANCELLED') text = String(r.human || '').trim() || 'Cancelled.';
else if (T[why]) text = T[why];
else text = "I couldn't confirm that cancellation went through. Please check the calendar before trying again.";
return [{ json: { output: text, directCancel: { status: st, reason: why } } }];"""

GP_ANCHOR = "// --- v168 (live, 28 Sep): they said no, and the same summary went out again"
GP_BLOCK = r"""// --- v177 Prepare Cancel: the cancel card IS the reply -----------------------------------------------------
// Same rule as a prepared booking summary: when the latest Prepare Cancel call this turn returned PREPARED, the
// requester sees exactly its card (its check code covers the booking), and nothing below may change it.
try {
  const _s1 = (($input.first().json || {}).intermediateSteps) || [];
  for (let i = _s1.length - 1; i >= 0; i--) {
    const _t = String(((_s1[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
    if (_t !== 'prepare cancel') continue;
    let _o = null; try { _o = [].concat(JSON.parse(String((_s1[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_o && _o.status === 'PREPARED' && _o.card_text) { text = String(_o.card_text); _prepared = true; }
    break;
  }
} catch (e) {}

"""

PROMPT_OLD = """3. Show what you found. If exactly one event matches their description, state it and ask them to confirm — don't second-guess details that already match. If several match, list them and ask which. End with the line `Confirm to cancel. (yes/no)` on its own, and stop — Cancel Booking refuses without it.
4. On yes, call Cancel Booking with the raw event `id` from Find Booking (a short alphanumeric string, no `@`) and nothing else. Never guess an id or use a title."""
PROMPT_NEW = """3. If several bookings match, list them and ask which one. Once it is one booking, call Prepare Cancel with its title exactly as Find Booking returned it and its date. It checks the booking and whether they may cancel it, and returns a card: send the card as your whole reply and stop. Never write a cancel confirmation yourself.
4. Their yes to that card is carried out automatically - you do not call Cancel Booking for it. Call Cancel Booking yourself only when they confirmed a list of several bookings to cancel together, with each raw event `id` from Find Booking (a short alphanumeric string, no `@`). Never guess an id."""

def build_main(w):
    w["name"] = "Project Jessie — v177 (Prepare Cancel)"
    N = {n["name"]: n for n in w["nodes"]}
    ct = N["Cancel Booking"]
    pc = copy.deepcopy(ct); pc["id"] = uid(); pc["name"] = "Prepare Cancel"; pc["position"] = [75424, 6896]
    pc["parameters"]["description"] = ("Show the requester a booking they want to cancel, before they confirm. Give it the booking title "
        "exactly as Find Booking returned it and the date it falls on, and the event id if Find Booking gave one. It finds the booking, "
        "checks they may cancel it, and returns a card. Send the card as your whole reply, exactly as it is, and stop - their yes cancels "
        "that booking automatically. If it refuses, tell the requester the reason and stop.")
    v = pc["parameters"]["workflowInputs"]["value"]
    v["confirmed"] = "={{ false }}"; v["mode"] = "prepare"
    for k, desc in (("booking_date", "The date the booking falls on, as yyyy-MM-dd, from the Find Booking result."),
                    ("title", "The booking title exactly as Find Booking returned it, e.g. FALCON / Jem Lim / TL."),
                    ("event_id", "The Google Calendar event id, copied character for character from the id field of a Find Booking result. Leave empty if you do not have one - never construct, adapt or guess an id.")):
        v[k] = "={{ $fromAI('" + k + "', '" + desc.replace("'", "") + "', 'string'" + (", ''" if k == "event_id" else "") + ") }}"
    sch = pc["parameters"]["workflowInputs"]["schema"]
    base = next(s for s in sch if s["id"] == "title")
    for k in ("mode", "check_code"):
        if not any(s["id"] == k for s in sch): e = dict(base); e.update({"id": k, "displayName": k}); sch.append(e)
    ct["parameters"]["workflowInputs"]["value"]["check_code"] = "={{ (($('Prepared Cancel').first().json || {})._cancelDirect || {}).card_code || '' }}"
    csch = ct["parameters"]["workflowInputs"]["schema"]
    if not any(x["id"] == "check_code" for x in csch): e = dict(next(x for x in csch if x["id"] == "title")); e.update({"id": "check_code", "displayName": "check_code"}); csch.append(e)
    tool_conns = w["connections"].get("Cancel Booking")
    w["connections"]["Prepare Cancel"] = copy.deepcopy(tool_conns)
    # Cancel Direct: Execute Workflow -> Cancel Booking with the card's title, date and code
    bd = N["Book Direct"]
    cd = copy.deepcopy(bd); cd["id"] = uid(); cd["name"] = "Cancel Direct"; cd["position"] = [75152, 6592]
    cd["parameters"]["workflowId"] = {"__rl": True, "value": "bAyDw7udhmY0NL38", "mode": "list", "cachedResultName": "Jessie — Cancel Booking",
                                      "cachedResultUrl": "/workflow/bAyDw7udhmY0NL38"}
    P = "$('Prepared Cancel').first().json._cancelDirect"
    cd["parameters"]["workflowInputs"] = {"mappingMode": "defineBelow", "matchingColumns": [], "schema": [],
        "attemptToConvertTypes": False, "convertFieldsToString": True,
        "value": {"event_id": "", "title": "={{ " + P + ".title }}", "booking_date": "={{ " + P + ".booking_date }}",
                  "check_code": "={{ " + P + ".check_code }}", "mode": "",
                  "confirmed": "={{ $('Gate Context').first().json.confirmedCancel }}",
                  "requester": "={{ $('Slack Trigger').first().json.user }}",
                  "requester_name": "={{ $('Get Booker').first().json.fields.Name }}",
                  "authority": "={{ ($('Get Booker').first().json.fields.Authority || []).map(a => (a && a.name) || a).join(', ') }}",
                  "department": "={{ ($('Get Booker').first().json.fields.Department || []).map(a => (a && a.name) || a).join(', ') }}"}}
    cd["onError"] = "continueRegularOutput"
    bdq = N["Book Direct?"]
    q = copy.deepcopy(bdq); q["id"] = uid(); q["name"] = "Cancel Direct?"; q["position"] = [74976, 6592]
    q["parameters"]["conditions"]["conditions"][0].update({"id": uid(), "leftValue": "={{ ($json._cancelDirect || {}).use === true ? 'yes' : 'no' }}", "rightValue": "yes"})
    pcn = {"parameters": {"mode": "runOnceForAllItems", "jsCode": PREPARED_CANCEL}, "id": uid(), "name": "Prepared Cancel",
           "position": [74800, 6592], "type": "n8n-nodes-base.code", "typeVersion": 2}
    rep = {"parameters": {"mode": "runOnceForAllItems", "jsCode": CANCEL_DIRECT_REPLY}, "id": uid(), "name": "Cancel Direct Reply",
           "position": [75328, 6592], "type": "n8n-nodes-base.code", "typeVersion": 2}
    w["nodes"] += [pc, cd, q, pcn, rep]
    C = w["connections"]
    br = C["Book Direct?"]["main"]
    assert [t["node"] for t in br[1]] == ["Jessie AI Agent"], br
    br[1] = [{"node": "Prepared Cancel", "type": "main", "index": 0}]
    link(C, "Prepared Cancel", "Cancel Direct?")
    link(C, "Cancel Direct?", "Cancel Direct", 0); link(C, "Cancel Direct?", "Jessie AI Agent", 1)
    link(C, "Cancel Direct", "Cancel Direct Reply"); link(C, "Cancel Direct Reply", "Send Reply")
    g = N["Guard Probe"]; g["parameters"]["jsCode"] = sub1(g["parameters"]["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "guard probe")
    ag = N["Jessie AI Agent"]["parameters"]["options"]
    ag["systemMessage"] = sub1(ag["systemMessage"], PROMPT_OLD, PROMPT_NEW, "prompt")
    return w

if __name__ == "__main__":
    ci, mi, co, mo = sys.argv[1:5]
    c = build_cancel(json.load(open(ci))); m = build_main(json.load(open(mi)))
    json.dump(c, open(co, "w"), indent=2, ensure_ascii=False); json.dump(m, open(mo, "w"), indent=2, ensure_ascii=False)
    print("wrote", co, len(c["nodes"]), "nodes;", mo, len(m["nodes"]), "nodes")
