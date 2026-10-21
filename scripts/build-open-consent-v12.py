#!/usr/bin/env python3
"""Builds workflows/open-consent-request-v12.json - "Jessie — Open Consent Request", v12 (requests with buttons), 21 Oct.

Slice 2 (docs/design/slice-2-approvals.md). Built on the live 29 Sep snapshot
(workflows/live/jessie-open-consent-request__nEHnCMMXS0am59Zy.json) - NOT on the unimported v11 candidate (gotcha 24).
  1. The row keeps the REAL Slack ids (Requester / Approver / Approver 2); the QA redirect moved to where the messages are
     sent (Jessie — Request Messages, every message to Howard while testing). v10 stored Howard's id in place of anyone not on
     ALLOW, so the row no longer said who had to answer.
  2. A priority request goes to the booking's booker AND engineer (PENDING 80): the engineer is read off the booking itself
     (Get Incumbent - its "Engineer:" line matched in Bookers, else its team ids) into Approver 2.
  3. Names come from Bookers (the reference cache), never blank (PENDING 78).
  4. The same requester asking again for the same room and time gets the open request back - no second row, no second set
     of messages (PENDING 27).
  5. The messages: Jessie — Request Messages (mode open) posts the requester's card and the request (buttons, not "reply
     yes"), and where each went is kept on the row (Messages) so they can be updated when it ends. "DM Incumbent" goes.
  6. Returns the request id, its deadline and who was asked, for the form's "Request sent" (Book Session v120).
The Consent Requests tab needs four more headers after Req Payload: Approver 2, Approver 2 Name, Messages, Withdrawn At.
The Request Messages workflow id is set by scripts/set-request-messages-id.py after it is imported.
"""
import json
import os
import uuid

from approvals_js import DEADLINE_JS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "live", "jessie-open-consent-request__nEHnCMMXS0am59Zy.json")
OUT = os.path.join(ROOT, "workflows", "open-consent-request-v12.json")
SI = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v36-imported.json")))["nodes"]}
FIN = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "live", "jessie-finalize-consent__TO1UnZTZ2LhtE9J3.json")))["nodes"]}
SW = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "live", "jessie-consent-sweep__QHHDevaWhMk8gSBX.json")))["nodes"]}
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
REQUEST_MESSAGES_ID = "REQUEST_MESSAGES_ID"   # scripts/set-request-messages-id.py


def copy(src, name, pos, params=None):
    n = json.loads(json.dumps(src))
    n.update({"id": str(uuid.uuid4()), "name": name, "position": pos})
    if params is not None:
        n["parameters"] = params
    return n


def code(name, js, pos, extra=None):
    n = {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}
    n.update(extra or {})
    return n


