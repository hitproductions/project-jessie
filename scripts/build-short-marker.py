#!/usr/bin/env python3
"""One-line confirmation (29 Sep): "Book it? Reply yes or no." replaces the two lines
'Reply only with "yes" to book, or "no" to change anything.' + 'Confirm to book.' (same for cancel / move).

  scripts/build-short-marker.py <main-in.json> <main-out.json>

Applied on top of a main build. Guard Probe keeps working on the canonical two-line form internally (every check in
it keys on "Confirm to X."): a short line the model copies back is turned into that form on the way in, and the
canonical block becomes the short line as the very last step. Gate Context, Prepared Booking and Prepared Cancel
accept both forms, so summaries sent before the change still confirm. Book Session, the tools and the prompt still
tell the model "Confirm to X." - Guard Probe rewrites whatever it writes.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

GP_IN_OLD = "let text = (typeof raw === 'string' ? raw : '').trim();\n"
GP_IN_NEW = GP_IN_OLD + (
    "// 29 Sep: the confirmation line sent is \"Book it? Reply yes or no.\" Everything below keys on the canonical\n"
    "// \"Confirm to book.\" form, so a short line the model copied back from the conversation is turned into that first;\n"
    "// the short line is put back as the very last step.\n"
    "text = text.replace(/(Book|Cancel|Move) it\\? Reply yes or no\\.\\s*$/i, (w, v) => 'Confirm to ' + v.toLowerCase() + '.');\n")
GP_OUT_OLD = 'const fallback = "Sorry — I lost the thread on that one. Could you say it again?";\n'
GP_OUT_NEW = (
    "// 29 Sep: the confirmation goes out as one line - \"Book it? Reply yes or no.\" (Gate Context accepts both forms).\n"
    "{ const _short = (w, v) => '\\n\\n' + v.charAt(0).toUpperCase() + v.slice(1).toLowerCase() + ' it? Reply yes or no.';\n"
    "  text = text.replace(/\\n*Reply only with \"yes\" to (book|cancel|move)\\b[^\\n]*\\n\\s*Confirm to \\1\\.\\s*$/i, _short)\n"
    "             .replace(/\\n*Confirm to (book|cancel|move)\\.\\s*(?:\\((?:y\\/n|yes\\/no)\\))?\\s*$/i, _short).trim(); }\n") + GP_OUT_OLD

GATE_OLD = "const endsWith = m => found && tail.endsWith(m);\n"
GATE_NEW = ("// 29 Sep: the line is now \"Book it? Reply yes or no.\"; the older \"Confirm to book.\" still counts - summaries sent\n"
            "// before the change are in the history window this reads.\n"
            "const SHORT = { 'confirm to book.': 'book it? reply yes or no.', 'confirm to cancel.': 'cancel it? reply yes or no.', 'confirm to move.': 'move it? reply yes or no.' };\n"
            "const endsWith = m => found && (tail.endsWith(m) || tail.endsWith(SHORT[m]));\n")

PB_OLD = "if (!/Confirm to book\\.\\s*(?:\\(yes\\/no\\)\\s*)?$/i.test(t.trim()))"
PB_NEW = "if (!/(?:Confirm to book\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Book it\\? Reply yes or no\\.\\s*)$/i.test(t.trim()))"

PC_OLDS = ["else if (!/Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?$/i.test(t)) d.reason",
           "if (/Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?$/i.test(t) && code) d.card_code"]
PC_RE_OLD = "/Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?$/i"
PC_RE_NEW = "/(?:Confirm to cancel\\.\\s*(?:\\(yes\\/no\\)\\s*)?|Cancel it\\? Reply yes or no\\.\\s*)$/i"

def apply(w):
    g = node(w, "Guard Probe"); c = g["parameters"]["jsCode"]
    c = sub1(c, GP_IN_OLD, GP_IN_NEW, "gp in"); c = sub1(c, GP_OUT_OLD, GP_OUT_NEW, "gp out"); g["parameters"]["jsCode"] = c
    n = node(w, "Gate Context"); n["parameters"]["jsCode"] = sub1(n["parameters"]["jsCode"], GATE_OLD, GATE_NEW, "gate")
    n = node(w, "Prepared Booking"); n["parameters"]["jsCode"] = sub1(n["parameters"]["jsCode"], PB_OLD, PB_NEW, "prepared booking")
    pc = next((x for x in w["nodes"] if x["name"] == "Prepared Cancel"), None)
    if pc:
        c = pc["parameters"]["jsCode"]
        if c.count(PC_RE_OLD) != 2: raise SystemExit("prepared cancel: expected 2 marker tests")
        pc["parameters"]["jsCode"] = c.replace(PC_RE_OLD, PC_RE_NEW)
    return w

if __name__ == "__main__":
    w = apply(json.load(open(sys.argv[1])))
    json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
