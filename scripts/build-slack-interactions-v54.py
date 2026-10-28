#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v54.json - Jessie — Slack Interactions — v54 (picks kept), 28 Oct.

Howard's Slack test of v53, 28 Oct: step 2 came back with a problem (a misspelled client, "Did you mean …?") and the studios picked
under "+ Multiple studios" were gone. The form comes back through formAgain, which keeps typed text, single dropdowns and radio
buttons - not multi-selects, so "+ Multiple studios", "Vocal booths" (v53) and Holding rooms (since v25) were all emptied (fixes
v25-v53). Found with it, the same gap on Change: a change that comes back with a problem (a room taken, a client question) or goes
on in the DM ("Continue changing") was redrawn from the first room only, so added studios, booths and holding rooms were lost, and
the "✅ Changed" card listed only the first room (v22-v53).

v54:
1. **formAgain** (After Prepare, After Book, After Prepare Series) keeps multi-select picks too.
2. **The DM paths** ("Book a room" filled in again, "Continue booking"): Read Step 2's saved answers also carry the extra studios /
   rooms, the booths and the holding rooms (mr / bo / ho), and Build Step 2 picks them again when they are still free.
3. **Change:** a change that comes back (To Move's client question, After Move's problem) or goes on in the DM (Ask DM) keeps every
   room on it; the "✅ Changed" card shows every room.
4. **Which room is taken:** with several rooms on the booking, the Book form names the room that was just taken (Book Session says
   which), and Change says one of the rooms is taken by what - not the first room's name. One-room bookings word it as before.
Built on workflows/imported/slack-interactions-v53-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v53-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


def code(name):
    return by[name]["parameters"]["jsCode"]


def setc(name, js):
    by[name]["parameters"]["jsCode"] = js


# 1 + 4 (Book): formAgain keeps multi-select picks; a taken room named when the booking has several
FA_OLD = ("      if (o) e.initial_option = o; else delete e.initial_option;\n"
          "    }\n")
FA_NEW = ("      if (o) e.initial_option = o; else delete e.initial_option;\n"
          "    }\n"
          "    else if (e.type === 'multi_static_select' && Array.isArray(sv.selected_options)) {   // v54: + Multiple studios, Vocal booths, Holding rooms - picks kept\n"
          "      const want = sv.selected_options.map(x => x.value), all = (e.options || []).concat(...((e.option_groups || []).map(g => g.options || [])));\n"
          "      const os = all.filter(x => want.indexOf(x.value) !== -1);\n"
          "      if (os.length) e.initial_options = os; else delete e.initial_options;\n"
          "    }\n")
RO_OLD = "  if (reason === 'ROOM_OCCUPIED') return { warn: 'That room was just taken. Pick another room, or go *Back*.' };"
RO_NEW = ("  if (reason === 'ROOM_OCCUPIED') {   // v54: several rooms on the booking - say which one was taken (Book Session names it)\n"
          "    let _n = 1; try { _n = String($('Read Step 2').first().json.rooms || '').split(',').filter(x => x.trim()).length; } catch (e) {}\n"
          "    const _cr = [...new Set([].concat(r.conflicts || []).map(c => c && c.room).filter(Boolean))];\n"
          "    if (_n > 1 && _cr.length) return { warn: '*' + _cr.join('* and *') + '* ' + (_cr.length > 1 ? 'were' : 'was') + ' just taken. Take ' + (_cr.length > 1 ? 'them' : 'it') + ' off, or go *Back* and pick another time.' };\n"
          "    return { warn: 'That room was just taken. Pick another room, or go *Back*.' }; }")
for nm in ["After Prepare", "After Book", "After Prepare Series"]:
    js = sub(code(nm), FA_OLD, FA_NEW)
    js = sub(js, RO_OLD, RO_NEW)
    setc(nm, js)

