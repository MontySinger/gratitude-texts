---
name: gratitude-texts
description: Find the people you actually talk to in your iMessage history and send each one a short holiday message, with a personal line drawn from your last real conversation. Thanksgiving by default; works for any occasion. Builds a review sheet first, so nothing sends until you approve it. Mac only. Triggers - "gratitude texts", "thanksgiving texts", "send happy thanksgiving to my friends", "holiday check-in messages", "who should I text this holiday", "touch base with everyone".
user-invocable: true
---

# Gratitude Texts

Holidays are a good excuse to reach out. This skill reads your local iMessage history, finds the people you have real two-way conversations with, and drafts a short message for each one: your template plus one specific line from your last conversation. You review the full list, then it sends through the Messages app.

Three rules hold the whole way through:

1. **Nothing sends without the user's explicit yes in chat**, given after they have seen the final list. Approval for the list doesn't cover any later changes to it.
2. **The data stays local.** The scripts read the databases read-only and write to a folder on the user's machine. Only the recent snippets you use for drafting pass through the model.
3. **Never make anything up.** A personal line has to come from something actually in the messages. If nothing fits, send the plain template.

## Requirements

- macOS with Messages signed in. Texts to non-iPhone numbers need iPhone "Text Message Forwarding" turned on.
- Full Disk Access for the app Claude Code runs in (System Settings > Privacy & Security > Full Disk Access), so it can read `~/Library/Messages/chat.db` and Contacts. If the user hasn't granted it, `find_people.py` prints these steps. If access is still denied after they grant it, the app almost always needs a full quit (Cmd+Q) and reopen; closing the window isn't enough. Tell them that once rather than retrying in a loop.
- The first send triggers a macOS prompt that lets the app control Messages. The user has to click Allow themselves.

Scripts are in `scripts/` next to this file. Set the working folder to `~/gratitude-texts/<year>/`.

## Step 1: Ask three things, then go

Ask these in a single message, each with a default the user can accept:

- **Occasion**: default Thanksgiving.
- **Template**: default: `Hey {first}, happy Thanksgiving! Grateful to have you in my life. {personal} Where are you celebrating? Looking forward to catching up soon.` Keep the user's wording if they give their own.
- **Who to exclude**: for example family (they may want to call them instead), coworkers, or exes. Default: no exclusions, which the review sheet can fix later.

## Step 2: Find people

```bash
python3 scripts/find_people.py --out ~/gratitude-texts/$(date +%Y)
```

Defaults: a 2-year lookback, at least 3 messages each way, and the top 150 people by score. Score favors two-way volume and recency. Tell the user how many people it found. If the count looks too high or too low, rerun with `--days`, `--min-each-way` or `--limit`.

### Optional: widen the net with email and calendar

If the user wants everyone from the past year rather than only the people they text most:

1. Rerun the finder wider: `--days 365 --min-each-way 1 --limit 5000 --out <dir>/master`.
2. Email: if a Gmail connector is available, search `in:sent after:<one year ago>` in date slices of 1 to 2 months, because results cap at 50 per call and may not paginate. Write every recipient address (to, cc, bcc), one per line, to `<dir>/master/email_sent.txt`.
3. Calendar: list the past year's events and save the guests as `[{name, email, last, count}]` to `<dir>/master/calendar.json`.
4. Merge: `python3 scripts/merge_sources.py --dir <dir>/master --self <the user's own addresses>`. It matches emails to people through Contacts and through names spelled in the address, and drops automated senders.

Each connector only sees its own account. Tell the user which inboxes and calendars were covered and which weren't.

## Step 3: Triage

Read `people.json`. Mark a person **skip**, and give a short reason, if they are:

- A business, service, landlord, recruiter, or delivery/automated thread
- Someone whose recent messages show conflict, a breakup, or a request to stop contact
- Someone the user asked to exclude
- Someone you've already swapped holiday wishes or plans with in the last few days
- Family, by default (most people would rather call them); mark the reason `family` so the user can flip it to `y`
- A thread that is only logistics or a transaction (selling furniture, club dues, a deal that was declined)

Mark **check** for romantic or dating threads, past conflict, work and client threads where the tone is uncertain, and any open favor that might make the message read as a nudge.

For anyone texted in the last ~2 days, write a shorter message by hand: drop "Looking forward to catching up soon" (you just did) and refer to the latest exchange instead.

For number-only people (`in_contacts: false`), find their name in the messages if it's there, for example "it's Sam from the climbing gym". If it isn't, mark them **check** and leave `{first}` out of their message.

Leave skips in the sheet, marked `send=n`. Don't drop them silently, so the user can see what was cut.

## Step 4: Draft

For each person who isn't skipped, write the `{personal}` line from their `recent` messages:

- One short sentence of at most about 15 words, in the user's own casual register (copy how the user texts this person).
- Refer to something specific and true: "Hope the Denver move settled in." or "Still thinking about that ramen place."
- Prefer things from the last 6 months. Treat anything older as past ("hope the marathon went well"), not ongoing.
- **Don't write a personal line** if the recent topic is sensitive: health, grief, money, divorce, job loss, legal trouble. Use the plain template for these people, and the line simply drops out.
- Never invent details, and don't repeat private things back in a way that reads as surveillance. When unsure, skip the line.
- Adjust the template where needed: drop "Where are you celebrating?" if the thread already says where.

## Step 5: Review sheet

Write `review.csv` in the working folder with these columns:

`send,name,handle,last_message,why,message`

- `send`: `y` for drafted rows, `n` for skips, `?` for check rows
- `why`: a few words on the source of the personal line, or the reason for a skip

Open it for the user (`open review.csv` opens it in Numbers). In chat, summarize the counts (y / n / ?) and show 5 sample messages. Ask them to change `send` values and edit message text, save the file as CSV, and tell you when they're done. If they would rather you make the edits ("drop Alex, shorten Priya's"), make them in the CSV yourself.

Reread the CSV after their edits. Don't assume it is unchanged.

## Step 6: Test, then send

1. Do a dry run and show the output: `python3 scripts/send.py ~/gratitude-texts/$(date +%Y)/review.csv`
2. Offer a test send to the user's own number: `--test-to <their number>`. The macOS automation prompt appears here.
3. State the exact count ("Ready to send 64 messages") and wait for a clear yes.
4. Do the real send: `python3 scripts/send.py ~/gratitude-texts/$(date +%Y)/review.csv --send`. It waits 4 to 10 seconds between messages and logs to `sent.log`. Run it in the background for long lists.

Sending is idempotent: on a rerun, anyone already marked OK in `sent.log` is skipped. If sends fail, show the errors. Common causes are no iMessage account or forwarding being off for SMS. Retry only the failed rows, and only after the user agrees.

## Step 7: After

Tell the user how many messages went out and point them to `sent.log`. Suggest they keep `review.csv`, since it doubles as next year's starting list. Replies arrive in Messages as usual. The skill doesn't read or answer them.
