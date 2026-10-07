#!/usr/bin/env python3
"""main v232 + Book Session v96 (am/pm range + "for sasa") - live 7 Oct 17:22-17:24 PHT on main v231 / Book Session v95:
  "book studio 7 tomorrow" -> "vo recording, project coild jacket. for sasa. 10-12pm" -> "Who's the client? (or "none")" ->
  "for sasa" -> "Nothing was booked - the end time is not after the start time."
  1. "10-12pm": Booked For reads it as 10 AM - 12 PM (the "11 to 1pm" rule), but the model passed 22:00, and a model time
     in the list of times "typed" (timesMentioned) is kept - so Prepare Booking got 10 PM - 12 PM. 22:00 was in that list
     twice over: the list read the range without that rule, and Jessie's own heads-up ("free ... 5:00 PM – 10:00 PM", v231)
     counts too. The list now applies the rule, and Jessie's times count only when they came after the requester's own
     range (an offer they then took).
  2. "for sasa": a client after "for" was only taken when capitalised. A lowercase "for <name>" that stands as its own
     phrase ("... jacket. for sasa. 10-12pm", or the whole message) is taken too, through the same filters (staff, rooms,
     session types, departments, date words, the project). Sasa Abella is in Clients; Book Session's lookup finds her.
  3. The answer "for sasa" to "Who's the client?" was dropped: the bare answer kept a name only after "it's / client is";
     "for", "it's for", "producer is", "the producer is" are taken off too.
  4. Book Session v96: DURATION_INVALID went out as "Nothing was booked - the end time is not after the start time." It now
     carries a question for Guard Probe to relay: "What time does it start and end?"
  scripts/build-time-client-fixes.py <main-v231> <main-out> <book-v95> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- main: Booked For
MEN_OLD = """  { const re = new RegExp(RANGE.source, 'gi'); let m; while ((m = re.exec(allText))) { if (m[3] || m[6]) { const a = hm(m[1], m[2], m[3] || m[6]); if (a) mentioned.add(a); } } }"""
MEN_NEW = """  // v232 (live 7 Oct 17:23, "10-12pm" -> 10 PM): the start of a range takes the same "11 to 1pm" rule as the range itself
  { const re = new RegExp(RANGE.source, 'gi'); let m; while ((m = re.exec(allText))) { if (m[3] || m[6]) { let a = hm(m[1], m[2], m[3] || m[6]); const b = hm(m[4], m[5], m[6] || m[3]);
      if (!m[3] && a && b && a >= b) a = hm(m[1], m[2], String(m[6]).toLowerCase().startsWith('p') ? 'am' : 'pm');
      if (a) mentioned.add(a); } } }"""

PUSH_OLD = """      theirs.push(t);"""
PUSH_NEW = """      theirs.push(t); __theirsAt.push(mine.length);   // v232: how many of the requester's messages are newer"""
DECL_OLD = """  const mine = [], theirs = [];   // v165: theirs = Jessie's messages in this booking"""
DECL_NEW = """  const mine = [], theirs = [];   // v165: theirs = Jessie's messages in this booking
  const __theirsAt = [];"""
ALL_OLD = """  const allText = mine.join('\\n') + '\\n' + String(out.botText || '');"""
ALL_NEW = """  // v232 (live 7 Oct 17:23): Jessie's times count as "typed" only when they came after the requester's own range (an offer
  // they then took). Her heads-up "free ... 5:00 PM – 10:00 PM" came before "10-12pm", and made the model's 10 PM stand.
  const __rangeIdx = out.timeStart ? mine.findIndex(t => TIMEISH.test(t)) : -1;
  const allText = mine.join('\\n') + '\\n' + (__rangeIdx < 0 ? String(out.botText || '') : theirs.filter((x, i) => __theirsAt[i] <= __rangeIdx).join('\\n'));"""

