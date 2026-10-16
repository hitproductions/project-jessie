#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v24.json - "Jessie — Slack Interactions", v24: round 7 of the Slack-test notes (16 Oct).

  1. Step 1 asks "What's it for?" first - it decides every other field.
  2-4. The Change form: "What's it for?" at the top (the booking's session type, read from its calendar event's "SType:" line),
     changeable; the details shown at once for that type (no "Change other session details" box); a new type redraws them.
  5-6. The fields per session type come from Airtable (Session Types: Engineer Role Required): an engineer, an arranger, or -
     where both roles apply - "Engineer and arranger: pick one or both." with both optional.
  7. Meetings, events and M booths: "Booking this for someone else?" -> anyone in Bookers; they are on the booking ("team:"),
     told about it, and the M booth title carries their name.
  8. Meetings: a Department, set to the booker's.
  9. The Note field is shown (no "Add a note" box), on Book and on Change. 10. Repeats stays behind its box.
  11. Localization: the project code is a type-to-search list from Localization Projects (Slack's Options Load URL, PENDING
     119) that also takes a new code ("Use … as a new code"); picking one shows the title, client and people under it and sets
     the Engineer from the project for the session type (Dubbing: Recordist, Editing: Editor, Mixing: Mixer; QC: anyone).
Built on workflows/imported/slack-interactions-v23-imported.json (the live download). With Move Booking v33 (Notes, SType on a
change) and main v274 (the session type on the chat's booking rows).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v23-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v24.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:90], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def prepend(node, code):
    by[node]["parameters"]["jsCode"] = code + "\n" + by[node]["parameters"]["jsCode"]


def everywhere(a, b, want=None):
    hit = 0
    for n in wf["nodes"]:
        js = n["parameters"].get("jsCode")
        if js and a in js:
            n["parameters"]["jsCode"] = js.replace(a, b); hit += 1
    assert want is None or hit == want, (a[:70], hit, want)
    return hit


def replace_fn(name, end_marker, new_text, want):
    """Replace a whole function (from 'function <name>(' up to end_marker, exclusive) in every node that has it."""
    hit = 0
    for n in wf["nodes"]:
        js = n["parameters"].get("jsCode") or ""
        i = js.find("function " + name + "(")
        if i == -1:
            continue
        j = js.find(end_marker, i)
        assert j != -1, (n["name"], name)
        n["parameters"]["jsCode"] = js[:i] + new_text + js[j:]
        hit += 1
    assert hit == want, (name, hit, want)


def add_node(name, ntype, params, pos, extra=None):
    node = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "position": pos}
    node.update(extra or {})
    wf["nodes"].append(node)
    by[name] = node
    return node


def wire(a, b, out=0):
    C.setdefault(a, {"main": []})
    while len(C[a]["main"]) <= out:
        C[a]["main"].append([])
    C[a]["main"][out] = [{"node": b, "type": "main", "index": 0}]


def insert_between(a, new, b):
    assert C[a]["main"][0][0]["node"] == b, (a, b)
    C[a]["main"][0] = [{"node": new, "type": "main", "index": 0}]
    C[new] = {"main": [[{"node": b, "type": "main", "index": 0}]]}


