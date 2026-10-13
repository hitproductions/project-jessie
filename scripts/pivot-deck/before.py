"""The "now" side of the pivot deck: real replies from the 13 Oct 2026 wide test (Jessie's DM, main v261 on Claude
Haiku 5.5, test dates a year ahead). Client and staff names, and other bookings' titles, are replaced; nothing else is changed. r = requester,
j = Jessie."""

B = {}

B["loop"] = [
    ("r", "book studio 6 next monday"),
    ("j", "What's the session type, project and client? (or \"none\" for no client)"),
    ("r", "actually make it studio 8, 1-3pm"),
    ("j", "I need the session type, project title and client (or \"none\") to prepare the Studio 8 booking for Monday, October 25, 1:00–3:00 PM."),
    ("r", "music mixing, project QAW7"),
    ("j", "🗓️ Studio 8 · Monday, October 25 · 1:00 PM – 3:00 PM\n\nWho’s the client? (or \"none\")"),
    ("r", "wait, make it post mixing. client is [client]"),
    ("j", "Which kind of mixing - Post Mixing, Localization Mixing, Localization Atmos Mixing or Music Mixing?"),
    ("r", "post mixing"),
    ("j", "Which kind of mixing - Post Mixing, Localization Mixing, Localization Atmos Mixing or Music Mixing?"),
]

B["freetext"] = [
    ("r", "pa-book naman ng studio 8 bukas 2-4pm, vo rec, proj QAW1, walang client"),
    ("j", "What date works?"),
    ("r", "book stdio 7 on friday 3pm-5pm voice over project qaw3 no client"),
    ("j", "*QAW3 / HL*\n*Date:* Friday, October 15, 2027\n*Time:* 3:00 PM – 5:00 PM\n*Room:* Studio F\n\nI picked Studio F. Tell me if you’d like another room.\n\nBook it? Reply yes or no."),
]

B["carry"] = [
    ("r", "no"),
    ("j", "No problem - nothing was booked. What would you like to change?"),
    ("r", "i need a room tomorrow afternoon for VO"),
    ("j", "*QAW3 / HL*\n*Date:* Thursday, October 14, 2027\n*Time:* 3:00 PM – 5:00 PM\n*Room:* Studio 4\n\nI picked Studio 4. Tell me if you’d like another room.\n\nBook it? Reply yes or no."),
    ("r", "book studio 8 at 10am next tues, vo, project QAW6, no client"),
    ("j", "The session type is VO Recording (typical duration 60 minutes), and it's Audio Post. [Requester] is the engineer. How long does the session run? I'll assume 1 hour unless you say otherwise."),
]

B["book"] = [
    ("r", "book studio 8 friday 4-5pm, vo recording, project QAW9, no client"),
    ("j", "❌ Heads up: *Studio 8 is already booked 3:00 PM – 5:00 PM* on Friday, October 15 by another session\n\n✅ Studio 8 is free on the same day at:\n• 5:00 PM – 6:00 PM\n• 2:00 PM – 3:00 PM\n\n✅ Free at that time:\nStudio F · Studio C · Studio 4 · Studio 5 · Studio 6\n\n✅ Studio 8 is free at that time on:\n• Saturday, October 16\n\nWant one of those, or another day or time?"),
    ("r", "5-6pm then"),
    ("j", "*QAW9 / HL*\n*Date:* Friday, October 15, 2027\n*Time:* 5:00 PM – 6:00 PM\n*Room:* Studio 8\n\nBook it? Reply yes or no."),
    ("r", "yes"),
    ("j", "Booked."),
]

B["two"] = [
    ("r", "book studio 8 friday 10-11am and studio f friday 2-3pm, both vo recording, project QAW8, no client"),
    ("j", "*QAW8 / HL*\n*Date:* Friday, October 15, 2027\n*Time:* 2:00 PM – 3:00 PM\n*Room:* Studio F\n\nBook it? Reply yes or no."),
]

B["series"] = [
    ("r", "book studio c every tuesday 10am-12nn for 3 weeks starting next week, vo recording, project QAW11, no client"),
    ("j", "*QAW11 / HL*\n*Dates (3):*\n- Tuesday, 19 October 2027\n- Tuesday, 26 October 2027\n- Tuesday, 2 November 2027\n*Time:* 10:00 AM – 12:00 PM\n*Room:* Studio C\n\nBook it? Reply yes or no."),
]

B["avail"] = [
    ("r", "what's free tomorrow afternoon?"),
    ("j", "🗓️ October 14 (Thursday), 10:00 AM – 11:00 AM\n\n✅ Free studios:\nStudios 1, 2, 3, 4, 5, 6, 7, 8, C, E, F, and M.\nVocal booths A, B, and D.\nM2, M3, M5, M8."),
    ("r", "is studio 8 free on friday?"),
    ("j", "🗓️ October 15 (Friday), 10:00 AM – 11:00 AM\n\n✅ Studio 8 is free 10:00 AM – 11:00 AM.\n\n✅ Usual rooms for VO Recording free then:\nStudios 7, C, and F."),
]

B["mine"] = [
    ("r", "what do i have booked this week?"),
    ("j", "Your bookings this week that I can find (Oct 13–17):\n\n*THUNDER CAT / [client] / HL*\n Date: October 13, 2027 (Wed)\n Time: 8:00 PM – 10:00 PM\n Room: Studio 7\n\n*YES / [client] / HL*\n Date: October 14, 2027 (Thu)\n Time: 2:00 PM – 5:00 PM\n Room: Studio 7\n\n*SOUPS / [client] / DR*\n Date: October 14, 2027 (Thu)\n Time: 1:00 PM – 4:00 PM\n Room: Studio 8 (booked by you, for [colleague]; [colleague] engineering)"),
]

B["change"] = [
    ("r", "actually can you cancel my friday booking"),
    ("j", "*QAW9 / HL*\n*Date:* Friday, October 15, 2027\n*Time:* 5:00 PM – 6:00 PM\n*Room:* Studio 8\n\nCancel it? Reply yes or no."),
    ("r", "no wait, just move it to 2-3pm same day"),
    ("j", "*QAW9 / HL*\n*Now:* Friday, October 15, 2027, 5:00 PM – 6:00 PM, Studio 8\n*Moving to:* Friday, October 15, 2027, 2:00 PM – 3:00 PM, Studio 8\n\nMove it? Reply yes or no."),
    ("r", "no"),
    ("j", "Okay - it stays where it is."),
]

B["weather"] = [
    ("r", "nvm, thanks! btw what's the weather like today?"),
    ("j", "❌ Heads up: *Studio 7 is already booked 3:00 PM – 6:00 PM* on Wednesday, October 13 by another session\n\n✅ Studio 7 is free on the same day at:\n• 2:00 PM – 3:00 PM\n\n✅ Free at that time:\nStudio 1 · Studio 2 · Studio 8 · Studio F · Studio 3\n\n✅ Studio 7 is free at that time on:\n• Sunday, October 17\n\nWant one of those, or another day or time?"),
]
