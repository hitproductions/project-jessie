#!/usr/bin/env python3
"""Builds workflows/book-session-v121.json - "Jessie — Book Session", v121 (the form's booking type wins), 22 Oct.

QA (22 Oct 9:33, Howard on mobile): Van Recording in Studio M with an arranger (Mike Villegas) came back "Couldn't tell which
booking type this is" (NEED_SESSION_TYPE, "Which one - Van Recording or Music Recording?"). The form's words for Book Session
carry the department its people decide - here "Music" (the arranger) - and the type check reads "Music" as naming Music
Recording ({music} once "recording" is left out), so two types were fully named and it asked. The same would hit Celebrity
Recording or Band Recording with an arranger - and, the sweep found (598 combinations), almost any type whose project or client
name holds another type's word ("band demo", "vo spot", "event teaser", "qc pass"; Music Recording + "mix tape" was even swapped to
Music Mixing). The type check now accepts the type sent whenever its words are all there (the form's type is picked from a
list); it still asks when the type sent is not named at all.
Built on workflows/imported/book-session-v120-imported.json (the live download). Only Check Conflicts changes.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v120-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v121.json")
wf = json.load(open(SRC))
n = next(x for x in wf["nodes"] if x["name"] == "Check Conflicts")
js = n["parameters"]["jsCode"]
a = "const _ok = _fulls.length ? (_fulls.length === 1 && _fulls[0].t === _cur) : (!!_curO && _named(_curO));"
assert js.count(a) == 1
js = js.replace(a, "const _ok = _curFull || (_fulls.length ? (_fulls.length === 1 && _fulls[0].t === _cur) : (!!_curO && _named(_curO)));   // v121")
a = "if (_fulls.length === 1 && _fulls[0].t !== _cur) {"
assert js.count(a) == 1
js = js.replace(a, "// v121 (QA 22 Oct): the type sent wins whenever its words are all there - other words (the department its people decide,\n"
    "// a project or client name like \"mix tape\" / \"band demo\" / \"event teaser\") no longer make it ask \"Which one\" or swap it\n"
    "const _curFull = _fulls0.some(o => o.t === _cur);\n"
    "if (!_curFull && _fulls.length === 1 && _fulls[0].t !== _cur) {")
n["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Book Session — v121 (the form's booking type wins)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