# ---- shared: what each session type needs; Localization Projects
TYPE_JS = r"""// v24: what each session type needs, from Airtable (Session Types: Engineer Role Required); Localization Projects
function typeKind(t) { t = String(t || '').trim(); if (!t) return ''; if (t === '__booth') return 'booth'; if (/^(meeting|event)$/i.test(t)) return 'meeting';
  if (/^(localization|qc)\b/i.test(t)) return 'loc'; if (/^post processing$/i.test(t)) return 'post'; return 'studio'; }
function typeRoles(data, t) {
  const r = ((data && data.sessionTypes) || []).find(x => String((x.fields || {}).Type || '').trim().toLowerCase() === String(t || '').trim().toLowerCase());
  const roles = r ? [].concat((r.fields || {})['Engineer Role Required'] || []).map(x => String((x && x.name) || x)).filter(Boolean) : [];
  if (!r || !roles.length) return { known: false, eng: true, arr: /music|band/i.test(String(t || '')), either: false };   // no roles in Airtable: as before
  const eng = roles.some(x => /engineer/i.test(x)), arr = roles.some(x => /arranger/i.test(x));
  return { known: true, eng, arr, either: eng && arr };
}
function sessionTypeOpts(data, group) {
  const pt = x => ({ type: 'plain_text', text: x });
  const types = ((data && data.sessionTypes) || []).map(r => String((r.fields || {}).Type || '').trim()).filter(Boolean);
  return (group === 'meeting' ? types.filter(t => /^(meeting|event)$/i.test(t)) : types.filter(t => !/^(meeting|event)$/i.test(t)).sort())
    .slice(0, 100).map(t => ({ text: pt(t), value: t }));
}
function locRows(items) { return (items || []).map(i => { const j = (i && i.json) || {}; return j.fields || j; }).filter(f => f && f['Project Code']); }
function locFind(rows, code) { const c = String(code || '').trim().toLowerCase(); return c ? rows.find(f => String(f['Project Code']).trim().toLowerCase() === c) || null : null; }
function locNames(v) { return [].concat(v || []).map(x => String((x && x.name) || x || '').trim()).filter(Boolean); }
function locRoleField(t) { return /dubbing/i.test(t) ? 'Recordist' : /editing/i.test(t) ? 'Editor' : /mixing/i.test(t) ? 'Mixer' : ''; }   // QC: anyone
function locIds(proj, t, data) {
  const f = locRoleField(t); if (!proj || !f) return [];
  const names = locNames(proj[f]).map(x => x.toLowerCase()), out = [];
  for (const b of (data && data.bookers) || []) { const g = b.fields || {}; const id = String(g['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0]; if (!id) continue;
    const full = String(g.Name || '').trim().toLowerCase(), first = full.split(/\s+/)[0];
    const alias = ((String(g.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1] || '').split(/,|\band\b/).map(x => x.trim().replace(/\.$/, '').toLowerCase()).filter(Boolean);
    const at = names.findIndex(n => n === full || n === first || alias.indexOf(n) !== -1);
    if (at !== -1) out.push({ id, at }); }
  return out.sort((x, y) => x.at - y.at).map(x => x.id);
}
function locInfo(proj, code) {
  if (!proj) return code ? 'New project code - it is booked as typed.' : '';
  const cl = proj['Client Name'] ? String((proj['Client Name'] && proj['Client Name'].name) || proj['Client Name']).trim() : '';
  const team = ['Recordist', 'Editor', 'Mixer'].map(k => k + ': ' + (locNames(proj[k]).join(', ') || '-')).join(' · ');
  return '*' + String(proj['Project Title'] || '').trim() + '*' + (cl ? ' · ' + cl : '') + '\n' + team;
}"""
for n in ["Build Step 2", "Note Toggle", "Build Change", "Read Change", "To Move", "After Move", "Read Step 2"]:
    prepend(n, TYPE_JS)

# ---- routes: the project-code search (block_suggestion) and the new redraws
patch("Check Signature", [
    ("""const ROUTES = { refused: 0, hello_open: 1, hello_submit: 2, other: 3, open_book: 4, book_step1: 5, book_step2: 6, my_bookings: 7, note_toggle: 8, bk_cancel: 9, bk_change: 10, change_booking: 11, my_page: 12, series_confirm: 13 };""",
     """const ROUTES = { refused: 0, hello_open: 1, hello_submit: 2, other: 3, open_book: 4, book_step1: 5, book_step2: 6, my_bookings: 7, note_toggle: 8, bk_cancel: 9, bk_change: 10, change_booking: 11, my_page: 12, series_confirm: 13, suggest: 14 };   // v24: suggest"""),
    ("""else if (p.type === 'block_actions' && action === 'hello_open') route = ROUTES.hello_open;""",
     """else if (p.type === 'block_suggestion') route = ROUTES.suggest;   // v24: the project-code search (Options Load URL)
else if (p.type === 'block_actions' && action === 'hello_open') route = ROUTES.hello_open;"""),
    ("""['note_toggle', 'repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio']""",
     """['note_toggle', 'repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c']"""),
])
route = by["Route"]
route["parameters"]["numberOutputs"] = 15
rx, ry = route["position"]
AIR = {"operation": "search",
       "base": {"__rl": True, "cachedResultName": "Project Jessie Knowledge Base", "mode": "list", "value": "app8GQxEInqJi1NRP"},
       "table": {"__rl": True, "cachedResultName": "Localization Projects", "mode": "list", "value": "tbljkG6z7odPUtTIf"},
       "options": {"fields": ["Project Code", "Project Title", "Client Name", "Recordist", "Editor", "Mixer", "QC"]}}
AIR_EXTRA = {"typeVersion": 2.2, "alwaysOutputData": True, "executeOnce": True, "onError": "continueRegularOutput",
             "credentials": {"airtableTokenApi": {"id": "S0hmu58Rb55jqAv0", "name": "Airtable Personal Access Token account"}}}
