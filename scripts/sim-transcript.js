#!/usr/bin/env node
// sim-transcript (main v243, PENDING 99): runs Build Transcript from a main build against made-up Slack histories and
// checks the transcript the agent gets - nothing recent missed, nothing from before a reset or before today, cards as
// summaries, the "Sent using" footer dropped, the current message left out. Offline; reads the file only.
//   node scripts/sim-transcript.js [workflows/project-jessie-vN.json]   (default: the newest main build)
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', 'workflows');
const file = process.argv[2] || path.join(dir, fs.readdirSync(dir).filter(f => /^project-jessie-v\d+\.json$/.test(f))
  .sort((a, b) => +a.match(/\d+/)[0] - +b.match(/\d+/)[0]).pop());
const wf = JSON.parse(fs.readFileSync(file, 'utf8'));
const node = wf.nodes.find(n => n.name === 'Build Transcript');
if (!node) { console.log('Build Transcript is not in ' + path.basename(file)); process.exit(1); }
const code = node.parameters.jsCode;

const now = Date.now() / 1000;
const ts = secAgo => (now - secAgo).toFixed(6);
const BOT = { bot_id: 'B0BTVF2HTPC' };
const run = ({ history, recent = [], trigger, epoch = '', bookedFor = { bookedFor: '' }, throwHistory = false }) => {
  const $ = name => {
    const items = {
      'Get Transcript': throwHistory ? null : history.map(json => ({ json })),
      'Get Recent Messages': recent.map(json => ({ json })),
      'Slack Trigger': [{ json: { ts: trigger, text: 'x' } }],
      'Gate Context': [{ json: { epoch } }],
      'Booked For': [{ json: bookedFor }],
    }[name];
    if (!items) throw new Error('no node ' + name);
    return { all: () => items, first: () => items[0] };
  };
  return new Function('$', code)($)[0].json;
};
let pass = 0, fail = 0;
const check = (label, ok, got) => { ok ? pass++ : fail++; console.log((ok ? '  ok    ' : '  FAIL  ') + label + (ok ? '' : '  ::  ' + JSON.stringify(got).slice(0, 300))); };

// a normal run: request, card, yes, Booked., availability question and answer; then the new message
const trig = ts(0);
const H = [
  { ts: trig, user: 'U1', text: 'move it to 3pm\n*Sent using* <@U0AVDBNH1K4|Claude>' },
  { ts: ts(20), ...BOT, text: 'Studio 7 is taken 10:00 AM – 11:00 AM by *QATEST / Jem Lim / HL*. Free the rest of the day.' },
  { ts: ts(40), user: 'U1', text: 'is studio 7 free on december 14 2027?' },
  { ts: ts(60), ...BOT, text: 'Booked.' },
  { ts: ts(80), user: 'U1', text: 'yes\n*Sent using* <@U0AVDBNH1K4|Claude>' },
  { ts: ts(100), ...BOT, text: '*QATEST / Jem Lim / HL*\n*Date:* Tuesday, December 14, 2027\n*Time:* 10:00 AM – 11:00 AM\n*Room:* Studio 7\n\nBook it? Reply yes or no.' },
  { ts: ts(120), user: 'U1', text: 'book studio 7 on december 14 2027 from 10am to 11am for a VO recording, project QATEST, client Jem Lim' },
];
let r = run({ history: H, trigger: trig });
const L = r.transcript.split('\n');
check('every earlier message is there, oldest first (6 lines)', L.length === 6 && r.transcriptLines === 6, L);
check('the requester\'s words are exact', L[0] === 'Requester: book studio 7 on december 14 2027 from 10am to 11am for a VO recording, project QATEST, client Jem Lim', L[0]);
check('a card is one summary line', L[1] === 'Jessie showed a booking card (waiting for yes or no): QATEST / Jem Lim / HL | Date: Tuesday, December 14, 2027 | Time: 10:00 AM – 11:00 AM | Room: Studio 7', L[1]);
check('the "Sent using" footer is dropped', L[2] === 'Requester: yes', L[2]);
check('a reply sent from code ("Booked.") is there', L[3] === 'Jessie: Booked.', L[3]);
check('the last answer before the new message is there', /^Jessie: Studio 7 is taken 10:00 AM – 11:00 AM by QATEST \/ Jem Lim \/ HL\. Free the rest of the day\.$/.test(L[5]), L[5]);
check('the new message itself is not in it', !/move it to 3pm/.test(r.transcript), r.transcript);
check('Booked For\'s fields pass through', r.bookedFor === '' && r.transcriptSource === 'Get Transcript', r);

// reset: nothing at or before it
const resetTs = ts(70);
r = run({ history: [...H, { ts: resetTs, user: 'U1', text: 'reset' }], trigger: trig, epoch: resetTs });
check('nothing from before a reset', r.transcript.split('\n').length === 3 && !/book studio 7/.test(r.transcript) && !/^Requester: reset/m.test(r.transcript), r.transcript);
check('...and what came after it is all there', /^Jessie: Booked\.$/m.test(r.transcript) && /is studio 7 free/.test(r.transcript), r.transcript);

