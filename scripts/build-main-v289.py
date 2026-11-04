#!/usr/bin/env python3
"""Builds workflows/project-jessie-v289.json - Project Jessie — v289 (Localization feedback), 4 Nov.

From the Localization coordinator's first week (3 Nov):
- "book studio 1 and a" opened the form with Studio 1 only. Booked For's room list (v287) read a lone lowercase "a" as the word
  "a"; it is now Studio A when nothing follows it but the end, punctuation, a number, another room or a date / time word ("studio 7
  and a booth" is still a word). Form Offer uses that list: the vocal booths typed go to Vocal booths, the first other room is the
  room, the rest go to + Multiple studios (Slack Interactions' step 2 picks them: pre.bo / pre.mr). "studio 1 or a" (a choice)
  leaves the room to the form, as before. The offer shows every room ("Studio 1 + Studio A").
- "what are my bookings for november next year" listed this November. Mine Check now reads "next year" and a written year
  ("nov 2027", "november, 2027").
- My bookings' headline: "🗓️ *Your bookings:*" then "*Nov 4 – Nov 10*" (the year when it is not this year), and a "Jump to a date"
  picker (Slack Interactions v64 answers it, as it does Previous / Next 7 days).
Built on workflows/imported/project-jessie-v288-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "project-jessie-v288-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


# ---- Booked For: a lowercase "a" in a room list is Studio A when nothing but the end / a number / a room / a date word follows
p = by["Booked For"]["parameters"]
js = p["jsCode"]
# a number before "-5pm" is a time too ("studios 1 and a, 3-5pm" read Studio 3)
js = sub(js, "hrs?\\\\b|hours?\\\\b|mins?\\\\b))';", "hrs?\\\\b|hours?\\\\b|mins?\\\\b|[-\u2013]\\\\s*\\\\d))';   // v289: 3-5pm")
js = sub(js, "  const all = [];\n  let m;\n  const rs = ",
    "  // v289 (Localization, 3 Nov: \"book studio 1 and a\"): a lowercase \"a\" is Studio A when what follows it is the end, punctuation, a\n"
    "  // number, another room or a date / time word - \"studio 7 and a booth\" stays a word\n"
    "  const A_OK = /^\\s*(?:$|[,.;:!?)]|\\d|(?:and|or|&|\\/|studio|m\\d|tomorrow|today|tonight|next|this|on|at|from|for|in|by|until|till|mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|please|pls)\\w*\\b)/i;\n"
    "  const all = [];\n  let m;\n  const rs = ")
js = sub(js, "    while ((t = rt.exec(tail))) if (t[1] !== 'a') all.push([m.index + 1 + t.index, 'Studio ' + t[1].toUpperCase()]);",
    "    while ((t = rt.exec(tail))) if (t[1] !== 'a' || A_OK.test(x.slice(m.index + m[0].length - tail.length + t.index + t[0].length))) all.push([m.index + 1 + t.index, 'Studio ' + t[1].toUpperCase()]);   // v289",
    n=2)
p["jsCode"] = js

# ---- Form Offer: several rooms typed -> the room, its vocal booths, + Multiple studios
p = by["Form Offer"]["parameters"]
js = p["jsCode"]
js = sub(js, "    const rNow = roomsIn(t), rAll = roomsIn(ctx);\n    if (rNow.length === 1) P.r = rNow[0]; else if (rNow.length > 1) delete P.r;   // v266: not from earlier messages (rAll)",
    "    // v289 (Localization, 3 Nov): Booked For's list of the rooms in this message (it reads \"studio 1 and a\"), else this node's own\n"
    "    const _asked = String(bf.askedRooms || '').split(',').map(x => x.trim()).filter(n => NAMES.indexOf(n) !== -1);\n"
    "    const rNow = _asked.length >= 2 ? _asked : roomsIn(t), rAll = roomsIn(ctx);\n"
    "    if (rNow.length === 1) P.r = rNow[0];   // v266: not from earlier messages (rAll)\n"
    "    else if (rNow.length > 1) {\n"
    "      // one booking in several rooms: the vocal booths go to Vocal booths, the first other room is the room, the rest go to\n"
    "      // + Multiple studios; \"studio 1 or a\" is a choice - the room is left to the form, as before\n"
    "      if (/\\b(?:or|either)\\b/i.test(t)) delete P.r;\n"
    "      else {\n"
    "        const _vb = n => (roomRows.find(f => String(f['Room Name']).trim() === n) || {})['Vocal Booth'] === true;\n"
    "        const _rm = rNow.find(n => !_vb(n)) || rNow[0];\n"
    "        const _bo = rNow.filter(n => n !== _rm && _vb(n)), _mr = rNow.filter(n => n !== _rm && !_vb(n));\n"
    "        P.r = _rm; if (_bo.length) P.bo = _bo.join(','); if (_mr.length) P.mr = _mr.join(',');\n"
    "      }\n"
    "    }")
js = sub(js, "const head = [P.r, P.rep ?",
    "const head = [[P.r].concat(String(P.mr || '').split(','), String(P.bo || '').split(',')).filter(Boolean).join(' + '), P.rep ?")   # v289
p["jsCode"] = js

# ---- Mine Check: "next year", a written year
p = by["Mine Check"]["parameters"]
js = p["jsCode"]
js = sub(js, "|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\\b(?!\\s*\\d)/);",
    "|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\\b(?!\\s*\\d{1,2}(?:st|nd|rd|th)?\\b)/);   // v289: \"nov 2027\" is a month")
js = sub(js, "      const y = mo < mo0 ? y0 + 1 : y0;\n",
    "      // v289 (Localization, 3 Nov: \"my bookings for november next year\" listed this November): a written year, or \"next year\"\n"
    "      const _yw = mm ? t.match(new RegExp('\\\\b' + mm[1] + '\\\\.?,?\\\\s*(20\\\\d\\\\d)\\\\b')) : null;\n"
    "      const y = _yw ? +_yw[1] : /\\bnext year\\b/.test(t) ? y0 + 1 : mo < mo0 ? y0 + 1 : y0;\n")
js = sub(js, "      if (start < today && mo === mo0) start = today;", "      if (start < today && mo === mo0 && y === y0) start = today;")
p["jsCode"] = js

# "show me bookings i made on december 2027" reached the AI (Howard's Slack test, 4 Nov 3:56 PM): a list in words, no Change / Cancel.
# More ways to ask: "bookings (that) i made / booked / have", "what bookings do i have", "what have i booked"; and "next month".
js = p["jsCode"]
js = sub(js, "    || (/\\bdid i (?:book|reserve)\\b|",
    "    || /\\b(?:bookings?|sessions?|reservations?)(?: (?:that|which))? (?:i|ive|i have) (?:made|booked|have|did|reserved|set up)\\b|\\bwhat (?:bookings?|sessions?) (?:do|did|have) i\\b|\\bwhat (?:have|did) i (?:booked|book|reserved)\\b/.test(t)   // v289: \"bookings i made\"\n"
    "    || /\\b(?:booked|bookings?|sessions?|reservations?) under (?:my name|me)\\b|\\b(?:everything|all|anything) (?:that )?i (?:booked|reserved|made)\\b|\\bwhat (?:sessions?|bookings?) am i (?:in|on)\\b|\\bmy reservations?\\b|\\b(?:bookings?|booking|sessions?|schedule|sched|reservations?) ko\\b/.test(t)   // v289: under my name, everything i booked, \"bookings ko\"\n"
    "    || (/\\bdid i (?:book|reserve)\\b|")
js = sub(js, "    else if (/\\bnext week\\b/.test(t)) { start = add(today, 7); end = add(today, 14); }\n",
    "    else if (/\\bnext week\\b/.test(t)) { start = add(today, 7); end = add(today, 14); }\n"
    "    else if (/\\bnext month\\b/.test(t) && !mm) { const _y = +today.slice(0, 4), _m = +today.slice(5, 7);   // v289\n"
    "      start = new Date(Date.UTC(_y, _m, 1)).toISOString().slice(0, 10); end = new Date(Date.UTC(_y, _m + 1, 1)).toISOString().slice(0, 10); week = false; }\n")
p["jsCode"] = js

# ---- Mine Reply: the headline, Jump to a date
p = by["Mine Reply"]["parameters"]
js = p["jsCode"]
js = sub(js, "const head = mc.end === addD(mc.start, 1) ? dayShort(mc.start) : dayShort(mc.start) + ' – ' + dayShort(addD(mc.end, -1));\n"
    "const blocks = [{ type: 'section', text: md('*Your bookings' + (mc.room ? ' in ' + mc.room : '') + '* · ' + head) }];   // v279: a room asked about",
    "// v289 (Localization, 3 Nov): \"🗓️ Your bookings:\" over the dates; the year when it is not this year\n"
    "const _md = d => { const x = new Date(d + 'T12:00:00Z'); return _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); };\n"
    "const _last = addD(mc.end, -1), _yNow = String(new Date(Date.now() + 8 * 3600000).getUTCFullYear());\n"
    "const head = (mc.end === addD(mc.start, 1) ? _md(mc.start) : _md(mc.start) + ' – ' + _md(_last)) + (_last.slice(0, 4) !== _yNow ? ', ' + _last.slice(0, 4) : '');\n"
    "const blocks = [{ type: 'section', text: md('🗓️ *Your bookings' + (mc.room ? ' in ' + mc.room : '') + ':*\\n*' + head + '*') }];   // v279: a room asked about")
js = sub(js, "blocks.push({ type: 'actions', block_id: 'menu_nav', elements: [",
    "{ const _j = { type: 'datepicker', action_id: 'my_page_jump', initial_date: mc.start, placeholder: { type: 'plain_text', text: 'Jump to a date' } };   // v289\n"
    "  const _nv = blocks.find(b => b.block_id === 'my_nav'); if (_nv) _nv.elements.push(_j); else blocks.push({ type: 'actions', block_id: 'my_nav', elements: [_j] }); }\n"
    "blocks.push({ type: 'actions', block_id: 'menu_nav', elements: [")
js = sub(js, "text: 'Your bookings · ' + head, blocks, count", "text: 'Your bookings: ' + head, blocks, count")
p["jsCode"] = js

wf["name"] = "Project Jessie — v289 (Localization feedback)"
out = os.path.join(ROOT, "workflows", "project-jessie-v289.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
