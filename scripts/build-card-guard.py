#!/usr/bin/env python3
"""main v238 (card guard) - Slack round on Claude Haiku, 8 Oct 14:43 (main v237): "cancel QATEST on december 14 2027" got a
cancel card the model wrote itself, copied from the earlier cards in the conversation, with no tool called
(intermediateSteps empty) - showing 10-11 AM for a booking moved to 2-3 PM one step earlier. The prompt already says
"Never write a cancel confirmation yourself"; Haiku did anyway. Every other guard stops a wrong booking being made or a
change being claimed; nothing stopped a card no tool made.

Guard Probe: every real card comes from a tool (Prepare Booking, Prepare Series, Prepare Cancel / Cancel Booking, Move
Booking - `_prepared`) or from the series-change code in Guard Probe itself (`_codeCard`, new). A reply ending in a
confirmation line that neither made is withdrawn - "Sorry, I couldn't check that against the calendar just now, so
nothing was <cancelled>. Could you send that again?" - and the Turn Log's tools column says so. Only when
intermediateSteps is on the input (always, live); without it nothing is judged, as with the claim check.
System message: while that sentence is in Jessie's messages for the current booking, the model is told its card was
withdrawn and which tool makes each card.
  scripts/build-card-guard.py <main-v237> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

MARK = "check that against the calendar just now"

GUARD = r"""// --- v238 (card guard): a card no tool made never goes out -------------------------------------------------------------
// Slack round on Claude Haiku, 8 Oct 14:43 (main v237): "cancel QATEST on december 14 2027" got a cancel card the model
// wrote itself - no tool called, copied from earlier cards, showing the time from before a move one step earlier. Every real
// card comes from a tool (_prepared) or from the series-change code above (_codeCard). A reply ending in a confirmation line
// that neither made is withdrawn; the system message then tells the model which tool makes each card. Judged only when
// intermediateSteps is on the input (always, live), like the claim check.
let cardProbe = 'no card';
try {
  const _stC = ($input.first().json || {}).intermediateSteps;
  const _mk = text.match(/(?:\b(Book|Cancel|Move) it\? Reply yes or no\.|Confirm to (book|cancel|move)\.(?:\s*\((?:y\/n|yes\/no)\))?)\s*$/i);
  if (_mk) {
    if (_prepared || _codeCard) cardProbe = 'card from ' + (_prepared ? 'a tool' : 'code');
    else if (Array.isArray(_stC)) {
      const _v = String(_mk[1] || _mk[2]).toLowerCase();
      text = "Sorry, I couldn't """ + MARK + r""", so nothing was " + ({ book: 'booked', cancel: 'cancelled', move: 'moved' })[_v] + '. Could you send that again?';
      cardProbe = 'WITHDRAWN: a ' + _v + ' card no tool made';
    } else cardProbe = 'card, no intermediateSteps on input';
  }
} catch (e) {}

"""

NOTICE = ("{{ String(($('Booked For').first().json || {}).botText || '').includes('" + MARK + "') ? "
          "'YOUR LAST CARD WAS WITHDRAWN: you wrote it yourself instead of getting it from a tool, so nothing was changed. "
          "A booking card comes only from Prepare Booking or Prepare Series, a cancel card only from Prepare Cancel, a move card "
          "only from Move Booking - call that tool and send its card. Never write a card yourself, even when the same booking "
          "was shown earlier in this conversation.' : '' }}")

def main(w):
    w["name"] = "Project Jessie — v238 (card guard)"
    gp = node(w, "Guard Probe")["parameters"]
    s = gp["jsCode"]
    s = once(s, "let _prepared = false;\n", "let _prepared = false, _codeCard = false;   // v238: _codeCard = a card written below, in code\n", "_prepared")
    s = once(s, "+ '\\n\\nMove it? Reply yes or no.';\n    } else if (_nx8.length",
             "+ '\\n\\nMove it? Reply yes or no.';\n      _codeCard = true;\n    } else if (_nx8.length", "series card")
    s = once(s, "    if (_bf8.seriesNextCard && _moved8 && !/Move it\\? Reply yes or no\\.\\s*$/i.test(text))\n      text = text.trim() + '\\n\\n' + String(_bf8.seriesNextCard);",
             "    if (_bf8.seriesNextCard && _moved8 && !/Move it\\? Reply yes or no\\.\\s*$/i.test(text)) {\n      text = text.trim() + '\\n\\n' + String(_bf8.seriesNextCard); _codeCard = true; }", "next series card")
    s = once(s, "// v194: a compact list of this turn's tool calls", GUARD + "// v194: a compact list of this turn's tool calls", "guard")
    s = once(s, "return [{ json: { output: text.length ? text : fallback, claimProbe: claimProbe, toolsLog } }];",
             "if (/^WITHDRAWN/.test(cardProbe)) toolsLog = '[' + cardProbe + '] ' + toolsLog;   // v238\n"
             "return [{ json: { output: text.length ? text : fallback, claimProbe: claimProbe, cardProbe, toolsLog } }];", "return")
    gp["jsCode"] = s

    o = node(w, "Jessie AI Agent")["parameters"]["options"]
    o["systemMessage"] = once(o["systemMessage"], "{{ $('Booked For').first().json.notice }}\n",
                              "{{ $('Booked For').first().json.notice }}\n" + NOTICE + "\n", "system message")
    if "'" in NOTICE.split("? '", 1)[1].split("' : ''")[0]: raise SystemExit("apostrophe inside the notice text")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
