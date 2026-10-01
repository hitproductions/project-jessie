#!/usr/bin/env node
// Offline tests for main v198 (series change fix) and v199 (v198 fixed: the first card written by code; one date per yes) - PENDING 63, decided 30 Sep: ask which date. 29 Sep 23:13 PHT:
// "make it 3pm instead" right after a 2-date series moved 9 Nov only, nothing asked. Real main execution 16685 for
// the nodes not replayed here.
//   node scripts/sim-series-change.js <main-execution.json>
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const code = (w, n) => w.nodes.find(x => x.name === n).parameters.jsCode;
const M = WF(process.env.MAIN || 'project-jessie-v201.json'), O99 = WF('project-jessie-v199.json'), O200 = WF('imported/project-jessie-v200-imported.json'), OM = WF('imported/project-jessie-v197-imported.json'), O98 = WF('imported/project-jessie-v198-imported.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, last: () => it[it.length - 1] });
const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
const ME = 'U08V3CKDGJF';
let T = 1790800000;
const U = text => ({ json: { ts: String(T++) + '.1', text, user: ME } }), B = text => ({ json: { ts: String(T++) + '.1', text, bot_id: 'B1' } });
const SUM = '*QATYPE2 / Jem Lim / DR*\n*Dates (2):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio 8\n*Session Type:* VO Recording\n*Client:* Jem Lim\n*Engineer:* Daryl Reyes\n*Booked by:* Howard Luistro\n\nBook it? Reply yes or no.';
const BOOKED = 'Booked 2 sessions:\n- November 2, 2027 (Tue)\n- November 9, 2027 (Tue)';
const ASK = 'That was a series of 2. Which date should change?\n- Tuesday, November 2\n- Tuesday, November 9\nOr say "all" to change every date.';
const CARD2 = '*QATYPE2 / Jem Lim / DR*\n*Now:* Tuesday, November 2, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.';
const NEXT9 = "_Next: QATYPE2 / Jem Lim / DR on Tuesday, November 9, 2027 - I'll show it after this one._";
// conversation, oldest first -> newest first for Get Recent Messages
const bf = (w, convo) => { const h = convo.slice().reverse();
  const $ = n => n === 'Get Recent Messages' ? wrap(h) : n === 'Slack Trigger' ? wrap([h[0]]) : wrap(rec(n) || [{ json: {} }]);
  return new Function('$', '$input', code(w, 'Booked For'))($, wrap([{ json: {} }]))[0].json; };
const base = [U('book qatype2 studio 8 every tuesday 10am-12pm nov 2 and 9, vo recording, client jem lim, engineer drey'), B(SUM), U('yes'), B(BOOKED)];

console.log('Booked For - the change right after a series');
let r = bf(M, [...base, U('make it 3pm instead')]);
ok(r.seriesAsk === ASK && !r.changeJustBooked, 'no date named -> the question, and no booking picked', r.seriesAsk || r.justBooked);
ok(/DID NOT SAY WHICH DATE/.test(r.notice || ''), 'the model is told to ask, not to move');
ok(!bf(OM, [...base, U('make it 3pm instead')]).seriesAsk, '  (v197: nothing asked - the model picked 9 Nov)');
for (const ans of ['the 9th', 'nov 9', '9 November', 'the second one', 'the last one']) {
  r = bf(M, [...base, U('make it 3pm instead'), B(ASK), U(ans)]);
  ok(r.changeJustBooked && r.justBooked.iso === '2027-11-09' && r.moveStart === '15:00' && r.moveEnd === '17:00' && !r.seriesAsk && !r.seriesQueueNext,
     '"' + ans + '" -> 9 Nov, 3-5 PM (the length kept), one card', [r.justBooked, r.moveStart, r.moveEnd]); }
r = bf(M, [...base, U('make nov 2 3pm instead')]);
ok(r.justBooked && r.justBooked.iso === '2027-11-02' && r.moveStart === '15:00' && !r.seriesAsk, 'a date in the change itself -> no question', r.justBooked);
r = bf(M, [...base, U('make it 3pm instead'), B(ASK), U('all of them')]);
ok(r.justBooked && r.justBooked.iso === '2027-11-02' && JSON.stringify(r.seriesQueueNext) === JSON.stringify([NEXT9]) && !r.seriesNextCard,
   '"all of them" -> 2 Nov first, 9 Nov queued', [r.justBooked, r.seriesQueueNext]);
r = bf(M, [...base, U('make it 3pm instead'), B(ASK), U('all of them'), B(CARD2.replace('\n\nMove it?', '\n' + NEXT9 + '\n\nMove it?')), U('yes')]);
ok(r.seriesNextCard === '*QATYPE2 / Jem Lim / DR*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.',
   'the yes to the 2 Nov card -> the 9 Nov card is ready (same new time and room)', r.seriesNextCard);
r = bf(M, [...base, U('make it 3pm instead'), B(ASK), U('both'), B(CARD2.replace('*Moving to:* Tuesday, November 2, 2027', '*Moving to:* Friday, November 5, 2027')), U('yes')]);
ok(!r.seriesNextCard, 'a date change (not a time change) is not chained', r.seriesNextCard);
r = bf(M, [...base, U('make it 3pm instead'), B(ASK), U('make it all day')]);
ok(!!r.seriesAsk, '"all day" is not "all"');
{ const S3 = SUM.replace('*Dates (2):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027', '*Dates (3):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027\n- Tuesday, 16 November 2027');
  const B3 = BOOKED.replace('2 sessions', '3 sessions') + '\n- November 16, 2027 (Tue)';
  const MOVED = 'Moved "QATYPE2 / Jem Lim / DR" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM in Studio 8.\n\n*QATYPE2 / Jem Lim / DR*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n'
    + "_Next: QATYPE2 / Jem Lim / DR on Tuesday, November 16, 2027 - I'll show it after this one._\n\nMove it? Reply yes or no.";
  r = bf(M, [U('book ...'), B(S3), U('yes'), B(B3), U('make it 3pm instead'), B('...'), U('all'), B('card'), U('yes'), B(MOVED), U('yes')]);
  ok(/THE MOVE THEY JUST APPROVED IS THE CARD AT THE END OF YOUR LAST MESSAGE: "QATYPE2 \/ Jem Lim \/ DR" on Tuesday, November 9, 2027, from 10:00 AM – 12:00 PM to 3:00 PM – 5:00 PM/.test(r.notice || ''),
     'three dates: the yes to the 9 Nov card -> the model is told that one, not the one already moved', r.notice);
  ok(/\*Now:\* Tuesday, November 16, 2027, 10:00 AM – 12:00 PM, Studio 8\n\*Moving to:\* Tuesday, November 16, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it\?/.test(r.seriesNextCard || ''), '... and the 16 Nov card is next', r.seriesNextCard); }
{ const SF = SUM.replace('- Tuesday, 9 November 2027', '- Friday, 5 November 2027'), BF = BOOKED.replace('November 9, 2027 (Tue)', 'November 5, 2027 (Fri)');
  r = bf(M, [U('book ...'), B(SF), U('yes'), B(BF), U('change the friday one to 3pm')]);
  ok(r.justBooked && r.justBooked.iso === '2027-11-05', 'a weekday only one date has ("change the friday one to 3pm") -> that date', r.justBooked); }
r = bf(M, [U('book qaone studio 8 nov 2 10am-12pm'), B('*QAONE / DR*\n*Date:* Tuesday, November 2, 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.'), U('yes'), B('Booked.'), U('make it 3pm instead')]);
ok(r.changeJustBooked && r.justBooked.iso === '2027-11-02' && r.moveStart === '15:00' && !r.seriesAsk && !r.seriesQueueNext, 'a single booking -> unchanged (move of that booking)', r.justBooked);

console.log('Guard Probe - what is sent');
const g16685 = (rec('Guard Probe') || [{ json: {} }])[0].json;
const gp = (w, bfOut, steps, output) => new Function('$input', '$', code(w, 'Guard Probe'))(
  wrap([{ json: { ...g16685, output, intermediateSteps: steps } }]), n => n === 'Booked For' ? wrap([{ json: bfOut }]) : wrap(rec(n) || [{ json: {} }]))[0].json.output;
const mv = (o, ti = {}) => [{ action: { tool: 'Move_Booking', toolInput: ti }, observation: JSON.stringify([o]) }];
let o = gp(M, { seriesAsk: ASK }, mv({ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: CARD2.replace('Move it? Reply yes or no.', 'Confirm to move.') }), 'x');
ok(o === ASK, 'the question replaces a move card the model prepared for one date', o);
o = gp(M, { seriesQueueNext: [NEXT9] }, mv({ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: CARD2.replace('Move it? Reply yes or no.', 'Confirm to move.') }), 'x');
ok(o === CARD2.replace('\n\nMove it?', '\n' + NEXT9 + '\n\nMove it?'), 'the first card carries the "_Next:" line, confirmation last', o);
const NC = '*QATYPE2 / Jem Lim / DR*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.';
o = gp(M, { seriesNextCard: NC }, mv({ status: 'MOVED', human: 'Moved' }), 'Moved "QATYPE2 / Jem Lim / DR" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM in Studio 8.');
ok(/^Moved "QATYPE2/.test(o) && o.endsWith('\n\n' + NC), 'the move went through -> "Moved ..." then the 9 Nov card', o);
o = gp(M, { seriesNextCard: NC }, mv({ status: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'taken' }), 'Studio 8 is taken then.');
ok(o.indexOf('*Now:* Tuesday, November 9') === -1, 'the move did not go through -> no next card', o);
ok(gp(M, {}, mv({ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: CARD2.replace('Move it? Reply yes or no.', 'Confirm to move.') }), 'x') === CARD2, 'no series -> the card as before');

console.log('Gate Context - the yes to a card that went out with "Moved ..."');
{ const src = code(M, 'Gate Context');
  const last = 'Moved "QATYPE2 / Jem Lim / DR" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM in Studio 8.\n\n' + NC;
  const hist = [{ text: 'yes', user: ME, ts: '1790900002.1' }, { text: last, bot_id: 'B1', ts: '1790900001.1' }];
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? hist[0] : n === 'Get Booker' ? { fields: { Name: 'Howard Luistro' } } : {} }), all: () => hist.map(j => ({ json: j })) });
  const g = new Function('$', '$getWorkflowStaticData', src)($, () => ({}))[0].json;
  ok(/THE MOVE IS ALREADY APPROVED/.test(g.moveNotice || ''), 'the next card is approved by its own yes (the confirmation is last)', g.moveNotice); }

