#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v33.json - "Jessie — Slack Interactions", v33 (M booth "for" name), round 13 (20 Oct).

With main v277: "book m4 for japs" -> the M booth's "Who is it for?" starts on Japs (pre.fn from Form Offer); without one, the
booker's first name as before. "Book a room" again (a DM when the window is gone, a decline from Room Check) carries the name.
Also (Howard, 20 Oct): Dylan Diaz is "Dilan Diaz" in Bookers - the Post Processing fallbacks (an old form; a Change form whose
booking's initials match no one) find him by either spelling. The dropdowns read names from Bookers and need nothing.
Built on workflows/imported/slack-interactions-v32-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v32-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v33.json")
wf = json.load(open(SRC))
CHANGE_NODES = ["Build Change", "Read Change", "To Move", "After Move", "Note Toggle"]
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Build Step 2", [("blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(mine.name || '').split(/\\s+/)[0])), notes);",
                        "blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(pre.fn || '').trim().slice(0, 40) || String(mine.name || '').split(/\\s+/)[0])), notes);   // v33: \"for <name>\" typed (main v277)")])
patch("Read Step 2", [("  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId };",
                       "  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId, fn: s.kind === 'booth' ? forName : '' };   // v33: the M booth's name")])
# Howard, 20 Oct: Dylan Diaz is "Dilan Diaz" in Bookers now - the two fallbacks that looked him up by name take either spelling
patch("Read Step 2", [
    ("const pb = (data.bookers || []).map(b => b.fields || {}).find(f => String(f.Name || '').trim() === 'Dylan Diaz');",
     "const pb = (data.bookers || []).map(b => b.fields || {}).find(f => /^d[iy]lan\\s+diaz$/i.test(String(f.Name || '').trim()));   // v33: Dilan (was Dylan)"),
    ("'Dylan Diaz isn’t in Bookers yet - ask for the booker to be added.'", "'Dilan Diaz isn’t in Bookers yet - ask for the booker to be added.'")])
for n in ["Build Change", "Read Change", "To Move", "After Move", "Note Toggle"]:
    patch(n, [("const dyl = st.find(x => x.name === 'Dylan Diaz');", "const dyl = st.find(x => /^d[iy]lan\\s+diaz$/i.test(x.name));   // v33: Dilan (was Dylan)")])

# ---- Howard, 20 Oct (later): Post Processing asks "Who is it for?" (text) instead of the Booker dropdown; "for <colleague>" typed
# before the type was known goes in the box of the type picked; Finance / Management / People & Culture are left out of the people
# dropdowns (not of typed names - Howard)
HELPERS = r"""// v33 (Howard, 20 Oct): people in Finance, Management or People & Culture are left out of the people dropdowns (typed names
// still match anyone)
const NOLIST = /^(?:finance|management|p\s*&\s*c|people\s*(?:&|and)\s*culture)$/i;
function listable(f) { return ![].concat((f && (f.Department || f.dept)) || []).some(d => NOLIST.test(String((d && d.name) || d).trim())); }
// v33: a typed name that is exactly one person in Bookers (name, first name, "Goes by") -> their Slack id, else ''
function oneBooker(data, name) { const q = String(name || '').trim().toLowerCase(); if (!q) return '';
  const hits = ((data && data.bookers) || []).map(x => x.fields || {}).filter(f => { const full = String(f.Name || '').trim().toLowerCase(), fst = full.split(/\s+/)[0];
    const al = ((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1] || '').split(/,|\band\b/).map(x => x.trim().replace(/\.$/, '').toLowerCase()).filter(Boolean);
    return q === full || q === fst || al.indexOf(q) !== -1; });
  return hits.length === 1 ? String(hits[0]['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' : ''; }
"""
for n in ["Build Step 2", "Read Step 2"] + CHANGE_NODES:
    by[n]["parameters"]["jsCode"] = HELPERS + by[n]["parameters"]["jsCode"]