// yesterday is left out
r = run({ history: [{ ts: trig, user: 'U1', text: 'hi' }, { ts: ts(36 * 3600), user: 'U1', text: 'cancel OLDJOB' }, { ts: ts(30), ...BOT, text: 'Hi Howard! What do you need?' }], trigger: trig });
check('a message from an earlier day is left out', !/OLDJOB/.test(r.transcript) && /Hi Howard/.test(r.transcript), r.transcript);

// cards of every kind, the withdrawal sentence, a cancel card
r = run({ trigger: trig, history: [
  { ts: ts(10), ...BOT, text: "Sorry, I couldn't check that against the calendar just now, so nothing was cancelled. Could you send that again?" },
  { ts: ts(20), ...BOT, text: '*QS / Jem Lim / HL*\n*Dates (2):*\n- Tuesday, 7 December 2027\n- Tuesday, 14 December 2027\n*Time:* 1:00 PM – 2:00 PM\n\nBook it? Reply yes or no.' },
  { ts: ts(30), ...BOT, text: '*QATEST / Jem Lim / HL*\n*Now:* Tuesday, December 14, 2027, 10:00 AM – 11:00 AM, Studio 7\n*Moving to:* Tuesday, December 14, 2027, 2:00 PM – 3:00 PM, Studio 7\n\nMove it? Reply yes or no.' },
  { ts: ts(40), ...BOT, text: '*QATEST / Jem Lim / HL*\n*Date:* Tuesday, December 14, 2027\n*Time:* 2:00 PM – 3:00 PM\n*Room:* Studio 7\n\nCancel it? Reply yes or no.' },
]});
const C = r.transcript.split('\n');
check('a cancel card is a cancel summary', /^Jessie showed a cancel card \(waiting for yes or no\): QATEST \/ Jem Lim \/ HL \| Date: Tuesday, December 14, 2027 \| Time: 2:00 PM – 3:00 PM/.test(C[0]), C[0]);
check('a move card keeps both times', /^Jessie showed a move card .*Now: Tuesday, December 14, 2027, 10:00 AM – 11:00 AM, Studio 7 \| Moving to: .*2:00 PM – 3:00 PM/.test(C[1]), C[1]);
check('a series card is a series summary with its dates', /^Jessie showed a series booking card .*- Tuesday, 7 December 2027 \| - Tuesday, 14 December 2027/.test(C[2]), C[2]);
check('a withdrawn card reads as nothing done', C[3] === 'Jessie said she could not check it against the calendar, so nothing was done.', C[3]);

// at most 20 lines, the newest kept
const many = []; for (let i = 1; i <= 30; i++) many.push({ ts: ts(i * 10), user: 'U1', text: 'msg ' + i });
r = run({ history: many, trigger: trig });
const M = r.transcript.split('\n');
check('at most 20 lines, the newest kept', M.length === 20 && M[19] === 'Requester: msg 1' && M[0] === 'Requester: msg 20', [M.length, M[0], M[19]]);

// a failed fetch falls back to Get Recent Messages; nothing at all is an empty transcript, never an error
r = run({ history: [], recent: [{ ts: ts(10), user: 'U1', text: 'from the 12' }], trigger: trig });
check('Get Transcript empty -> Get Recent Messages', r.transcript === 'Requester: from the 12' && r.transcriptSource === 'Get Recent Messages', r);
r = run({ history: [], recent: [], trigger: trig });
check('no history: an empty transcript', r.transcript === '' && r.transcriptLines === 0, r);
r = run({ history: [], recent: [], trigger: trig, throwHistory: true });
check('a node that cannot be read never throws', r.transcript === '', r);

// the wiring: Booked For -> Get Transcript -> Build Transcript -> Prepared Key, no memory on the agent
const c = wf.connections;
check('wiring: Booked For -> Get Transcript -> Build Transcript -> Prepared Key',
  c['Booked For'].main[0][0].node === 'Get Transcript' && c['Get Transcript'].main[0][0].node === 'Build Transcript' && c['Build Transcript'].main[0][0].node === 'Prepared Key', null);
check('no memory node is connected to the agent', !Object.values(c).some(o => o.ai_memory), null);
const gt = wf.nodes.find(n => n.name === 'Get Transcript');
check('Get Transcript reads 25 messages, once, and never stops the turn', gt.parameters.limit === 25 && gt.executeOnce && gt.alwaysOutputData && gt.onError === 'continueRegularOutput', gt);
const ag = wf.nodes.find(n => n.name === 'Jessie AI Agent').parameters;
check('the agent prompt is the transcript, then the new message', /Build Transcript/.test(ag.text) && /\$\('Slack Trigger'\)\.first\(\)\.json\.text \}\}$/.test(ag.text), ag.text);

console.log(`\n${pass} passing, ${fail} failing  (${path.basename(file)})`);
process.exit(fail ? 1 : 0);
