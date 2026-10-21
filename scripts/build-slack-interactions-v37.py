#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v37.json - "Jessie — Slack Interactions", v37 (room requests), 21 Oct.

Slice 2 - approvals and shared rooms (docs/design/slice-2-approvals.md; Howard's answers 21 Oct: A Give it up yes, B the small
form, C the Change form later, D deadlines unchanged, E no series). Built on the v36 download.
  1. Step 2: "Choose a different room" gets a second group, "Booked – ask to use" - the booked rooms a request can be made for
     (Book Session's own rules; only rooms that normally do this booking type; not for a series). With no free room but one
     that can be asked for, step 2 is no longer a dead end. Picking one shows what happens under it (who is asked, the
     deadline) and the button says Send request (Note Toggle); Read Step 2 sends request_ok to Book Session (v120).
  2. After Book: Book Session's PREEMPT_PENDING -> "📨 Request sent" on the form; the requester's card is in the DM already
     (Open Consent Request v12 -> Jessie — Request Messages), so no "Not booked" DM.
  3. The buttons on a request (route 16): Keep my booking / Keep it -> REJECTED; Withdraw request -> WITHDRAWN (both update the
     row, then every message of the request through Request Messages); Let them use it (M booth) and I've cleared it with them
     (M booth) -> Finalize; Give it up -> the booking cancelled (as its booker), then Finalize. Only the people the request is
     for (or Howard, while every request message goes to him) can answer; a request that already ended just redraws.
  4. Move my booking (cr_move) opens the Change form on the booking (route 10, without touching the request message); when the
     change goes through, Move Booking's tail hook places the requester (live since 21 Sep).
  5. I've cleared it with them on a priority request (route 17): a small form - "Move it, I'll pick where" or "They gave it up"
     (route 18). Move: the Change form for their booking, changed as its booker (To Move: meta.as); gave up: cancelled as above.
  6. Pick another room (cr_pick) opens Book a room at the same date and time (route 4).
LAUNCH SWITCH: Request Act and Give Up Plan carry DEV_REDIRECT (Howard answers for everyone while testing) - '' at launch.
Ids: Jessie — Request Messages by scripts/set-request-messages-id.py; Finalize Consent TO1UnZTZ2LhtE9J3, Cancel Booking as live.
"""
import json
import os
import uuid

from approvals_js import ASK_JS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v36-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v37.json")
SW = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "live", "jessie-consent-sweep__QHHDevaWhMk8gSBX.json")))["nodes"]}
MV = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "move-booking-v34-imported.json")))["nodes"]}
FIN = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "live", "jessie-finalize-consent__TO1UnZTZ2LhtE9J3.json")))["nodes"]}
REQUEST_MESSAGES_ID = "REQUEST_MESSAGES_ID"   # scripts/set-request-messages-id.py
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def sub(node, a, b, count=1):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == count, (node, js.count(a), a[:90])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


def code(name, js, pos):
    return {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}


def copy(src, name, pos, params=None):
    n = json.loads(json.dumps(src))
    n.update({"id": str(uuid.uuid4()), "name": name, "position": pos})
    if "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    if params is not None:
        n["parameters"] = params
    return n


L = lambda *a: {"main": [[{"node": x, "type": "main", "index": 0} for x in a]]}

# ---- 1. routes
sub("Check Signature", "rm_keep: 15 };", "rm_keep: 15, cr: 16, cr_cleared: 17, cr_cleared_submit: 18 };   // v37: room requests")
sub("Check Signature", "else if (p.type === 'block_actions' && action === 'open_book') route = ROUTES.open_book;",
    "else if (p.type === 'block_actions' && (action === 'open_book' || action === 'cr_pick')) route = ROUTES.open_book;   // v37: Pick another room")
sub("Check Signature", "else if (p.type === 'block_actions' && action === 'bk_change') route = ROUTES.bk_change;",
    "else if (p.type === 'block_actions' && (action === 'bk_change' || action === 'cr_move')) route = ROUTES.bk_change;   // v37: Move my booking\n"
    "else if (p.type === 'block_actions' && ['cr_keep', 'cr_giveup', 'cr_allow', 'cr_withdraw', 'cr_attest'].indexOf(action) !== -1) route = ROUTES.cr;   // v37\n"
    "else if (p.type === 'block_actions' && action === 'cr_cleared') route = ROUTES.cr_cleared;   // v37\n"
    "else if (p.type === 'view_submission' && cb === 'cr_cleared') route = ROUTES.cr_cleared_submit;   // v37")
by["Route"]["parameters"]["numberOutputs"] = 19
while len(C["Route"]["main"]) < 19:
    C["Route"]["main"].append([])

# ---- 2. step 2: "Booked – ask to use"
sub("Build Step 2", "// Build Step 2: the free rooms that fit", ASK_JS + "\n// Build Step 2: the free rooms that fit")
sub("Build Step 2", "// v21: booths and holding rooms on top of the studio (free on every date of a series)\n",
    "// v37: the booked rooms a request can be made for - rooms that normally do this type (an M booth for a booth booking)\n"
    "const _usualNames = (() => { const nameOf = {}; for (const r of data.rooms || []) nameOf[r.id] = String((r.fields || {})['Room Name'] || '').trim();\n"
    "  const f = (ST || {}).fields || {}; return [].concat(f.Priority || [], f['Last Resort'] || []).map(id => nameOf[id]).filter(Boolean); })();\n"
    "const asks = ASK.rooms(ra, data, s, n => sameKind(n) && (!ONLY || n === ONLY) && (s.kind === 'booth' ? /^M\\d+$/i.test(n) : _usualNames.indexOf(n) !== -1));\n"
    "// v21: booths and holding rooms on top of the studio (free on every date of a series)\n")
sub("Build Step 2", "if (!rooms.length) {\n  if (preNote)", "if (!rooms.length && !asks.length) {   // v37: nothing free and nothing to ask for\n  if (preNote)")
sub("Build Step 2", "  const ini = rooms.find(o => o.value === (preRoom || rooms[0]).value) || rooms[0];",
    "  const ini = rooms.length ? (rooms.find(o => o.value === (preRoom || rooms[0]).value) || rooms[0]) : null;   // v37: none free, only requests")
sub("Build Step 2", "  blocks.push({ type: 'section', block_id: 'room_label', text: md('*' + (noUsual ? 'Available rooms:' : needBooth ? 'Recommended studios:' : 'Recommended rooms:') + '*') },\n"
    "    ...(noUsual ? [{ type: 'context', block_id: 'room_why', elements: [md('The usual rooms for this type of booking are not available in your chosen schedule')] }] : []),\n"
    "    { type: 'actions', block_id: 'room', elements: [{ type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: ini }] });",
    "  if (ini) blocks.push({ type: 'section', block_id: 'room_label', text: md('*' + (noUsual ? 'Available rooms:' : needBooth ? 'Recommended studios:' : 'Recommended rooms:') + '*') },\n"
    "    ...(noUsual ? [{ type: 'context', block_id: 'room_why', elements: [md('The usual rooms for this type of booking are not available in your chosen schedule')] }] : []),\n"
    "    { type: 'actions', block_id: 'room', elements: [{ type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: ini }] });\n"
    "  else blocks.push({ type: 'section', block_id: 'room_label', text: md('Nothing that does ' + label + ' is free then – you can ask for a booked room below.') });   // v37")
sub("Build Step 2", "  if (others.length) blocks.push({ type: 'input', block_id: 'room_other', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'Choose a different room' },   // v26: no hint\n"
    "    element: { type: 'static_select', action_id: 'room_other_pick', placeholder: { type: 'plain_text', text: 'Select a room' }, options: others.map(n => opt(n, n)) } });",
    "  if (others.length || asks.length) blocks.push({ type: 'input', block_id: 'room_other', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'Choose a different room' },   // v26: no hint\n"
    "    element: Object.assign({ type: 'static_select', action_id: 'room_other_pick', placeholder: { type: 'plain_text', text: 'Select a room' } },\n"
    "      asks.length ? { option_groups: [].concat(others.length ? [{ label: { type: 'plain_text', text: 'Available' }, options: others.map(n => opt(n, n)) }] : [],   // v37\n"
    "        [{ label: { type: 'plain_text', text: 'Booked – ask to use' }, options: asks.map(a => opt(a.text, ASK.value(a))) }]) } : { options: others.map(n => opt(n, n)) }) });")
sub("Build Step 2", "  if (BX) blocks.push(...boothBlocks(ini.value, BX));", "  if (BX && ini) blocks.push(...boothBlocks(ini.value, BX));   // v37: no booth for a request")
sub("Build Step 2", "    BX ? { bx: BX } : {})), blocks };", "    BX ? { bx: BX } : {}, rooms.length && asks.length ? { sub: 'Book' } : {})), blocks };   // v37: sub - the button back after a request is unpicked")
sub("Build Step 2", "if (rooms.length) view.submit = { type: 'plain_text', text: SER ? 'Check ' + SER.dates.length + ' dates' : 'Book' };   // v13",
    "if (rooms.length) view.submit = { type: 'plain_text', text: SER ? 'Check ' + SER.dates.length + ' dates' : 'Book' };   // v13\n"
    "else if (asks.length) view.submit = { type: 'plain_text', text: 'Send request' };   // v37: only booked rooms - the one picked is asked for")

# Note Toggle: the line under a picked request, and the button
sub("Note Toggle", "// v29: a room ticked with nothing to clear", ASK_JS + "\n// v37: a booked room picked under \"Booked – ask to use\" - what happens, under it; the button says Send request (and Book again when\n"
    "// a free room is picked instead)\nlet askSubmit = null;\n"
    "if (which === 'room_radio' || which === 'room_other_pick') {\n"
    "  for (let k = blocks.length - 1; k >= 0; k--) if (blocks[k].block_id === 'ask_note') blocks.splice(k, 1);\n"
    "  const pv = which === 'room_other_pick' ? String((a.selected_option || {}).value || '') : '';\n"
    "  let M4 = {}; try { M4 = JSON.parse(V.private_metadata || '{}'); } catch (e) {}\n"
    "  const q = ASK.parse(pv);\n"
    "  if (q) { const info = String(((a.selected_option || {}).text || {}).text || '').split(' · ').slice(1).join(' · ');\n"
    "    const oi = blocks.findIndex(b => /^room_other(~\\d+)?$/.test(b.block_id || ''));\n"
    "    blocks.splice(oi === -1 ? blocks.length : oi + 1, 0, { type: 'context', block_id: 'ask_note', elements: [{ type: 'mrkdwn', text: ASK.line(q.k, q.room, info, M4) }] });\n"
    "    askSubmit = 'Send request'; }\n"
    "  else if (M4.sub) askSubmit = M4.sub;\n"
    "}\n// v29: a room ticked with nothing to clear")
sub("Note Toggle", "    const picked = String((a.selected_option || {}).value || '');",
    "    const picked = String((a.selected_option || {}).value || '').replace(/^ask:[PM]\\|/, '');   // v37: a request - the booth follows its room")
sub("Note Toggle", "if (V.submit) view.submit = V.submit;", "if (V.submit) view.submit = V.submit;\nif (askSubmit) view.submit = { type: 'plain_text', text: askSubmit };   // v37")

# Read Step 2: the request
sub("Read Step 2", "const room0 = valA('room_other_pick') || valA('room_radio');   // v25: one or the other",
    "const room00 = valA('room_other_pick') || valA('room_radio');   // v25: one or the other\n"
    "// v37 (slice 2): a booked room picked under \"Booked – ask to use\" (\"ask:P|Studio F\") - Book Session opens a request for it\n"
    "const askK = (String(room00).match(/^ask:([PM])\\|/) || [])[1] || '';\n"
    "const room0 = askK ? String(room00).replace(/^ask:[PM]\\|/, '') : room00;")
sub("Read Step 2", "  asked_text: s.asked || '', move_instead: '', series_alt: false, reference_data: ''\n};",
    "  asked_text: s.asked || '', move_instead: '', series_alt: false, reference_data: '',\n  request_ok: !!askK   // v37: Book Session v120 opens a request only when asked\n};")
sub("Read Step 2", "    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + roomsAll.join(' + ') + '…*\\n' + (function () {",
    "    : [{ type: 'section', text: { type: 'mrkdwn', text: (askK ? '⏳ *Sending a request for ' : '⏳ *Booking ') + roomsAll.join(' + ') + '…*\\n' + (function () {   // v37")
js = by["Read Step 2"]["parameters"]["jsCode"]
i = js.rfind("return [{ json: {")
assert i != -1 and "valid, calTitle" in js[i:i + 200], js[i:i + 120]
by["Read Step 2"]["parameters"]["jsCode"] = js[:i] + js[i:].replace("return [{ json: { valid, calTitle,", "return [{ json: { ask: askK, valid, calTitle,", 1)
assert "ask: askK, valid" in by["Read Step 2"]["parameters"]["jsCode"]

# After Book: a request was sent
sub("After Book", "if (r.status !== 'CREATED') {",
    "// v37 (slice 2): a request was opened - the form says so; the requester's card is in the DM already (Request Messages)\n"
    "if (r.status === 'PREEMPT_PENDING') {\n"
    "  const rm = String(R.rooms || R.room || '').split(',')[0].trim();\n"
    "  const txt = (r.existing ? '📨 *You already asked for ' + rm + ' then* – that request is still open.' : '📨 *Request sent – ' + rm + '.*')\n"
    "    + (r.asked ? '\\nJessie asked ' + r.asked + '.' : '') + '\\nYou’ll get the answer in your DM.';\n"
    "  return [{ json: { ok: false, req: true, view_id: R.viewId, view: { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' },\n"
    "    close: { type: 'plain_text', text: 'Done' }, blocks: [{ type: 'section', text: { type: 'mrkdwn', text: txt } }] }, channel: R.channel, text: txt, warn: '' } }];\n"
    "}\nif (r.status !== 'CREATED') {")
sub("Result DM", "if (A.ok === true) return [];", "if (A.ok === true || A.req === true) return [];   // v37: a request - its card is in the DM already")

# Move my booking: the Change form, not touching the request message
sub("Build Change", "const meta = { b, ch: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts: (p.container && p.container.message_ts) || '', requester: c.user };",
    "const meta = { b, ch: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts: (p.container && p.container.message_ts) || '', requester: c.user };\n"
    "if (((p.actions || [])[0] || {}).action_id === 'cr_move') { meta.ch = ''; meta.ts = ''; }   // v37: from a request - its message is updated by Finalize")
sub("To Move", "requester: R.u", "requester: (R.meta && R.meta.as) || R.u")   # v37: changed as its booker ("I've cleared it with them")

# ---- 3. route 16: the buttons on a request
x, y = 118208, 7300
ack16 = copy(by["Ack Keep"], "Ack Request", [x, y])
read16 = copy(SW["Read Pending Rows"], "Read Requests", [x + 240, y])
read16.update({"alwaysOutputData": True, "onError": "continueRegularOutput"})
REQUEST_ACT = r"""// Request Act (v37, slice 2): a button on a room request - is it one of the people it is for, is the request still open, and what
// to do. Answers: 0 an ending written to the row (Keep -> REJECTED, Withdraw -> WITHDRAWN) then every message updated; 1 placed
// through Finalize (Let them use it, I've cleared it with them on an M booth); 2 given up (cancelled as its booker, then
// Finalize); 3 nothing; 4 already ended - its messages redrawn.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const a = (p.actions || [])[0] || {};
let v = {}; try { v = JSON.parse(a.value || '{}'); } catch (e) { v = {}; }
// LAUNCH SWITCH: '' at launch. While testing every request message goes to Howard, so he answers for whoever it is for.
const DEV_REDIRECT = 'U08V3CKDGJF';
const row = $input.all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(v.id || ''));
if (!row) return [{ json: { go: 3, why: 'no such request' } }];
const st = String(row['Status'] || '').toUpperCase(), MB = String(row['Kind'] || '').toUpperCase() === 'MBOOTH';
const ids = { r: String(row['Requester'] || ''), a1: String(row['Approver'] || ''), a2: String(row['Approver 2'] || '') };
const names = { r: String(row['Requester Name'] || ''), a1: String(row['Approver Name'] || ''), a2: String(row['Approver 2 Name'] || '') };
const w = ['r', 'a1', 'a2'].indexOf(v.w) !== -1 ? v.w : '';
if (!w || !(c.user === ids[w] || (DEV_REDIRECT && c.user === DEV_REDIRECT))) return [{ json: { go: 3, why: 'not theirs' } }];
if (st !== 'PENDING') return [{ json: { go: 4, row, extra: { how: String(row['Resolved Via'] || '') } } }];
const now = new Date().toISOString(), by = names[w], act = a.action_id;
const end = (status, how, more) => ({ go: 0, row, upd: Object.assign({ 'Request ID': row['Request ID'], 'Status': status, 'Resolved Via': how, 'Decided At': now }, more || {}), extra: { how, by } });
if (act === 'cr_keep' && w !== 'r') return [{ json: end('REJECTED', 'kept') }];
if (act === 'cr_withdraw' && w === 'r') return [{ json: end('WITHDRAWN', 'withdrawn', { 'Withdrawn At': now }) }];
if (act === 'cr_allow' && w !== 'r' && MB) return [{ json: { go: 1, row, how: 'holder', by } }];
if (act === 'cr_attest' && w === 'r' && MB) return [{ json: { go: 1, row, how: 'attestation', by } }];
if (act === 'cr_giveup' && w !== 'r' && !MB) return [{ json: { go: 2, row, how: 'gave-up', by } }];
return [{ json: { go: 3, why: 'not for this request' } }];
"""
act16 = code("Request Act", REQUEST_ACT, [x + 480, y])
sw16 = copy(by["Route"], "Act Route", [x + 720, y], {"mode": "expression", "numberOutputs": 5, "output": "={{ $json.go }}"})
rowupd = code("Row Update", "// the row's new status - the sheet's columns only\nreturn [{ json: $('Request Act').first().json.upd }];\n", [x + 960, y - 200])
upd16 = copy(FIN["Mark Done"], "Update Request", [x + 1200, y - 200])
upd16["onError"] = "continueRegularOutput"


def reqmsgs(name, row_expr, extra_expr, pos):
    return {"parameters": {"workflowId": {"__rl": True, "mode": "id", "value": REQUEST_MESSAGES_ID, "cachedResultName": "Jessie — Request Messages"},
                           "workflowInputs": {"mappingMode": "defineBelow", "value": {"mode": "end", "row": row_expr, "extra": extra_expr},
                                              "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                           "options": {"waitForSubWorkflow": False}},
            "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": pos,
            "alwaysOutputData": True, "onError": "continueRegularOutput"}


def finalize(name, row_expr, how_expr, by_expr, pos):
    n = copy(MV["Call Finalize"], name, pos)
    n["parameters"]["workflowInputs"]["value"] = {"row": row_expr, "resolvedVia": how_expr, "attestedBy": by_expr}
    n["parameters"]["options"] = {"waitForSubWorkflow": False}
    n["onError"] = "continueRegularOutput"
    return n


endm16 = reqmsgs("End Messages", "={{ JSON.stringify(Object.assign({}, $('Request Act').first().json.row, $('Request Act').first().json.upd || {})) }}",
                 "={{ JSON.stringify($('Request Act').first().json.extra || {}) }}", [x + 1440, y - 100])
fin16 = finalize("Finalize Request", "={{ JSON.stringify($('Request Act').first().json.row) }}", "={{ $('Request Act').first().json.how }}",
                 "={{ $('Request Act').first().json.by }}", [x + 960, y])

GIVE_UP = r"""// Give Up Plan (v37): free the room - the booking cancelled as its booker (the request's authority), then Finalize places the
// requester. From the booker's / engineer's Give it up (Request Act) or the requester's "They gave it up" (Read Cleared).
// LAUNCH SWITCH: '' at launch (Howard answers for everyone while testing).
const DEV_REDIRECT = 'U08V3CKDGJF';
const c = $('Check Signature').first().json;
let RC = null; try { RC = $('Read Cleared').first().json; } catch (e) { RC = null; }
let row = null, how = 'gave-up', by = '';
if (RC) {
  row = $input.all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(RC.rid || '')) || null;
  how = 'cleared-gave-up';
  if (row && !(c.user === String(row['Requester'] || '') || (DEV_REDIRECT && c.user === DEV_REDIRECT))) row = null;
  by = row ? String(row['Requester Name'] || '') : '';
} else { const A = $('Request Act').first().json; row = A.row; by = A.by || ''; }
if (!row || String(row['Status'] || '').toUpperCase() !== 'PENDING') return [{ json: { ok: false, channel: c.channel || c.user,
  text: 'That request isn’t open any more – nothing was changed.' } }];