add_node("Loc Projects S", "n8n-nodes-base.airtable", json.loads(json.dumps(AIR)), [rx + 260, ry + 1700], AIR_EXTRA)
add_node("Suggest Codes", "n8n-nodes-base.code", {"jsCode": TYPE_JS + r"""
// Suggest Codes (v24): Slack asks for the project-code options as the person types (block_suggestion); answered from
// Localization Projects - matching codes or titles, then "Use 'X' as a new code" when nothing matches it exactly.
const p = $('Read Request').first().json.payload || {};
const q = String(p.value || '').trim(), ql = q.toLowerCase();
const rows = locRows($input.all());
const pt = x => ({ type: 'plain_text', text: String(x).slice(0, 75) });
const hits = rows.filter(f => !ql || String(f['Project Code']).toLowerCase().indexOf(ql) !== -1 || String(f['Project Title'] || '').toLowerCase().indexOf(ql) !== -1)
  .sort((a, b) => String(a['Project Code']).localeCompare(String(b['Project Code']))).slice(0, 99);
const options = hits.map(f => ({ text: pt(String(f['Project Code']).trim() + ' · ' + String(f['Project Title'] || '').trim()), value: String(f['Project Code']).trim().slice(0, 150) }));
const clean = q.replace(/[^A-Za-z0-9 _-]/g, '').trim().toUpperCase().slice(0, 60);
if (clean && !rows.some(f => String(f['Project Code']).trim().toLowerCase() === clean.toLowerCase())) options.push({ text: pt('Use “' + clean + '” as a new code'), value: 'new:' + clean });
return [{ json: { answer: { options } } }];"""}, [rx + 480, ry + 1700], {"typeVersion": 2})
add_node("Answer Suggest", "n8n-nodes-base.respondToWebhook",
         {"respondWith": "json", "responseBody": "={{ JSON.stringify($json.answer) }}", "options": {"responseCode": 200}}, [rx + 700, ry + 1700], {"typeVersion": 1.1})
wire("Route", "Loc Projects S", 14)
C["Loc Projects S"] = {"main": [[{"node": "Suggest Codes", "type": "main", "index": 0}]]}
C["Suggest Codes"] = {"main": [[{"node": "Answer Suggest", "type": "main", "index": 0}]]}
# the project list where the forms are drawn: step 2 (before Room Availability) and the redraws (before Note Toggle)
for nm_, a, b, dx in (("Loc Projects 2", "Read Cache 2", "To Room Availability", 0), ("Loc Projects 9", "Read Cache 9", "Note Toggle", 0)):
    px, py = by[b]["position"]
    add_node(nm_, "n8n-nodes-base.airtable", json.loads(json.dumps(AIR)), [px - 40, py + 180], AIR_EXTRA)
    insert_between(a, nm_, b)

# ---- 1: step 1 asks "What's it for?" first
patch("Build Step 1", [
    ("""// v21: M booth already picked (typed) -> the All day box under it""",
     """// v24: "What's it for?" first - it decides every other field
{ const B = view.blocks, pi = B.findIndex(b => b.block_id === 'purpose'); if (pi > 1) { const [pb] = B.splice(pi, 1); B.splice(1, 0, pb); } }
// v21: M booth already picked (typed) -> the All day box under it"""),
])

