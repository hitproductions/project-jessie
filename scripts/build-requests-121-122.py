#!/usr/bin/env python3
"""Builds PENDING 121 + 122 (27 Oct) - room requests, from the live downloads:

  workflows/move-booking-v40.json          Jessie — Move Booking — v40 (request follows the booking)
  workflows/slack-interactions-v49.json    Jessie — Slack Interactions — v49 (one answer at a time)
  workflows/consent-sweep-v4.json          Jessie — Consent Sweep — v4 (waits for an answer in progress)

121 - a change to the booking in the way ended the request. Move's Consent Hook finalized on ANY successful change of the booking a
      request names (a move that still overlaps, an edit of only its engineer / title / note), and Finalize then failed
      (ROOM_OCCUPIED) - FAILED, "Couldn't book … after all". Now the hook finalizes only when the changed booking no longer
      overlaps the requested slot (time or room); otherwise the request follows the booking: Retarget Row writes the new event
      id, title and Messages.inc (date, times, rooms) to the row, and it stays PENDING. Slack Interactions v49's Build Change C
      ("I've cleared it with them - they'll move it") opens the booking the row names now, not the one on the button.
122 - two answers within seconds both counted (Keep / Withdraw and Give it up together: the booking cancelled, then Finalize read
      REJECTED and placed nothing - the room ended up empty). Now an answer claims the request first: Claim Row writes the
      "Claim" column (execution id @ time), waits 2 s, reads it back, and only the answer whose claim is still there acts
      (Claim Check); one that finds a fresh claim (< 2 min) does nothing. The requester's "They gave it up" goes through the same
      claim. Consent Sweep v4 waits a round on a row with a fresh claim. Also: a "Pick another room" booking from the request
      card no longer writes the old card (live buttons) back over a request that ended meanwhile - Source Done's update reads
      the message first and leaves it when the "⏳" line is gone (Source Check).
Needs a "Claim" header in the Consent Requests tab (Jessie Log spreadsheet) before Slack Interactions v49 goes in.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMP = os.path.join(ROOT, "workflows", "imported")


def load(name):
    wf = json.load(open(os.path.join(IMP, name)))
    return wf, {n["name"]: n for n in wf["nodes"]}, wf["connections"]


def mk_sub(by):
    def sub(node, a, b, n=1):
        js = by[node]["parameters"]["jsCode"]
        assert js.count(a) == n, (node, js.count(a), a[:90])
        by[node]["parameters"]["jsCode"] = js.replace(a, b)
    return sub


def save(wf, title, out):
    wf["name"] = title
    p = os.path.join(ROOT, "workflows", out)
    with open(p, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(p, ROOT), len(wf["nodes"]), "nodes")


def clone(node, name, pos, **params):
    n = json.loads(json.dumps(node))
    n["name"] = name; n["id"] = str(uuid.uuid4()); n["position"] = pos
    if "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    for k, v in params.items():
        n["parameters"][k] = v
    return n


def code(name, js, pos):
    return {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}


def to(*names):
    return [{"node": n, "type": "main", "index": 0} for n in names]


si0, si0_by, _ = load("slack-interactions-v48-imported.json")
UPDATE_REQUEST = si0_by["Update Request"]          # Sheets update on Consent Requests, matching Request ID
READ_REQUESTS = si0_by["Read Requests"]            # Sheets read of Consent Requests
WAIT = si0_by["Pretend Work"]                       # a Wait node (amount 3)

# ---------------------------------------------------------------- Move Booking v40 (121)
wf, by, C = load("move-booking-v39-imported.json")
by["Consent Hook"]["parameters"]["jsCode"] = r"""// Move tail hook - after a successful move, place a requester whose consent request this move freed.
// v40 (27 Oct, PENDING 121): only when the changed booking no longer overlaps the requested slot (time or room). A change that
// still overlaps (a move within the slot, an edit of the title / people / note) leaves the request open and makes it follow
// the booking: retarget = the row's new event id, title and Messages.inc. Fail-safe: the move already succeeded.
const rows = $input.all().map(i => (i && i.json) || {});
const RB = ($('Resolve Booking').first().json) || {};
const origId = String(RB.original_id || '').trim();
function findConsentForMove(id, rows){ if(!id) return null; for(const r of (rows||[])){ if(!r) continue; if(String(r['Status']||'').toUpperCase()!=='PENDING') continue; const inc=String(r['Incumbent Event Id']||'').trim(); if(inc && inc===id) return r; } return null; }
const matched = findConsentForMove(origId, rows);
if (!matched) return [{ json: { hasMatch: false, matched: {}, retarget: false } }];
const ms = x => { const s = String(x || ''); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? Date.parse(s + 'T00:00:00+08:00') : Date.parse(s); };
const ns = ms(RB.new_start), ne = ms(RB.new_end), rs = ms(matched['Req Start']), re = ms(matched['Req End']);
const timeOverlap = !(ne <= rs || ns >= re);   // a time that cannot be read counts as overlapping (the request stays open)
const norm = r => String(r || '').split(',').map(x => x.replace(/^KDC Plaza-Top Level-/i, '').replace(/(?:\s*\([^)]*\))+\s*$/, '').trim().toLowerCase()).filter(Boolean);
const want = norm(matched['Room/Booth'])[0] || '', have = norm(RB.location);
const roomOverlap = !want || !have.length || have.indexOf(want) !== -1;
if (!(timeOverlap && roomOverlap)) return [{ json: { hasMatch: true, matched, retarget: false } }];
let newId = ''; try { newId = String((($('Create Replacement').first() || {}).json || {}).id || ''); } catch (e) { newId = ''; }
if (!newId) return [{ json: { hasMatch: false, matched: {}, retarget: false } }];
const mnl = t => { if (!Number.isFinite(t)) return { d: '', hm: '' }; const d = new Date(t + 8 * 3600000); return { d: d.toISOString().slice(0, 10), hm: d.toISOString().slice(11, 16) }; };
let M = {}; try { M = JSON.parse(matched['Messages'] || '{}') || {}; } catch (e) { M = {}; }
const a = mnl(ns), b = mnl(ne), allDay = /^\d{4}-\d{2}-\d{2}$/.test(String(RB.new_start || ''));
M.inc = Object.assign({}, M.inc || {}, { id: newId, t: String(RB.title || (M.inc || {}).t || matched['Incumbent Title'] || ''),
  d: isNaN(ns) ? (M.inc || {}).d : a.d, s: allDay ? '' : (isNaN(ns) ? (M.inc || {}).s : a.hm), e: allDay ? '' : (isNaN(ne) ? (M.inc || {}).e : b.hm),
  r: String(RB.location || (M.inc || {}).r || '') });
