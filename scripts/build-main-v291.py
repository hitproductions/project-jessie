#!/usr/bin/env python3
"""Builds workflows/project-jessie-v291.json - Project Jessie — v291 (several engineers typed), 6 Nov.

Howard's Slack test of Slack Interactions v70 (6 Nov 4:12 PM): "book a vo recording tomorrow 2-4pm for studio 7, engineers howard and
eli. project two-eng test" - the form opened with Howard only (the requester, as the default); "engineers howard and eli" named no one,
because Booked For reads one person per role ("engineer Eli", "engineered by Eli"). Now a list after "engineer(s)" / "arranger(s)" -
"engineers howard and eli", "engineer: Howard, Eli", "arrangers BP & Mike" - is read when every name in it is one person in Bookers;
Form Offer pre-fills them all (en / ar as a comma list, which Slack Interactions v70 picks in its multi-selects) and shows
"Engineer: Howard Luistro, Elijah Gan". One person: as before.
Built on workflows/imported/project-jessie-v290-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "project-jessie-v290-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


p = by["Booked For"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "  for (const t of mine) { const r = findRole(t, 'arranger'); if (r) { out.arranger = r.who || r.raw; out.arrangerResolved = !!r.who; out.arrangerPhrase = r.phrase; break; } }\n",
    "  for (const t of mine) { const r = findRole(t, 'arranger'); if (r) { out.arranger = r.who || r.raw; out.arrangerResolved = !!r.who; out.arrangerPhrase = r.phrase; break; } }\n"
    "  // v291 (Howard, 6 Nov: \"engineers howard and eli\"): several people named for one role - every name one person in Bookers\n"
    "  const findList = (text, role) => {\n"
    "    const re = new RegExp('\\\\b' + role + 's?\\\\s*(?:are|is|will be|:|=|-)?\\\\s+(' + W + '(?:\\\\s+' + W + ')?(?:\\\\s*(?:,|&|\\\\band\\\\b)\\\\s*' + W + '(?:\\\\s+' + W + ')?)+)', 'i');\n"
    "    const m = re.exec(text); if (!m) return null;\n"
    "    const who = [];\n"
    "    for (const part of m[1].split(/\\s*(?:,|&|\\band\\b)\\s*/).map(x => x.trim()).filter(Boolean)) {\n"
    "      const r = resolveWords(part.split(/\\s+/)); if (!r || !r.who) break; if (who.indexOf(r.who) === -1) who.push(r.who); }   // the list ends at the first non-person (\", arrangers mike\")\n"
    "    return who.length > 1 ? { who, phrase: m[0].trim() } : null;\n"
    "  };\n"
    "  out.engineers = []; out.arrangers = [];\n"
    "  for (const t of mine) { const r = findList(t, 'engineer'); if (r) { out.engineers = r.who; out.engineer = r.who[0]; out.engineerResolved = true; out.engineerPhrase = r.phrase; break; } }\n"
    "  for (const t of mine) { const r = findList(t, 'arranger'); if (r) { out.arrangers = r.who; out.arranger = r.who[0]; out.arrangerResolved = true; out.arrangerPhrase = r.phrase; break; } }\n")

p["jsCode"] = sub(p["jsCode"], "      new RegExp('\\\\b' + noun + '(?:\\\\s+(?:is|will be|would be|should be|to be|to|will|=))?",
    "      new RegExp('\\\\b' + noun + 's?(?:\\\\s+(?:are|is|will be|would be|should be|to be|to|will|=))?")   # v291: \"arrangers mike\", \"engineers are eli\"

p = by["Form Offer"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "    if (bf.engineer && bf.engineerResolved && inT(bf.engineerPhrase)) { const id = slackOf(bf.engineer); if (id) { P.en = id; P.enN = cut(bf.engineer, 60); } }\n"
    "    if (bf.arranger && bf.arrangerResolved && inT(bf.arrangerPhrase)) { const id = slackOf(bf.arranger); if (id) { P.ar = id; P.arN = cut(bf.arranger, 60); } }\n",
    "    // v291: several engineers / arrangers typed -> every one (a comma list - Slack Interactions v70 picks them all)\n"
    "    const _many = (names, phrase) => { if (!Array.isArray(names) || names.length < 2 || !inT(phrase)) return null; const ids = names.map(slackOf);\n"
    "      return ids.every(Boolean) ? { ids: ids.join(','), names: cut(names.join(', '), 120) } : null; };\n"
    "    const _mE = _many(bf.engineers, bf.engineerPhrase), _mA = _many(bf.arrangers, bf.arrangerPhrase);\n"
    "    if (_mE) { P.en = _mE.ids; P.enN = _mE.names; }\n"
    "    else if (bf.engineer && bf.engineerResolved && inT(bf.engineerPhrase)) { const id = slackOf(bf.engineer); if (id) { P.en = id; P.enN = cut(bf.engineer, 60); } }\n"
    "    if (_mA) { P.ar = _mA.ids; P.arN = _mA.names; }\n"
    "    else if (bf.arranger && bf.arrangerResolved && inT(bf.arrangerPhrase)) { const id = slackOf(bf.arranger); if (id) { P.ar = id; P.arN = cut(bf.arranger, 60); } }\n")

wf["name"] = "Project Jessie — v291 (several engineers typed)"
out = os.path.join(ROOT, "workflows", "project-jessie-v291.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