# ---- 5-9, 11: step 2's details, by session type, shown at once
B2 = by["Build Step 2"]["parameters"]["jsCode"]
i = B2.index("  // Engineers and arrangers come from Bookers (Info names the role)")
j = B2.index("const view = { type: 'modal', callback_id: 'book_step2'")
B2 = B2[:i] + r"""  // v24: the details each kind of booking needs, all shown at once; engineer / arranger from the session type's roles (Airtable)
  const people = (data.bookers || []).map(b => { const f = b.fields || {};
    return { name: String(f.Name || '').trim(), info: String(f.Info || ''), dept: [].concat(f.Department || []).map(x => String((x && x.name) || x)),
             slack: String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' }; }).filter(p => p.name && p.slack);
  const popt = p => ({ text: { type: 'plain_text', text: p.name }, value: p.slack });
  const iv = (el, v) => { v = String(v || '').trim().slice(0, 150); if (v) el.initial_value = v; return el; };   // v9: typed values
  const notes = input('notes', 'Note', { type: 'plain_text_input', action_id: 'notes_in', multiline: true,
    placeholder: { type: 'plain_text', text: 'Anything the session needs' } }, { optional: true });   // v24: shown, no tick box
  const RR = typeRoles(data, s.purpose);
  const engs = people.filter(p => /\bengineer\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const arrs = people.filter(p => /\barranger\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const me = engs.find(p => p.slack === s.requester), meArr = arrs.find(p => p.slack === s.requester);
  // Localization: the project's people for this session type first and preset (QC: anyone, nothing preset)
  const LOC = locRows($('Loc Projects 2').all());
  const proj = s.kind === 'loc' && pre.cd ? locFind(LOC, pre.cd) : null;
  const locFirst = s.kind === 'loc' ? locIds(proj, s.purpose, data) : [];
  const engOrder = locFirst.map(id => engs.find(p => p.slack === id)).filter(Boolean).concat(engs.filter(p => locFirst.indexOf(p.slack) === -1));
  const NONE_E = { text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }, NONE_A = { text: { type: 'plain_text', text: 'No arranger' }, value: 'none' };   // a picked dropdown cannot be emptied
  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: "Who's engineering?" }, options: (RR.either ? [NONE_E] : []).concat(engOrder.slice(0, RR.either ? 99 : 100).map(popt)) };
  const fromProj = engs.find(p => p.slack === locFirst[0]) || null, typed = engs.find(p => p.slack === pre.en) || null;
  const engDefault = typed || fromProj || ((RR.either && meArr && !me) ? null : me) || null;
  if (engDefault) engEl.initial_option = popt(engDefault);
  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'Choose' }, options: [NONE_A].concat(arrs.slice(0, 99).map(popt)) };
  const arrDefault = arrs.find(p => p.slack === pre.ar) || (meArr && !me ? meArr : null);
  if (arrDefault) arrEl.initial_option = popt(arrDefault);
  const engHint = typed ? 'As you typed it.' : fromProj ? 'From the project. Change it if someone else is engineering.'
    : engDefault && engDefault === me ? 'Set to you. Change it if someone else is engineering.' : 'Only engineers are listed (from Bookers).';
  const engineer = input('engineer', 'Engineer', engEl, Object.assign({ hint: { type: 'plain_text', text: engHint } }, RR.either ? { optional: true } : {}));
  const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, { optional: true }) : null;
  const team = [].concat(RR.either ? [{ type: 'context', block_id: 'team_note', elements: [md('Engineer and arranger: pick one or both.')] }] : [])
    .concat(RR.eng || !RR.known ? [engineer] : []).concat(RR.arr && arranger ? [arranger] : []);
  // meetings, events, M booths: who it is for (anyone in Bookers); a meeting's department, set to the booker's
  const forWho = { type: 'actions', block_id: 'forwho_toggle', elements: [{ type: 'checkboxes', action_id: 'forwho_toggle',
    options: [{ text: { type: 'plain_text', text: 'Booking this for someone else?' }, value: 'for' }] }] };
  const dOpts = [...new Set(people.reduce((acc, p) => acc.concat(p.dept), []))].filter(Boolean).sort().slice(0, 100).map(x => ({ text: { type: 'plain_text', text: x }, value: x }));
  const myDept = ((people.find(p => p.slack === s.requester) || {}).dept || [])[0];
  const dIni = dOpts.find(o => o.value === myDept);
  if (s.kind === 'meeting') {
    blocks.push(input('title', s.purpose === 'Event' ? 'Event title' : 'Meeting title', { type: 'plain_text_input', action_id: 'title_in' }));
    if (s.purpose !== 'Event' && dOpts.length) blocks.push(input('department', 'Department', Object.assign({ type: 'static_select', action_id: 'department_pick',
      placeholder: { type: 'plain_text', text: 'Choose' }, options: dOpts }, dIni ? { initial_option: dIni } : {}), { hint: { type: 'plain_text', text: dIni ? 'Set to yours. Change it if the meeting is for another team.' : 'Which team is the meeting for?' } }));
    blocks.push(forWho, notes);
  } else if (s.kind === 'booth') {
    blocks.push(forWho, notes);
  } else if (s.kind === 'post') {   // v21: Post Processing - the booker is set, a project title, no client
    blocks.push({ type: 'section', block_id: 'booker', text: md('*Booker*\n' + POST_BOOKER) },
      input('project', 'Project title', iv({ type: 'plain_text_input', action_id: 'project_in' }, pre.pj)), notes);
  } else if (s.kind === 'loc') {
    const cd = String(pre.cd || '').trim().toUpperCase();
    const codeEl = Object.assign({ type: 'external_select', action_id: 'code_pick', min_query_length: 0, placeholder: { type: 'plain_text', text: 'Type or pick a code' } },
      cd ? { initial_option: { text: { type: 'plain_text', text: (cd + (proj ? ' · ' + String(proj['Project Title'] || '').trim() : '')).slice(0, 75) }, value: (proj ? '' : 'new:') + cd.slice(0, 140) } } : {});
    blocks.push(input('code', 'Project code', codeEl, { dispatch_action: true, hint: { type: 'plain_text', text: 'Type to search Localization Projects. A new code is fine.' } }));
    if (cd) blocks.push({ type: 'context', block_id: 'code_info', elements: [md(locInfo(proj, cd))] });
    blocks.push(engineer, notes);
  } else {
    blocks.push(input('project', 'Project', iv({ type: 'plain_text_input', action_id: 'project_in' }, pre.pj)),
      input('client', 'Client', iv({ type: 'plain_text_input', action_id: 'client_in' }, pre.c),
        { optional: true, hint: { type: 'plain_text', text: "Leave empty if there's no client. A new name is fine." } }), ...team, notes);
  }
}
""" + B2[j:]
by["Build Step 2"]["parameters"]["jsCode"] = B2

