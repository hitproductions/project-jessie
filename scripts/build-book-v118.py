#!/usr/bin/env python3
"""Builds workflows/book-session-v118.json - "Jessie — Book Session", v118 (the Post Processing title kept), 20 Oct.

Howard, 20 Oct: a Post Processing booking is titled "POST PROCESSING - <PROJECT> / <who it is for>" ("POST PROCESSING - <who>"
without a project) - Slack Interactions v33 writes it. Check Conflicts reshapes titles in ~15 places for PROJECT / Client /
initials (the initials check TITLE_INITIALS, initials rewritten from Bookers, the client put back, ...), which would refuse it
("the last part must be initials") or turn the name into initials. Now:
  - the title as it arrived is kept when the session type is Post Processing and it starts "POST PROCESSING - ";
  - TITLE_INITIALS skips it, and so does the "what's the project?" check (it read "POST PROCESSING - X" as the project);
  - after every check has passed, final_summary is put back to that title (final_client '').
Also: Check Conflicts' list of Music types - Music Recording (was Music Vocal Recording), Music Mixing, Music Arranging, Music Presentation, Band Recording (Howard, 20 Oct).
Every other booking is untouched. Built on workflows/imported/book-session-v117-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v117-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v118.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Check Conflicts"]["parameters"]["jsCode"]
HEAD = ("// v118 (Howard, 20 Oct): a Post Processing title is \"POST PROCESSING - <PROJECT> / <who it is for>\" as the form wrote it - kept\n"
        "// whole: the PROJECT / Client / initials checks and rewrites below do not apply to it (they would make the name initials)\n"
        "const __postTitle0 = (() => { try { const R = $('When Executed by Another Workflow').first().json || {};\n"
        "  return /^post processing$/i.test(String(R.session_type || '').trim()) && /^\\s*POST PROCESSING\\s+-\\s+\\S/i.test(String(R.summary || ''))\n"
        "    ? String(R.summary).trim().replace(/\\s+/g, ' ') : ''; } catch (e) { return ''; } })();\n")
assert js.startswith("let __cliAsk = false;"), js[:40]
js = HEAD + js
a = "  if (_tp.length === 3 || _studio2) {"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, "  if ((_tp.length === 3 || _studio2) && !(typeof __postTitle0 !== 'undefined' && __postTitle0)) {   // v118: not a Post Processing title")
a = "})();\n// v84 (decided 2 Oct): ask for everything missing in one message"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, "})();\n// v118: the Post Processing title back, once every check has passed\n"
                   "try { const _j0 = __ccResult && __ccResult[0] && __ccResult[0].json;\n"
                   "  if (__postTitle0 && _j0 && _j0.verdict !== 'REJECTED' && _j0.final_summary !== undefined) { _j0.final_summary = __postTitle0; _j0.final_client = ''; } } catch (e) {}\n"
                   "// v84 (decided 2 Oct): ask for everything missing in one message")
a = "      if (_studioB && _sum.indexOf(' / ') !== -1) {"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, "      if (_studioB && _sum.indexOf(' / ') !== -1 && !(typeof __postTitle0 !== 'undefined' && __postTitle0)) {   // v118: a Post Processing title's first part is not a project")
a = "      'music': ['Music Vocal Recording', 'Band Recording', 'Music Mixing'],"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, "      'music': ['Music Recording', 'Music Vocal Recording', 'Band Recording', 'Music Mixing', 'Music Arranging', 'Music Presentation'],   // v118: the Music types (20 Oct)")
by["Check Conflicts"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Book Session — v118 (the Post Processing title kept)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
