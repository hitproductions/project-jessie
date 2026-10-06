#!/usr/bin/env python3
"""Book Series v4 + main v225 (deterministic series) - decided 6 Oct after live 15:13 PHT (PENDING 90): a series is now
prepared and booked like a single booking - code writes the card, and the yes books exactly that card, never the model.

Before: the model called Expand Series, wrote the series card itself (Guard Probe tidied it, v183/v204), and at the yes the
model was trusted to call Book Series once (Gate Context's seriesNotice). On 6 Oct the yes re-sent the card (v224 fixes the
notice), and nothing but the model stood between a yes and the booking.

Book Series v4
  - mode "prepare" (the new Prepare Series tool): expands the dates as before, then runs Book Session in prepare mode for
    every date (each one through every guard: session type, client, engineer, title, room, conflicts - the same questions a
    single booking asks). A question goes back as Book Session wrote it ("Ask exactly this ..."). Dates whose room is taken
    are left out and named on the card. Otherwise the card is written here, in one fixed format:
        *TITLE*  /  *Dates (N):*  /  - Friday, 8 October 2027 ...  /  *Time:*  /  *Room:*  /  notes  /  Confirm to book.
    and the series is stored (Store Series, the same data table as Store Prepared) under a key over the requester and the
    title, dates, time and room shown.
  - a `dates` input: when given (Series Direct), exactly those dates are booked instead of re-expanding the pattern.
main v225
  - Prepare Series tool (Book Series, mode prepare); the prompt says to use it for every repeating booking and that the yes
    books it by itself. Guard Probe sends its card as written (like a cancel card, v177) and relays its questions (v203).
  - Prepared Key works out the series key from the card; Prepared Series reads the stored series back, checks it is intact,
    under 12 hours old and exactly what the card shows, and with the gate's yes Series Direct calls Book Series with it -
    no model. Series Direct Reply sends Book Series' own "Booked 3 sessions: ..." text.
  scripts/build-series-direct.py <book-series-v3> <book-series-out> <main-v224> <main-out>
"""
import json, sys, copy, uuid
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# shared by Book Series "Aggregate" and main "Prepared Key" / "Prepared Series" - keep identical
SKEY = r"""const PB_SALT = '4539361661025d1d';
const pbNorm = s => String(s == null ? '' : s).replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/[*_]/g, '').replace(/\s+/g, ' ').trim();
const pbHash = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
const seriesKey = (ref, f) => 'prep-s' + pbHash(PB_SALT + '|series|' + String(ref || '').trim() + '|' + pbNorm(f.Title) + '|' + (f.Dates || []).map(pbNorm).join(';') + '|' + pbNorm(f.Time) + '|' + pbNorm(f.Room));
const seriesCode = inputs => pbHash(PB_SALT + '|series-code|' + JSON.stringify(inputs));
"""

# ================================================================ Book Series v4
TRIG_ADD = ["mode", "asked_text", "staff_data", "authority", "dates"]
ED_OLD = """const res = expandDates(REQ);"""
ED_NEW = """// v4 (deterministic series): Series Direct passes the exact dates the requester approved - book those, not a re-expansion
const __given = String(REQ.dates || '').split(',').map(s => s.trim()).filter(s => /^\\d{4}-\\d{2}-\\d{2}$/.test(s));
const __allDay = REQ.all_day === true || String(REQ.all_day).toLowerCase() === 'true';
const __t = s => String(s || '').padStart(5, '0');
const res = __given.length
  ? { status: 'OK', count: __given.length, occurrences: __given.map(d => __allDay ? { date: d, all_day: true }
      : { start_iso: d + 'T' + __t(REQ.time_start) + ':00+08:00', end_iso: d + 'T' + __t(REQ.time_end) + ':00+08:00', all_day: false }) }
  : expandDates(REQ);
const __prep = String(REQ.mode || '').trim().toLowerCase() === 'prepare';"""
ED_ITEM_OLD = """    room_override:false, confirmed: REQ.confirmed, series:true,
    all_day: !!o.all_day
  };"""