# 2. the saved answers carry the extra rooms, booths and holding rooms; Build Step 2 picks them again
js = code("Read Step 2")
js = sub(js, "  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId, fn: (s.kind === 'booth' || s.kind === 'post') ? forName : '' };   // v33: the M booth's name\n",
    "  pj: project, c: client, cd: code, en: engineerId, ar: arrangerId, fn: (s.kind === 'booth' || s.kind === 'post') ? forName : '',   // v33: the M booth's name\n"
    "  mr: moreRooms.join(','), bo: booths.join(','), ho: holding.join(',') };   // v54: + Multiple studios / rooms, Vocal booths, Holding rooms\n")
setc("Read Step 2", js)

js = code("Build Step 2")
js = sub(js, "  if (BX && ini) blocks.push(...boothBlocks(ini.value, BX));   // v37: no booth for a request\n",
    "  // v54: picks saved from an earlier try (a DM's Book a room / Continue booking) - picked again when still on offer\n"
    "  const _preL = k => String(pre[k] || '').split(',').map(x => x.trim()).filter(Boolean);\n"
    "  const _repick = (bl, k) => { const w = _preL(k); if (!w.length || !bl || !bl.element) return bl; const os = (bl.element.options || []).filter(o => w.indexOf(o.value) !== -1);\n"
    "    if (os.length) bl.element.initial_options = os; return bl; };\n"
    "  if (BX && ini) blocks.push(...boothBlocks(ini.value, BX).map(bl => (pre.r && pre.r === ini.value) ? _repick(bl, 'bo') : bl));   // v37: no booth for a request\n")
js = sub(js, "element: { type: 'multi_static_select', action_id: 'holding_pick', placeholder: { type: 'plain_text', text: 'Select holding rooms' }, options: holds.slice(0, 100).map(n => opt(n, n)) } }",
    "element: Object.assign({ type: 'multi_static_select', action_id: 'holding_pick', placeholder: { type: 'plain_text', text: 'Select holding rooms' }, options: holds.slice(0, 100).map(n => opt(n, n)) },\n"
    "        (os => os.length ? { initial_options: os } : {})(holds.slice(0, 100).filter(n => _preL('ho').indexOf(n) !== -1).map(n => opt(n, n)))) }")
js = sub(js, "      options: MORE.slice(0, 100).map(n => opt(n, n)) } });",
    "      options: MORE.slice(0, 100).map(n => opt(n, n)) } });\n"
    "  if (MORE.length > 1) _repick(blocks[blocks.length - 1], 'mr');   // v54")
setc("Build Step 2", js)

# 3 + 4 (Change): every room kept when the form comes back or goes on in the DM; the Changed card; which room is taken
js = code("Ask DM")
js = sub(js, "n: R.n || {},", "n: Object.assign({}, R.n || {}, R.newRooms ? { r: R.newRooms } : {}),   // v54: every room on it")
setc("Ask DM", js)
js = code("To Move")
js = sub(js, "view: changeView(R.b, R.n, warn,", "view: changeView(R.b, Object.assign({}, R.n, R.newRooms ? { r: R.newRooms } : {}), warn,")   # v54
setc("To Move", js)
js = code("After Move")
js = sub(js, "r: n.r || b.r,", "r: R.newRooms || n.r || b.r,")   # v54: the Changed card - every room
js = sub(js, "const why = r.reason === 'ROOM_OCCUPIED' ? (n.r || b.r || 'The room') + ' is taken then'",
    "const _nr = String(R.newRooms || '').split(',').map(x => x.trim()).filter(Boolean);   // v54: several rooms - one of them is taken, by what\n"
    "const _cs = [].concat(r.conflicts || []).map(c => c && c.summary).filter(Boolean);\n"
    "const why = r.reason === 'ROOM_OCCUPIED' ? (_nr.length > 1 ? 'One of the rooms (' + _nr.join(', ') + ') is taken then' + (_cs.length ? ' by \"' + _cs.join('\", \"') + '\"' : '') : (n.r || b.r || 'The room') + ' is taken then')")
js = sub(js, "view: changeView(b, n, why,", "view: changeView(b, Object.assign({}, n, R.newRooms ? { r: R.newRooms } : {}), why,")   # v54
setc("After Move", js)

wf["name"] = "Jessie — Slack Interactions — v54 (picks kept)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v54.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
