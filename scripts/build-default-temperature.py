#!/usr/bin/env python3
"""main v236 (default temperature) - Google AI Studio notice, 7 Oct: custom temperature / top_p / top_k will return 400
INVALID_ARGUMENT on upcoming Gemini models (already ignored since 3.6 Flash), and thinking_budget must become thinking_level.
Jessie sets none of top_p, top_k or thinking_budget; both Gemini nodes set temperature 0.2. Decided 8 Oct: remove it from
both, so the model uses Google's default (1.0) and a model upgrade can never fail on it. On the Fallback (3.8 Flash) this
changes nothing; on the primary (3.5 Flash Lite) it may - replies can vary more than at 0.2.
  scripts/build-default-temperature.py <main-v235> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)

def main(w):
    w["name"] = "Project Jessie — v236 (default temperature)"
    for n in ("Google Gemini Chat Model", "Gemini Fallback"):
        o = node(w, n)["parameters"].setdefault("options", {})
        if "temperature" not in o: raise SystemExit(f"{n}: no temperature to remove")
        del o["temperature"]
    for x in w["nodes"]:
        s = json.dumps(x.get("parameters", {}))
        for k in ("temperature", "topP", "topK", "thinkingBudget"):
            if "lmChat" in x["type"] and f'"{k}"' in s: raise SystemExit(f"{x['name']}: {k} still set")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