ED_ITEM_NEW = """    room_override: REQ.room_override === true || String(REQ.room_override).toLowerCase() === 'true', confirmed: __prep ? false : REQ.confirmed, series: !__prep,
    all_day: !!o.all_day,
    // v4: prepare mode runs each date through Book Session's prepare checks, as a single booking on that date
    mode: __prep ? 'prepare' : '', asked_text: REQ.asked_text || '', staff_data: REQ.staff_data || '', authority: REQ.authority || ''
  };"""
ED_DATE_OLD = """  else { j.start_iso = o.start_iso; j.end_iso = o.end_iso; j._date = o.start_iso.slice(0,10); }"""
ED_DATE_NEW = """  else { j.start_iso = o.start_iso; j.end_iso = o.end_iso; j._date = o.start_iso.slice(0,10); }
  if (__prep) j.expected_date = j._date;"""

AGG_OLD = """const occ = $('Expand Dates').all().map(i => i.json).filter(o => o._go);
const results = $input.all().map(i => i.json);"""
AGG_NEW = SKEY + r"""const occ = $('Expand Dates').all().map(i => i.json).filter(o => o._go);
const results = $input.all().map(i => i.json);
// --- v4 (deterministic series): prepare mode - the card, written here, and the series stored for the yes ---------------
const REQ0 = $('When Executed by Another Workflow').first().json || {};
if (String(REQ0.mode || '').trim().toLowerCase() === 'prepare') {
  const MONP = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const DAYP = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const long = d => { const x = new Date(d + 'T00:00:00Z'); return DAYP[x.getUTCDay()] + ', ' + x.getUTCDate() + ' ' + MONP[x.getUTCMonth()] + ' ' + x.getUTCFullYear(); };
  const ok = [], taken = [];
  let first = null, ask = null;
  for (let i = 0; i < occ.length; i++) {
    const r = results[i] || {}, d = occ[i]._date;
    let P = null; try { P = r.prep_payload ? JSON.parse(r.prep_payload) : null; } catch (e) {}
    if (r.status === 'PREPARED' && P && P.F && !r.needs_consent) { ok.push(d); if (!first) first = { r, P, d }; }
    else if (r.status === 'PREPARED' || r.reason === 'ROOM_OCCUPIED' || r.reason === 'ROOM_DECLINED') taken.push(d);
    else if (!ask) ask = r;
  }
  if (ask) return [{ json: { status: 'REJECTED', reason: ask.reason || 'FAILED', human: ask.human || 'Nothing was prepared.' } }];   // a question, as Book Session wrote it
  if (!first) return [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED',
    human: 'Nothing was prepared - the room is taken on every one of those dates (' + taken.map(long).join('; ') + '). Ask exactly this, in one message: "The room is taken on all of those dates. Another room or time?"' } }];
  const F = first.P.F;
  const shown = ok.map(long);
  // notes from the first date's card ("Not a usual ... room", "Want a holding room?") - never a date-specific one
  const _notes = String(first.r.summary_text || '').split('\n\n').slice(1, -1).join('\n').split('\n').map(s => s.trim())
    .filter(s => s && !/already passed|^Heads up: \S.* is booked|picked|No time given/i.test(s));
  const L = ['*' + F['Title'] + '*', '*Dates (' + ok.length + '):*'].concat(shown.map(s => '- ' + s), ['*Time:* ' + F['Time'], '*Room:* ' + F['Room']]);
  const _for = (String(F['Booked by'] || '').match(/\(for\s+([^)]+)\)/i) || [])[1]; if (_for) L.push('*For:* ' + _for.trim());
  const notes = _notes.slice();
  if (taken.length) notes.unshift('Heads up: ' + F['Room'] + ' is taken on ' + taken.map(long).join(', ') + ' - ' + (taken.length === 1 ? 'that date' : 'those dates') + ' left out.');
  const card = L.join('\n') + (notes.length ? '\n\n' + notes.join('\n') : '') + '\n\nConfirm to book.';
  const ref = String(first.P.ref || ((String(REQ0.description || '').match(/\bref:\s*([A-Z0-9]+)/) || [])[1]) || '').trim();
  const desc = ['Engineer: ' + F['Engineer']].concat(F['Arranger'] ? ['Arranger: ' + F['Arranger']] : [])
    .concat(String(REQ0.description || '').split('|').map(s => s.trim()).filter(s => s && !/^(engineer|arranger)\s*:/i.test(s))).join(' | ');
  const inputs = { summary: F['Title'], rooms: F['Room'], session_type: F['Session Type'] || '', client: /^none$/i.test(F['Client'] || '') ? '' : (F['Client'] || ''),
    engineer: F['Engineer'] || '', description: desc, bookingType: F['Booking Type'] || '', department: F['Department'] || '',
    room_override: F['Override'] === 'yes', all_day: !!occ[0].all_day,
    time_start: String(REQ0.time_start || ''), time_end: String(REQ0.time_end || ''), dates: ok.join(','),
    requester_text: String(REQ0.requester_text || '') };
  const key = ref ? seriesKey(ref, { Title: F['Title'], Dates: shown, Time: F['Time'], Room: F['Room'] }) : '';
  return [{ json: { status: 'PREPARED', card_text: card, title: F['Title'], dates: ok, skipped: taken, prep_key: key,
    prep_payload: JSON.stringify({ v: 1, kind: 'series', ref, code: seriesCode(inputs), inputs, card: { Title: F['Title'], Dates: shown, Time: F['Time'], Room: F['Room'] }, at: new Date().toISOString() }),
    human: 'The series card is ready and is sent to the requester automatically, exactly as prepared. Do not write anything about this booking yourself. Their yes books it - do not call Book Series.' } }];
}"""

