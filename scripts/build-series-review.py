#!/usr/bin/env python3
"""Book Series v5 + main v226 (series review fixes) - review of the v4 / v225 candidates (6 Oct, not imported):
  1. main v225 left Expand Series on the agent with its description "Use this for any repeating booking before you present the
     series ... Its answer also says how to present the series and what to do when they reply yes - follow it", and its answer
     says "Present these dates in ONE summary". That contradicts the new prompt line, and a tool's own instruction tends to win:
     the model would keep writing series cards itself, which Series Direct never books. main v226 takes Expand Series off the
     agent (the node stays, unconnected) - Prepare Series is the only way to show a series - and the Book Series / Prepare
     Series input descriptions no longer say "same as Expand Series". Book Series stays as the fallback for a yes the code
     could not verify (Gate Context's seriesNotice), described as such.
  2. Book Series v4 wrote the stored description as "Engineer: <name>" even when there is none (a conference room or M booth
     series) -> "Engineer: " on every event. v5 writes the Engineer / Arranger segments only when they are there.
  3. With no room named, Book Session picks the free usual room per date, so dates could be checked in different rooms while
     the card showed the first one for all. v5 keeps the first date's room; a date prepared in another room counts as taken
     (that room was not free) and is named on the card.
  The prompt ("A series ... goes through Expand Series and Book Series") and Prepare Booking's description ("(Expand Series, then
  Book Series)") said the same - both now name Prepare Series (gotcha 9).
  4. A second yes while the series is still being booked (a series takes ~25 s a date; on 6 Oct two yeses came 16 s apart) found
     the card still newest and would have booked it again - the repeat-yes guard (Already Done?) only works once the reply is
     posted. main v226: Series Direct first writes a lock row (Lock Series, the same data table, "lock-" + the series key);
     Read Prepared also reads it, and a yes to the same card within 15 minutes of the lock gets "Still booking that series"
     (Series Busy? -> Series Busy Reply) - never a second booking, never the model.
  scripts/build-series-review.py <book-series-v4> <book-series-out> <main-v225> <main-out>
"""
import json, sys, copy, uuid
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

AG_ROOM_OLD = """    if (r.status === 'PREPARED' && P && P.F && !r.needs_consent) { ok.push(d); if (!first) first = { r, P, d }; }"""
AG_ROOM_NEW = """    // v5: every date in the first date's room - one prepared in another room (no room named) means that room was not free
    if (r.status === 'PREPARED' && P && P.F && !r.needs_consent && (!first || pbNorm(P.F['Room']) === pbNorm(first.P.F['Room']))) { ok.push(d); if (!first) first = { r, P, d }; }"""
AG_DESC_OLD = """  const desc = ['Engineer: ' + F['Engineer']].concat(F['Arranger'] ? ['Arranger: ' + F['Arranger']] : [])"""
AG_DESC_NEW = """  const desc = (F['Engineer'] ? ['Engineer: ' + F['Engineer']] : []).concat(F['Arranger'] ? ['Arranger: ' + F['Arranger']] : [])   // v5: none for a room with no engineer"""

def book_series(w):
    w["name"] = "Jessie — Book Series — v5 (series review fixes)"
    ag = node(w, "Aggregate")["parameters"]; s = ag["jsCode"]
    s = sub1(s, AG_ROOM_OLD, AG_ROOM_NEW, "room"); s = sub1(s, AG_DESC_OLD, AG_DESC_NEW, "desc"); ag["jsCode"] = s
    return w

PROMPT_OLD = """Their yes books the series automatically - do not call Book Series yourself. Use Expand Series only to answer which dates a pattern gives, never to present a booking."""
PROMPT_NEW = """Their yes books the series automatically - do not call Book Series yourself. To answer which dates a pattern gives, use Prepare Series too: its card lists them."""
DESC_SWAPS = [(" Same as Expand Series.", ""), (" Same value you gave Expand Series.", ""), ("First date YYYY-MM-DD, same as Expand Series.", "First date YYYY-MM-DD, resolved against today.")]
BS_DESC = ("Only when you are told a series is already approved and it was not booked automatically (a yes the code could not match to a "
           "Prepare Series card). Give the same pattern and booking details you gave Prepare Series. It books each date, skips any whose room "
           "is taken, and returns what was booked and skipped. Call it once - never for a Prepare Series card, and never Book Session for a series.")

PROMPT2_OLD = "A series is the exception: it goes through Expand Series and Book Series (see *Recurring bookings*), never Prepare Booking."
PROMPT2_NEW = "A series is the exception: it goes through Prepare Series (see *Recurring bookings*), never Prepare Booking."
PB_OLD = "not for a recurring series (Expand Series, then Book Series)"
PB_NEW = "not for a recurring series (Prepare Series)"
LOCK_OLD = """    else { out.ok = true; out.p = P.inputs; }"""
LOCK_NEW = """    else {
      out.ok = true; out.p = P.inputs;
      // v226: a yes while this same series is still being booked (Lock Series, written as Series Direct starts) is not a
      // second booking - a series takes ~25 s a date and the card stays the newest message until the result is posted
      let lk = null; try { lk = $('Read Prepared').all().map(i => (i && i.json) || {}).find(r => r.cache_key === 'lock-' + k); } catch (e) {}
      const la = lk ? Date.now() - Date.parse(lk.refreshed_at || '') : NaN;
      if (la >= -60000 && la < 15 * 60000) { out.ok = false; out.busy = true; out.reason = 'this series is already being booked'; }
    }"""
