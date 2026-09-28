#!/usr/bin/env python3
"""QA bugs 16-18 (29 Sep live QA), applied to a fresh pull of main.

  scripts/build-bugfix-16-18.py <main-pull.json> <main-out.json>

16  "Friday next week" / "next week Friday" was read as THIS Friday (the bare-weekday rule saw "Friday" alone), and
    "every Tuesday in November" set the date under discussion to the coming Tuesday. Gate Context now reads the first
    as next week's day and skips a weekday after "every" / "each".
17  A bare "yes" right after Jessie reported a result ("Booked." / "Cancelled ..." / "Moved ...") went to the model,
    which retried and said the room was taken by the requester's own booking. It is answered in code now.
18  A yes to a series summary was answered by calling Expand Series again and re-sending the summary. Gate Context
    now tells the model the series is approved and that its next action is Book Series (as it already does for
    cancel and move). The code-written series summary is Howard's recurring-bookings item.
"""
import copy, json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def uid(): return str(uuid.uuid4())
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
def link(C, a, b, br=0):
    arr = C.setdefault(a, {}).setdefault("main", [])
    while len(arr) <= br: arr.append([])
    arr[br].append({"node": b, "type": "main", "index": 0})

G_NEXT_OLD = "const reNext = new RegExp('\\\\bnext\\\\s+' + DAYRE + '\\\\b', 'gi');\n"
G_NEXT_NEW = (
    "// 29 Sep (QA bug 16): \"Friday next week\" / \"next week Friday\" is next week's Friday. The bare-weekday rule\n"
    "// below used to see \"Friday\" on its own and answer THIS Friday.\n"
    "const reNextWeekDay = new RegExp('\\\\b' + DAYRE + '\\\\s+(?:of\\\\s+)?next\\\\s+week\\\\b|\\\\bnext\\\\s+week(?:\\'s)?\\\\s+' + DAYRE + '\\\\b', 'gi');\n"
    "while ((dm = reNextWeekDay.exec(msgText)) !== null)\n"
    "  note(dm[0], addDays(weekMonday, 7 + ((dayIndex(dm[1] || dm[2]) + 6) % 7)));\n"
    + G_NEXT_OLD)
G_BARE_OLD = "const reBare = new RegExp('(?<!\\\\b(?:next|this|last)\\\\s)\\\\b' + DAYRE + '\\\\b', 'gi');\n"
G_BARE_NEW = (
    "// Not a weekday that belongs to \"... next week\" (above), and not \"every / each Tuesday\" - a pattern is not a date.\n"
    "const reBare = new RegExp('(?<!\\\\b(?:next|this|last|every|each)\\\\s)(?<!\\\\bnext\\\\s+week(?:\\'s)?\\\\s+)\\\\b' + DAYRE + '\\\\b(?!\\\\s+(?:of\\\\s+)?next\\\\s+week)', 'gi');\n")
G_RANGE_OLD = "if ((rm = msgText.match(/\\bnext\\s+week\\b/i))) rangeNote(rm[0], addDays(weekMonday, 7), addDays(weekMonday, 13));\n"
G_RANGE_NEW = ("if ((rm = msgText.match(/\\bnext\\s+week\\b/i)) && !new RegExp(DAYRE + '\\\\s+(?:of\\\\s+)?next\\\\s+week|next\\\\s+week(?:\\'s)?\\\\s+' + DAYRE, 'i').test(msgText))\n"
               "  rangeNote(rm[0], addDays(weekMonday, 7), addDays(weekMonday, 13));\n")
G_SERIES_ANCHOR = "const cancelNotice = confirmedCancel\n"
G_SERIES = (
    "// 29 Sep (QA bug 18): a yes to a SERIES summary (written by the model: a \"Dates:\" list) was answered by calling\n"
    "// Expand Series again and re-sending the summary - nothing was booked. Say what the next action is, as for cancel\n"
    "// and move below.\n"
    "// Dates may be a list or one comma-separated line, so count the dates after \"Dates:\" wherever they are.\n"
    "// ... with or without a year (\"November 2, 2027\", \"Dec 7\").\n"
    "const _seriesDates = ((lastBotText.split(/\\bDates:/i)[1] || '').match(/\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\.? \\d{1,2}\\b/g) || []).length;\n"
    "const seriesNotice = (confirmed && /\\bDates:/i.test(lastBotText) && _seriesDates >= 2)\n"
    "  ? 'THE SERIES IS ALREADY APPROVED. They have just said yes to the series summary you showed them. Your next '\n"
    "    + 'action is one call to Book Series with exactly the pattern, times and details in that summary. Do not call '\n"
    "    + 'Expand Series again and do not show the summary again.'\n"
    "  : '';\n")