read_rows = copy(SW["Read Pending Rows"], "Read Requests", [220, 0])
read_rows.update({"alwaysOutputData": True, "onError": "continueRegularOutput"})
get_inc = copy(SI["List My Events"], "Get Incumbent", [440, 0], {
    "url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com') }}/events/"
           "{{ encodeURIComponent($('When Executed by Another Workflow').first().json.incumbentEventId || 'none') }}",
    "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}})
get_inc.update({"executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput"})
read_cache = copy(SI["Read Cache 4"], "Read Cache", [660, 0])

BUILD = r"""// Build Request (v12, slice 2): the row for a room request - real Slack ids, names from Bookers, the booking's engineer as a
// second approver (priority requests), and the same request asked again returns the open one. Deadlines as since 25 Sep.
const c = $('When Executed by Another Workflow').first().json || {};
__DEADLINE__
function readCache(rows) { let best = null;
  for (const r of rows || []) { if (!r || r.cache_key !== 'jessie-reference') continue; let d; try { d = JSON.parse(r.payload); } catch (e) { continue; }
    if (!d || !Array.isArray(d.bookers)) continue; const at = Date.parse(r.refreshed_at || '') || 0; if (!best || at > best.at) best = { at, d }; }
  return best ? best.d : null; }
const data = readCache($('Read Cache').all().map(i => i.json || {})) || { bookers: [] };
const staff = (data.bookers || []).map(b => b.fields || {}).map(f => ({ name: String(f.Name || '').trim(),
  slack: String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' })).filter(p => p.name && p.slack);
const nameOf = id => (staff.find(p => p.slack === String(id || '')) || {}).name || '';
const kind = String(c.kind || 'PREEMPT').toUpperCase() === 'MBOOTH' ? 'MBOOTH' : 'PREEMPT';
// the booking in the way, read from the calendar (its engineer, times and rooms)
let ev = {}; try { ev = $('Get Incumbent').first().json || {}; } catch (e) { ev = {}; }
if (!ev || !ev.id || ev.error) ev = {};
const desc = String(ev.description || '');
const roomName = x => String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/(?:\s*\([^)]*\))+\s*$/, '').trim();
const evRooms = (ev.attendees || []).filter(a => a.resource || /@resource\.calendar\.google\.com$/i.test(String(a.email || ''))).map(a => roomName(a.displayName)).filter(Boolean);
const mnl = x => new Date(new Date(x).getTime() + 8 * 3600000).toISOString();
const sd = ev.start && ev.start.dateTime, ed = ev.end && ev.end.dateTime;
const inc = ev.id ? { id: ev.id, d: sd ? mnl(sd).slice(0, 10) : String((ev.start && ev.start.date) || ''), s: sd ? mnl(sd).slice(11, 16) : '', e: ed ? mnl(ed).slice(11, 16) : '',
  r: (evRooms.length ? evRooms : [c.room]).join(', '), t: String(ev.summary || c.incumbentTitle || ''), st: ((desc.match(/SType:\s*([^\n|]+)/i) || [])[1] || '').trim() }
  : { id: String(c.incumbentEventId || ''), d: '', s: '', e: '', r: String(c.room || ''), t: String(c.incumbentTitle || ''), st: '' };
// PENDING 80: the booking's engineer answers too (priority requests) - its Engineer line in Bookers, else its team ids
const engName = ((desc.match(/Engineer:\s*([^(|\n]+)/) || [])[1] || '').trim().toLowerCase();
const team = ((desc.match(/team:\s*([^|\n]+)/) || [])[1] || '').split(/[\s,]+/).filter(Boolean);
let eng = (staff.find(p => p.name.toLowerCase() === engName) || {}).slack || '';
if (!eng) eng = team.find(x => x !== c.approver && x !== c.requester) || '';
const approver2 = kind === 'PREEMPT' && eng && eng !== c.approver && eng !== c.requester ? eng : '';
// PENDING 27: the same requester, room and time asked again -> the open request, not a second one
const rows = $('Read Requests').all().map(i => i.json || {}).filter(r => r['Request ID']);
const same = rows.find(r => String(r['Status'] || '').toUpperCase() === 'PENDING' && String(r['Requester'] || '') === String(c.requester || '')
  && String(r['Room/Booth'] || '') === String(c.room || '') && Date.parse(r['Req Start']) === Date.parse(c.reqStart));
const now = new Date().toISOString();
const id = now.replace(/[-:T.]/g, '').slice(0, 14) + '-' + String(c.requester || 'unknown');
const deadline = requestDeadline(kind, now, c.reqStart);
const holdName = (String(c.incumbentTitle || '').match(/^\s*M\d+\s*-\s*(.+?)\s*$/i) || [])[1] || '';
const row = {
  'Request ID': id, 'Status': 'PENDING', 'Kind': kind,
  'Requester': String(c.requester || ''), 'Requester Name': nameOf(c.requester) || String(c.requesterName || ''),
  'Approver': String(c.approver || ''), 'Approver Name': nameOf(c.approver) || String(c.approverName || '') || holdName,
  'Room/Booth': String(c.room || ''), 'Req Start': String(c.reqStart || ''), 'Req End': String(c.reqEnd || ''),
  'Incumbent Event Id': String(c.incumbentEventId || ''), 'Incumbent Title': String(c.incumbentTitle || ''),
  'Incumbent New Start': '', 'Incumbent New End': '',
  'Req Priority': (c.reqPriority == null ? '' : c.reqPriority), 'Inc Priority': (c.incPriority == null ? '' : c.incPriority),
  'Deadline': deadline, 'Requester DM': '', 'Approver DM': '', 'Log Thread TS': '', 'Resolved Via': '', 'Attested By': '', 'Decided At': '',
  'Req Payload': (c.reqPayload == null ? '' : (typeof c.reqPayload === 'string' ? c.reqPayload : JSON.stringify(c.reqPayload))),
  'Approver 2': approver2, 'Approver 2 Name': nameOf(approver2), 'Messages': JSON.stringify({ m: [], inc }), 'Withdrawn At': ''
};
const R = same || row;
const asked = kind === 'MBOOTH' ? (R['Approver Name'] || 'the holder')
  : [R['Approver Name'] ? R['Approver Name'] + ' (booker)' : '', R['Approver 2 Name'] ? R['Approver 2 Name'] + ' (engineer)' : ''].filter(Boolean).join(' and ');
return [{ json: { dup: !!same, row, existing: same || null, inc, asked } }];
""".replace("__DEADLINE__", DEADLINE_JS)

build = by["Build Request"]
build["parameters"]["jsCode"] = BUILD
build["position"] = [880, 0]
dup = copy(FIN["Plan OK?"], "Again?", [1100, 0])
dup["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $json.dup }}"
ret_ex = code("Return Existing", r"""// The same request is already open (PENDING 27) - nothing new is written or sent.
const B = $('Build Request').first().json, R = B.existing || {};
return [{ json: { status: 'PENDING', existing: true, request_id: R['Request ID'] || '', deadline: R['Deadline'] || '', asked: B.asked || '',
  message: 'You already asked for ' + (R['Room/Booth'] || 'this room') + ' then - that request is still open.' } }];
""", [1320, -200])
row_only = code("Row Only", "// the row exactly as the sheet's columns\nreturn [{ json: $('Build Request').first().json.row }];\n", [1320, 0])
write = by["Write Pending Row"]
write["position"] = [1540, 0]
post = {"parameters": {"workflowId": {"__rl": True, "mode": "id", "value": REQUEST_MESSAGES_ID, "cachedResultName": "Jessie — Request Messages"},
                       "workflowInputs": {"mappingMode": "defineBelow", "value": {
                           "mode": "open",
                           "row": "={{ JSON.stringify($('Build Request').first().json.row) }}",
                           "extra": "={{ JSON.stringify({ inc: $('Build Request').first().json.inc }) }}"},
                           "matchingColumns": [], "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                       "options": {}},
        "id": str(uuid.uuid4()), "name": "Post Messages", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2,
        "position": [1760, 0], "alwaysOutputData": True, "onError": "continueRegularOutput"}
save = code("Save Messages", r"""// where each message went - kept on the row so they can be updated when the request ends
const B = $('Build Request').first().json;
const r = $input.first().json || {};
return [{ json: { 'Request ID': B.row['Request ID'], 'Messages': JSON.stringify({ m: Array.isArray(r.messages) ? r.messages : [], inc: B.inc }) } }];
""", [1980, 0])
upd = copy(FIN["Mark Done"], "Update Row", [2200, 0])
upd["onError"] = "continueRegularOutput"
bm = by["Build Messages"]
bm["position"] = [2420, 0]
bm["parameters"]["jsCode"] = bm["parameters"]["jsCode"].replace(
    "const R = $('Build Request').first().json || {};", "const R = $('Build Request').first().json.row || {};")
assert "json.row || {}" in bm["parameters"]["jsCode"]
pa = by["Post to Approvals"]
pa["position"] = [2640, 0]
ret = by["Return"]
ret["position"] = [2860, 0]
ret["parameters"]["jsCode"] = r"""// v12: the request id, its deadline and who was asked - for the form's "Request sent" (Book Session v120)
const B = $('Build Request').first().json;
return [{ json: { status: 'PENDING', request_id: B.row['Request ID'], deadline: B.row['Deadline'], asked: B.asked || '',
  message: 'Asked ' + (B.asked || 'the holder') + ' for ' + B.row['Room/Booth'] + '.' } }];
"""
by["About"]["parameters"]["content"] = (
    "## Open Consent Request (v12, slice 2)\nWrites a PENDING row to the Consent Requests tab (real Slack ids; the booking's engineer "
    "as Approver 2 for a priority request; the same request asked again returns the open one), then Jessie — Request Messages posts "
    "the requester's card and the request with buttons, and where they went is kept on the row (Messages). An audit line still goes "
    "to #jessie-approvals. Called by Book Session (and Move Booking) at the ROOM_OCCUPIED + request point.")

wf["nodes"] = [n for n in wf["nodes"] if n["name"] != "DM Incumbent"] + [read_rows, get_inc, read_cache, dup, ret_ex, row_only, post, save, upd]
T = "When Executed by Another Workflow"
L = lambda a: {"main": [[{"node": a, "type": "main", "index": 0}]]}
wf["connections"] = {
    T: L("Read Requests"), "Read Requests": L("Get Incumbent"), "Get Incumbent": L("Read Cache"), "Read Cache": L("Build Request"),
    "Build Request": L("Again?"),
    "Again?": {"main": [[{"node": "Return Existing", "type": "main", "index": 0}], [{"node": "Row Only", "type": "main", "index": 0}]]},
    "Row Only": L("Write Pending Row"), "Write Pending Row": L("Post Messages"), "Post Messages": L("Save Messages"),
    "Save Messages": L("Update Row"), "Update Row": L("Build Messages"), "Build Messages": L("Post to Approvals"),
    "Post to Approvals": L("Return"),
}
read_cache["executeOnce"] = True
wf["name"] = "Jessie — Open Consent Request — v12 (requests with buttons)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
