#!/usr/bin/env python3
"""Book Session v110 (details passed back): Return Rejection kept only reason / conflicts / alternatives / human, so the
Slack-app form got a client check with no typed name and no suggestions ("" and ** on the form, Slack test 15 Oct; fixes
v109's interplay with Slack Interactions v7). It now also passes the question's own fields - typed, suggestions, options,
askClient, client, staff, guessed, removed - when the check sent them. The chat reads only `human`, so it is unchanged.
Built on the v109 download (workflows/imported/book-session-v109-imported.json).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v109-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v110.json")

wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Return Rejection"]["parameters"]["jsCode"]
old = "  own_booking: v.own_booking === true,\n"
assert old in js, "Return Rejection changed - rebuild on the new download"
new = old + """  // v110: the question's own fields, for the Slack-app form (the chat reads only human). Only when the check sent them.
  typed: v.typed !== undefined ? v.typed : undefined, suggestions: Array.isArray(v.suggestions) ? v.suggestions : undefined,
  options: Array.isArray(v.options) ? v.options : undefined, askClient: v.askClient === true ? true : undefined,
  client: v.client !== undefined ? v.client : undefined, staff: v.staff !== undefined ? v.staff : undefined,
  guessed: v.guessed !== undefined ? v.guessed : undefined, removed: v.removed !== undefined ? v.removed : undefined,
"""
by["Return Rejection"]["parameters"]["jsCode"] = js.replace(old, new, 1)
wf["name"] = "Jessie — Book Session — v110 (details passed back)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
