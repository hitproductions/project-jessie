#!/usr/bin/env node
// Offline tests for main v224 (series yes recognised; live 6 Oct 15:13 PHT): a yes to the short series card is seen as
// approving the series (seriesNotice), so the model books it instead of re-sending the card.
//   node scripts/sim-series-yes.js
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v224.json'), OM = WF('project-jessie-v223.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d))); } };
Date.now = () => Date.parse('2026-10-06T07:13:33Z');
const ME = 'U08V3CKDGJF';
const gate = (w, text, hist) => { const store = {};
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: ME, ts: '1791270813.1', channel: 'D1' } : n === 'Get Booker' ? { fields: { Name: 'Howard Luistro', Department: ['Audio Post'] } } : {} }),
    all: () => hist.map(h => ({ json: h })) });
  return new Function('$', '$getWorkflowStaticData', code(w, 'Gate Context'))($, () => store)[0].json; };
const CARD = '*ASIM KILIG / John Estrada / HL*\n*Dates (3):*\n- Friday, 8 October 2027\n- Friday, 15 October 2027\n- Friday, 22 October 2027\n*Time:* 3:00 PM – 6:00 PM\n*Room:* Studio 7\n\nBook it? Reply yes or no.';
const H = card => [{ user: ME, text: 'yes', ts: '1791270813.1' }, { bot_id: 'B1', text: card, ts: '1791270807.1' }, { user: ME, text: 'book studio 7 every friday for the next three weeks for project asim kilig 3-6pm. client john estrada for vo reecordings', ts: '1791270800.1' }];
let g = gate(M, 'yes', H(CARD));
ok(/THE SERIES IS ALREADY APPROVED/.test(g.seriesNotice), 'live 15:13: yes to the short series card -> approved', g.seriesNotice);
ok(!gate(OM, 'yes', H(CARD)).seriesNotice, '  (v223: not recognised - the card was sent again)');
ok(/THE SERIES IS ALREADY APPROVED/.test(gate(M, 'yes', H('*X / HL*\nDates: November 2, 2027, November 9, 2027\nTime: 2-4 PM\n\nConfirm to book. (yes/no)')).seriesNotice), 'the older "Dates:" / "November 2" summary still recognised');
ok(!gate(M, 'no', H(CARD)).seriesNotice, '"no" -> not approved');
ok(!gate(M, 'yes', H('*ASIM KILIG / HL*\n*Date:* Friday, 8 October 2027\n*Time:* 3:00 PM – 6:00 PM\n*Room:* Studio 7\n\nBook it? Reply yes or no.')).seriesNotice, 'a single booking card -> no series notice');
ok(!gate(M, 'yes', H('*X / HL*\n*Dates (1):*\n- Friday, 8 October 2027\n\nBook it? Reply yes or no.')).seriesNotice, 'one date -> not a series');
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