STORE_SERIES = {
  "parameters": {"operation": "upsert",
    "dataTableId": {"__rl": True, "value": "CsdJhgDxCsqq9K9j", "mode": "list", "cachedResultName": "Jessie Reference Cache", "cachedResultUrl": "/projects/518sXYqvqTl1cuns/datatables/CsdJhgDxCsqq9K9j"},
    "matchType": "allConditions",
    "filters": {"conditions": [{"keyName": "cache_key", "keyValue": "={{ $('Aggregate').first().json.prep_key || 'prep-none' }}"}]},
    "columns": {"mappingMode": "defineBelow", "value": {"cache_key": "={{ $('Aggregate').first().json.prep_key || 'prep-none' }}", "payload": "={{ $('Aggregate').first().json.prep_payload }}", "refreshed_at": "={{ new Date().toISOString() }}"},
      "matchingColumns": [], "schema": [
        {"id": "cache_key", "displayName": "cache_key", "required": False, "defaultMatch": False, "display": True, "type": "string", "readOnly": False, "removed": False},
        {"id": "payload", "displayName": "payload", "required": False, "defaultMatch": False, "display": True, "type": "string", "readOnly": False, "removed": False},
        {"id": "refreshed_at", "displayName": "refreshed_at", "required": False, "defaultMatch": False, "display": True, "type": "string", "readOnly": False, "removed": False}],
      "attemptToConvertTypes": False, "convertFieldsToString": False}, "options": {}},
  "name": "Store Series", "type": "n8n-nodes-base.dataTable", "onError": "continueRegularOutput"}
SERIES_OUT = """// Series Out (Book Series v4): hands the prepared series back unchanged - Store Series only saved it. If the save failed the
// card still goes out; at the yes main finds nothing stored, so Series Direct does not run and the model is told the series
// is approved (Gate Context's seriesNotice) - never a booking with missing details.
return $('Aggregate').all().map(i => ({ json: Object.assign({}, i.json, { prep_stored: (function () { try { const s = $('Store Series').first().json || {}; return !s.error; } catch (e) { return false; } })() }) }));"""
STORED_IF = {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
    "conditions": [{"id": "sp", "leftValue": "={{ $json.status === 'PREPARED' && !!$json.prep_key }}", "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
    "combinator": "and"}, "options": {}}, "name": "Series Prepared?", "type": "n8n-nodes-base.if", "typeVersion": 2}