patch("Build Step 2", [
    ("const engs = people.filter(p => /\\bengineer\\b/i.test(p.info)).sort(", "const engs = people.filter(p => /\\bengineer\\b/i.test(p.info) && listable(p)).sort("),
    ("const arrs = people.filter(p => /\\barranger\\b/i.test(p.info)).sort(", "const arrs = people.filter(p => /\\barranger\\b/i.test(p.info) && listable(p)).sort("),
    ("typed = engs.find(p => p.slack === pre.en) || null;", "typed = engs.find(p => p.slack === pre.en) || engs.find(p => p.slack === pre.fid) || null;   // v33: + \"for <engineer>\" typed before the type"),
    ("const arrDefault = arrs.find(p => p.slack === pre.ar) || (meArr && !me ? meArr : null);",
     "const arrDefault = arrs.find(p => p.slack === pre.ar) || (pre.fid && !engs.some(p => p.slack === pre.fid) ? arrs.find(p => p.slack === pre.fid) : null) || (meArr && !me ? meArr : null);   // v33"),
    ("""  } else if (s.kind === 'post') {   // v21: Post Processing - a project title, no client; v30: Booker is a dropdown (everyone in Bookers)
    const bks = people.slice().sort((a, b) => a.name.localeCompare(b.name)), meB = bks.find(p => p.slack === (pre.en || s.requester));
    const bopts = (meB && bks.indexOf(meB) >= 100 ? [meB].concat(bks.filter(p => p !== meB)) : bks).slice(0, 100).map(popt);
    const bIni = meB ? bopts.find(o => o.value === meB.slack) : null;
    blocks.push(input('booker', 'Booker', Object.assign({ type: 'static_select', action_id: 'booker_pick', placeholder: { type: 'plain_text', text: 'Select a booker' }, options: bopts }, bIni ? { initial_option: bIni } : {})),
      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);""",
     """  } else if (s.kind === 'post') {   // v21: Post Processing - a project title, no client; v33 (Howard, 20 Oct): "Who is it for?" (text, like an M
    // booth - was v30's Booker dropdown): "for <name>" typed, else your first name; a name that is one person in Bookers gives the title their initials
    const _fp = people.find(p => p.slack === pre.en) || null;
    blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(pre.fn || '').trim().slice(0, 40) || (_fp ? _fp.name.split(/\\s+/)[0] : '') || String(mine.name || '').split(/\\s+/)[0])),
      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);"""),
])
patch("Read Step 2", [
    ("if (s.kind === 'post' && val('booker', 'booker_pick')) engineerId = val('booker', 'booker_pick');   // v30: the Booker picked\n",
     "let postFor = '';   // v33: a Post Processing \"Who is it for?\" that is not one person in Bookers - written in the notes\n"
     "if (s.kind === 'post' && val('booker', 'booker_pick')) engineerId = val('booker', 'booker_pick');   // v30: the Booker picked (a v30-v32 form still open)\n"
     "else if (s.kind === 'post' && forName) { const _id = oneBooker(data, forName); engineerId = _id || s.requester; if (!_id) postFor = forName; }   // v33: \"Who is it for?\"\n"),
    ("  'Booked by: ' + (req.Name || '')", "  postFor ? 'For: ' + postFor : '', 'Booked by: ' + (req.Name || '')"),
    ("""if (s.kind === 'booth' && forName) { const q = forName.toLowerCase();
  const hits = (data.bookers || []).map(x => x.fields || {}).filter(f => { const full = String(f.Name || '').trim().toLowerCase(), fst = full.split(/\\s+/)[0];
    const al = ((String(f.Info || '').match(/goes by\\s+([^\\n]*)/i) || [])[1] || '').split(/,|\\band\\b/).map(x => x.trim().replace(/\\.$/, '').toLowerCase()).filter(Boolean);
    return q === full || q === fst || al.indexOf(q) !== -1; });
  const id = hits.length === 1 ? String(hits[0]['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';
  forId = id && id !== s.requester ? id : ''; }""",
     """if (s.kind === 'booth' && forName) { const id = oneBooker(data, forName); forId = id && id !== s.requester ? id : ''; }   // v33: oneBooker"""),
    ("fn: s.kind === 'booth' ? forName : '' };", "fn: (s.kind === 'booth' || s.kind === 'post') ? forName : '' };"),
])
import re as _re
for n in CHANGE_NODES:
    js = by[n]["parameters"]["jsCode"]
    a1 = "  return { name: String(f.Name || '').trim(), info: String(f.Info || ''), ini: String(f.Initials || '').trim(),\n"
    assert js.count(a1) == 1, (n, "staffOf")
    js = js.replace(a1, "  return { name: String(f.Name || '').trim(), info: String(f.Info || ''), ini: String(f.Initials || '').trim(), dept: [].concat(f.Department || []),   // v33: dept\n")
    for role, key in [("engineer", "en"), ("arranger", "ar")]:
        a2 = "st.filter(x => /\\b" + role + "\\b/i.test(x.info)).sort("
        assert js.count(a2) == 1, (n, role, js.count(a2))
        js = js.replace(a2, "st.filter(x => /\\b" + role + "\\b/i.test(x.info) && (listable(x) || x.slack === V." + key + ")).sort(")
    m = _re.search(r"  if \(K === 'post'\) \{ const bks = [\s\S]*?notes\]; \}", js)
    assert m, (n, "post block")
    js = js[:m.start()] + ("  if (K === 'post') { const _p = st.find(x => x.slack === V.en);   // v33 (Howard, 20 Oct): \"Who is it for?\" (text), the booking's person to start\n"
                            "    return [inp('det_project', 'Project title', txt('det_project_in', V.project)), inp('det_forname', 'Who is it for?', txt('det_forname_in', V.forname != null ? V.forname : (_p ? _p.name.split(/\\s+/)[0] : ''))), notes]; }") + js[m.end():]
    by[n]["parameters"]["jsCode"] = js
