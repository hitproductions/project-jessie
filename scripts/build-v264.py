#!/usr/bin/env python3
"""main v264 (offer wording + project): two fixes to v263's Form Offer, from the Slack test (15 Oct 01:30):
  - the reply read "Client Jem Lim · Engineer Howard Luistro" - now "Project: ORANGE · Client: Jem Lim · Engineer: Howard
    Luistro" (a colon after every label);
  - "book studio 7 tomorrow 2-4pm VO recording for ORANGE, client Jem Lim" found no project: Booked For reads "for X" as
    the client (decision (a), 28 Sep) and drops it when the client is named outright. Form Offer now reads "for X" as the
    project when the client is named separately, or when X is in capitals (projects are written in caps) - never a
    colleague, a room, a session type or a date word. Otherwise "for X" stays the client, as before.
Built on workflows/imported/project-jessie-v263-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v263-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v264.json")

wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Form Offer"]["parameters"]["jsCode"]


def rep(a, b):
    global js
    assert js.count(a) == 1, a[:80]
    js = js.replace(a, b)


rep("// Form Offer (main v263):", "// Form Offer (main v263; v264: labels with colons, \"for X\" as the project):")
rep("""    const client = bf.client || bf.forClient || '';""", """    // v264: "for ORANGE, client Jem Lim" - "for X" is the project when the client is named separately, or when X is in
    // capitals; never a colleague, a room, a session type or a date word. Otherwise "for X" stays the client (Booked For).
    if (!P.pj && !bf.project) {
      const STOP = /^(?:client|clients|engineer|arranger|with|at|in|on|from|to|and|by|tomorrow|today|tonight|next|this|the|a|an|my|me|us|him|her|them|room|studio|session|sessions|recording|mixing|booth|please|pls|po|project|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)$/i;
      const sep = !!bf.client && !bf.forClient;
      const staffKeys = new Set();
      for (const i of $('All Bookers').all()) { const f = (i.json || {}).fields || {}; const nm = String(f.Name || '').trim().toLowerCase();
        if (nm) { staffKeys.add(nm); staffKeys.add(nm.split(/\\s+/)[0]); }
        const gb = (String(f.Info || '').match(/goes by\\s+([^\\n.]*)/i) || [])[1]; if (gb) gb.split(/,|\\bor\\b/).forEach(a => { a = a.trim().toLowerCase(); if (a) staffKeys.add(a); }); }
      const re = /\\bfor\\s+([^,.;:!?\\n]+)/gi; let m;
      while ((m = re.exec(t))) {
        const keep = [];
        for (const w of m[1].trim().split(/\\s+/)) { if (STOP.test(w) || /\\d/.test(w) || keep.length >= 4) break; keep.push(w); }
        const X = keep.join(' ');
        if (!X) continue;
        const lx = X.toLowerCase();
        if (staffKeys.has(lx) || staffKeys.has(lx.split(/\\s+/)[0]) || (bf.matched && lx.indexOf(String(bf.matched).toLowerCase()) === 0)) continue;
        if (roomsIn(X).length || TYPES.some(ty => ty.toLowerCase() === lx || ty.toLowerCase().indexOf(lx + ' ') === 0) || typeIn(X) || (bf.client && lx === String(bf.client).toLowerCase())) continue;
        const caps = /[A-Z]{2}/.test(X) && X === X.toUpperCase();
        if (sep || caps) { P.pj = cut(X, 80); break; }
      }
    }
    const client = bf.client || bf.forClient || '';""")
rep("""const more = [P.p === '__booth' ? 'M booth' : P.p, P.pj ? 'Project ' + P.pj : '', P.cd ? 'Code ' + P.cd : '', P.c ? 'Client ' + P.c : '',
        P.enN ? 'Engineer ' + P.enN : '', P.arN ? 'Arranger ' + P.arN : ''].filter(Boolean).join(' · ');""",
    """const more = [P.p === '__booth' ? 'M booth' : P.p, P.pj ? 'Project: ' + P.pj : '', P.cd ? 'Code: ' + P.cd : '', P.c ? 'Client: ' + P.c : '',
        P.enN ? 'Engineer: ' + P.enN : '', P.arN ? 'Arranger: ' + P.arN : ''].filter(Boolean).join(' · ');""")
by["Form Offer"]["parameters"]["jsCode"] = js
wf["name"] = "Project Jessie — v264 (offer wording + project)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