let M = {}; try { M = JSON.parse(row['Messages'] || '{}') || {}; } catch (e) { M = {}; }
const inc = M.inc || {};
return [{ json: { ok: true, row, how, by, channel: c.channel || c.user,
  cancel: { event_id: inc.id || String(row['Incumbent Event Id'] || ''), booking_date: inc.d || '', title: inc.t || String(row['Incumbent Title'] || ''),
    confirmed: true, requester: String(row['Approver'] || ''), requester_name: String(row['Approver Name'] || ''), authority: '', department: '',
    mode: '', check_code: '', card_time: '', card_room: '', booking_time: inc.s || '' } } }];
"""
plan16 = code("Give Up Plan", GIVE_UP, [x + 960, y + 200])
can = copy(FIN["Plan OK?"], "Can Free?", [x + 1200, y + 200])
can["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $json.ok }}"
tocan = code("To Cancel G", "// Cancel Booking's inputs (as its booker)\nreturn [{ json: $('Give Up Plan').first().json.cancel }];\n", [x + 1440, y + 200])
cang = copy(by["Cancel"], "Cancel G", [x + 1680, y + 200])
freed = copy(FIN["Plan OK?"], "Freed?", [x + 1920, y + 200])
freed["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $json.status === 'CANCELLED' }}"
fing = finalize("Finalize Given Up", "={{ JSON.stringify($('Give Up Plan').first().json.row) }}", "={{ $('Give Up Plan').first().json.how }}",
                "={{ $('Give Up Plan').first().json.by }}", [x + 2160, y + 100])
note = code("Freed Note", "// the room could not be freed (or the request had ended) - said in the DM\n"
            "let G = {}; try { G = $('Give Up Plan').first().json || {}; } catch (e) {}\n"
            "const r = $input.first().json || {};\n"
            "const text = G.ok === false ? G.text : '⚠️ Couldn’t cancel *' + ((G.cancel || {}).title || 'the booking') + '* just now – nothing was changed. Try again in a moment.';\n"
            "return [{ json: { channel: G.channel, text, blocks: [{ type: 'section', text: { type: 'mrkdwn', text } }] } }];\n", [x + 2160, y + 300])
dmnote = copy(by["DM Booked"], "DM Freed Note", [x + 2400, y + 300])
dmnote["parameters"]["jsonBody"] = "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}"

# ---- 4. route 17: "I've cleared it with them" (priority) - the small form
x2, y2 = 118208, 7900
ack17 = copy(by["Ack Keep"], "Ack Cleared", [x2, y2])
CLEARED_MODAL = r"""// Cleared Modal (v37): "I've cleared it with them" on a priority request - what did they agree to? (Howard, 21 Oct: B)
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
let v = {}; try { v = JSON.parse((((p.actions || [])[0]) || {}).value || '{}'); } catch (e) { v = {}; }
const inc = v.inc || {};
const pt = t => ({ type: 'plain_text', text: t });
const o = (t, val) => ({ text: pt(t), value: val });
const opts = [o('They’ll move it – I’ll pick where', 'move'), o('They gave it up – cancel it', 'gaveup')];
return [{ json: { trigger_id: c.triggerId, view: { type: 'modal', callback_id: 'cr_cleared', title: pt('Cleared with them'), submit: pt('Next'), close: pt('Cancel'),
  private_metadata: JSON.stringify({ rid: v.id || '', as: v.as || '', inc }).slice(0, 2900),
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'What did they agree to for *' + (inc.t || 'their booking') + '*?' } },
    { type: 'input', block_id: 'cleared', label: pt('Their booking'), element: { type: 'radio_buttons', action_id: 'cleared_pick', options: opts, initial_option: opts[0] } },
    { type: 'context', elements: [{ type: 'mrkdwn', text: 'Jessie changes or cancels it for them and tells them, then books the room for you.' }] }] } } }];