console.log('v199 - the live QASER test (30 Sep 16:38): "all" -> the model carded 9 Nov; one yes moved both');
{ const QS = SUM.replace(/QATYPE2 \/ Jem Lim \/ DR/g, 'QASER / HL'), QB = BOOKED;
  const conv = [U('book qaser ...'), B(QS), U('yes'), B(QB), U('make it 3pm instead'), B(ASK), U('all')];
  const card9 = '*QASER / HL*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nConfirm to move.';
  const steps9 = mv({ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: card9 });
  const want = '*QASER / HL*\n*Now:* Tuesday, November 2, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n'
    + "_Next: QASER / HL on Tuesday, November 9, 2027 - I'll show it after this one._\n\nMove it? Reply yes or no.";
  let b = bf(M, conv), o2 = gp(M, b, steps9, 'x');
  ok(o2 === want, 'the model carded 9 Nov -> the 2 Nov card is sent, written by code, with 9 Nov next', o2);
  const b98 = bf(O98, conv), o98 = gp(O98, b98, steps9, 'x');
  ok(/\*Now:\* Tuesday, November 9[\s\S]*_Next: QASER \/ HL on Tuesday, November 9/.test(o98), '  (v198: the 9 Nov card with "Next: ... November 9" - the wrong note)');
  b = bf(M, [...conv, B(want), U('yes')]);
  ok(/THE MOVE THEY JUST APPROVED IS THE CARD IN YOUR LAST MESSAGE ONLY: "QASER \/ HL" on Tuesday, November 2, 2027\. Call Move Booking ONCE/.test(b.notice || ''), 'the yes -> the model is told: 2 Nov only, once', b.notice);
  ok(/\*Now:\* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n\*Moving to:\* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it\?/.test(b.seriesNextCard || ''), '... and the 9 Nov card follows the move', b.seriesNextCard);
  ok(!/APPROVED IS THE CARD IN YOUR LAST MESSAGE ONLY/.test(bf(O98, [...conv, B(want), U('yes')]).notice || ''), '  (v198: nothing said - it moved both)');
  b = bf(M, [...conv.slice(0, 6), U('the 9th')]); o2 = gp(M, b, mv({ status: 'REJECTED', reason: 'NOT_CONFIRMED', card_text: card9.replace(/November 9/g, 'November 2') }), 'x');
  ok(/^\*QASER \/ HL\*\n\*Now:\* Tuesday, November 9, 2027/.test(o2) && !/_Next:/.test(o2), 'one date picked ("the 9th") -> that date\'s card, even if the model carded another', o2); }

