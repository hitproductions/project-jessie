#!/usr/bin/env python3
"""Builds workflows/book-session-v121.json - "Jessie — Book Session", v121 (the form's booking type wins), 22 Oct.

QA (22 Oct 9:33, Howard on mobile): Van Recording in Studio M with an arranger (Mike Villegas) came back "Couldn't tell which
booking type this is" (NEED_SESSION_TYPE, "Which one - Van Recording or Music Recording?"). The form's words for Book Session
carry the department its people decide - here "Music" (the arranger) - and the type check reads "Music" as naming Music
Recording ({music} once "recording" is left out), so two types were fully named and it asked. The same would hit Celebrity
Recording or Band Recording with an arranger. The type check now accepts the type sent when it is one of the types named
(the form's type is picked from a list); it still asks when the type sent is not named at all.
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
js = js.replace(a, "const _ok = _fulls.length ? _fulls.some(o => o.t === _cur) : (!!_curO && _named(_curO));   // v121: the type sent wins when it is one of those named (QA 22 Oct: Van Recording + \"Music\" from the arranger)")
n["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Book Session — v121 (the form's booking type wins)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