USE_OLD = """  out.use = out.ok && gate.confirmed === true;"""
USE_NEW = """  out.use = out.ok && gate.confirmed === true;
  out.busy = out.busy === true && gate.confirmed === true;"""
BUSY_REPLY = """// Series Busy Reply (main v226): a yes to a series card that is already being booked (Lock Series) - said, not booked again.
return [{ json: { output: 'Still booking that series - I\u2019ll post what was booked here when it\u2019s done.', directBooking: { status: 'IN_PROGRESS', series: true } } }];"""
def main(w):
    w["name"] = "Project Jessie — v226 (series review fixes)"
    if "Expand Series" in w["connections"]: del w["connections"]["Expand Series"]
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]; ag["systemMessage"] = sub1(sub1(ag["systemMessage"], PROMPT_OLD, PROMPT_NEW, "prompt"), PROMPT2_OLD, PROMPT2_NEW, "prompt 2")
    pb = node(w, "Prepare Booking")["parameters"]; k = "description" if "description" in pb else "toolDescription"; pb[k] = sub1(pb[k], PB_OLD, PB_NEW, "prepare booking desc")
    for nm in ("Book Series", "Prepare Series"):
        n = node(w, nm); s = json.dumps(n["parameters"], ensure_ascii=False)
        for a, b in DESC_SWAPS: s = sub1(s, a, b, nm + ": " + a)
        n["parameters"] = json.loads(s)
    node(w, "Book Series")["parameters"]["description"] = BS_DESC
    # 4. the in-progress lock
    rp = node(w, "Read Prepared")["parameters"]; rp["matchType"] = "anyCondition"
    rp["filters"]["conditions"].append({"keyName": "cache_key", "keyValue": "={{ 'lock-' + ($('Prepared Key').first().json.prep_key || 'prep-none') }}"})
    ps = node(w, "Prepared Series")["parameters"]
    ps["jsCode"] = sub1(ps["jsCode"], LOCK_OLD, LOCK_NEW, "lock check"); ps["jsCode"] = sub1(ps["jsCode"], USE_OLD, USE_NEW, "busy")
    sdq = node(w, "Series Direct?"); x, y = sdq["position"]
    lk = {"parameters": {"operation": "upsert", "dataTableId": copy.deepcopy(rp["dataTableId"]), "matchType": "allConditions",
            "filters": {"conditions": [{"keyName": "cache_key", "keyValue": "={{ 'lock-' + $('Prepared Key').first().json.prep_key }}"}]},
            "columns": {"mappingMode": "defineBelow", "value": {"cache_key": "={{ 'lock-' + $('Prepared Key').first().json.prep_key }}", "payload": "={{ JSON.stringify({ lock: true, dates: $('Prepared Series').first().json._seriesDirect.p.dates }) }}", "refreshed_at": "={{ new Date().toISOString() }}"},
              "matchingColumns": [], "schema": [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True, "type": "string", "readOnly": False, "removed": False} for c in ("cache_key", "payload", "refreshed_at")],
              "attemptToConvertTypes": False, "convertFieldsToString": False}, "options": {}},
          "name": "Lock Series", "type": "n8n-nodes-base.dataTable", "typeVersion": node(w, "Read Prepared")["typeVersion"], "id": str(uuid.uuid4()),
          "position": [x + 100, y - 160], "onError": "continueRegularOutput"}
    sbq = copy.deepcopy(sdq); sbq["id"] = str(uuid.uuid4()); sbq["name"] = "Series Busy?"; sbq["position"] = [x + 200, y + 160]
    c0 = sbq["parameters"]["conditions"]["conditions"][0]; c0["id"] = str(uuid.uuid4())
    c0["leftValue"] = "={{ (($('Prepared Series').first().json._seriesDirect || {}).busy === true) ? 'yes' : 'no' }}"
    sbr = {"parameters": {"jsCode": BUSY_REPLY}, "name": "Series Busy Reply", "type": "n8n-nodes-base.code", "typeVersion": 2, "id": str(uuid.uuid4()), "position": [x + 400, y + 100]}
    w["nodes"] += [lk, sbq, sbr]
    C = w["connections"]
    C["Series Direct?"] = {"main": [[{"node": "Lock Series", "type": "main", "index": 0}], [{"node": "Series Busy?", "type": "main", "index": 0}]]}
    C["Lock Series"] = {"main": [[{"node": "Series Direct", "type": "main", "index": 0}]]}
    C["Series Busy?"] = {"main": [[{"node": "Series Busy Reply", "type": "main", "index": 0}], [{"node": "Already Done?", "type": "main", "index": 0}]]}
    C["Series Busy Reply"] = {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book_series(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