console.log('v200 - the yes moves what the card showed (live 30 Sep 16:56: one yes moved both dates on v199)');
{ const QS = SUM.replace(/QATYPE2 \/ Jem Lim \/ DR/g, 'QASER / HL');
  const card2 = '*QASER / HL*\n*Now:* Tuesday, November 2, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8\n'
    + "_Next: QASER / HL on Tuesday, November 9, 2027 - I'll show it after this one._\n\nMove it? Reply yes or no.";
  const conv = [U('book qaser ...'), B(QS), U('yes'), B(BOOKED), U('make it 3pm instead'), B(ASK), U('all'), B(card2), U('yes')];
  const b = bf(M, conv);
  ok(JSON.stringify(b.approvedMove) === JSON.stringify({ title: 'QASER / HL', booking_date: '2027-11-02', new_start_iso: '2027-11-02T15:00:00+08:00', new_end_iso: '2027-11-02T17:00:00+08:00', new_rooms: '',
     ...(b.approvedMove && 'to_line' in b.approvedMove ? { to_line: 'Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 8' } : {}), date_label: 'Tuesday, November 2, 2027', to_label: '3:00 PM – 5:00 PM' }), 'the yes -> approvedMove = the card: 2 Nov, 3-5 PM, same room', b.approvedMove);
  // the Move Booking tool inputs, as n8n would evaluate them, for the model's SECOND call (9 Nov)
  const V = M.nodes.find(n => n.name === 'Move Booking').parameters.workflowInputs.value;
  const evalIn = (k, fromAI) => new Function('$', '$fromAI', 'return ' + V[k].replace(/^=\{\{ /, '').replace(/ \}\}$/, ''))(
    n => ({ first: () => ({ json: n === 'Booked For' ? b : n === 'Gate Context' ? { confirmedMove: true } : {} }) }), () => fromAI);
  const second = { title: 'QASER / HL', booking_date: '2027-11-09', new_start_iso: '2027-11-09T15:00:00+08:00', new_end_iso: '2027-11-09T17:00:00+08:00', new_rooms: '' };
  ok(['title', 'booking_date', 'new_start_iso', 'new_end_iso'].every(k => evalIn(k, second[k]) === b.approvedMove[k]), 'the model asks to move 9 Nov too -> Move Booking still gets 2 Nov (the card)',
     ['booking_date', 'new_start_iso'].map(k => evalIn(k, second[k])));
  ok(evalIn('new_rooms', 'Studio 7') === '', 'a room the card did not show is not used');
  const bNo = { ...b };
  const evalNo = (k, v) => new Function('$', '$fromAI', 'return ' + V[k].replace(/^=\{\{ /, '').replace(/ \}\}$/, ''))(
    n => ({ first: () => ({ json: n === 'Booked For' ? bNo : n === 'Gate Context' ? { confirmedMove: false } : {} }) }), () => v);
  ok(evalNo('booking_date', '2027-11-09') === '2027-11-09', 'not an approved move (no yes to a card) -> the model\'s value, as before');
  ok(!bf(O99, conv).approvedMove, '  (v199: nothing fixed the inputs - it moved both)');
  const NC = b.seriesNextCard;
  const o3 = gp(M, b, mv({ status: 'MOVED', title: 'QASER / HL' }), 'Moved both sessions to 3:00 PM – 5:00 PM:\n- November 2, 2027 (Tue)\n- November 9, 2027 (Tue)');
  ok(o3 === 'Moved "QASER / HL" on Tuesday, November 2, 2027 to 3:00 PM – 5:00 PM.\n\n' + NC, 'the reply: code-written "Moved ... on 2 Nov" then the 9 Nov card - not "Moved both sessions"', o3);
  ok(/\*Now:\* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM/.test(NC), '  the 9 Nov card shows where 9 Nov really is (it did not move)');
  const b2 = bf(M, [...conv.slice(0, -1), U('yes'), B('Moved "QASER / HL" on Tuesday, November 2, 2027 to 3:00 PM – 5:00 PM.\n\n' + NC), U('yes')]);
  ok(b2.approvedMove && b2.approvedMove.booking_date === '2027-11-09' && b2.approvedMove.new_start_iso === '2027-11-09T15:00:00+08:00', 'the next yes -> the 9 Nov card is the move', b2.approvedMove);
  const single = bf(M, [U('book qaone ...'), B('*QAONE / DR*\n*Date:* Tuesday, November 2, 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no.'), U('yes'), B('Booked.'), U('move it to studio 7 at 3pm'),
    B('*QAONE / DR*\n*Now:* Tuesday, November 2, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 2, 2027, 3:00 PM – 5:00 PM, Studio 7\n\nMove it? Reply yes or no.'), U('yes')]);
  ok(single.approvedMove && single.approvedMove.new_rooms === 'Studio 7' && single.approvedMove.booking_date === '2027-11-02', 'any move card (not only a series): the yes moves what it showed, a new room included', single.approvedMove); }

