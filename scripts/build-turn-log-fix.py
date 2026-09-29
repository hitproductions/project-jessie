#!/usr/bin/env python3
"""main v194 (v193 fixed) - the Turn Log wrote Slack's raw reply receipt instead of its row (29 Sep 23:15 PHT).
  scripts/build-turn-log-fix.py <main-live> <main-out>

v193's Turn Log Row failed on every turn with n8n's "Unknown error" (the code runner giving up - the gotcha 11 signature)
and, set to continue on error, passed Send Reply's output through to the sheet. Two things in it no other node does:
a node looked up by a variable name (`$(n)` - n8n decides which nodes' data to hand the runner from the literal names in
the code), and a direct read of the AI Agent node. Now:
- Guard Probe, which already receives the agent's tool steps as its input, returns a compact `toolsLog` with its reply.
- Turn Log Row reads only literal names on the main path: Slack Trigger, Get Booker, Guard Probe, Book Direct,
  Cancel Direct, Already Done Reply - each in its own try.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

GP_OLD = "return [{ json: { output: text.length ? text : fallback, claimProbe: claimProbe } }];"
GP_NEW = r"""// v194: a compact list of this turn's tool calls, for the Turn Log (Turn Log Row cannot read the agent itself).
let toolsLog = '';
try {
  const _cl = (s, n) => { s = String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n) + '...' : s; };
  const _K = ['title', 'booking_date', 'start', 'end', 'new_start', 'new_end', 'rooms', 'window_start', 'window_end', 'window_room', 'engineer', 'client', 'summary'];
  toolsLog = _cl(((($input.first().json || {}).intermediateSteps) || []).map(s => {
    const a = (s && s.action) || {}, ti = a.toolInput || {};
    let o = null; try { o = [].concat(JSON.parse(String(s.observation || '')))[0]; } catch (e) {}
    return (a.tool || '?') + '(' + _K.filter(k => ti[k] !== undefined && ti[k] !== '').map(k => k + '=' + _cl(ti[k], 60)).join(', ') + ') -> '
      + (o ? [o.status || o.verdict || '', o.reason || ''].filter(Boolean).join(' ') : _cl(s.observation, 60));
  }).join(' | '), 6000);
} catch (e) { toolsLog = '(tools log error: ' + e.message + ')'; }
return [{ json: { output: text.length ? text : fallback, claimProbe: claimProbe, toolsLog } }];"""

TURN_ROW = r"""// Turn Log Row (main v194). From 29 Sep nobody's scripts read n8n's executions, so each turn leaves one row in the
// Jessie Log sheet's "Turn Log" tab. v193 failed on every turn ("Unknown error") - it looked nodes up by a variable name
// and read the AI Agent directly. Now: only literal node names on the main path, each in its own try; the tool calls come
// from Guard Probe's toolsLog. Never throws: a failure only means a missing log row.
const clip = (s, n) => { s = String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n) + '...' : s; };
const row = { Time: '', Exec: '', User: '', Message: '', Path: '', Tools: '', Reply: '', Claim: '', Seconds: '', Build: '' };
try {
  row.Time = new Date().toLocaleString('en-CA', { timeZone: 'Asia/Manila', hour12: false }).replace(',', '');
  try { row.Exec = String($execution.id || ''); } catch (e) {}
  try { row.Build = String($workflow.name || ''); } catch (e) {}
  let t = {}; try { t = $('Slack Trigger').first().json || {}; } catch (e) {}
  row.User = String(t.user || '');
  try { row.User = ((($('Get Booker').first() || {}).json || {}).fields || {}).Name || row.User; } catch (e) {}
  row.Message = clip(t.text, 1000);
  const inp = ($input.first() || {}).json || {};
  let gp = null, bd = null, cd = null, ad = null;
  try { gp = $('Guard Probe').first().json || null; } catch (e) {}
  try { bd = $('Book Direct').first().json || null; } catch (e) {}
  try { cd = $('Cancel Direct').first().json || null; } catch (e) {}
  try { ad = $('Already Done Reply').first().json || null; } catch (e) {}
  row.Path = inp._dup ? 'duplicate dropped' : bd ? 'book direct' : cd ? 'cancel direct' : ad ? 'already done' : 'agent';
  const res = r => r ? [r.status || r.verdict || '', r.reason || ''].filter(Boolean).join(' ') : '';
  row.Tools = bd ? 'Book Direct -> ' + res(bd) : cd ? 'Cancel Direct -> ' + res(cd) : clip((gp && gp.toolsLog) || '', 6000);
  row.Claim = String((gp && gp.claimProbe) || '');
  row.Reply = inp._dup ? '(nothing sent: a late copy of a message already answered)' : clip((inp.message && inp.message.text) || inp.text || '', 1500);
  const ts = parseFloat(String(t.ts || '0')) || 0;
  if (ts) row.Seconds = ((Date.now() / 1000) - ts).toFixed(1);
} catch (e) { row.Reply = row.Reply || ('(log error: ' + e.message + ')'); }
return [{ json: row }];
"""

def main_fix(w):
    w["name"] = "Project Jessie — v194 (v193 fixed)"
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_OLD, GP_NEW, "guard")
    node(w, "Turn Log Row")["parameters"]["jsCode"] = TURN_ROW
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
