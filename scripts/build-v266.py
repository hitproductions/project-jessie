#!/usr/bin/env python3
"""main v266 (only this message; menu after openers): two fixes from the Slack test of v265 (15 Oct 11:04-11:05).
  - "book me a studio" was offered as "Studio 8 · 4:00 PM - 6:00 PM, Client: harold orozcor, Engineer: Howard Luistro" -
    the details of the booking made just before. Booked For reads this booking's messages back to the booking request or
    to Jessie's "Booked." - but the form's DM starts "✅ *Booked.*", so it read past it into the earlier request (and "book me
    a studio" is too short to count as a new request). Form Offer now reads a request only from the message itself
    (times only when they are in it, a room / type / project / client / engineer / arranger only when typed in it); typed
    details after an offer still build on the offer. Booked For also stops at "✅ Booked." / "✅ Changed." / "❌ Cancelled:"
    (with the emoji as Slack sends it back).
  - "dsfadfsa" after "Hi Howard! What do you need?" went to the agent: Menu Check took any question of Jessie's as
    waiting for an answer. Now a general opener ("What do you need?", "What can I help with?", "What would you like to
    do?") and the menu itself do not count; a real question ("Who's the client?") still does.
Built on workflows/imported/project-jessie-v265-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v265-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v266.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70])
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Form Offer", [
    ("// Form Offer (main v263; v264: labels with colons, \"for X\" as the project):",
     "// Form Offer (main v263; v264: labels with colons, \"for X\" as the project; v266: read only from this message):"),
    ("""    if (/^\\d{2}:\\d{2}$/.test(String(bf.timeStart || '')) && /^\\d{2}:\\d{2}$/.test(String(bf.timeEnd || '')) && bf.timeStart < bf.timeEnd) {""",
     """    // v266 (live 11:05): Booked For reads back through earlier messages - "book me a studio" got the previous booking's room,
    // time and client. A request is read only from this message: what Booked For found counts only when it is in it.
    const lowT = t.toLowerCase();
    const inT = x => !!x && lowT.indexOf(String(x).toLowerCase().trim()) !== -1;
    if (bf.timeInNewest && /^\\d{2}:\\d{2}$/.test(String(bf.timeStart || '')) && /^\\d{2}:\\d{2}$/.test(String(bf.timeEnd || '')) && bf.timeStart < bf.timeEnd) {"""),
    ("if (rNow.length === 1) P.r = rNow[0]; else if (rNow.length > 1) delete P.r; else if (!P.r && rAll.length === 1) P.r = rAll[0];",
     "if (rNow.length === 1) P.r = rNow[0]; else if (rNow.length > 1) delete P.r;   // v266: not from earlier messages (rAll)"),
    ("if (tyNow) P.p = tyNow; else if (!P.p && tyAll) P.p = tyAll;", "if (tyNow) P.p = tyNow;   // v266: not from earlier messages (tyAll)"),
    ("if (bf.project) P.pj = cut(bf.project, 80);", "if (bf.project && inT(bf.project)) P.pj = cut(bf.project, 80);"),
    ("if (bf.projectCode) P.cd = cut(bf.projectCode, 40);", "if (bf.projectCode && inT(bf.projectCode)) P.cd = cut(bf.projectCode, 40);"),
    ("const client = bf.client || bf.forClient || '';",
     "const client = (bf.client && inT(bf.clientPhrase || bf.client) ? bf.client : '') || (bf.forClient && inT(bf.forClientPhrase || bf.forClient) ? bf.forClient : '');"),
    ("if (bf.engineer && bf.engineerResolved) {", "if (bf.engineer && bf.engineerResolved && inT(bf.engineerPhrase)) {"),
    ("if (bf.arranger && bf.arrangerResolved) {", "if (bf.arranger && bf.arrangerResolved && inT(bf.arrangerPhrase)) {"),
])
patch("Booked For", [
    ("if (/^\\s*\\*?(booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(t))",
     "if (/^\\s*(?:(?:✅|❌|:white_check_mark:|:x:)\\s*)?\\*?(booked\\b|done\\s*-|moved\\b|changed\\b|cancell?ed\\b)|has been booked/i.test(t))"),
])
patch("Menu Check", [
    ("    const waiting = g.confirmed || g.confirmedCancel || g.confirmedMove || gate.presentedBook || gate.presentedCancel || gate.presentedMove\n      || /\\?\\s*$/.test(lastText) || lastButtons.some(x => x === 'open_book:{');",
     "    // v266 (live 11:04): a general opener (\"What do you need?\") or the menu is not a question waiting for an answer\n"
     "    const opener = /(?:what do you need|what can i (?:do|help)(?: you)? with|how can i help|what would you like to do|anything else)\\?\\s*$/i.test(lastText)\n"
     "      || lastButtons.some(x => x === 'open_book:m');\n"
     "    const waiting = g.confirmed || g.confirmedCancel || g.confirmedMove || gate.presentedBook || gate.presentedCancel || gate.presentedMove\n"
     "      || (/\\?\\s*$/.test(lastText) && !opener) || lastButtons.some(x => x === 'open_book:{');"),
])
wf["name"] = "Project Jessie — v266 (only this message; menu after openers)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
