#!/usr/bin/env python3
"""Builds workflows/project-jessie-v277.json - "Project Jessie", main v277 ("for <someone>" fills the form), round 13 (20 Oct).

Howard, 20 Oct 21:18: "hello book dubbing session tomorrow studio 4 2-4pm for josiah" -> the form opened without Josiah as the
engineer. Booked For read "for josiah" = Josiah Lateo (bookedFor, staff), but Form Offer filled the Engineer only from
"engineer <name>" - "for <colleague>" was the chat's on-behalf idea, dropped in the form (14 Oct).
Form Offer now, when neither an engineer nor an arranger was typed and "for <name>" is in this message:
  - a colleague whose Bookers Info says engineer -> Engineer (shown "Engineer: Josiah Lateo"); an arranger -> Arranger
  - Post Processing or an M booth -> "Who is it for?" = the name as typed, capitalised ("for japs" -> Japs), staff or not; never
    the client (Howard, 20 Oct: Post Processing's Booker dropdown becomes "Who is it for?" - Slack Interactions v33)
  - no booking type typed yet ("book studio e for dilan"): the colleague (fid) and the name (fn) ride along; step 2 puts them in
    the box of the type picked. Studio E alone means Post Processing, Studio M alone Van Recording
  - anyone else on staff -> nothing (the form books as the person typing); not staff -> the client, as before
Booked For: a two-letter "Goes by" nickname counts in any case ("for bp" / "for BP" = BP Valenzuela, an arranger - Howard,
20 Oct); a two-letter name that is just the person's initials (DR, KD) only in capitals; common short words never. Before,
every key under 3 letters was left out, so "for BP" became a client named BP.
Built on workflows/imported/project-jessie-v276-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v276-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v277.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


ARR = "    if (bf.arranger && bf.arrangerResolved && inT(bf.arrangerPhrase)) { const id = slackOf(bf.arranger); if (id) { P.ar = id; P.arN = cut(bf.arranger, 60); } }\n"
patch("Form Offer", [
    (ARR, ARR +
     "    // v277 (Howard, 20 Oct: \"... studio 4 2-4pm for josiah\"): \"for <someone>\" in this message fills the form like the chat did\n"
     "    // (PENDING 94), when neither an engineer nor an arranger was typed:\n"
     "    //   a known booking type: an engineer colleague -> Engineer, an arranger -> Arranger; Post Processing / an M booth -> \"Who is\n"
     "    //   it for?\" (the name as typed - staff or not, never the client); anyone else on staff: nothing; not staff: the client;\n"
     "    //   no type yet (\"book studio e for dilan\"): the colleague (fid) and the name (fn) ride along and step 2 puts them in the box\n"
     "    //   the type picked has (Slack Interactions v33). Studio E is only for Post Processing, Studio M only for Van Recording.\n"
     "    if (P.r === 'Studio E' && !P.p) P.p = 'Post Processing';\n"
     "    if (P.r === 'Studio M' && !P.p) P.p = 'Van Recording';\n"
     "    const _forTyped = String(bf.matched || '').replace(/^\\s*(?:for|on behalf of)\\s+/i, '').trim();\n"
     "    const _isPost = /^post processing$/i.test(String(P.p || '')), _nameBox = _isPost || P.p === '__booth';\n"
     "    const _fs = bf.bookedFor && inT(bf.matched) ? staff.find(s => String(s.Name).trim().toLowerCase() === String(bf.bookedFor).trim().toLowerCase()) || null : null;\n"
     "    const _fid = _fs ? String(_fs['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';\n"
     "    if (_fid && !P.en && !P.ar && !_nameBox) {\n"
     "      const info = String(_fs.Info || '');\n"
     "      if (P.p && /\\bengineer\\b/i.test(info)) { P.en = _fid; P.enN = cut(_fs.Name, 60); }\n"
     "      else if (P.p && /\\barranger\\b/i.test(info)) { P.ar = _fid; P.arN = cut(_fs.Name, 60); }\n"
     "      else if (!P.p) { P.fid = _fid; P.fidN = cut(_fs.Name, 60); }\n"
     "    }\n"
     "    // the name for a \"Who is it for?\" box: the colleague as typed, or a name that is not staff (lowercase too - the words after \"for\",\n"
     "    // up to a date or time word)\n"
     "    let _nm = _fs ? (_forTyped || String(_fs.Name).split(/\\s+/)[0]) : (bf.forClient && inT(bf.forClientPhrase || bf.forClient) ? String(bf.forClient).trim() : '');\n"
     "    if (!_nm && (_nameBox || !P.p)) { const _SF = /^(?:tomorrow|today|tonight|next|this|the|a|an|at|from|to|on|in|and|all|whole|day|morning|afternoon|evening|noon|am|pm|please|pls|po|booth|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|m\\d)$/i;\n"
     "      const _m = t.match(/\\bfor\\s+([^\\s\\d][^\\s]*(?:\\s+[^\\s\\d][^\\s]*){0,2})/i);\n"
     "      if (_m) { const keep = []; for (const w0 of _m[1].split(/\\s+/)) { const w = w0.replace(/[.,!?;:]+$/, ''); if (!w || _SF.test(w) || /\\d/.test(w) || keep.length >= 3) break; keep.push(w); if (w0 !== w) break; } _nm = keep.join(' '); } }\n"
     "    if (_nm && (_nameBox || !P.p)) { P.fn = cut(_nm.replace(/(^|[\\s\\-'’])(\\p{Ll})/gu, (m, p, c) => p + c.toUpperCase()), 40); if (_nameBox) delete P.c; }\n"),
    ("        P.enN ? 'Engineer: ' + P.enN : '', P.arN ? 'Arranger: ' + P.arN : ''].filter(Boolean).join(' · ');",
     "        P.enN ? 'Engineer: ' + P.enN : '', P.arN ? 'Arranger: ' + P.arN : '', (/^post processing$/i.test(String(P.p || '')) || P.p === '__booth') && P.fn ? 'For: ' + P.fn : (P.fidN ? 'For: ' + P.fidN : '')].filter(Boolean).join(' · ');   // v277"),
])
patch("Booked For", [
    ("  const lookup = k => (keyMap[k] && keyMap[k].size === 1) ? [...keyMap[k]][0] : '';\n",
     "  const lookup = k => (keyMap[k] && keyMap[k].size === 1) ? [...keyMap[k]][0] : '';\n"
     "  // v277: two-letter \"Goes by\" names (keys under 3 letters are left out above, so \"for me\" / \"for a\" are never people): a\n"
     "  // nickname that is not the person's initials counts in any case (\"for bp\" / \"for BP\" = BP Valenzuela, initials BPV); one that is\n"
     "  // just their initials (DR, KD) only in capitals (\"for dr cruz\" is not Daryl); common short words never\n"
     "  const caps2 = {}, nick2 = {}, COMMON2 = /^(?:me|us|it|am|pm|an|ok|po|no|so|to|in|on|at|by|my|hi|yo|or|of|up|go|do|be|is|as|we|he|ya)$/i;\n"
     "  for (const f of staff) { const gb2 = String(f.Info || '').match(/goes by\\s+([^\\n]*)/i), ini2 = String(f.Initials || '').replace(/\\s+/g, '').toUpperCase(), first2 = String(f.Name || '').trim().split(/\\s+/)[0].toUpperCase();\n"
     "    for (const a of (gb2 ? gb2[1] : '').split(/,|\\band\\b/i)) { const x = a.trim().replace(/[.;:]+$/, ''); if (!/^[A-Za-z]{2}$/.test(x) || COMMON2.test(x)) continue;\n"
     "      const M2 = (x.toUpperCase() === ini2 && x.toUpperCase() !== first2) ? caps2 : nick2, key = M2 === caps2 ? x.toUpperCase() : x.toLowerCase();\n"
     "      (M2[key] = M2[key] || new Set()).add(String(f.Name).trim()); }\n"
     "    if (/^[A-Za-z]{2}$/.test(first2) && !COMMON2.test(first2)) (nick2[first2.toLowerCase()] = nick2[first2.toLowerCase()] || new Set()).add(String(f.Name).trim()); }   // a two-letter first name (BP)\n"
     "  const one = set => (set && set.size === 1) ? [...set][0] : '';\n"
     "  const cap2 = w => { w = String(w || ''); if (!/^[A-Za-z]{2}$/.test(w) || COMMON2.test(w)) return ''; return one(nick2[w.toLowerCase()]) || (/^[A-Z]{2}$/.test(w) ? one(caps2[w]) : ''); };\n"),
    ("        const who = lookup(norm(words.slice(0, k).join(' ')));\n        if (!who) continue;\n        // One word (\"Japs\")",
     "        const who = lookup(norm(words.slice(0, k).join(' '))) || (k === 1 ? cap2(words[0]) : '');   // v277: \"for BP\"\n        if (!who) continue;\n        // One word (\"Japs\")"),
])
# Music types (Howard, 20 Oct): Music Arranging, Music Mixing, Music Presentation, Music Recording (was Music Vocal Recording)
patch("Form Offer", [("const ALIAS = { voiceover: 'vo', 'voice over': 'vo', celeb: 'celebrity', dub: 'dubbing', meeting: 'meeting', meetings: 'meeting' };",
                      "const ALIAS = { voiceover: 'vo', 'voice over': 'vo', celeb: 'celebrity', dub: 'dubbing', meeting: 'meeting', meetings: 'meeting', vocal: 'music recording', vocals: 'music recording' };   // v277: Music Vocal Recording is Music Recording")])
_st = by["Session Types"]["parameters"]
_s = json.dumps(_st)
_a = "Meeting, Music Mixing, Music Vocal Recording, Post Mixing"
assert _s.count(_a) == 1, _s.count(_a)
by["Session Types"]["parameters"] = json.loads(_s.replace(_a, "Meeting, Music Arranging, Music Mixing, Music Presentation, Music Recording, Post Mixing"))
wf["name"] = "Project Jessie — v277 (for someone fills the form)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