patch("Read Change", [("d.teamShown = !!(v.det_engineer || v.det_arranger);\n",
                       "d.teamShown = !!(v.det_engineer || v.det_arranger);\n"
                       "  // v33: Post Processing's \"Who is it for?\" - one person in Bookers is the booking's person (engineer line), anyone else none\n"
                       "  if ((typeKind(d.st || b.st || '') || O.kind) === 'post' && v.det_forname) { const _id = oneBooker(data, d.forname); d.en = _id || c.user; d.teamShown = true; }\n")])

# ---- Howard, 20 Oct (later): the Post Processing title is "POST PROCESSING - <PROJECT> / <who it is for>" (no project:
# "POST PROCESSING - <who>"), and the project is optional
patch("Build Step 2", [("      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);\n  } else if (s.kind === 'loc')",
                        "      input('project', 'Project title', txtIn('project_in', pre.pj), { optional: true }), notes);   // v33: optional\n  } else if (s.kind === 'loc')")])
patch("Read Step 2", [
    ("if ((s.kind === 'studio' || s.kind === 'post' || s.kind === 'atmos') && !project) errors.project = 'What is the project called?';",
     "if ((s.kind === 'studio' || s.kind === 'atmos') && !project) errors.project = 'What is the project called?';   // v33: optional for Post Processing"),
    ("else calTitle = [project.toUpperCase(), client, [ini(engineerId), ini(arrangerId)].filter(Boolean).join(' x ')].filter(Boolean).join(' / ');",
     "else if (s.kind === 'post' && forName) calTitle = 'POST PROCESSING - ' + (project ? project.toUpperCase() + ' / ' : '') + forName;   // v33 (Howard, 20 Oct)\n"
     "else calTitle = [project.toUpperCase(), client, [ini(engineerId), ini(arrangerId)].filter(Boolean).join(' x ')].filter(Boolean).join(' / ');"),
])
for n in CHANGE_NODES:
    js = by[n]["parameters"]["jsCode"]
    a1 = "function parseTitle(b) {\n  const t = String(b.t || ''), r = String(b.r || '');\n"
    assert js.count(a1) == 1, (n, "parseTitle")
    js = js.replace(a1, a1 + "  // v33: \"POST PROCESSING - <PROJECT> / <who>\" (or \"POST PROCESSING - <who>\")\n"
                             "  { const pm = t.match(/^\\s*POST PROCESSING\\s+-\\s+(?:(.+?)\\s+\\/\\s+)?(.+?)\\s*$/i); if (pm) return { kind: 'post', project: (pm[1] || '').trim(), name: pm[2].trim() }; }\n")
    a2 = "txt('det_forname_in', V.forname != null ? V.forname : (_p ? _p.name.split(/\\s+/)[0] : ''))), notes]; }"
    assert js.count(a2) == 1, (n, "post forname")
    js = js.replace(a2, "txt('det_forname_in', V.forname != null ? V.forname : (O.kind === 'post' && O.name ? O.name : (_p ? _p.name.split(/\\s+/)[0] : '')))), notes]; }")
    a3 = "    return [inp('det_project', 'Project title', txt('det_project_in', V.project)), inp('det_forname', 'Who is it for?',"
    assert js.count(a3) == 1, (n, "post project")
    js = js.replace(a3, "    return [inp('det_project', 'Project title', txt('det_project_in', V.project), true), inp('det_forname', 'Who is it for?',")
    a4 = "  if (K === 'atmos') return [String(d.project ? d.project : (O.project || O.code || '')).trim().toUpperCase(), ei].filter(Boolean).join(' / ');   // v25: PROJECT / initials\n"
    assert js.count(a4) == 1, (n, "detTitle")
    js = js.replace(a4, "  if (K === 'post') { const _who = d.forname != null && String(d.forname).trim() !== '' ? cap1(d.forname) : (O.kind === 'post' ? O.name : '');   // v33: the Post Processing title\n"
                        "    const _pj = String(d.project != null ? d.project : (O.project || '')).trim().replace(/^(?:project|proj)\\s+/i, '').toUpperCase();\n"
                        "    if (_who) return 'POST PROCESSING - ' + (_pj ? _pj + ' / ' : '') + _who; }\n" + a4)
    by[n]["parameters"]["jsCode"] = js
