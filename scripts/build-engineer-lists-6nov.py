#!/usr/bin/env python3
"""Builds Reminders v10, Open Consent Request v15 and Request Messages v7 (several engineers), 6 Nov.

With Slack Interactions v70 / Book Session v128 a booking can carry "Engineer: Howard Luistro, Elijah Gan" (several engineers /
arrangers, Howard 6 Nov). The readers of that line take it as a list:
- Reminders v10: every engineer / arranger named gets the reminder (team: already lists them; the names are the fallback);
- Open Consent Request v15: the first engineer named answers a priority request (as the one engineer did);
- Request Messages v7: the people told about a placed request pair team ids with every name, not one engineer and one arranger.
Built on the live downloads (reminders-v9, open-consent-request-v14, request-messages-v6).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


def build(src, out, title, node, edits):
    wf = json.load(open(os.path.join(ROOT, "workflows", "imported", src)))
    n = next(x for x in wf["nodes"] if x["name"] == node)
    js = n["parameters"]["jsCode"]
    for a, b in edits:
        js = sub(js, a, b)
    n["parameters"]["jsCode"] = js
    wf["name"] = title
    p = os.path.join(ROOT, "workflows", out)
    with open(p, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(p, ROOT), len(wf["nodes"]), "nodes")


build("reminders-v9-imported.json", "reminders-v10.json", "Jessie — Reminders — v10 (several engineers)", "Build Reminders", [
    ("(desc.match(/(?:^|\\|)\\s*For:\\s*([^|]+)/) || [])[1]].map(byName).filter(Boolean",
     "(desc.match(/(?:^|\\|)\\s*For:\\s*([^|]+)/) || [])[1]].flatMap(x => String(x || '').split(/\\s*,\\s*/)).map(byName).filter(Boolean   /* v10: several engineers */")])
build("open-consent-request-v14-imported.json", "open-consent-request-v15.json", "Jessie — Open Consent Request — v15 (several engineers)", "Build Request", [
    ("const engName = ((desc.match(/Engineer:\\s*([^(|\\n]+)/) || [])[1] || '').trim().toLowerCase();",
     "const engName = ((desc.match(/Engineer:\\s*([^(|\\n]+)/) || [])[1] || '').trim().toLowerCase().split(/\\s*,\\s*/)[0];   // v15: several engineers - the first answers")])
build("request-messages-v6-imported.json", "request-messages-v7.json", "Jessie — Request Messages — v7 (several engineers)", "Render", [
    ("const _named = [_eng ? 'engineer' : '', _arr ? 'arranger' : '', _forN ? 'for' : ''].filter(Boolean);",
     "// v7 (6 Nov): several engineers / arrangers - one role and one name per person, in team: order\n"
     "const _engL = _eng ? _eng.split(/\\s*,\\s*/) : [], _arrL = _arr ? _arr.split(/\\s*,\\s*/) : [];\n"
     "const _named = [].concat(_engL.map(() => 'engineer'), _arrL.map(() => 'arranger'), _forN ? ['for'] : []);\n"
     "const _nameAt = [].concat(_engL, _arrL, _forN ? [_forN] : []);"),
    ("name: _named[i] === 'engineer' ? _eng : _arr, as: _named[i]", "name: _nameAt[i], as: _named[i]")])