def book_series(w):
    w["name"] = "Jessie — Book Series — v4 (deterministic series)"
    tr = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    have = {v["name"] for v in tr}
    for k in TRIG_ADD:
        if k not in have: tr.append({"name": k})
    if "room_override" not in have: tr.append({"name": "room_override", "type": "boolean"})
    ed = node(w, "Expand Dates")["parameters"]; s = ed["jsCode"]
    s = sub1(s, ED_OLD, ED_NEW, "ed res"); s = sub1(s, ED_ITEM_OLD, ED_ITEM_NEW, "ed item"); s = sub1(s, ED_DATE_OLD, ED_DATE_NEW, "ed date")
    ed["jsCode"] = s
    ag = node(w, "Aggregate"); ag["parameters"]["jsCode"] = sub1(ag["parameters"]["jsCode"], AGG_OLD, AGG_NEW, "agg")
    x, y = ag["position"]
    ifn = dict(copy.deepcopy(STORED_IF), id=str(uuid.uuid4()), position=[x + 220, y])
    st = dict(copy.deepcopy(STORE_SERIES), id=str(uuid.uuid4()), typeVersion=node_tv(w), position=[x + 440, y - 100])
    so = {"parameters": {"jsCode": SERIES_OUT}, "name": "Series Out", "type": "n8n-nodes-base.code", "typeVersion": 2, "id": str(uuid.uuid4()), "position": [x + 660, y - 100]}
    sr = {"parameters": {"jsCode": "// Series Result (v4): every other Aggregate answer - booked, skipped, a question - passed back as it is.\nreturn $input.all();"},
          "name": "Series Result", "type": "n8n-nodes-base.code", "typeVersion": 2, "id": str(uuid.uuid4()), "position": [x + 440, y + 100]}
    w["nodes"] += [ifn, st, so, sr]
    C = w["connections"]
    C["Aggregate"] = {"main": [[{"node": "Series Prepared?", "type": "main", "index": 0}]]}
    C["Series Prepared?"] = {"main": [[{"node": "Store Series", "type": "main", "index": 0}], [{"node": "Series Result", "type": "main", "index": 0}]]}
    C["Store Series"] = {"main": [[{"node": "Series Out", "type": "main", "index": 0}]]}
    return w
_BS = None
def node_tv(w):   # the data table node version Book Session uses
    return next(n for n in _BS["nodes"] if n["name"] == "Store Prepared")["typeVersion"]

# ================================================================ main v225
PK_OLD = """  if (/(?:Confirm to book\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Book it\\? Reply yes or no\\.\\s*)$/i.test(t.trim()) && !/_check [0-9a-f]{8}_/.test(t)) {"""
PK_NEW = """  // v225 (deterministic series): a series card is keyed over the title, the dates listed, the time and the room
  if (/(?:Confirm to book\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Book it\\? Reply yes or no\\.\\s*)$/i.test(t.trim()) && /^\\s*\\*Dates \\(\\d+\\):\\*\\s*$/m.test(t)) {
""" + "\n".join("    " + l for l in SKEY.strip().split("\n")) + """
    const lines = t.split('\\n').map(l => l.trim());
    const title = (lines.find(l => /^\\*[^*\\n]+\\*$/.test(l) && !/:\\*/.test(l)) || '');
    const di = lines.findIndex(l => /^\\*Dates \\(\\d+\\):\\*$/.test(l)), dates = [];
    for (let i = di + 1; i < lines.length && /^- /.test(lines[i]); i++) dates.push(lines[i].slice(2));
    const val = k => { const l = lines.find(x => new RegExp('^\\\\*' + k + ':\\\\*\\\\s*').test(x)); return l ? l.replace(new RegExp('^\\\\*' + k + ':\\\\*\\\\s*'), '') : ''; };
    const ref = String((($('Slack Trigger').first() || {}).json || {}).user || '');
    if (ref && title && dates.length) key = seriesKey(ref, { Title: title, Dates: dates, Time: val('Time'), Room: val('Room') });
  } else
  if (/(?:Confirm to book\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Book it\\? Reply yes or no\\.\\s*)$/i.test(t.trim()) && !/_check [0-9a-f]{8}_/.test(t)) {"""

