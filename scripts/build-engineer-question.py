#!/usr/bin/env python3
"""Book Session v75 + main v207 (engineer question) - live Slack E2E 1 Oct 14:36: a series booked by an engineer was
asked "Who's the client, and who's engineering?" (PENDING 73). Decided 1 Oct: an engineer booking is never asked who
the engineer is, and when the question is asked it reads "Who's the engineer?".
  scripts/build-engineer-question.py <book-live> <book-out> <main-live> <main-out>

Book Session v75: its scripted question is "Who's the engineer?" (was "Who's engineering?").
main v207:
  - Guard Probe, last rewrite before Slack: when Booked For already has the engineer (the requester is an engineer and
    named no one else, or a named engineer resolved), any generic engineer question is taken out of the reply - "Who's
    the client, and who's engineering?" -> "Who's the client?". Otherwise the question is worded "Who's the engineer?".
    Only generic asks are touched ("who's engineering", "who is the assigned engineer", "which engineer", "an engineer
    in mind"); a question naming people ("Is Daryl the engineer?") is left alone.
  - Prompt and Booked For notices say "Who's the engineer?".
  - Booked For read a bare "me" / "bp" answer only after a straight-apostrophe "Who's ..."; Book Session's questions
    use the curly one ("Who's the arranger?", since v73), so the answer was missed. Both apostrophes now.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
def suball(s, old, new, label):
    if s.count(old) < 1: raise SystemExit(f"{label}: no match")
    return s.replace(old, new)

def book(w):
    w["name"] = "Jessie — Book Session — v75 (engineer question)"
    cc = node(w, "Check Conflicts")["parameters"]
    cc["jsCode"] = sub1(cc["jsCode"], 'Ask exactly this, in one message: "Who\\u2019s engineering?"', 'Ask exactly this, in one message: "Who\\u2019s the engineer?"', "bs question")
    return w

GP_ANCHOR = "// v194: a compact list of this turn's tool calls, for the Turn Log (Turn Log Row cannot read the agent itself)."
GP_BLOCK = r"""// v207 (PENDING 73, 1 Oct): an engineer booking is never asked who the engineer is (live 14:36: a series got "Who's
// the client, and who's engineering?"), and when the question is asked it reads "Who's the engineer?". Booked For has the
// engineer when the requester is an engineer who named no one else, or named one it resolved. Only generic asks are
// touched - a question naming people ("Is Daryl the engineer?", "Which Daryl?") is left as it is.
try {
  const _bfE = (($('Booked For').first() || {}).json) || {};
  const _known = !!_bfE.engineerResolved;
  const _GEN = /^(?:who(?:['’]s|\s+is|\s+will\s+be)?\s+(?:the\s+|your\s+)?(?:assigned\s+|session\s+)?engineer(?:ing)?|who(?:['’]s|\s+is|\s+will\s+be)\s+engineering|who\s+will\s+engineer|(?:do\s+you\s+have\s+)?an?\s+engineer\s+in\s+mind|(?:which|what)\s+engineer(?:\s+would\s+you\s+like)?|the\s+engineer)(?:\s+(?:for\s+)?(?:this|it|them|these|the\s+session|this\s+session|the\s+sessions|the\s+booking|this\s+one))?$/i;
  const _fixQ = sent => {
    const m = /^(.*?)\?\s*$/.exec(sent); if (!m) return sent;
    const lead = (/^\s*(?:and|also|plus)\s+/i.exec(m[1]) || [''])[0];
    const parts = m[1].slice(lead.length).split(/\s*,\s*(?:and\s+|or\s+)?|\s+and\s+(?=(?:who|what|which|when|where|how|is|are|do|does|will|can|should|any)\b)/i).map(p => p.trim()).filter(Boolean);
    let hit = false; const kept = [];
    for (const p of parts) { if (_GEN.test(p)) { hit = true; if (!_known) kept.push('who’s the engineer'); } else kept.push(p); }
    if (!hit) return sent;
    if (!kept.length) return '';
    const s = kept.length === 1 ? kept[0] : kept.length === 2 ? kept[0] + ' and ' + kept[1] : kept.slice(0, -1).join(', ') + ', and ' + kept[kept.length - 1];
    const cap = x => x.replace(/^./, c => c.toUpperCase());
    return (lead ? cap(lead.trim()) + ' ' + s : cap(s)) + '?';
  };
  if (/engineer/i.test(text)) {
    const _was = text;
    text = text.split('\n').map(line => {
      if (!/\?/.test(line) || /^\s*[*_•-]/.test(line)) return line;   // card lines are never questions
      return line.split(/(?<=[.!?])\s+/).map(_fixQ).filter(x => x !== '').join(' ');
    }).join('\n').replace(/\n{3,}/g, '\n\n').trim();
    if (!text && _was) {   // the engineer was the only thing asked
      const _hasClient = !!String(_bfE.client || _bfE.forClient || '').trim();
      text = _hasClient ? 'Anything else before I show you the booking?' : 'Who’s the client? (or "none")';
    }
  }
} catch (e) {}

"""

def main(w):
    w["name"] = "Project Jessie — v207 (engineer question)"
    ag = node(w, "Jessie AI Agent")["parameters"]
    opts = ag.get("options", {})
    key = "systemMessage" if "systemMessage" in opts else None
    if not key: raise SystemExit("no systemMessage on the agent")
    sm = opts[key]
    sm = sub1(sm, 'Ask "Who\'s engineering?"', 'Ask "Who\'s the engineer?"', "prompt ask")
    sm = sub1(sm, "and who's engineering?\"", "and who's the engineer?\"", "prompt good example")
    opts[key] = sm
    bf = node(w, "Booked For")["parameters"]; s = bf["jsCode"]
    s = suball(s, "Do not ask who is engineering", "Do not ask who the engineer is", "bf notice 1")
    s = suball(s, "do not ask who is engineering", "do not ask who the engineer is", "bf notice 2")
    s = sub1(s, "const _q = /\\bwho(?:'s|\\s+is|\\s+will\\s+be)?\\s+(?:the\\s+|your\\s+)?(arranger|engineer)\\b/i.exec(_last);",
             "const _q = /\\bwho(?:['’]s|\\s+is|\\s+will\\s+be)?\\s+(?:the\\s+|your\\s+)?(arranger|engineer)\\b/i.exec(_last);   // v207: ’ too", "bf bare q")
    s = sub1(s, "/\\bwho(?:'s|\\s+is|\\s+will\\s+be)?\\s+(?:the\\s+)?engineer|\\bwho'?s\\s+engineering\\b/i.test(_lastQ)",
             "/\\bwho(?:['’]s|\\s+is|\\s+will\\s+be)?\\s+(?:the\\s+)?engineer|\\bwho['’]?s\\s+engineering\\b/i.test(_lastQ)", "bf bare me")
    bf["jsCode"] = s
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
