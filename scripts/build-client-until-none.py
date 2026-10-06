#!/usr/bin/env python3
"""main v219 + Book Session v90 (client until none) - decided 6 Oct (Howard), on top of the v218 / v89 candidates:
  the client question is asked until the requester names one or declines - "none", "no client", "nope", "n/a", "wala",
  "walang client", "nobody", "no one", "not applicable", "none yet", "client is tbd" ... v89 stopped after two asks.
  - Book Session v90: no cap on asks; one wider "declined" pattern (__SAIDNONE).
  - main v219 Booked For: a bare answer to Jessie's client question ("john ableton" after 'Who’s the client? (or
    "none")') is the client - the tool inputs fall back to Booked For when the model passes none, so asking until
    answered cannot loop on a name the model dropped. The same wider "declined" words end the client scan.
  - main v219 Guard Probe: the model-written client question is not added after any of those words.
  scripts/build-client-until-none.py <book-v89> <book-out> <main-v218> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# one pattern for "there is no client" - Book Session's __SAIDNONE, also used (inline) in main
NONE_CORE = (r"\b(?:no|without(?: a| any)?|walang)\s+(?:a\s+)?(?:client|kliyente)s?\b|\bclient\s*(?:is|:|=|will be)?\s*(?:none|n\/?a|wala|nobody|no one|not applicable|tbd|tba)\b"
             r"|(?:^|\n)\s*(?:none|nope|nah|wala|n\/?a|nobody|no one|not applicable)\b(?![ \t]+(?:of|from)\b)")
NONE_RE = "/" + NONE_CORE + r"|(?:^|\n)\s*no\s*[.!]?\s*(?:\n|$)/i"     # Book Session: a bare "no" on its own line too (as before)
NONE_RE_BF = "/" + NONE_CORE + "/i"                                       # Booked For: not a bare "no" (often a no to a card)

SN_OLD = """const __SAIDNONE = /\\b(no|without(?: a| any)?|walang)\\s+(?:a\\s+)?(client|kliyente)\\b|\\bclient\\s*(?:is|:|=)?\\s*(?:none|n\\/?a|wala)\\b|(?:^|\\n)\\s*(?:none|no|wala)\\s*[.!]?\\s*(?:\\n|$)/i;"""
SN_NEW = "// v90 (decided 6 Oct): the client is asked until they name one or decline - every way of declining counts\nconst __SAIDNONE = " + NONE_RE + ";"

CAP_OLD = """  const _asked = (String(REQ.asked_text || '').match(/\\bthe client\\b/gi) || []).length;
  __cliAsk = !_now && !_loc && (!!_st || __studioRoom) && !/^(meeting|event)$/i.test(_st) && !__SAIDNONE.test(_rt)
    && !/^(Internal|Personal)$/.test(__tyWords(_rt)) && _asked < 2;"""
CAP_NEW = """  __cliAsk = !_now && !_loc && (!!_st || __studioRoom) && !/^(meeting|event)$/i.test(_st) && !__SAIDNONE.test(_rt)
    && !/^(Internal|Personal)$/.test(__tyWords(_rt));   // v90 (decided 6 Oct): asked until answered or declined - no cap"""
ASK2_OLD = """  const _cliAsked = (String(REQ.asked_text || '').match(/\\bthe client\\b/gi) || []).length >= 2;   // v89: asked at most twice (the first time with the first questions)
  const _needCli = !_typed && !_code && !_loc3 && !_noCliSaid && !_cliAsked;"""
ASK2_NEW = """  const _needCli = !_typed && !_code && !_loc3 && !_noCliSaid;   // v90 (decided 6 Oct): asked until answered or declined"""
CMT_OLD = """// end to add "who's the client? (or "none")" - asked at most twice; a requester who passes it by twice has no client."""
CMT_NEW = """// end to add "who's the client? (or "none")". v90 (decided 6 Oct): asked until they name one or decline (__SAIDNONE)."""

def book(w):
    w["name"] = "Jessie — Book Session — v90 (client until none)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, SN_OLD, SN_NEW, "saidnone"); s = sub1(s, CAP_OLD, CAP_NEW, "cap"); s = sub1(s, ASK2_OLD, ASK2_NEW, "needCli"); s = sub1(s, CMT_OLD, CMT_NEW, "comment")
    cc["jsCode"] = s
    return w

BF_NC_OLD = """  const NOCLIENT = /\\b(?:no|without(?: an?)?|walang)\\s+client\\b|\\bclient\\s*(?:is|:|=)?\\s*(?:none|n\\/?a|wala)\\b/i;"""
BF_NC_NEW = "  const NOCLIENT = " + NONE_RE_BF + ";   // v219: every way of declining (Book Session v90's __SAIDNONE)"
BF_ANCHOR = """  // Times: the newest message that says anything about time decides."""
BF_BARE = """  // v219 (decided 6 Oct): the client is asked until answered, so a bare answer to the client question alone - "john
  // ableton" after 'Who’s the client? (or "none")' - is the client, as v188 does for the arranger. Only when that was
  // the whole question (a combined one is often answered with something else: "post mixing").
  try {
    const _lastQ = String(theirs[0] || '').replace(/^Heads up:[^\\n]*?\\)\\.\\s*/, '').trim();
    const _ans = String(mine[0] || '').trim().replace(/[.!?]+$/, '');
    if (!out.client && /^Who[’']s the client\\? \\(or "none"\\)$/.test(_lastQ) && _ans && _ans.split(/\\s+/).length <= 5 && !NOCLIENT.test(_ans)
        && !/\\d|\\b(?:studio|room|booth|session|recording|mixing|tomorrow|today|am|pm|engineer|arranger|project|internal|personal|my own)\\b/i.test(_ans)) {
      const _cl = takeName(_ans.replace(/^(?:it'?s|its|the client is|client is|client:?)\\s+/i, ''), true);
      if (_cl) { out.client = _cl; out.clientPhrase = _ans; }
    }
  } catch (e) {}
"""
GP_OLD = """&& !/\\bclients?\\b|\\bprodu(?:cer)?\\b|\\b(?:none|wala)\\b/i.test(_rt)"""
GP_NEW = """&& !/\\bclients?\\b|\\bprodu(?:cer)?\\b|\\b(?:none|nope|nah|wala|n\\/?a|nobody|no one|not applicable)\\b/i.test(_rt)"""

def main(w):
    w["name"] = "Project Jessie — v219 (client until none)"
    bf = node(w, "Booked For")["parameters"]; s = bf["jsCode"]
    s = sub1(s, BF_NC_OLD, BF_NC_NEW, "bf noclient"); s = sub1(s, BF_ANCHOR, BF_BARE + BF_ANCHOR, "bf bare"); bf["jsCode"] = s
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_OLD, GP_NEW, "gp none")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
