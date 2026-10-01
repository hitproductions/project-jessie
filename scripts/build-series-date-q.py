#!/usr/bin/env python3
"""main v206 (series date question) - fixes v164's added date question on a recurring booking: live Slack E2E
1 Oct 14:31 (exec 20295). "book qaseries every monday in november 2027 2-4pm ..." -> the model called Expand Series
(OK) and asked only for the client; Guard Probe added "And which day is it for?" because Gate Context names no date
for a recurring request. The question is now skipped when this turn's Expand Series answered OK, or when the
requester's words describe a repeat (every / each <day>, weekly, daily, "Mondays").
Also: the Turn Log's Tools column shows Expand Series' inputs (it showed "Expand_Series()").
  scripts/build-series-date-q.py <main-live> <main-out>
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = "  if (_asks && _booking && _noDate && _aboutBooking && !/\\b(date|day|when|which day)\\b/i.test(text)) text = text.trim() + '\\nAnd which day is it for?';"
NEW = r"""  // v206 (live 1 Oct 14:31): a recurring booking names its dates as a pattern, which Gate Context does not count -
  // "every monday in november 2027" was asked "And which day is it for?". Not for a series (Expand Series answered OK
  // this turn, or the requester's words describe a repeat).
  let _series = /\b(every|each)\s+(day|week|weekday|mon|tue|wed|thu|fri|sat|sun)[a-z]*\b|\b(weekly|daily|fortnightly|bi-?weekly)\b|\b(mon|tues|wednes|thurs|fri|satur|sun)days\b/i.test(_rt);
  try { for (const s of (($input.first().json || {}).intermediateSteps || [])) {
    if (String(((s || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase() !== 'expand series') continue;
    let o = null; try { o = [].concat(JSON.parse(String(s.observation || '')))[0]; } catch (e) {}
    if (o && o.status === 'OK') _series = true;
  } } catch (e) {}
  if (_asks && _booking && _noDate && _aboutBooking && !_series && !/\b(date|day|when|which day)\b/i.test(text)) text = text.trim() + '\nAnd which day is it for?';"""

K_OLD = "'window_start', 'window_end', 'window_room', 'engineer', 'client', 'summary'];"
K_NEW = "'window_start', 'window_end', 'window_room', 'engineer', 'client', 'summary', 'recur_frequency', 'recur_days', 'recur_start', 'recur_count', 'recur_until', 'recur_time_start', 'recur_time_end'];   // v206: series inputs too"

def main(w):
    w["name"] = "Project Jessie — v206 (series date question)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], OLD, NEW, "gp date q")
    gp["jsCode"] = sub1(gp["jsCode"], K_OLD, K_NEW, "gp tools log")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