FC_OLD = """  for (const t of mine) { const c = findClient(t); if (c) { out.forClient = c.client; out.forClientPhrase = c.phrase; break; } }"""
FC_NEW = """  // v232 (live 7 Oct 17:23, "... jacket. for sasa. 10-12pm"): a lowercase "for <name>" that stands as its own phrase is the
  // client too - same filters as findClient; the name is capitalised ("Sasa") and Book Session looks it up in Clients
  const findClientLower = text => {
    if (/\\bclients?\\b|\\bprodu(cer)?\\b/i.test(text)) return null;
    const proj = projectOf(text);
    const re = /(?:^|[.;,!?\\n]\\s*)for\\s+([a-zà-ÿ][a-zà-ÿ'’-]*(?:\\s+[a-zà-ÿ][a-zà-ÿ'’-]*){0,2})\\s*(?=$|[.;,!?\\n])/gim;
    let m;
    while ((m = re.exec(text))) {
      const words = m[1].split(/\\s+/);
      if (words.some(w => NOTNAME.test(w) || OKNEXT.test(w) || JOIN.test(w))) continue;
      const phrase = words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '), low = phrase.toLowerCase();
      if (findFor('for ' + phrase) || keyMap[norm(phrase)] || norm(phrase) === requester) continue;
      if (proj && low === proj) continue;
      if (depts.has(low)) continue;
      if (roomNames.some(r => r && (low === r || low.indexOf(r) === 0))) continue;
      if (typeNames.some(t => t && (low === t || low.indexOf(t) === 0 || t.indexOf(low) === 0))) continue;
      if (/^(?:today|tonight|tomorrow|now|later|lunch|dinner|breakfast|break|a while|awhile|good|real|sure|free|it|that|this|them|him|her|us|everyone|testing|test|practice|rehearsal|review|prep|backup)$/i.test(low)) continue;
      return { client: phrase, phrase: m[0].replace(/^[.;,!?\\n\\s]+/, '').trim() };
    }
    return null;
  };
  for (const t of mine) { const c = findClient(t) || findClientLower(t); if (c) { out.forClient = c.client; out.forClientPhrase = c.phrase; break; } }"""

BA_OLD = """      const _cl = takeName(_ans.replace(/^(?:it'?s|its|the client is|client is|client:?)\\s+/i, ''), true);"""
BA_NEW = """      // v232 (live 7 Oct 17:24, "for sasa"): "for", "it's for", "the producer is" ... are not part of the name
      const _cl = takeName(_ans.replace(/^(?:(?:it'?s|its)\\s+(?:for\\s+)?|for\\s+|the client is\\s+|client is\\s+|client:?\\s+|(?:the\\s+)?producer(?:\\s+is|:)?\\s+)/i, ''), true);"""

def main(w):
    w["name"] = "Project Jessie — v232 (am-pm range + for client)"
    bf = node(w, "Booked For")["parameters"]; s = bf["jsCode"]
    s = sub1(s, DECL_OLD, DECL_NEW, "decl"); s = sub1(s, PUSH_OLD, PUSH_NEW, "push"); s = sub1(s, ALL_OLD, ALL_NEW, "alltext")
    s = sub1(s, MEN_OLD, MEN_NEW, "mentioned"); s = sub1(s, FC_OLD, FC_NEW, "for client"); s = sub1(s, BA_OLD, BA_NEW, "bare answer")
    bf["jsCode"] = s
    return w

# ---------------------------------------------------------------- Book Session: Check Conflicts
DUR_OLD = """    human: 'Nothing was booked - the end time is not after the start time. Check the times with the '
         + 'requester and try again.' } }];"""
DUR_NEW = """    // v96 (live 7 Oct 17:24): the old text was sent as it was - "Nothing was booked - the end time is not after the start
    // time." in the middle of collecting the details. A question Guard Probe relays instead.
    human: 'The end time is not after the start time. Ask exactly this: "What time does it start and end?"' } }];"""

def book(w):
    w["name"] = "Jessie — Book Session — v96 (time question)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = sub1(cc["jsCode"], DUR_OLD, DUR_NEW, "duration")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
