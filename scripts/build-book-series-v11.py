#!/usr/bin/env python3
"""Builds workflows/book-series-v11.json - Jessie — Book Series — v11 (moved dates choosable), 4 Nov.

Howard's Slack test of the review (4 Nov ~14:50): "for nov 10, is there a way where i can choose? because it chose for me studio 2".
A date moved to another room now carries options too, with the room Jessie picked first (it stays the default - Book all books it as
before): the other suitable rooms free then (up to five more for the first room taken), the nearest free time that day in the rooms
asked (earlier / later, ending 11:59 PM at the latest), or skip. Stored in the saved series like the taken dates' options.
Built on workflows/imported/book-series-v10-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-series-v10-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Aggregate"]["parameters"]
js = p["jsCode"]
js = sub(js, "  const dur = t1m - t0m;\n",
    "  const dur = t1m - t0m;\n"
    "  // v11: the rooms that can stand in for a taken one (same as the swap below), and the nearest free times for the rooms asked\n"
    "  const poolFor = (k, D) => k === 'vbooth' ? [].concat((D.vocal_booths || {}).free || [])\n"
    "    : k === 'studio' ? [].concat(D.free_priority || []).filter(x => kindOf(x) === 'studio')\n"
    "    : k === 'common' ? [].concat(D.free_priority || [], D.free_rooms || []).filter(x => kindOf(x) === 'common')\n"
    "    : [].concat(D.free_rooms || []).filter(x => /^M\\d$/.test(x));\n"
    "  const okRoom = (x, k) => !(x === 'Studio M' && !/^van recording$/i.test(st)) && !(x === 'Studio E' && !post && k === 'studio');\n"
    "  const nearTimes = D => { const out = []; if (allDay || !(dur > 0) || !D.day_busy) return out;\n"
    "    const ivs = [].concat(...B.map(x => (D.day_busy || {})[x] || [])), freeAt = s => ivs.every(([a, b]) => s + dur <= a || s >= b);\n"
    "    let before = null, after = null;\n"
    "    for (let s = 360; s + dur <= 1440; s += 30) { if (s === t0m || !freeAt(s)) continue; if (s < t0m) before = s; else if (after === null) after = s; }\n"
    "    if (before !== null) { const be = Math.min(before + dur, 1439); out.push({ v: 'a', start: mHM(before), end: mHM(be), rooms: B.join(', '), label: B.join(' + ') + ' · ' + t12(before) + ' – ' + t12(be) + ' (earlier)' }); }\n"
    "    if (after !== null) { const ae = Math.min(after + dur, 1439); out.push({ v: 'b', start: mHM(after), end: mHM(ae), rooms: B.join(', '), label: B.join(' + ') + ' · ' + t12(after) + ' – ' + t12(ae) + ' (later)' }); }\n"
    "    return out; };\n")
js = sub(js,
    "    if (fixed) {\n"
    "      const rooms = B.map(x => rep[x] || x).join(', ');\n"
    "      perDate[d] = { rooms, start: '', end: '' };\n"
    "      items.push({ d, kind: 'moved', note: taken.map(t => rep[t] + ' instead of ' + t).join(', ') });\n"
    "      ok.push(d); continue;\n"
    "    }\n",
    "    if (fixed) {\n"
    "      const rooms = B.map(x => rep[x] || x).join(', ');\n"
    "      perDate[d] = { rooms, start: '', end: '' };\n"
    "      // v11 (Howard, 4 Nov: \"is there a way where i can choose?\"): Jessie's room first (the default), then the other suitable rooms\n"
    "      // free then for the first room taken, the nearest free times in the rooms asked, or skip\n"
    "      const lbl = rp => taken.map(t => rp[t] + ' instead of ' + t).join(', ').slice(0, 75);\n"
    "      const mo = [{ v: 'r0', rooms, start: '', end: '', label: lbl(rep) }];\n"
    "      const t0r = taken[0], k0 = kindOf(t0r);\n"
    "      for (const c of poolFor(k0, D)) {\n"
    "        if (mo.length >= 6) break;\n"
    "        if (c === rep[t0r] || B.indexOf(c) !== -1 || busy.has(c) || !okRoom(c, k0) || Object.keys(rep).some(t => t !== t0r && rep[t] === c)) continue;\n"
    "        const rp = Object.assign({}, rep, { [t0r]: c });\n"
    "        mo.push({ v: 'r' + mo.length, rooms: B.map(x => rp[x] || x).join(', '), start: '', end: '', label: lbl(rp) });\n"
    "      }\n"
    "      const opts = mo.concat(nearTimes(D), [{ v: 'skip', label: 'Skip – find another time later' }]);\n"
    "      choices[d] = opts;\n"
    "      items.push({ d, kind: 'moved', note: lbl(rep), options: opts.map(x => ({ v: x.v, label: x.label })), dflt: 'r0' });\n"
    "      ok.push(d); continue;\n"
    "    }\n")
p["jsCode"] = js
wf["name"] = "Jessie — Book Series — v11 (moved dates choosable)"
out = os.path.join(ROOT, "workflows", "book-series-v11.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
