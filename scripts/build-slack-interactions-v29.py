#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v29.json - "Jessie — Slack Interactions", v29 (faster redraws + clean-up), round 11 (20 Oct).

  1. The Localization Projects table (Airtable) is read only when it is used: Find rooms reads it for a Localization booking
     only (was every booking - Loc Projects 2), and a redraw only for a typed project code (was every redraw - Loc Projects 9:
     every room tick since v25, Repeats, What's it for?).
  2. A room ticked with nothing to clear or follow (no other room picked, no booth on the form) is not redrawn at all.
  3. Department (round 11 note 1, Howard 19 Oct): no Department field (v27) - for a booking type whose roles span
     departments, Read Step 2 takes it from the people picked: an arranger -> Music; else the engineer's role in Bookers Info
     (Post Engineer -> Audio Post, Music Engineer -> Music, Loc Engineer -> Localization); an engineer with several roles, or
     nobody -> the booker's own department if it is one of the type's, else the type's first. Book Session never asks.
  4. Dead code out: the project-code search route (Loc Projects S -> Suggest Codes -> Answer Suggest, unused since v25's text
     box); a block_suggestion now goes to "other".
  5. A refused request DMs the tester only when it looked like Slack's (it carried a timestamp); an unsigned probe (curl, a link
     preview - 19 Oct 16:03) is refused quietly.
Built on workflows/imported/slack-interactions-v28-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v28-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v29.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def wire(a, b, out=0):
    C.setdefault(a, {"main": []})
    while len(C[a]["main"]) <= out:
        C[a]["main"].append([])
    C[a]["main"][out] = [{"node": b, "type": "main", "index": 0}]


