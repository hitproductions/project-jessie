#!/usr/bin/env python3
"""main v237 (Haiku primary) - decided 8 Oct: Claude Haiku 4.5 becomes Jessie's model, paid from the monthly Claude API
credits on the Max/Team plan, and Gemini 3.5 Flash Lite (the old primary, same node, same credential) becomes the fallback.
The 3.8 Flash fallback node is removed (it stays in v236 and git). If the credits run out, Anthropic refuses the request
and the agent's fallback answers on Gemini, so Jessie degrades to the old model instead of going silent.

Haiku uses Anthropic's default temperature (1.0), like both Gemini nodes since v236 (decided 8 Oct). It also means a later
move to Sonnet 5.5 / Opus 5.5, which reject any temperature, cannot fail on it.
The Anthropic credential is created by hand in n8n; pass its id (from the credential's URL) and name so the import lands
with it set and check-import after can MATCH. Without them the node imports with no credential and must be set by hand.
  scripts/build-haiku.py <main-v236> <main-out> [<anthropic-credential-id> <credential-name>]
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)

def main(w, cred_id=None, cred_name=None):
    w["name"] = "Project Jessie — v237 (Haiku primary)"
    gem, old_fb = node(w, "Google Gemini Chat Model"), node(w, "Gemini Fallback")
    if gem["parameters"].get("modelName") != "models/gemini-3.5-flash-lite": raise SystemExit("primary is not 3.5 Flash Lite")
    if not node(w, "Jessie AI Agent")["parameters"].get("needsFallback"): raise SystemExit("agent has no fallback slot")

    haiku = {
        "parameters": {"model": {"__rl": True, "mode": "id", "value": "claude-haiku-4-5"},
                       "options": {}},
        "id": "5b0f3c1e-9a7d-4e2b-8c61-3d2f7a9e4b10",
        "name": "Claude Haiku",
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "position": gem["position"],
        "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 2000,
    }
    if cred_id: haiku["credentials"] = {"anthropicApi": {"id": cred_id, "name": cred_name}}

    gem["position"] = old_fb["position"]
    w["nodes"] = [x for x in w["nodes"] if x["name"] != "Gemini Fallback"] + [haiku]
    c = w["connections"]
    del c["Gemini Fallback"]
    c["Claude Haiku"] = {"ai_languageModel": [[{"node": "Jessie AI Agent", "type": "ai_languageModel", "index": 0}]]}
    c["Google Gemini Chat Model"] = {"ai_languageModel": [[{"node": "Jessie AI Agent", "type": "ai_languageModel", "index": 1}]]}

    s = json.dumps(w)
    if "Gemini Fallback" in json.dumps(w["nodes"]) or "Gemini Fallback" in json.dumps(c): raise SystemExit("Gemini Fallback still referenced")
    if "gemini-3.8" in s: raise SystemExit("3.8 Flash still present")
    for x in w["nodes"]:
        if "lmChat" in x["type"] and "temperature" in json.dumps(x["parameters"]): raise SystemExit(f"{x['name']}: temperature set")
    models = sorted((v["ai_languageModel"][0][0]["index"], k) for k, v in c.items() if "ai_languageModel" in v)
    if models != [(0, "Claude Haiku"), (1, "Google Gemini Chat Model")]: raise SystemExit(f"model wiring: {models}")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) not in (2, 4): print(__doc__.strip()); sys.exit(2)
    w = main(json.load(open(a[0])), *(a[2:4] if len(a) == 4 else ()))
    json.dump(w, open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