patch("Read Change", [("  if ((KD === 'studio' || KD === 'post' || KD === 'atmos') && v.det_project && !d.project) errors.det_project = 'What is the project called?';\n",
                       "  if ((KD === 'studio' || KD === 'atmos') && v.det_project && !d.project) errors.det_project = 'What is the project called?';   // v33: optional for Post Processing\n")])

# Post Processing on the Change form: the booking's person is read from the title's "who" (one person in Bookers), and a typed
# name that matches no one leaves the engineer line as it was - so an unchanged form says "Nothing changed."
for n in CHANGE_NODES:
    js = by[n]["parameters"]["jsCode"]
    a1 = "  return Object.assign({}, P, { en: e ? e.slack : '', ar: a ? a.slack : (P.kind === 'studio' ? 'none' : '') }); }"
    assert js.count(a1) == 1, (n, "detOrig")
    js = js.replace(a1, "  return Object.assign({}, P, { en: P.kind === 'post' ? oneBooker(data, P.name) : (e ? e.slack : ''), ar: a ? a.slack : (P.kind === 'studio' ? 'none' : '') }); }   // v33: post - the title's who")
    by[n]["parameters"]["jsCode"] = js
patch("Read Change", [("{ const _id = oneBooker(data, d.forname); d.en = _id || c.user; d.teamShown = true; }",
                       "{ const _id = oneBooker(data, d.forname); d.en = _id; d.teamShown = true; }")])

# ---- Music types (Howard, 20 Oct): for a Music session that takes an engineer or an arranger, the Arranger comes first
ARRFIRST = r"""// v33 (Howard, 20 Oct): a Music session (every role Music Engineer / Music Arranger) puts the Arranger above the Engineer
function arrFirst(data, t) { const r = ((data && data.sessionTypes) || []).find(x => String((x.fields || {}).Type || '').trim().toLowerCase() === String(t || '').trim().toLowerCase());
  const roles = r ? [].concat((r.fields || {})['Engineer Role Required'] || []).map(x => String((x && x.name) || x).trim()).filter(Boolean) : [];
  return roles.length > 0 && roles.every(x => /^music (?:engineer|arranger)$/i.test(x)) && roles.some(x => /arranger/i.test(x)); }
"""
for n in ["Build Step 2"] + CHANGE_NODES:
    by[n]["parameters"]["jsCode"] = ARRFIRST + by[n]["parameters"]["jsCode"]
patch("Build Step 2", [("const team = [].concat(RR.eng || !RR.known ? [engineer] : []).concat(RR.arr && arranger ? [arranger] : []);",
                        "let team = [].concat(RR.eng || !RR.known ? [engineer] : []).concat(RR.arr && arranger ? [arranger] : []);\n"
                        "  if (arrFirst(data, s.purpose)) team = team.slice().reverse();   // v33: Music - the Arranger first")])
for n in CHANGE_NODES:
    js = by[n]["parameters"]["jsCode"]
    a1 = "  if (R.eng || !R.known) out.push(engIn(R.either));\n  if (R.arr) out.push(inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar, 'No arranger'), true));\n"
    assert js.count(a1) == 1, (n, "team order")
    js = js.replace(a1, "  const _team = [].concat(R.eng || !R.known ? [engIn(R.either)] : []).concat(R.arr ? [inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar, 'No arranger'), true)] : []);\n"
                        "  out.push(...(arrFirst(data, T) ? _team.slice().reverse() : _team));   // v33: Music - the Arranger first\n")
    by[n]["parameters"]["jsCode"] = js
# a type that takes an arranger only (Airtable: Music Arranger alone - Music Arranging / Music Presentation until Music Engineer
# is added) needs its arranger: required on the form, "Pick the arranger." on Book
patch("Build Step 2", [("const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, { optional: true }) : null;",
                        "const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, (RR.known && RR.arr && !RR.eng) ? {} : { optional: true }) : null;   // v33: required when it is the only role")])
patch("Read Step 2", [("    else if ((RR.eng || !RR.known) && !engineerId) errors.engineer = 'Pick the engineer.'; } }",
                       "    else if ((RR.eng || !RR.known) && !engineerId) errors.engineer = 'Pick the engineer.';\n"
                       "    else if (RR.known && RR.arr && !RR.eng && !arrangerId) errors.arranger = 'Pick the arranger.'; } }   // v33: an arranger-only type")])
wf["name"] = "Jessie — Slack Interactions — v33 (Who is it for, for someone)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
