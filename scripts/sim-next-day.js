#!/usr/bin/env node
// sim-next-day (main v255, PENDING 107, decided 9 Oct): "next <day>" is that day of next week, except when today is later in
// the week (Mon-Sun) than the day named - then the coming one + 7. "next next <day>" / "<day> after next" one week more.
//   node scripts/sim-next-day.js workflows/project-jessie-vN.json
const fs=require('fs');const w=JSON.parse(fs.readFileSync(process.argv[2]));const src=w.nodes.find(n=>n.name==='Gate Context').parameters.jsCode;
const run=(now,text)=>{Date.now=()=>Date.parse(now);const $=name=>({first:()=>({json:name==='Slack Trigger'?{text,user:'U1',ts:'1791900000.1',channel:'D1'}:name==='Get Booker'?{fields:{Name:'Howard Luistro'}}:{}}),all:()=>[]});
 const j=new Function('$','$input','$getWorkflowStaticData',src)($,{first:()=>({json:{}}),all:()=>[]},()=>({}))[0].json; return j.datesInMessage;};
// Jessie's dates are +1 year; 2026-10-09 is Fri -> 2027-10-09 Sat
const cases=[['2026-10-09T03:00:00Z','book studio 7 next thurs','2027-10-21'],['2026-10-09T03:00:00Z','next next thursday i mean','2027-10-28'],
['2026-10-09T03:00:00Z','thursday after next','2027-10-28'],['2026-10-09T03:00:00Z','book thursday','2027-10-14'],['2026-10-09T03:00:00Z','book next sunday','2027-10-17'],
['2026-10-09T03:00:00Z','book next monday','2027-10-18'],['2026-10-04T03:00:00Z','book next thursday','2027-10-14'],['2026-10-06T03:00:00Z','next thursday','2027-10-14'],['2026-10-05T03:00:00Z','the following thursday','2027-10-21'],['2026-10-09T03:00:00Z','friday next week','2027-10-15'],['2026-10-09T03:00:00Z','this thursday','2027-10-07']];
for (const [n,t,want] of cases){const got=run(n,t);console.log((got===want?'ok  ':'FAIL')+'  '+n.slice(0,10)+' '+JSON.stringify(t)+' -> '+got+' (want '+want+')');if(got!==want)process.exitCode=1;}