G_RET_OLD = "  moveNotice: moveNotice,\n"
G_RET_NEW = "  moveNotice: moveNotice,\n  seriesNotice: seriesNotice,\n"
P_OLD = "{{ $('Gate Context').first().json.moveNotice }}\n"
P_NEW = P_OLD + "{{ $('Gate Context').first().json.seriesNotice }}\n"

PC_OLD = "return [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d }) }];"
PC_NEW = r"""// 29 Sep (QA bug 17): a second bare "yes" after Jessie already reported the result went to the model, which retried
// and replied that the room was taken - by the requester's own booking. Answered here instead.
let done = '';
try {
  const g2 = ((($('Gate Context').first() || {}).json || {}).gate) || {};
  let ms = []; try { ms = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const b = ms.find(m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message');
  const bt = b ? String(b.text || (b.message && b.message.text) || '').trim() : '';
  if (g2.saidYes === true && !d.use) {
    if (/^Booked\b/.test(bt)) done = "That's already booked - nothing else was changed.";
    else if (/^Cancelled\b/.test(bt)) done = "That's already cancelled - nothing else was changed.";
    else if (/^Moved\b/.test(bt)) done = "That's already moved - nothing else was changed.";
  }
} catch (e) { done = ''; }
return [{ json: Object.assign({}, $input.first().json || {}, { _cancelDirect: d, _alreadyDone: done }) }];"""

def apply(w):
    w["name"] = "Project Jessie — v180 (v179 fixed)"
    g = node(w, "Gate Context"); c = g["parameters"]["jsCode"]
    c = sub1(c, G_NEXT_OLD, G_NEXT_NEW, "gate next-week day")
    c = sub1(c, G_BARE_OLD, G_BARE_NEW, "gate bare weekday")
    c = sub1(c, G_RANGE_OLD, G_RANGE_NEW, "gate next-week range")
    c = sub1(c, G_SERIES_ANCHOR, G_SERIES + G_SERIES_ANCHOR, "gate series notice")
    c = sub1(c, G_RET_OLD, G_RET_NEW, "gate return")
    g["parameters"]["jsCode"] = c
    a = node(w, "Jessie AI Agent")["parameters"]["options"]
    a["systemMessage"] = sub1(a["systemMessage"], P_OLD, P_NEW, "prompt notice")
    pc = node(w, "Prepared Cancel"); pc["parameters"]["jsCode"] = sub1(pc["parameters"]["jsCode"], PC_OLD, PC_NEW, "prepared cancel")
    q = copy.deepcopy(node(w, "Cancel Direct?")); q["id"] = uid(); q["name"] = "Already Done?"; q["position"] = [75328, 6400]
    q["parameters"]["conditions"]["conditions"][0].update({"id": uid(), "leftValue": "={{ $json._alreadyDone ? 'yes' : 'no' }}", "rightValue": "yes"})
    r = {"parameters": {"mode": "runOnceForAllItems", "jsCode": "return [{ json: { output: $('Prepared Cancel').first().json._alreadyDone } }];"},
         "id": uid(), "name": "Already Done Reply", "position": [75504, 6400], "type": "n8n-nodes-base.code", "typeVersion": 2}
    w["nodes"] += [q, r]
    C = w["connections"]
    br = C["Cancel Direct?"]["main"]
    assert [t["node"] for t in br[1]] == ["Jessie AI Agent"], br
    br[1] = [{"node": "Already Done?", "type": "main", "index": 0}]
    link(C, "Already Done?", "Already Done Reply", 0); link(C, "Already Done?", "Jessie AI Agent", 1)
    link(C, "Already Done Reply", "Send Reply")
    return w

if __name__ == "__main__":
    w = apply(json.load(open(sys.argv[1]))); json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    ns = w["nodes"]; ov = [(x["name"], y["name"]) for i, x in enumerate(ns) for y in ns[i + 1:] if abs(x["position"][0] - y["position"][0]) < 120 and abs(x["position"][1] - y["position"][1]) < 100]
    print("wrote", sys.argv[2], len(ns), "nodes; overlaps:", ov)
