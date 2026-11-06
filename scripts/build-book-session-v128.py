#!/usr/bin/env python3
"""Builds workflows/book-session-v128.json - Jessie — Book Session — v128 (several engineers), 6 Nov.

Howard, 6 Nov: engineers and arrangers are multi-selects (not Localization - one engineer there), and the title's initials list
them with spaces, the arranger(s) after " x ": "HL AEG x MV". The form sends the engineer as "Howard Luistro, Elijah Gan" and the
description as "Engineer: Howard Luistro, Elijah Gan | Arranger: …". Check Conflicts now resolves each name against Bookers (one
unknown name refuses the booking, as before), writes the canonical names back, puts every person's initials in the title, and the
title check accepts "HL AEG x MV". One engineer: exactly as before.
Built on workflows/imported/book-session-v127-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-session-v127-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


p = by["Check Conflicts"]["parameters"]
js = p["jsCode"]
js = sub(js, "  const _checks = [['engineer', _engRaw], ['arranger', _arrRaw]].filter(c => _split(c[1]).who);",
    "  // v128 (Howard, 6 Nov): several engineers / arrangers, comma-separated (\"Howard Luistro, Elijah Gan\") - each one checked\n"
    "  const _checks = [].concat(...[['engineer', _engRaw], ['arranger', _arrRaw]].map(([r, raw]) => String(raw || '').split(/\\s*,\\s*/).map(x => [r, x])))\n"
    "    .filter(c => _split(c[1]).who);")
js = sub(js, "  const _found = {};\n", "  const _found = {}, _foundL = { engineer: [], arranger: [] };   // v128: everyone, in order\n")
js = sub(js, "    _found[role] = { hit, role: p.role };\n",
    "    if (!_foundL[role].some(x => x.hit.name === hit.name)) _foundL[role].push({ hit, role: p.role });\n"
    "    if (!_found[role]) _found[role] = { hit, role: p.role };\n")
js = sub(js,
    "  if (_found.engineer) {\n    const e = _found.engineer;\n    REQ.engineer = e.hit.name + e.role;\n    if (_eIdx !== -1) _segs[_eIdx] = ' Engineer: ' + e.hit.name + e.role + ' ';\n  }\n"
    "  if (_found.arranger) {\n    const a = _found.arranger;\n    _segs[_aIdx] = ' Arranger: ' + a.hit.name + a.role + ' ';\n  }\n",
    "  if (_found.engineer) {\n    const e = _found.engineer;\n"
    "    const _en = _foundL.engineer.length > 1 ? _foundL.engineer.map(x => x.hit.name).join(', ') : e.hit.name + e.role;   // v128: several - names only\n"
    "    REQ.engineer = _en;\n    if (_eIdx !== -1) _segs[_eIdx] = ' Engineer: ' + _en + ' ';\n  }\n"
    "  if (_found.arranger) {\n    const a = _found.arranger;\n"
    "    const _an = _foundL.arranger.length > 1 ? _foundL.arranger.map(x => x.hit.name).join(', ') : a.hit.name + a.role;\n"
    "    _segs[_aIdx] = ' Arranger: ' + _an + ' ';\n  }\n")
js = sub(js,
    "  if (_found.engineer && (_tp.length === 3 || _twoSeg) && _found.engineer.hit.initials) {\n"
    "    const last = _tp.length - 1;\n    const parts = _tp[last].split(' x ');\n    parts[0] = _found.engineer.hit.initials;\n"
    "    if (_found.arranger && _found.arranger.hit.initials) parts[1] = _found.arranger.hit.initials;\n",
    "  if (_found.engineer && (_tp.length === 3 || _twoSeg) && _foundL.engineer.every(x => x.hit.initials)) {\n"
    "    const last = _tp.length - 1;\n    const parts = _tp[last].split(' x ');\n"
    "    parts[0] = _foundL.engineer.map(x => x.hit.initials).join(' ');   // v128: \"HL AEG\"\n"
    "    if (_found.arranger && _foundL.arranger.every(x => x.hit.initials)) parts[1] = _foundL.arranger.map(x => x.hit.initials).join(' ');\n")
js = sub(js, "    if (!/^[A-Z]{1,4}( x [A-Z]{1,4})*$/.test(_ini)) {",
    "    if (!/^[A-Z]{1,4}(?: [A-Z]{1,4})*(?: x [A-Z]{1,4}(?: [A-Z]{1,4})*)*$/.test(_ini)) {   // v128: \"HL AEG x MV\"")
p["jsCode"] = js
wf["name"] = "Jessie — Book Session — v128 (several engineers)"
out = os.path.join(ROOT, "workflows", "book-session-v128.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
