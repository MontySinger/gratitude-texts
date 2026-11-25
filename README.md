# gratitude-texts

A Claude Code skill for holiday check-ins. It finds the people you actually talk to, drafts a short message for each one with a personal line from your last conversation, shows you the whole list, and sends only what you approve. Everything runs on your Mac, and your data is only ever read, never changed.

Thanksgiving by default. Works for any occasion.

## Install

```bash
git clone https://github.com/MontySinger/gratitude-texts.git ~/gratitude-texts-skill
ln -s ~/gratitude-texts-skill/gratitude-texts ~/.claude/skills/gratitude-texts
```

Then give the app you run Claude Code in **Full Disk Access**: System Settings > Privacy & Security > Full Disk Access. After that, **quit the app with Cmd+Q and reopen it**. macOS ignores the new permission until the app restarts.

## Use

In Claude Code, type:

```
/gratitude-texts
```

or say "send thanksgiving texts to my friends".

## What it does

1. **Finds people.** It reads `~/Library/Messages/chat.db` and your Contacts, and keeps one-on-one threads where both of you wrote recently. Businesses, verification codes and group chats drop out.
2. **Widens the net (optional).** If Gmail or Google Calendar is connected to Claude, it adds people you emailed or met with. It matches them to phone numbers through Contacts.
3. **Drafts.** Each person gets your template plus one specific line from your recent messages with them. If the recent topic is sensitive (health, grief, money), it uses the plain template. It never makes up details.
4. **Review.** Everything lands in a `review.csv`, where you approve, skip or edit each row. If Google Drive is connected to Claude, it can put the sheet in Google Sheets instead, then pull your edits back before sending. Family, people you've already wished a happy holiday, and purely transactional threads start out as skips.
5. **Sends** through the Messages app, but only after a dry run, a test message to yourself, and your explicit yes. It waits a few seconds between texts and logs every one, so a rerun never double-texts anyone.

## Requirements

- macOS, signed in to Messages
- Python 3 (comes with the Xcode command line tools)
- To text non-iPhone numbers: on your iPhone, turn on Settings > Messages > Text Message Forwarding

## Privacy

The scripts read your Messages and Contacts databases without changing them, and write their output only to `~/gratitude-texts/`. Short excerpts of recent messages pass through Claude so it can write the personal lines. Nothing sends without your approval.

## License

MIT
