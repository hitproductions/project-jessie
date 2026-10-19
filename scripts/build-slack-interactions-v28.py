#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v28.json - "Jessie — Slack Interactions", v28 (details kept when not booked), 19 Oct.

Tara's message (16:07): while booking it showed "Your booking details:" and her room · date · time; when the booking came back
with a question and the window was gone, Source Done put the message back exactly as it was (her greeting and My bookings), so
her details seemed to vanish. Now, when the booking is not made and the window could not show why (views.update not ok - the
DM has the question since v27), the message keeps "Your booking details:" and the details, with "⚠️ Not booked yet – see below".
The window still open (the question shown there) -> as before. Booked -> "✅ Booked." as before.
Built on workflows/imported/slack-interactions-v27-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v27-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v28.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Source Done"][0]
js = n["parameters"]["jsCode"]
a = """let ok = false; try { ok = $('After Book').first().json.ok === true; } catch (e) { ok = false; }
return srcDone($('Mark Source').first().json, ok, '✅ Booked.');"""
b = """let ok = false; try { ok = $('After Book').first().json.ok === true; } catch (e) { ok = false; }
// v28: not booked and the window could not show why (views.update not ok - the question is in the DM since v27): the message keeps
// "Your booking details:" and the form's details, "⚠️ Not booked yet – see below" (it went back to the menu and looked empty)
const M = $('Mark Source').first().json;
const gone = (($input.first() || {}).json || {}).ok === false;
if (!ok && gone && M && M.ok && M.head) return [{ json: { channel: M.channel, ts: M.ts, blocks: srcMark(M.original, '⚠️ Not booked yet – see below', M.head), text: M.text } }];
return srcDone(M, ok, '✅ Booked.');"""
assert js.count(a) == 1
n["parameters"]["jsCode"] = js.replace(a, b)
wf["name"] = "Jessie — Slack Interactions — v28 (details kept when not booked)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
