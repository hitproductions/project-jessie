#!/usr/bin/env python3
"""main v251 (v250 fixed) - from the 9 Oct 11:49 Slack round on v250.

  - "book 11-1 instead" after the taken-room heads-up: the question came back "Sunday, October 10 · 11:00 AM – 1:00 PM /
    What's the session type, project, client and engineer?" - Studio 7 missing from the restated line, and the engineer
    asked of an engineer requester.
    Cause 1: Slack returns Jessie's own emoji as codes (":x: Heads up: ..."), so Early Room Plan (v249) never recognised its
    heads-up in the history: its other rooms counted as Jessie naming other rooms, the requester's Studio 7 was dropped, and
    the early check did not run. v235's "already told" check had the same blind spot.
    Cause 2: v247's fixed question keeps "engineer" even when Booked For knows the engineer.
main v251: Early Room Plan reads :x: / :white_check_mark: / :warning: / :spiral_calendar_pad: as the emoji; Guard Probe's
  details question leaves out the engineer when Booked For has one.

  scripts/build-v251.py <main-v250> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
EP_OLD = "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim();"
EP_NEW = ("  // v251 (live 9 Oct 11:49): Slack gives Jessie's own emoji back as codes - \":x: Heads up: ...\" - so they are read as the emoji\n"
          "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').replace(/:x:/g, '❌').replace(/:white_check_mark:/g, '✅')\n"
          "    .replace(/:warning:/g, '⚠️').replace(/:spiral_calendar_pad:/g, '🗓️').trim();")
GP_OLD = "      // v249 (PENDING 103): what is already known is said back first"
GP_NEW = ("      // v251 (live 9 Oct 11:49): an engineer Booked For knows (named, or the requester as the default) is not asked\n"
          "      try { const _be = (($('Booked For').first() || {}).json) || {}; if (_be.engineerResolved && String(_be.engineer || '').trim() && _it.indexOf('engineer') !== -1) _it.splice(_it.indexOf('engineer'), 1); } catch (e) {}\n"
          + GP_OLD)
def main(w):
    w["name"] = "Project Jessie — v251 (v250 fixed)"
    ep = node(w, "Early Room Plan")["parameters"]; ep["jsCode"] = once(ep["jsCode"], EP_OLD, EP_NEW, "clean")
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], GP_OLD, GP_NEW, "engineer")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