PREPARED_SERIES = SKEY + r"""// Prepared Series (main v225, deterministic series). A yes to a series card that Prepare Series wrote is booked in code,
// without the model, like Book Direct for a single booking. The card is the newest Jessie message; the series stored for it
// (Book Series v4 Store Series, under the key Prepared Key worked out) is used only when it is intact (its own code), under
// 12 hours old, and its title, dates, time and room are exactly the ones on the card. Anything else -> use false, and the
// turn goes to the model as before (Gate Context's seriesNotice). Never throws.
let out = { use: false, ok: false, reason: '', p: {} };
try {
  const gate = ($('Gate Context').first() || {}).json || {};
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const bot = msgs.find(isBot);
  const t = bot ? String(bot.text || (bot.message && bot.message.text) || '').replace(/\r/g, '') : '';
  if (!/^\s*\*Dates \(\d+\):\*\s*$/m.test(t) || !/(?:Confirm to book\.\s*(?:\(yes\/no\)\s*)?|Book it\? Reply yes or no\.\s*)$/i.test(t.trim())) out.reason = 'the last message is not a series card';
  else {
    const lines = t.split('\n').map(l => l.trim());
    const title = (lines.find(l => /^\*[^*\n]+\*$/.test(l) && !/:\*/.test(l)) || '');
    const di = lines.findIndex(l => /^\*Dates \(\d+\):\*$/.test(l)), dates = [];
    for (let i = di + 1; i < lines.length && /^- /.test(lines[i]); i++) dates.push(lines[i].slice(2));
    const val = k => { const l = lines.find(x => new RegExp('^\\*' + k + ':\\*\\s*').test(x)); return l ? l.replace(new RegExp('^\\*' + k + ':\\*\\s*'), '') : ''; };
    const shown = { Title: title, Dates: dates, Time: val('Time'), Room: val('Room') };
    const k = (($('Prepared Key').first() || {}).json || {}).prep_key || '';
    const ref = String((($('Slack Trigger').first() || {}).json || {}).user || '');
    let row = null; try { row = k ? $('Read Prepared').all().map(i => (i && i.json) || {}).find(r => r.cache_key === k && r.payload) : null; } catch (e) {}
    let P = null; try { P = row ? JSON.parse(row.payload) : null; } catch (e) {}
    const age = P ? Date.now() - Date.parse(row.refreshed_at || P.at || '') : NaN;
    if (!k || k !== seriesKey(ref, shown)) out.reason = 'no key for this card';
    else if (!P || P.kind !== 'series' || !P.inputs) out.reason = 'nothing stored for this card';
    else if (!(age >= -60000 && age < 12 * 3600000)) out.reason = 'the stored series is too old';
    else if (seriesCode(P.inputs) !== P.code) out.reason = 'the stored series is not intact';
    else if (pbNorm(P.card.Title) !== pbNorm(shown.Title) || pbNorm(P.card.Time) !== pbNorm(shown.Time) || pbNorm(P.card.Room) !== pbNorm(shown.Room)
             || P.card.Dates.map(pbNorm).join(';') !== shown.Dates.map(pbNorm).join(';')) out.reason = 'the card does not match what was stored';
    else if (String(P.inputs.dates || '').split(',').filter(Boolean).length !== dates.length) out.reason = 'the stored dates do not match the card';
    else { out.ok = true; out.p = P.inputs; }
  }
  out.use = out.ok && gate.confirmed === true;
} catch (e) {
  out = { use: false, ok: false, reason: 'error: ' + String((e && e.message) || e), p: {} };
}
return [{ json: Object.assign({}, $input.first().json || {}, { _seriesDirect: out }) }];"""

SERIES_DIRECT_REPLY = r"""// Series Direct Reply (main v225). A verified yes to a prepared series card was booked in code (Series Direct -> Book Series
// with the stored dates). Book Series' own text is the reply: "Booked 3 sessions: ..." and anything skipped or failed.
let r = {};
try { r = $input.first().json || {}; } catch (e) {}
let text = String(r.human || '').trim();
const st = String(r.status || '').toUpperCase();
if (!text) text = st === 'BOOKED_SERIES' ? 'Booked.' : "I couldn't confirm that series went through. Please check the calendar before booking it again.";
if (st !== 'BOOKED_SERIES' && /\b(?:the requester|Present the full list|end with the line)\b/i.test(text))
  text = 'Nothing was booked - something changed since that card. Send the series again and I’ll check it.';
return [{ json: { output: text, directBooking: { status: r.status || '', reason: r.reason || '', series: true, booked: r.booked || [], skipped: r.skipped || [] } } }];"""