"""
modal17 = code("Cleared Modal", CLEARED_MODAL, [x2 + 240, y2])
open17 = copy(by["Open Change"], "Open Cleared", [x2 + 480, y2])

# ---- 5. route 18: the small form submitted
READ_CLEARED = r"""// Read Cleared (v37): move -> the Change form for their booking (changed as its booker); gave up -> cancelled, then the room is yours
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const V = p.view || {};
let m = {}; try { m = JSON.parse(V.private_metadata || '{}'); } catch (e) { m = {}; }
const choice = ((((V.state || {}).values || {}).cleared || {}).cleared_pick || {}).selected_option || {};
const move = choice.value !== 'gaveup';
const loading = { type: 'modal', title: { type: 'plain_text', text: 'Change booking' }, close: { type: 'plain_text', text: 'Cancel' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ Opening their booking…' } }] };
return [{ json: { move, rid: m.rid || '', as: m.as || '', inc: m.inc || {}, viewId: c.viewId,
  answer: move ? { response_action: 'update', view: loading } : { response_action: 'clear' } } }];
"""
read18 = code("Read Cleared", READ_CLEARED, [x2, y2 + 300])
ans18 = copy(by["Answer Change"], "Answer Cleared", [x2 + 240, y2 + 300])
mv18 = copy(FIN["Plan OK?"], "Cleared Move?", [x2 + 480, y2 + 300])
mv18["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $('Read Cleared').first().json.move }}"
cache18 = copy(by["Read Cache 6"], "Read Cache C", [x2 + 720, y2 + 200])
bc = by["Build Change"]["parameters"]["jsCode"]
a = "const c = $('Check Signature').first().json;\nconst p = $('Read Request').first().json.payload || {};\nlet b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }"
assert bc.count(a) == 1, "Build Change head"
bc = bc.replace(a, "const c = $('Check Signature').first().json;\nconst p = {};\nconst RC = $('Read Cleared').first().json;   // v37: their booking, from the request\nlet b = Object.assign({}, RC.inc || {});")
assert bc.count("$('Read Cache 6')") == 1
bc = bc.replace("$('Read Cache 6')", "$('Read Cache C')")
a = "if (((p.actions || [])[0] || {}).action_id === 'cr_move') { meta.ch = ''; meta.ts = ''; }   // v37: from a request - its message is updated by Finalize"
assert bc.count(a) == 1
bc = bc.replace(a, "meta.ch = ''; meta.ts = ''; meta.as = RC.as; meta.rid = RC.rid;   // v37: changed as its booker; the request's messages are updated by Finalize")
a = "return [{ json: { trigger_id: c.triggerId, view: changeView("
assert bc.count(a) == 1
bc = bc.replace(a, "return [{ json: { view_id: RC.viewId, view: changeView(")
bca = code("Build Change C", bc, [x2 + 960, y2 + 200])
show18 = copy(by["Show Result"], "Show Change C", [x2 + 1200, y2 + 200])
read18b = copy(SW["Read Pending Rows"], "Read Requests C", [x2 + 720, y2 + 400])
read18b.update({"alwaysOutputData": True, "onError": "continueRegularOutput"})

wf["nodes"] += [ack16, read16, act16, sw16, rowupd, upd16, endm16, fin16, plan16, can, tocan, cang, freed, fing, note, dmnote,
                ack17, modal17, open17, read18, ans18, mv18, cache18, bca, show18, read18b]
C["Route"]["main"][16] = [{"node": "Ack Request", "type": "main", "index": 0}]
C["Route"]["main"][17] = [{"node": "Ack Cleared", "type": "main", "index": 0}]
C["Route"]["main"][18] = [{"node": "Read Cleared", "type": "main", "index": 0}]
C["Ack Request"] = L("Read Requests"); C["Read Requests"] = L("Request Act"); C["Request Act"] = L("Act Route")
C["Act Route"] = {"main": [[{"node": "Row Update", "type": "main", "index": 0}], [{"node": "Finalize Request", "type": "main", "index": 0}],
                           [{"node": "Give Up Plan", "type": "main", "index": 0}], [], [{"node": "End Messages", "type": "main", "index": 0}]]}
C["Row Update"] = L("Update Request"); C["Update Request"] = L("End Messages")
C["Give Up Plan"] = L("Can Free?")
C["Can Free?"] = {"main": [[{"node": "To Cancel G", "type": "main", "index": 0}], [{"node": "Freed Note", "type": "main", "index": 0}]]}
C["To Cancel G"] = L("Cancel G"); C["Cancel G"] = L("Freed?")
C["Freed?"] = {"main": [[{"node": "Finalize Given Up", "type": "main", "index": 0}], [{"node": "Freed Note", "type": "main", "index": 0}]]}
C["Freed Note"] = L("DM Freed Note")
C["Ack Cleared"] = L("Cleared Modal"); C["Cleared Modal"] = L("Open Cleared")
C["Read Cleared"] = L("Answer Cleared"); C["Answer Cleared"] = L("Cleared Move?")
C["Cleared Move?"] = {"main": [[{"node": "Read Cache C", "type": "main", "index": 0}], [{"node": "Read Requests C", "type": "main", "index": 0}]]}
C["Read Cache C"] = L("Build Change C"); C["Build Change C"] = L("Show Change C")
C["Read Requests C"] = L("Give Up Plan")

wf["name"] = "Jessie — Slack Interactions — v37 (room requests)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