return [{ json: { hasMatch: false, matched: {}, retarget: true,
  row: { 'Request ID': matched['Request ID'], 'Incumbent Event Id': newId, 'Incumbent Title': M.inc.t, 'Messages': JSON.stringify(M) } } }];"""
pic = by["Place If Consent?"]
ret_if = clone(pic, "Retarget?", [pic["position"][0] + 200, pic["position"][1] + 250])
ret_if["parameters"]["conditions"]["conditions"][0]["id"] = str(uuid.uuid4())
ret_if["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $json.retarget }}"
ret_code = code("Retarget Data", "// v40: the row's new event id, title and Messages.inc, for Retarget Row\nreturn [{ json: $('Consent Hook').first().json.row }];",
                [pic["position"][0] + 400, pic["position"][1] + 200])
ret_row = clone(UPDATE_REQUEST, "Retarget Row", [pic["position"][0] + 600, pic["position"][1] + 200])
ret_row["onError"] = "continueRegularOutput"
wf["nodes"] += [ret_if, ret_code, ret_row]
assert [x["node"] for x in C["Place If Consent?"]["main"][1]] == ["Notify?"]
C["Place If Consent?"]["main"][1] = to("Retarget?")
C["Retarget?"] = {"main": [to("Retarget Data"), to("Notify?")]}
C["Retarget Data"] = {"main": [to("Retarget Row")]}
C["Retarget Row"] = {"main": [to("Notify?")]}
save(wf, "Jessie — Move Booking — v40 (request follows the booking)", "move-booking-v40.json")

# ---------------------------------------------------------------- Slack Interactions v49 (122, and 121's Change C)
wf, by, C = load("slack-interactions-v48-imported.json")
sub = mk_sub(by)
FRESH = ("const _cl = String(row['Claim'] || ''), _at = Date.parse(_cl.split('@')[1] || '');   // v49 (PENDING 122): another answer is being acted on\n"
         "if (_cl && Number.isFinite(_at) && Date.now() - _at < 120000) return [{ json: { go: 3, why: 'being answered' } }];\n")
sub("Request Act", "if (st !== 'PENDING') return [{ json: { go: 4, row, extra: { how: String(row['Resolved Via'] || '') } } }];\n",
    "if (st !== 'PENDING') return [{ json: { go: 4, row, extra: { how: String(row['Resolved Via'] || '') } } }];\n" + FRESH)

CLAIM_ROW = r"""// Claim Row (v49, 27 Oct, PENDING 122): an answer that acts on a request (Keep, Withdraw, Let them use it, Give it up, the
// requester's "They gave it up") claims it first - the Claim column, this execution @ now. Write Claim, wait 2 s, Read Claim:
// Claim Check lets only the answer whose claim is still there act. No open row, or someone else's fresh claim -> nothing written.
let RC = null; try { RC = $('Read Cleared').first().json; } catch (e) { RC = null; }
let row = null;
if (RC) row = $('Read Requests C').all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(RC.rid || '')) || null;
else row = ($input.first().json || {}).row || null;
const rid = row ? String(row['Request ID'] || '') : '';
let ex = ''; try { ex = String($execution.id || ''); } catch (e) { ex = ''; }
const tok = (ex || Math.random().toString(36).slice(2, 10)) + '@' + new Date().toISOString();
const cl = row ? String(row['Claim'] || '') : '', at = Date.parse(cl.split('@')[1] || '');
const busy = !!cl && Number.isFinite(at) && Date.now() - at < 120000;
const skip = !rid || String((row || {})['Status'] || '').toUpperCase() !== 'PENDING' || busy;
return [{ json: { 'Request ID': rid, 'Claim': tok, skip } }];"""
WRITE_DATA = "// v49: the claim, as the row's two columns\nconst j = $('Claim Row').first().json;\nreturn [{ json: { 'Request ID': j['Request ID'], 'Claim': j['Claim'] } }];"
CLAIM_CHECK = r"""// Claim Check (v49, PENDING 122): the request read back 2 s after claiming - only the answer whose claim is still there (and the
// request still open) acts; any other answer does nothing (the winner's messages update the cards). The requester's "They gave
// it up" goes on to Give Up Plan either way, which says why when it may not act.
const CR = $('Claim Row').first().json;
let rows = []; try { rows = $('Read Claim').all().map(i => i.json || {}); } catch (e) { rows = []; }
const r = rows.find(x => x['Request ID'] && String(x['Request ID']) === String(CR['Request ID'] || '')) || null;
const mine = !CR.skip && !!r && String(r['Claim'] || '') === String(CR['Claim']) && String(r['Status'] || '').toUpperCase() === 'PENDING';
let RC = null; try { RC = $('Read Cleared').first().json; } catch (e) { RC = null; }
if (RC) return [{ json: { go: 2, mine } }];
const A = $('Request Act').first().json;
if (mine) return [{ json: Object.assign({}, A, { mine: true }) }];
if (r && String(r['Status'] || '').toUpperCase() !== 'PENDING') return [{ json: { go: 4, row: r, extra: { how: String(r['Resolved Via'] || '') }, mine: false } }];
return [{ json: { go: 3, why: 'answered by someone else', mine: false } }];"""
ra = by["Request Act"]["position"]
claim_if = clone(si0_by["Cleared Move?"], "Claim?", [ra[0] + 150, ra[1] + 300])
claim_if["parameters"]["conditions"]["conditions"][0].update({"id": str(uuid.uuid4()), "leftValue": "={{ [0, 1, 2].indexOf($json.go) !== -1 }}"})
write_if = clone(si0_by["Cleared Move?"], "Write Claim?", [ra[0] + 450, ra[1] + 300])
write_if["parameters"]["conditions"]["conditions"][0].update({"id": str(uuid.uuid4()), "leftValue": "={{ $json.skip === false }}"})
nodes = [claim_if, code("Claim Row", CLAIM_ROW, [ra[0] + 300, ra[1] + 300]), write_if,
         code("Claim Data", WRITE_DATA, [ra[0] + 600, ra[1] + 300]),
         clone(UPDATE_REQUEST, "Write Claim", [ra[0] + 750, ra[1] + 300]),
         clone(WAIT, "Wait Claim", [ra[0] + 900, ra[1] + 300], amount=2),
         clone(READ_REQUESTS, "Read Claim", [ra[0] + 1050, ra[1] + 300]),
         code("Claim Check", CLAIM_CHECK, [ra[0] + 1200, ra[1] + 300])]
nodes[4]["onError"] = "continueRegularOutput"; nodes[6]["onError"] = "continueRegularOutput"
nodes[6]["alwaysOutputData"] = True   # Claim Check runs even when the read returns nothing
wf["nodes"] += nodes
assert [x["node"] for x in C["Request Act"]["main"][0]] == ["Act Route"]
C["Request Act"]["main"][0] = to("Claim?")
C["Claim?"] = {"main": [to("Claim Row"), to("Act Route")]}
C["Claim Row"] = {"main": [to("Write Claim?")]}
C["Write Claim?"] = {"main": [to("Claim Data"), to("Claim Check")]}
C["Claim Data"] = {"main": [to("Write Claim")]}
C["Write Claim"] = {"main": [to("Wait Claim")]}
C["Wait Claim"] = {"main": [to("Read Claim")]}
C["Read Claim"] = {"main": [to("Claim Check")]}
C["Claim Check"] = {"main": [to("Act Route")]}
assert [x["node"] for x in C["Cleared Move?"]["main"][1]] == ["Give Up Plan"]
C["Cleared Move?"]["main"][1] = to("Claim Row")
# Give Up Plan: the requester's rows from Read Requests C (its input is Claim Check now); not theirs to act -> said
sub("Give Up Plan", "  row = $input.all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(RC.rid || '')) || null;",
    "  row = $('Read Requests C').all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(RC.rid || '')) || null;   // v49: input is Claim Check")
sub("Give Up Plan", "let M = {}; try { M = JSON.parse(row['Messages'] || '{}') || {}; } catch (e) { M = {}; }",
    "{ let _cc = null; try { _cc = $('Claim Check').first().json; } catch (e) { _cc = null; }   // v49 (PENDING 122): another answer is being acted on\n"
    "  if (_cc && _cc.mine === false) return [{ json: { ok: false, channel: c.channel || c.user, text: 'Someone answered this request at the same time – nothing was changed.' } }]; }\n"
    "let M = {}; try { M = JSON.parse(row['Messages'] || '{}') || {}; } catch (e) { M = {}; }")
# Give Up Plan's request (A path) as the claim saw it - the row read back fresh
sub("Give Up Plan", "} else { const A = $('Request Act').first().json; row = A.row; by = A.by || ''; }",
    "} else { const A = $('Request Act').first().json; row = A.row; by = A.by || '';\n"
    "  try { const _f = $('Read Claim').all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String((row || {})['Request ID'] || '')); if (_f) row = Object.assign({}, row, _f); } catch (e) {} }   // v49: fresh (Move v40 may have moved it)")
# 121: "they'll move it" opens the booking the row names now (Move v40 retargets the row when the booking moves within the slot)
sub("Build Change C", "// v12: the new values typed in the chat (main v265) - the form starts there; a start alone keeps the booking's length",
    "{ let _M = {}; try { _M = JSON.parse(_row['Messages'] || '{}') || {}; } catch (e) { _M = {}; }   // v49 (PENDING 121): the booking as the request has it now\n"
    "  if (_M.inc && _M.inc.id) b = Object.assign({}, b, _M.inc); }\n"
    "// v12: the new values typed in the chat (main v265) - the form starts there; a start alone keeps the booking's length")
# 122b: Source Done reads the message first - a request card that ended meanwhile is left as it is
SRC_CHECK = r"""// Source Check (v49, 27 Oct, PENDING 122): the message as it is now - when the "⏳" line Mark Source put on it is gone (a
// request card redrawn when the request ended, another update), it is left as it is; otherwise Source Done's update goes ahead.
const D = $('Source Done').first().json || {};
const m = ((($input.first() || {}).json || {}).messages || []).find(x => String(x.ts) === String(D.ts || '')) || null;
if (m && !(m.blocks || []).some(b => b.block_id === 'src_status')) return [];
return [{ json: D }];"""
sd = by["Source Done"]["position"]
wf["nodes"] += [clone(by["Get Source"], "Get Source 2", [sd[0] + 100, sd[1] + 250]), code("Source Check", SRC_CHECK, [sd[0] + 300, sd[1] + 250])]
by2 = {n["name"]: n for n in wf["nodes"]}
by2["Get Source 2"]["onError"] = "continueRegularOutput"
assert [x["node"] for x in C["Source Done"]["main"][0]] == ["Update Source"]
C["Source Done"]["main"][0] = to("Get Source 2")
C["Get Source 2"] = {"main": [to("Source Check")]}
C["Source Check"] = {"main": [to("Update Source")]}
upd = by2["Update Source"]["parameters"]
assert "$json" in json.dumps(upd), upd
save(wf, "Jessie — Slack Interactions — v49 (one answer at a time)", "slack-interactions-v49.json")

# ---------------------------------------------------------------- Consent Sweep v4 (122)
wf, by, C = load("consent-sweep-v3-imported.json")
sub = mk_sub(by)
sub("Sweep Decide", "if(status!=='PENDING') return 'skip';",
    "if(status!=='PENDING') return 'skip'; const _cl=String((row&&row.Claim)||''), _at=Date.parse(_cl.split('@')[1]||''); if(_cl && Number.isFinite(_at) && new Date(nowISO).getTime()-_at<120000) return 'wait'; /* v4 (PENDING 122): an answer is being acted on */")
save(wf, "Jessie — Consent Sweep — v4 (waits for an answer in progress)", "consent-sweep-v4.json")
