#!/usr/bin/env python3
"""Builds workflows/book-session-v119.json - "Jessie — Book Session", v119 (the most specific type named wins), 20 Oct.

Found 20 Oct 22:00 (execution 53049, Music Presentation from the form): REJECTED NEED_SESSION_TYPE - the form showed "Couldn't book
this". The type check compares the type with the words of the request, leaving out "recording" / "session": since the rename
(Music Vocal Recording -> Music Recording, Howard 20 Oct) "Music Recording" is just {music}, so "Music Presentation in Studio F …"
named both Music Presentation {music, presentation} and Music Recording {music}, and Book Session asked "Which one - Music Recording
or Music Presentation?". Now a type whose words are all inside another named type's words is left out: Music Presentation /
Music Mixing / Music Arranging win over Music Recording; "music recording" alone still names Music Recording.
Built on workflows/imported/book-session-v118-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v118-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v119.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Check Conflicts"]["parameters"]["jsCode"]
a = "    const _fulls = _all.filter(_full);\n"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, "    const _fulls0 = _all.filter(_full);\n"
                   "    // v119 (20 Oct): the most specific type named wins - a type whose words are all inside another named type's words is left\n"
                   "    // out (\"Music Presentation\" names {music, presentation}, which holds Music Recording's {music})\n"
                   "    const _fulls = _fulls0.filter(o => !_fulls0.some(p => p !== o && p.k.length > o.k.length && o.k.every(x => p.k.indexOf(x) !== -1)));\n")
by["Check Conflicts"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Book Session — v119 (the most specific type named wins)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
