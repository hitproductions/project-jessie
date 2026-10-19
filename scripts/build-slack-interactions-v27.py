#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v27.json - "Jessie — Slack Interactions", v27 (round 10: questions after Book reach the DM).

Found 19 Oct 16:07 (Tara, Celebrity Recording, execution 50920): Book pressed -> "You can close this window" -> she closed it ->
Book Session asked "Is this a Music or an Audio Post session?" (NEED_DEPARTMENT) -> Show Question's views.update answered
`not_found` (the window was gone) -> nothing reached her. Any question or problem after Book was lost the same way.

  1. Step 2 asks the Department up front when the booking type's roles span departments (Airtable Engineer Role Required:
     Post Engineer -> Audio Post, Loc Engineer -> Localization, Music Engineer / Arranger -> Music) - Celebrity Recording, Van
     Recording, Atmos Mixing once it has several - set to the booker's own department when it is one of them. Book Session
     then never has to ask it.
  2. When the window is gone (views.update not ok), the question or problem goes to the DM: "Not booked yet: …" with a Book a
     room button that opens the form filled in (date, times, type, room, project, client, code, engineer, arranger). The same
     for a series (its problem, or the dates checked but never confirmed) and for Change ("Not changed: …").
  3. The working lines say where the answer goes: "You can close this window – we’ll let you know in your DM once it’s done."
Built on workflows/imported/slack-interactions-v26-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v26-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v27.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def everywhere(a, b, want=None):
    hit = 0
    for n in wf["nodes"]:
        js = n["parameters"].get("jsCode")
        if js and a in js:
            n["parameters"]["jsCode"] = js.replace(a, b)
            hit += 1
    assert want is None or hit == want, (a[:80], hit, want)
    return hit


def add_node(name, ntype, ver, params, pos, extra=None):
    node = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    node.update(extra or {})
    wf["nodes"].append(node)
    by[name] = node
    return node


def add_out(a, b, out=0):
    C.setdefault(a, {"main": []})
    while len(C[a]["main"]) <= out:
        C[a]["main"].append([])
    C[a]["main"][out].append({"node": b, "type": "main", "index": 0})


# ---- 1: the department up front ----------------------------------------------------------------------------------------
patch("Build Step 2", [
    ("  if (s.kind === 'meeting') {\n    blocks.push(input('title',",
     "  // v27: a booking type whose roles span departments (Celebrity Recording: Music or Audio Post) - asked here, set to the\n"
     "  // booker's own when it is one of them, so Book Session never has to ask after Book (Tara, 19 Oct 16:07: the window was gone)\n"
     "  const _DMAP = { 'post engineer': 'Audio Post', 'loc engineer': 'Localization', 'music engineer': 'Music', 'music arranger': 'Music' };\n"
     "  const typeDepts = [...new Set([].concat(((ST || {}).fields || {})['Engineer Role Required'] || []).map(x => _DMAP[String((x && x.name) || x).trim().toLowerCase()]).filter(Boolean))];\n"
     "  const deptAsk = (s.kind === 'studio' || s.kind === 'atmos') && typeDepts.length > 1;\n"
     "  const tdOpts = typeDepts.map(x => ({ text: { type: 'plain_text', text: x }, value: x })), tdIni = tdOpts.find(o => o.value === myDept);\n"
     "  const deptBlock = deptAsk ? [input('department', 'Department', Object.assign({ type: 'static_select', action_id: 'department_pick',\n"
     "    placeholder: { type: 'plain_text', text: 'Select a department' }, options: tdOpts }, tdIni ? { initial_option: tdIni } : {}))] : [];\n"
     "  if (s.kind === 'meeting') {\n    blocks.push(input('title',"),
    ("    blocks.push(input('project', 'Project title or code', txtIn('project_in', pre.pj || pre.cd)), engineer, notes);",
     "    blocks.push(input('project', 'Project title or code', txtIn('project_in', pre.pj || pre.cd)), ...deptBlock, engineer, notes);"),
    ("      input('client', 'Client', txtIn('client_in', pre.c), { optional: true }), ...team, notes);",
     "      input('client', 'Client', txtIn('client_in', pre.c), { optional: true }), ...deptBlock, ...team, notes);"),
])

# ---- 2: what the DM needs ----------------------------------------------------------------------------------------------
patch("Read Step 2", [("return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId, forId, forName,",
                       "// v27: the form's answers, for a \"Book a room\" button that opens it filled in again (a DM when the window is gone)\n"
                       "const again = { d: s.date, s: s.allDay ? '' : s.t0, e: s.allDay ? '' : s.t1, p: s.kind === 'booth' ? '__booth' : s.purpose, r: room,\n"
                       "  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId };\n"
                       "Object.keys(again).forEach(k => { if (!again[k]) delete again[k]; });\n"
                       "return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId, forId, forName, again,")])
patch("After Prepare", [("return [{ json: { go: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), reason: r.reason || r.status || '' } }];",
                         "return [{ json: { go: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), reason: r.reason || r.status || '', warn: pr.warn } }];   // v27: warn, for the DM")])