console.log('v201 - the yes to the next card, and the series summary engineer (live 30 Sep 17:04-17:07)');
{ const pc = (w, lastBot) => { const hist = [{ text: 'yes', user: ME, ts: '1790900003.1' }, { text: lastBot, bot_id: 'B1', ts: '1790900002.1' }];
    const $ = n => ({ first: () => ({ json: n === 'Gate Context' ? { gate: { saidYes: true }, confirmedCancel: false } : n === 'Slack Trigger' ? hist[0] : {} }), all: () => (n === 'Get Recent Messages' ? hist : []).map(j => ({ json: j })) });
    return new Function('$', '$input', code(w, 'Prepared Cancel'))($, wrap([{ json: {} }]))[0].json._alreadyDone; };
  const movedCard = 'Moved "QASER / HL" on Tuesday, November 2, 2027 to 3:00 PM – 5:00 PM.\n\n*QASER / HL*\n*Now:* Tuesday, November 9, 2027, 10:00 AM – 12:00 PM, Studio 8\n*Moving to:* Tuesday, November 9, 2027, 3:00 PM – 5:00 PM, Studio 8\n\nMove it? Reply yes or no.';
  ok(pc(M, movedCard) === '', '"Moved ..." with the next card after it -> the yes goes on (it is that card\'s yes)', pc(M, movedCard));
  ok(pc(O200, movedCard) === "That's already moved - nothing else was changed.", "  (v200: \"That's already moved\" - 9 Nov never moved)");
  ok(pc(M, 'Moved "QASER / HL" to Tuesday, November 2, 2027, 3:00 PM – 5:00 PM in Studio 8.') === "That's already moved - nothing else was changed.", 'a plain "Moved ..." then yes -> still "already moved"');
  ok(pc(M, 'Booked.') === "That's already booked - nothing else was changed.", 'a plain "Booked." then yes -> still "already booked"');
  const ser = '*QASER / HL*\n*Dates (2):*\n- Tuesday, 2 November 2027\n- Tuesday, 9 November 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio 8\n*Session Type:* VO Recording\n*Client:* None\n*Engineer:* Howard\n*Booked by:* Howard Luistro\n\nBook it? Reply yes or no.';
  const out = gp(M, {}, [], ser);
  ok(/\*Engineer:\* Howard Luistro\n/.test(out), 'series summary "Engineer: Howard" -> "Howard Luistro" (one person in Bookers)', out.split('\n').filter(l => /Engineer/.test(l)));
  ok(/\*Engineer:\* Howard\n/.test(gp(O200, {}, [], ser)), '  (v200: "Howard")');
  ok(/\*Engineer:\* Drey\b|\*Engineer:\* Daryl Reyes/.test(gp(M, {}, [], ser.replace('*Engineer:* Howard', '*Engineer:* Drey'))) , 'a nickname ("Drey") -> resolved or left, never guessed');
  ok(/\*Engineer:\* Nobody Here/.test(gp(M, {}, [], ser.replace('*Engineer:* Howard', '*Engineer:* Nobody Here'))), 'a name nobody on staff has -> left as it is'); }

console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