# ---- step 2's answers: the code from the search list, the roles' rule, who it is for
patch("Read Step 2", [
    ("""const code = String(val('code', 'code_in')).trim();""",
     """const code = String(val('code', 'code_pick') || val('code', 'code_in')).replace(/^new:/, '').trim().toUpperCase();   // v24: the search list (or a new code)
const forId = val('forwho', 'forwho_pick');   // v24: a meeting / event / M booth booked for someone else"""),
    ("""if (s.kind === 'loc' && !code) errors.code = 'Type the project code.';""",
     """if (s.kind === 'loc' && !code) errors.code = 'Pick or type the project code.';"""),
    ("""if ((s.kind === 'studio' || s.kind === 'loc') && !engineerId && !(engPick === 'none' && arrangerId))
  errors.engineer = engPick === 'none' ? 'Pick an engineer or an arranger.' : 'Pick the engineer.';   // v22: never neither""",
     """// v24: who must be named comes from the session type's roles (below, once the reference data is read)"""),
    ("""const first = id => nm(id).split(/\\s+/)[0] || '';""",
     """const first = id => nm(id).split(/\\s+/)[0] || '';
{ const RR = typeRoles(data, s.purpose);   // v24: an engineer, an arranger, or (both roles) one or both
  if (s.kind === 'studio' || s.kind === 'loc') {
    if (RR.either) { if (!engineerId && !arrangerId) errors.engineer = 'Pick an engineer or an arranger.'; }
    else if ((RR.eng || !RR.known) && !engineerId) errors.engineer = 'Pick the engineer.'; } }"""),
    ("""else if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + first(s.requester);""",
     """else if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + first(forId || s.requester);   // v24: the person it is for"""),
    ("""  engineerId ? 'engineer ' + nm(engineerId) : (engPick === 'none' ? 'no engineer' : ''),   // v22: Book Session does not ask""",
     """  engineerId ? 'engineer ' + nm(engineerId) : (engPick === 'none' || arrangerId ? 'no engineer' : ''),   // v22 / v24: Book Session does not ask"""),
    ("""const team = s.kind === 'post' ? '' : [engineerId, arrangerId].filter(Boolean).join(' ');   // v21: no notice for Post Processing's booker""",
     """const team = s.kind === 'post' ? '' : [engineerId, arrangerId, forId].filter((x, k, a) => x && a.indexOf(x) === k).join(' ');   // v21; v24: + who it is for"""),
    ("""  'Booked by: ' + (req.Name || ''), 'ref: ' + s.requester,""",
     """  'Booked by: ' + (req.Name || '') + (forId && nm(forId) ? ' (for ' + nm(forId) + ')' : ''), 'ref: ' + s.requester,"""),   # v24: (for …)
    ("""return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId,""",
     """return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId, forId,"""),
])

# ---- 7: the person it is booked for is told
patch("Booked Notices", [
    ("""'👋 *' + actorName + ' ' + x.verb + ' you as the ' + x.role + (x.extra || '') + '.*\\n\\n' + body;""",
     """'👋 *' + actorName + ' ' + (x.line || (x.verb + ' you as the ' + x.role + (x.extra || ''))) + '.*\\n\\n' + body;   // v24: x.line"""),
    ("""                { id: R.arrangerId, role: 'arranger', verb: 'booked', name: whoIs(data, R.arrangerId) }], me,""",
     """                { id: R.arrangerId, role: 'arranger', verb: 'booked', name: whoIs(data, R.arrangerId) },
                { id: R.forId, line: 'booked this for you', name: whoIs(data, R.forId) }], me,"""),   # v24
])

# ---- the booking carries its session type (the event's "SType:" line) on every row's buttons
everywhere("""function evBooking(e) {""", """function evType(e) { return ((String(e.description || '').match(/\\n\\s*SType:\\s*([^\\n]+)/) || [])[1] || '').trim(); }   // v24
function evBooking(e) {""")
n_ev = everywhere("""r: evRoom(e), t: e.summary || '(no title)' };""", """r: evRoom(e), t: e.summary || '(no title)', st: evType(e) };""")
assert n_ev >= 10, n_ev
everywhere("""function bkValue(b) { return JSON.stringify({ id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150) }); }""",
           """function bkValue(b) { return JSON.stringify({ id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150), st: b.st || '' }); }   // v24: st""", 13)
patch("After Book", [
    ("""  r: F['Room'] || R.rooms || R.room || '', t: title };""",
     """  r: F['Room'] || R.rooms || R.room || '', t: title, st: (R.s && R.s.kind !== 'booth' ? R.s.purpose : '') || '' };   // v24: st"""),
])

# ---- 2-4, 9: the Change form - What's it for? at the top, the details for that type shown at once
everywhere("""  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' }""",
           """  // v24: "What's it for?" first - the booking's session type (its event's SType line), changeable; the details below follow it
  if (det && det.data && parseTitle(b).kind !== 'booth') { const grp = parseTitle(b).kind === 'meeting' ? 'meeting' : 'session';
    const tOpts = sessionTypeOpts(det.data, grp), tNow = String((det.vals && det.vals.st) || b.st || ''), tIni = tOpts.find(o => o.value === tNow);
    if (tOpts.length) blocks.push({ type: 'input', block_id: 'purpose_c', dispatch_action: true, optional: !tIni, label: pt("What's it for?"),
      element: Object.assign({ type: 'static_select', action_id: 'purpose_c', placeholder: pt('Choose'), options: tOpts }, tIni ? { initial_option: tIni } : {}),
      hint: pt(tIni ? 'Change it and the details below follow.' : 'Leave it empty to keep the session as it is.') }); }
  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' }""", 5)