patch("After Book", [("return [{ json: { ok: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), channel: R.channel, text: '' } }];",
                      "return [{ json: { ok: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), channel: R.channel, text: '', warn: pr.warn } }];   // v27: warn")])
patch("After Prepare Series", [("return [{ json: { view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked) } }];",
                                "return [{ json: { view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), warn: pr.warn } }];   // v27: warn")])
patch("After Move", [("return [{ json: { ok: false, view_id: R.viewId, view: changeView(b, n, why,",
                      "return [{ json: { ok: false, why, view_id: R.viewId, view: changeView(b, n, why,")])

DM_HEAD = r"""// v27 (round 10): the window was gone when this answer came back (views.update not ok - closed, as the form invites), so it
// goes to the DM instead - with a "Book a room" button that opens the form filled in again. Nothing to send -> no item.
const shown = $input.first().json || {};
if (shown.ok !== false) return [];
const md = t => ({ type: 'mrkdwn', text: t });
const again = (R) => { const v = JSON.stringify((R && R.again) || {}); return v.length <= 1900 ? v : '{}'; };
const bookBtn = (R) => ({ type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: 'open_book', value: again(R), text: { type: 'plain_text', text: 'Book a room' } },
  { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] });
const plain = t => String(t || '').replace(/\*/g, '');
"""
QUESTION_JS = DM_HEAD + r"""
const R = $('Read Step 2').first().json || {}, A = $('After Prepare').first().json || {};
const warn = String(A.warn || 'Something needs an answer before this can be booked.');
return [{ json: { channel: R.channel, text: 'Not booked yet: ' + plain(warn), blocks: [{ type: 'section', text: md('⚠️ *Not booked yet.* ' + warn) }, bookBtn(R)] } }];"""
RESULT_JS = DM_HEAD + r"""
let A = {}; try { A = $('After Book').first().json || {}; } catch (e) { A = {}; }
if (A.ok === true) return [];   // booked - the Booked card is DM'd already (DM Booked)
const R = $('Read Step 2').first().json || {};
const warn = String(A.warn || 'It couldn’t be booked just now.');
return [{ json: { channel: R.channel, text: 'Not booked: ' + plain(warn), blocks: [{ type: 'section', text: md('⚠️ *Not booked.* ' + warn) }, bookBtn(R)] } }];"""
SERIES_JS = DM_HEAD + r"""
const R = $('Read Step 2').first().json || {}, A = $('After Prepare Series').first().json || {};
const n = (((R.s || {}).series || {}).dates || []).length;
const text = A.warn ? '⚠️ *Not booked yet.* ' + A.warn
  : '⚠️ *Not booked yet.* Your ' + (n || 'repeating') + ' dates were checked, but the window was closed before you confirmed them. Press *Book a room* to go through it again.';
return [{ json: { channel: R.channel, text: plain(text), blocks: [{ type: 'section', text: md(text) }, bookBtn(R)] } }];"""
CHANGE_JS = DM_HEAD + r"""
const A = $('After Move').first().json || {};
if (A.ok === true) return [];   // changed - the Changed card is DM'd already (DM Changed)
const R = $('Read Change').first().json || {};
const t = String(((R.b || {}).t) || 'the booking');
const why = String(A.why || 'It couldn’t be changed just now.');
return [{ json: { channel: R.user, text: 'Not changed: ' + plain(why), blocks: [{ type: 'section', text: md('⚠️ *' + t + '* was not changed. ' + why) }] } }];"""

dm = json.loads(json.dumps(by["DM Booked"]))
dm.update({"id": str(uuid.uuid4()), "name": "DM Not Shown", "position": [by["DM Booked"]["position"][0], by["DM Booked"]["position"][1] + 520]})
dm["parameters"]["jsonBody"] = "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}"
dm["onError"] = "continueRegularOutput"
wf["nodes"].append(dm); by["DM Not Shown"] = dm
C.pop("DM Not Shown", None)
for name, js, src in [("Question DM", QUESTION_JS, "Show Question"), ("Result DM", RESULT_JS, "Show Result"),
                      ("Series DM", SERIES_JS, "Show Series Step"), ("Change DM", CHANGE_JS, "Show Change Result")]:
    x, y = by[src]["position"]
    add_node(name, "n8n-nodes-base.code", 2, {"jsCode": js}, [x + 160, y + 120], {"onError": "continueRegularOutput"})
    add_out(src, name)
    add_out(name, "DM Not Shown")

# ---- 3: the working lines say where the answer goes --------------------------------------------------------------------
everywhere("You can close this window – we’ll let you know once it’s done.", "You can close this window – we’ll let you know in your DM once it’s done.", want=3)
patch("Read Step 2", [("{ type: 'context', elements: [{ type: 'mrkdwn', text: 'Checking availability for each date.' }] }",
                       "{ type: 'context', elements: [{ type: 'mrkdwn', text: 'Checking availability for each date. You can close this window – we’ll let you know in your DM.' }] }")])

wf["name"] = "Jessie — Slack Interactions — v27 (questions reach the DM)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