PROMPT_OLD = """*Never work out the dates yourself — call Expand Series* with the pattern (frequency; weekday codes like TU or MO,WE; start date; count or stop date; all-day or start and end times). Its answer says how to present the series and what to do on the yes — follow it."""
PROMPT_NEW = """*Never work out the dates yourself — call Prepare Series* with the pattern (frequency; weekday codes like TU or MO,WE; start date; count or stop date; all-day or start and end times) and the booking details, as you would give Prepare Booking. It works out the dates, checks every one, and shows the requester the card itself: send nothing else. If it asks something, ask exactly that. Their yes books the series automatically - do not call Book Series yourself. Use Expand Series only to answer which dates a pattern gives, never to present a booking."""

GP_ANCHOR = "// --- v177 Prepare Cancel: the cancel card IS the reply -----------------------------------------------------"
GP_SERIES = r"""// --- v225 (deterministic series): Prepare Series' card IS the reply ----------------------------------------------------
// Same rule as a prepared booking or cancel card (v177): when the latest Prepare Series call this turn returned PREPARED,
// the requester sees exactly its card - Series Direct reads it back at the yes - and nothing below may change it.
try {
  const _sS = (($input.first().json || {}).intermediateSteps) || [];
  for (let i = _sS.length - 1; i >= 0; i--) {
    if (String(((_sS[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase() !== 'prepare series') continue;
    let _oS = null; try { _oS = [].concat(JSON.parse(String((_sS[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_oS && _oS.status === 'PREPARED' && _oS.card_text) { text = String(_oS.card_text); _prepared = true; }
    break;
  }
} catch (e) {}

"""
RELAY_OLD = """    if (!/^(prepare booking|book session)$/.test(_t9)) continue;"""
RELAY_NEW = """    if (!/^(prepare booking|book session|prepare series)$/.test(_t9)) continue;   // v225: Prepare Series' questions too"""

