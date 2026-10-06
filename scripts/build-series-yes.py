#!/usr/bin/env python3
"""main v224 (series yes recognised) - live 6 Oct 15:13 PHT on main v222: "book studio 7 every friday for the next three
weeks ..." -> the series card -> "yes" -> the same card again -> "yes" -> booked (3 events, 15:14-15:15).
  Gate Context's seriesNotice (29 Sep, QA bug 18) recognised a series card by "Dates:" and dates written "October 8". Since
  main v204 (1 Oct) Guard Probe writes the short card as "*Dates (3):*" with "Friday, 8 October 2027", so the notice never
  fired: the yes reached the model with nothing saying the series was approved, and it re-ran Expand Series and re-sent the
  card. The 1 Oct series test ended in "no", so it went unseen. Both headers and both date orders are matched now.
  scripts/build-series-yes.py <main-v223> <main-out>
"""
import json, sys
OLD = """const _seriesDates = ((lastBotText.split(/\\bDates:/i)[1] || '').match(/\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\.? \\d{1,2}\\b/g) || []).length;
const seriesNotice = (confirmed && /\\bDates:/i.test(lastBotText) && _seriesDates >= 2)"""
NEW = """// v224 (live 6 Oct 15:13): the short card (v204) says "*Dates (3):*" and "Friday, 8 October 2027" - neither matched, so
// the yes to it was never seen as approving the series and the card was sent again. Both headers, both date orders.
const _SDH = /\\bDates(?:\\s*\\(\\d+\\))?\\s*:/i;
const _MON = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*';
const _seriesDates = ((lastBotText.split(_SDH)[1] || '').match(new RegExp('\\\\b' + _MON + '\\\\.? \\\\d{1,2}\\\\b|\\\\b\\\\d{1,2} ' + _MON + '\\\\b', 'g')) || []).length;
const seriesNotice = (confirmed && _SDH.test(lastBotText) && _seriesDates >= 2)"""
w = json.load(open(sys.argv[1]))
w["name"] = "Project Jessie — v224 (series yes recognised)"
n = next(x for x in w["nodes"] if x["name"] == "Gate Context")
s = n["parameters"]["jsCode"]
if s.count(OLD) != 1: raise SystemExit("anchor")
n["parameters"]["jsCode"] = s.replace(OLD, NEW)
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