def if_node(name, expr, pos):
    # the same shape as the 14 IF nodes already live (typeVersion 2.2, conditions version 2)
    node = {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                          "combinator": "and",
                                          "conditions": [{"id": str(uuid.uuid4()), "leftValue": expr, "rightValue": True,
                                                          "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]},
                           "options": {}},
            "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": pos}
    wf["nodes"].append(node)
    by[name] = node
    return node


def remove_node(name):
    wf["nodes"].remove(by.pop(name))
    C.pop(name, None)
    for src in C.values():
        for outs in src.get("main", []):
            if outs:
                outs[:] = [c for c in outs if c["node"] != name]


# ---- 1: Localization Projects only when used ---------------------------------------------------------------------------
assert C["Read Cache 2"]["main"][0][0]["node"] == "Loc Projects 2" and C["Loc Projects 2"]["main"][0][0]["node"] == "To Room Availability"
x, y = by["Loc Projects 2"]["position"]
if_node("Loc Needed?", "={{ (($('Read Step 1').first().json || {}).s || {}).kind === 'loc' }}", [x - 40, y + 140])
wire("Read Cache 2", "Loc Needed?")
wire("Loc Needed?", "Loc Projects 2", 0)
wire("Loc Needed?", "To Room Availability", 1)
patch("Build Step 2", [("  const LOC = locRows($('Loc Projects 2').all());",
                        "  let LOC = []; try { LOC = locRows($('Loc Projects 2').all()); } catch (e) { LOC = []; }   // v29: read for Localization only")])

assert C["Read Cache 9"]["main"][0][0]["node"] == "Loc Projects 9" and C["Loc Projects 9"]["main"][0][0]["node"] == "Note Toggle"
x, y = by["Loc Projects 9"]["position"]
if_node("Code Typed?", "={{ ['code_in', 'det_code_in', 'code_pick'].indexOf(String((((($('Read Request').first().json || {}).payload || {}).actions || [])[0] || {}).action_id || '')) !== -1 }}",
        [x - 40, y + 140])
wire("Read Cache 9", "Code Typed?")
wire("Code Typed?", "Loc Projects 9", 0)
wire("Code Typed?", "Note Toggle", 1)
patch("Note Toggle", [("    const proj = pv.indexOf('new:') === 0 ? null : locFind(locRows($('Loc Projects 9').all()), code);",
                       "    let _lp = []; try { _lp = $('Loc Projects 9').all(); } catch (e) { _lp = []; }   // v29: read only for a typed code\n"
                       "    const proj = pv.indexOf('new:') === 0 ? null : locFind(locRows(_lp), code);")])

# ---- 2: a room tick with nothing to redraw -----------------------------------------------------------------------------
patch("Note Toggle", [("const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };",
                       "// v29: a room ticked with nothing to clear (no other room picked) or follow (no booth on the form) - no redraw at all\n"
                       "if (which === 'room_radio' && String((a.selected_option || {}).value || '') !== '__other' && !Object.keys(st).some(k => /^room_other/.test(k) && (((st[k] || {}).room_other_pick || {}).selected_option))\n"
                       "    && !(V.blocks || []).some(b => /^booth/.test(b.block_id || ''))) return [];\n"
                       "const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };")])

# ---- 3: the department from the people picked --------------------------------------------------------------------------
patch("Build Step 2", [("  const deptAsk = (s.kind === 'studio' || s.kind === 'atmos') && typeDepts.length > 1;",
                        "  const deptAsk = false;   // v29: no Department field - Read Step 2 takes it from the engineer / arranger picked")])
patch("Read Step 2", [
    ("const dept = val('department', 'department_pick');", "let dept = val('department', 'department_pick');   // v29: may be worked out below"),
    ("{ const RR = typeRoles(data, s.purpose);   // v24: an engineer, an arranger, or (both roles) one or both",
     "// v29 (Howard, 19 Oct): a booking type whose roles span departments (Celebrity Recording, Van Recording) takes its\n"
     "// department from the people picked - Book Session never has to ask it after Book\n"
     "if (!dept && (s.kind === 'studio' || s.kind === 'atmos')) {\n"
     "  const DMAP = { 'post engineer': 'Audio Post', 'loc engineer': 'Localization', 'music engineer': 'Music', 'music arranger': 'Music' };\n"
     "  const stRec = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === String(s.purpose || '').trim());\n"
     "  const tDepts = [...new Set([].concat(((stRec || {}).fields || {})['Engineer Role Required'] || []).map(x => DMAP[String((x && x.name) || x).trim().toLowerCase()]).filter(Boolean))];\n"
     "  if (tDepts.length > 1) {\n"
     "    const ofPerson = id => { const f = who(id); const info = String((f && f.Info) || '').toLowerCase();\n"
     "      return [...new Set(Object.keys(DMAP).filter(k => info.indexOf(k) !== -1).map(k => DMAP[k]))].filter(x => tDepts.indexOf(x) !== -1); };\n"
     "    let pick = '';\n"
     "    if (arrangerId && tDepts.indexOf('Music') !== -1) pick = 'Music';\n"
     "    else if (engineerId) { const r = ofPerson(engineerId); if (r.length === 1) pick = r[0]; }\n"
     "    if (!pick) { const mine = [].concat(((who(s.requester) || {}).Department) || []).map(x => String((x && x.name) || x));\n"
     "      pick = mine.find(x => tDepts.indexOf(x) !== -1) || tDepts[0]; }\n"
     "    dept = pick;\n"
     "  }\n"
     "}\n"
     "{ const RR = typeRoles(data, s.purpose);   // v24: an engineer, an arranger, or (both roles) one or both"),
])

# ---- 4: the unused project-code search ---------------------------------------------------------------------------------
patch("Check Signature", [("else if (p.type === 'block_suggestion') route = ROUTES.suggest;   // v24: the project-code search (Options Load URL)",
                           "else if (p.type === 'block_suggestion') route = ROUTES.other;   // v29: the project-code search is gone (a text box since v25)")])
for n in ["Loc Projects S", "Suggest Codes", "Answer Suggest"]:
    remove_node(n)

# ---- 5: quiet refusals for what is not Slack ---------------------------------------------------------------------------
patch("Report Refused", [("const c = $('Check Signature').first().json;",
                          "const c = $('Check Signature').first().json;\n"
                          "// v29: no Slack timestamp header -> not Slack (curl, a link preview, a scanner - 19 Oct 16:03): refused quietly, no DM\n"
                          "if (c.ageSec === null || c.ageSec === undefined) return [];")])

wf["name"] = "Jessie — Slack Interactions — v29 (faster redraws + clean-up)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