def main(w):
    w["name"] = "Project Jessie — v225 (deterministic series)"
    N = {n["name"]: n for n in w["nodes"]}
    # Prepare Series tool: a copy of Book Series, in prepare mode, with Prepare Booking's extra inputs
    bs = N["Book Series"]; ps = copy.deepcopy(bs); ps["id"] = str(uuid.uuid4()); ps["name"] = "Prepare Series"
    ps["position"] = [bs["position"][0] + 160, bs["position"][1] + 140]
    v = ps["parameters"]["workflowInputs"]["value"]; pb = N["Prepare Booking"]["parameters"]["workflowInputs"]["value"]
    v["mode"] = '={{ "prepare" }}'; v["confirmed"] = "={{ false }}"
    for k in ("asked_text", "staff_data", "authority", "room_override"): v[k] = pb[k]
    sch = ps["parameters"]["workflowInputs"].get("schema") or []
    have = {c.get("id") for c in sch}
    for k, ty in (("mode", "string"), ("asked_text", "string"), ("staff_data", "string"), ("authority", "string"), ("room_override", "boolean"), ("dates", "string")):
        if k not in have: sch.append({"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "canBeUsedToMatch": True, "type": ty})
    ps["parameters"]["workflowInputs"]["schema"] = sch
    ps["parameters"]["description"] = ("For any repeating booking (a series), before anything is booked: give the pattern (frequency, weekday codes, start "
        "date, a count or stop date, all-day or the times) and the booking details (title, room, session type, client, engineer, "
        "description). It works out the dates, checks every one like Prepare Booking, and shows the requester the series card "
        "itself - send nothing else. If it asks a question, ask exactly that. The yes books it automatically.")
    w["nodes"].append(ps)
    w["connections"]["Prepare Series"] = {"ai_tool": [[{"node": "Jessie AI Agent", "type": "ai_tool", "index": 0}]]}
    # Book Series tool also passes the new (empty) inputs so its schema matches the sub-workflow
    bsv = bs["parameters"]["workflowInputs"]["value"]
    bsv.setdefault("mode", '={{ "" }}'); bsv.setdefault("dates", '={{ "" }}')
    bsch = bs["parameters"]["workflowInputs"].get("schema") or []; bh = {c.get("id") for c in bsch}
    for k in ("mode", "dates"):
        if k not in bh: bsch.append({"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "canBeUsedToMatch": True, "type": "string"})
    bs["parameters"]["workflowInputs"]["schema"] = bsch
    # prompt
    ag = N["Jessie AI Agent"]["parameters"]["options"]; ag["systemMessage"] = sub1(ag["systemMessage"], PROMPT_OLD, PROMPT_NEW, "prompt")
    # Guard Probe
    gp = N["Guard Probe"]["parameters"]; s = gp["jsCode"]
    s = sub1(s, GP_ANCHOR, GP_SERIES + GP_ANCHOR, "gp series card"); s = sub1(s, RELAY_OLD, RELAY_NEW, "gp relay"); gp["jsCode"] = s
    # Prepared Key
    pk = N["Prepared Key"]["parameters"]; pk["jsCode"] = sub1(pk["jsCode"], PK_OLD, PK_NEW, "prepared key")
    # Prepared Series -> Series Direct? -> Series Direct -> Series Direct Reply -> Send Reply, between Move Direct? (no) and Already Done?
    md = N["Move Direct?"]; x, y = md["position"]
    pser = {"parameters": {"jsCode": PREPARED_SERIES}, "name": "Prepared Series", "type": "n8n-nodes-base.code", "typeVersion": 2, "id": str(uuid.uuid4()), "position": [x + 200, y + 200]}
    sdq = copy.deepcopy(N["Move Direct?"]); sdq["id"] = str(uuid.uuid4()); sdq["name"] = "Series Direct?"; sdq["position"] = [x + 400, y + 200]
    cond = sdq["parameters"]["conditions"]["conditions"][0]; cond["id"] = str(uuid.uuid4())
    cond["leftValue"] = "={{ (($('Prepared Series').first().json._seriesDirect || {}).use === true) ? 'yes' : 'no' }}"
    sd = copy.deepcopy(N["Move Direct"]); sd["id"] = str(uuid.uuid4()); sd["name"] = "Series Direct"; sd["position"] = [x + 600, y + 120]
    sd["parameters"]["workflowId"] = copy.deepcopy(bs["parameters"]["workflowId"])
    P = "$('Prepared Series').first().json._seriesDirect.p"
    sd["parameters"]["workflowInputs"]["value"] = {
        "summary": "={{ %s.summary }}" % P, "rooms": "={{ %s.rooms }}" % P, "session_type": "={{ %s.session_type }}" % P,
        "client": "={{ %s.client }}" % P, "engineer": "={{ %s.engineer }}" % P, "description": "={{ %s.description }}" % P,
        "bookingType": "={{ %s.bookingType }}" % P, "department": "={{ %s.department }}" % P,
        "room_override": "={{ %s.room_override === true }}" % P, "all_day": "={{ %s.all_day === true }}" % P,
        "time_start": "={{ %s.time_start }}" % P, "time_end": "={{ %s.time_end }}" % P, "dates": "={{ %s.dates }}" % P,
        "requester_text": "={{ %s.requester_text }}" % P,
        "frequency": "", "by_days": "", "start_date": "", "count": "={{ 0 }}", "until_date": "", "mode": "",
        "confirmed": "={{ $('Gate Context').first().json.confirmed === true }}",
        "reference_data": "={{ $('Room Table').first().json.referenceData }}",
        "staff_data": pb["staff_data"], "authority": pb["authority"], "asked_text": "" }
    sd["parameters"]["workflowInputs"]["attemptToConvertTypes"] = False; sd["parameters"]["workflowInputs"]["convertFieldsToString"] = False
    sdr = {"parameters": {"jsCode": SERIES_DIRECT_REPLY}, "name": "Series Direct Reply", "type": "n8n-nodes-base.code", "typeVersion": 2, "id": str(uuid.uuid4()), "position": [x + 800, y + 120]}
    w["nodes"] += [pser, sdq, sd, sdr]
    C = w["connections"]
    br = C["Move Direct?"]["main"]
    if [c["node"] for c in br[1]] != ["Already Done?"]: raise SystemExit("Move Direct? false branch changed")
    br[1] = [{"node": "Prepared Series", "type": "main", "index": 0}]
    C["Prepared Series"] = {"main": [[{"node": "Series Direct?", "type": "main", "index": 0}]]}
    C["Series Direct?"] = {"main": [[{"node": "Series Direct", "type": "main", "index": 0}], [{"node": "Already Done?", "type": "main", "index": 0}]]}
    C["Series Direct"] = {"main": [[{"node": "Series Direct Reply", "type": "main", "index": 0}]]}
    C["Series Direct Reply"] = {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    _BS = json.load(open("workflows/book-session-v92.json"))
    json.dump(book_series(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