everywhere("""  if (det && det.open) { tog.elements[0].initial_options = tog.elements[0].options; blocks.push(tog, ...detBlocks(b, det.data, det.vals)); }
  else blocks.push(tog);""",
           """  // v24: the details shown at once (no tick box)
  if (det && det.data) blocks.push({ type: 'divider', block_id: 'det_anchor' }, ...detBlocks(b, det.data, det.vals));
  else blocks.push(tog);""", 5)
DET = r"""function detBlocks(b, data, vals) {   // v24: the fields of the booking's session type (or the type picked on the form)
  const pt = x => ({ type: 'plain_text', text: x });
  const O = detOrig(b, data), V = Object.assign({}, O, vals || {}), st = staffOf(data);
  const T = String((vals && vals.st) || b.st || ''), K = typeKind(T) || O.kind;
  const R = T ? typeRoles(data, T) : { known: false, eng: K !== 'meeting', arr: K === 'studio' && !!O.ai, either: false };
  const iv = (el, v) => { v = String(v || '').trim().slice(0, 150); if (v) el.initial_value = v; return el; };
  const inp = (bid, label, el, opt) => Object.assign({ type: 'input', block_id: bid, label: pt(label), element: el }, opt ? { optional: true } : {});
  const popt = x => ({ text: pt(x.name), value: x.slack });
  const engs = (R.either ? [{ text: pt('No engineer'), value: 'none' }] : []).concat(st.filter(x => /\bengineer\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, R.either ? 99 : 100).map(popt));
  const arrs = [{ text: pt('No arranger'), value: 'none' }].concat(st.filter(x => /\barranger\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 99).map(popt));   // a picked dropdown cannot be emptied
  const sel = (aid, opts, val, ph) => { const o = opts.find(x => x.value === val); return Object.assign({ type: 'static_select', action_id: aid, placeholder: pt(ph || 'Choose'), options: opts }, o ? { initial_option: o } : {}); };
  const notes = inp('det_notes', 'Note', { type: 'plain_text_input', action_id: 'det_notes_in', multiline: true, placeholder: pt('Leave empty to keep the current note') }, true);
  if (K === 'booth') return [{ type: 'context', block_id: 'det_none', elements: [{ type: 'mrkdwn', text: 'An M booth booking has no other details to change.' }] }];
  if (K === 'meeting') return [inp('det_title', T === 'Event' ? 'Event title' : 'Meeting title', iv({ type: 'plain_text_input', action_id: 'det_title_in' }, V.title)), notes];
  if (K === 'loc') { const code = String(V.code || '').trim();
    return [Object.assign(inp('det_code', 'Project code', Object.assign({ type: 'external_select', action_id: 'code_pick', min_query_length: 0, placeholder: pt('Type or pick a code') },
        code ? { initial_option: { text: pt(code.slice(0, 75)), value: code.slice(0, 150) } } : {})), { dispatch_action: true }),
      inp('det_engineer', 'Engineer', sel('det_engineer_pick', engs, V.en, "Who's engineering?")), notes]; }
  if (K === 'post') return [inp('det_project', 'Project title', iv({ type: 'plain_text_input', action_id: 'det_project_in' }, V.project)),
    { type: 'context', block_id: 'det_booker', elements: [{ type: 'mrkdwn', text: 'Booker: Dylan Diaz' }] }, notes];
  const out = [inp('det_project', 'Project', iv({ type: 'plain_text_input', action_id: 'det_project_in' }, V.project)),
    inp('det_client', 'Client', iv({ type: 'plain_text_input', action_id: 'det_client_in' }, V.client), true)];
  if (R.either) out.push({ type: 'context', block_id: 'team_note', elements: [{ type: 'mrkdwn', text: 'Engineer and arranger: pick one or both.' }] });
  if (R.eng || !R.known) out.push(inp('det_engineer', 'Engineer', sel('det_engineer_pick', engs, V.en, "Who's engineering?"), R.either));
  if (R.arr) out.push(inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar), true));
  out.push(notes);
  return out;
}
"""
replace_fn("detBlocks", "// the new title from the details", DET, 5)
TITLE = r"""function detTitle(b, data, d, room) {   // v24: the title follows the session type picked on the form (its kind decides the shape)
  d = d || {};
  const O = detOrig(b, data), st = staffOf(data), ini = id => { const x = st.find(y => y.slack === id); return x ? x.ini : ''; };
  const K = typeKind(d.st || '') || O.kind;
  if (K === 'booth' || O.kind === 'booth') return b.t;
  if (K === 'meeting') return String(room || O.prefix || b.r || '').toUpperCase() + ' - ' + String(d.title != null ? d.title : (O.title || O.project || '')).trim();
  const ok = x => x && x !== 'none';
  const ei = d.teamShown ? (ok(d.en) ? ini(d.en) : '') : (ok(d.en) ? ini(d.en) : (d.en === 'none' ? '' : O.ei));
  const ai = d.teamShown ? (ok(d.ar) ? ini(d.ar) : '') : (ok(d.ar) ? ini(d.ar) : (d.ar === 'none' ? '' : O.ai));
  const inits = [ei, ai].filter(Boolean).join(' x ');
  if (K === 'loc') return [String(d.code ? d.code : (O.code || '')).trim(), inits].filter(Boolean).join(' / ');
  return [String(d.project != null && d.project !== '' ? d.project : (O.project || O.code || '')).trim().replace(/^(?:project|proj)\s+/i, '').toUpperCase(),
          K === 'post' ? '' : String(d.client != null ? d.client : (O.client || '')).trim(), K === 'post' ? (O.ei || ei) : inits].filter(Boolean).join(' / ');
}
"""
replace_fn("detTitle", "// v19: a room as the calendar", TITLE, 5)
patch("Build Change", [
    ("""view: changeView(b, cur, '', meta, roomLists(data)) } }];""",
     """view: changeView(b, cur, '', meta, roomLists(data), { data: data || { bookers: [], sessionTypes: [], rooms: [] } }) } }];   // v24: the details shown at once"""),
])
patch("After Move", [
    ("""changeView(b, n, why, R.meta || {}, roomLists(data), R.d ? { data, vals: R.d, open: true } : null)""",
     """changeView(b, n, why, R.meta || {}, roomLists(data), { data: data || { bookers: [], sessionTypes: [], rooms: [] }, vals: R.d || undefined, open: true })"""),
])
patch("Read Change", [
    ("""const open = Object.keys(v).some(k => /^det_(?:project|client|code|title|engineer|arranger)$/.test(k));""",
     """const open = Object.keys(v).some(k => /^det_(?:project|client|code|title|engineer|arranger|notes)$/.test(k) || k === 'purpose_c');   // v24"""),
    ("""code: txt('det_code', 'det_code_in'),""",
     """code: (sel('det_code', 'code_pick') || txt('det_code', 'det_code_in')).replace(/^new:/, '').trim().toUpperCase(),"""),
    ("""  d.client = capWords(d.client);   // v19
  if (O.kind === 'studio' && !d.project) errors.det_project = 'What is the project called?';
  if (O.kind === 'loc' && !d.code) errors.det_code = 'Type the project code.';
  if (O.kind === 'meeting' && !d.title) errors.det_title = 'Give the meeting a title.';
  if ((O.kind === 'studio' || O.kind === 'loc') && !d.en) errors.det_engineer = 'Pick the engineer.';
  if (d.en === 'none' && !(d.ar && d.ar !== 'none')) errors.det_engineer = 'Pick an engineer or an arranger.';   // v22""",
     """  d.client = capWords(d.client);   // v19
  // v24: the session type picked on the form (else the booking's), its kind and roles decide what is required
  d.st = sel('purpose_c', 'purpose_c') || ''; d.notes = txt('det_notes', 'det_notes_in'); d.teamShown = !!(v.det_engineer || v.det_arranger);
  const T = d.st || b.st || '', KD = typeKind(T) || O.kind, RD = T ? typeRoles(data, T) : { known: false, eng: true, either: false };
  const has = x => x && x !== 'none';
  if ((KD === 'studio' || KD === 'post') && v.det_project && !d.project) errors.det_project = 'What is the project called?';
  if (KD === 'loc' && v.det_code && !d.code) errors.det_code = 'Pick or type the project code.';
  if (KD === 'meeting' && v.det_title && !d.title) errors.det_title = 'Give it a title.';
  if (KD === 'studio' || KD === 'loc') {
    if (RD.either) { if (!has(d.en) && !has(d.ar)) errors[v.det_engineer ? 'det_engineer' : 'det_arranger'] = 'Pick an engineer or an arranger.'; }
    else if (v.det_engineer && !has(d.en)) errors.det_engineer = 'Pick the engineer.'; }"""),
    ("""const teamChanged = !!d && (O.kind === 'studio' || O.kind === 'loc') && (d.en !== O.en || (O.kind === 'studio' && d.ar !== O.ar));""",
     """const _n = x => (x && x !== 'none') ? x : '';
const teamChanged = !!d && d.teamShown && (_n(d.en) !== _n(O.en) || _n(d.ar) !== _n(O.ar));   // v24: the fields shown decide it"""),
    ("""const newDetails = teamChanged ? {""", """const newDetails0 = teamChanged ? {"""),
    ("""const clientTyped =""",
     """// v24: a new session type and a new note travel with the change (Move Booking v33 rewrites those lines)
const stChanged = !!(d && d.st && d.st !== (b.st || ''));
const extra = Object.assign({}, stChanged ? { SType: d.st } : {}, d && d.notes ? { Notes: d.notes.replace(/\\|/g, '/') } : {});
const newDetails = (newDetails0 || Object.keys(extra).length) ? Object.assign({}, newDetails0 || {}, extra) : null;
const clientTyped ="""),
])

