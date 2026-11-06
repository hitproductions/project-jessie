#!/usr/bin/env node
// Jessie — Say Hi v1 (6 Nov, Howard: Jessie DMs Ms. Letty the greeting so the app is easy to find on a phone).
//   node scripts/sim-say-hi.js [say-hi] [main] [slack-interactions]
const fs = require('fs');
const W = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const HI = W(process.argv[2] || 'workflows/say-hi-v1.json');
const MAIN = W(process.argv[3] || 'workflows/imported/project-jessie-v291-imported.json');
const SI = W(process.argv[4] || 'workflows/imported/slack-interactions-v75-imported.json');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const run = (wf, name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(wf, name).parameters.jsCode + '\n})();')(
  n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }), { first: () => input[0], all: () => input });
(async () => {
  const who = await run(HI, 'Who', [], {});
  ok(who.length === 1 && who[0].json.channel === 'U026JML76' && who[0].json.name === 'Letty', 'Who: one message, to Letty (U026JML76)', who.map(x => x.json.channel));
  // main's greeting, as Menu Check writes it for a first "hi"
  const mc = node(MAIN, 'Menu Check').parameters.jsCode;
  const head = mc.slice(mc.indexOf("const blocks = ["), mc.indexOf("];", mc.indexOf("const blocks = [")) + 2);
  const mainBlocks = new Function("const head = 'Hi, I’m Jessie!';\n" + head + '\nreturn blocks;')();
  ok(JSON.stringify(who[0].json.blocks) === JSON.stringify(mainBlocks), 'the same greeting and buttons as main sends ("Hi, I’m Jessie!", Book a room / My bookings)', who[0].json.blocks);
  const send = node(HI, 'Send Hi');
  const body = JSON.parse(new Function('$json', 'return (' + send.parameters.jsonBody.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(who[0].json));
  ok(send.parameters.url === 'https://slack.com/api/chat.postMessage' && body.channel === 'U026JML76' && body.text === 'Hi, I’m Jessie!' && body.blocks.length === 2, 'Send Hi: chat.postMessage to her member id (opens the DM with Jessie)', body);
  const remind = W('workflows/imported/reminders-v10-imported.json').nodes.find(n => n.name === 'Send Reminder');
  ok(JSON.stringify(send.credentials) === JSON.stringify(remind.credentials) && send.onError === 'continueRegularOutput', 'posted with the credential Reminders uses (Jessie Slack (signed)); a refusal reaches Report', send.credentials);
  const cs = node(SI, 'Check Signature').parameters.jsCode;
  ok(/'open_book'/.test(cs) && /'my_bookings'/.test(cs), 'Slack Interactions routes both buttons (open_book / my_bookings)');
  ok(!HI.nodes.some(n => /webhook|scheduleTrigger|slackTrigger/i.test(n.type)) && HI.active === false, 'run by hand only: no webhook, no schedule, not published');
  // two people, a duplicate, a bad id
  const two = node(HI, 'Who').parameters.jsCode.replace("['U026JML76', 'Letty'],", "['U026JML76', 'Letty'], ['U08V3CKDGJF', 'Howard'], ['U026JML76', 'Letty again'],");
  const r2 = await new Function('return (async function(){' + two + '\n})();')();
  ok(r2.map(x => x.json.channel).join() === 'U026JML76,U08V3CKDGJF', 'a longer list: each person once (a repeat is dropped)');
  let threw = '';
  try { await new Function('return (async function(){' + node(HI, 'Who').parameters.jsCode.replace("'U026JML76'", "'letty'") + '\n})();')(); } catch (e) { threw = e.message; }
  ok(/Not a Slack member id/.test(threw), 'a name instead of an id stops the run before anything is sent', threw);
  const rep = await run(HI, 'Report', [{ json: { ok: true, channel: 'D0LETTY' } }, { json: { ok: false, error: 'user_not_found' } }], { Who: r2 });
  ok(rep[0].json.sent === true && rep[0].json.dm === 'D0LETTY' && rep[1].json.sent === false && rep[1].json.error === 'user_not_found' && rep[1].json.name === 'Howard', 'Report: sent / not sent and why, per person', rep.map(x => x.json));
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