# ---- the redraws: a project picked, "for someone else", a new session type on the Change form; external lists keep their pick
patch("Note Toggle", [
    ("""const WH = ['repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio'];   // v21""",
     """const WH = ['repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c'];   // v21; v24"""),
    ("""  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? ['room_other'] : ['notes'];""",
     """  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? ['room_other']
  : which === 'code_pick' ? ['code_info'] : which === 'forwho_toggle' ? (on ? [] : ['forwho'])
  : which === 'purpose_c' ? ['team_note', 'det_project', 'det_client', 'det_code', 'code_info', 'det_title', 'det_engineer', 'det_arranger', 'det_none', 'det_notes', 'det_booker']
  : ['notes'];   // v24"""),
    ("""  else if (e.type === 'static_select' || e.type === 'radio_buttons') {""",
     """  else if (e.type === 'external_select') { if (sv.selected_option) e.initial_option = sv.selected_option; }   // v24: a searched list keeps its pick
  else if (e.type === 'static_select' || e.type === 'radio_buttons') {"""),
    ("""const at = blocks.findIndex(b => b.block_id === ({ purpose_pick: 'purpose', room_radio: 'room' }[which] || which));""",
     """const atId = which === 'code_pick' ? (blocks.some(b => b.block_id === 'code') ? 'code' : 'det_code') : ({ purpose_pick: 'purpose', room_radio: 'room' }[which] || which);   // v24
const at = blocks.findIndex(b => b.block_id === atId);"""),
    ("""  if (on && which === 'repeat_toggle') {""",
     """  // v24: a project code picked - its title, client and people under it; the engineer from the project for this session type
  if (which === 'code_pick') {
    const pv = String((a.selected_option || {}).value || ''), code = pv.replace(/^new:/, '');
    const proj = pv.indexOf('new:') === 0 ? null : locFind(locRows($('Loc Projects 9').all()), code);
    const typeNow = M2.purpose || (((st.purpose_c || {}).purpose_c || {}).selected_option || {}).value
      || (((blocks.find(b => b.block_id === 'purpose_c') || {}).element || {}).initial_option || {}).value || ((M2.b || {}).st) || '';
    if (code) blocks.splice(at + 1, 0, { type: 'context', block_id: 'code_info', elements: [{ type: 'mrkdwn', text: locInfo(proj, code) }] });
    const eb = blocks.find(b => b.block_id === 'engineer' || b.block_id === 'det_engineer');
    const ids = locIds(proj, typeNow, readCache($('Read Cache 9').all().map(i => i.json || {})));
    if (eb && eb.element && ids.length) { const opts = eb.element.options || [], first = ids.map(id => opts.find(o => o.value === id)).filter(Boolean);
      if (first.length) { eb.element.options = first.concat(opts.filter(o => first.indexOf(o) === -1)); eb.element.initial_option = first[0];
        eb.hint = pt('From the project. Change it if someone else is engineering.'); } }
  }
  // v24: "Booking this for someone else?" - anyone in Bookers
  if (on && which === 'forwho_toggle') { const ppl = staffOf(readCache($('Read Cache 9').all().map(i => i.json || {})) || { bookers: [] }).sort((x, y) => x.name.localeCompare(y.name));
    blocks.splice(at + 1, 0, { type: 'input', block_id: 'forwho', label: pt('Who is it for?'),
      element: { type: 'static_select', action_id: 'forwho_pick', placeholder: pt('Choose a person'), options: ppl.slice(0, 100).map(x => ({ text: pt(x.name), value: x.slack })) } }); }
  // v24: a new session type on the Change form - its details, with what was typed kept
  if (which === 'purpose_c') {
    const D9 = readCache($('Read Cache 9').all().map(i => i.json || {})) || { bookers: [], sessionTypes: [], rooms: [] };
    const sv2 = (bl, ac) => String((((st[bl] || {})[ac]) || {}).value || '').trim();
    const keep = { st: String((a.selected_option || {}).value || ''), project: sv2('det_project', 'det_project_in'), client: sv2('det_client', 'det_client_in'), title: sv2('det_title', 'det_title_in') };
    Object.keys(keep).forEach(k => { if (!keep[k]) delete keep[k]; });
    const ai = blocks.findIndex(b => b.block_id === 'det_anchor');
    blocks.splice(ai === -1 ? blocks.length : ai + 1, 0, ...detBlocks(M2.b || {}, D9, keep));
  }
  if (on && which === 'repeat_toggle') {"""),
])

wf["name"] = "Jessie — Slack Interactions — v24 (round 7: fields by session type)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes; evBooking rows", n_ev)
