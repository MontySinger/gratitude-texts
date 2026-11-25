# gratitude-texts

A Claude Code skill for holiday check-ins. It builds one Google Sheet of everyone you interacted with over the past year, ranks them by how close you are, and drafts a short personal message for your top ~25. You go down the list and reach out yourself.

**It never sends anything.** No texts, no emails. It reads your data and hands you a Sheet.

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

or say "who should I reach out to for Thanksgiving?"

It starts by explaining exactly what it will read and do, and waits for your yes.

## What you get

A private Google Sheet in your account, with a local copy at `~/gratitude-texts/<year>/people.csv`:

| column | what it is |
|---|---|
| `done` | a checkbox to tick as you reach out |
| `priority` | high / medium / low |
| `name`, `phone`, `email` | from Messages and Contacts |
| `sources` | text, email, calendar |
| `texts` | messages exchanged in the past year |
| `last_contact` | most recent text or meeting |
| `draft` | a short message, for high-priority people only |
| `notes` | where the draft came from, or why someone was ranked low (business, family, check first) |

It's sorted high to low, with a filter and a priority dropdown. Without a Google Drive connector, you get just the CSV.

## How it works

1. Reads `~/Library/Messages/chat.db` and your Contacts read-only. It keeps one-on-one threads where both of you wrote in the past year.
2. If Gmail or Google Calendar is connected, it adds people you emailed or met with. It reads only addresses and dates, not email bodies, and matches them to phone numbers through Contacts.
3. Ranks everyone. High means you text a lot and recently. Medium means a real back-and-forth, a meeting, or more than one channel. Low is everyone else.
4. For high-priority people only, it writes one line from your recent messages ("Hope the Denver move settled in"). Sensitive topics like health, grief or money get no personal line. It never makes up details.

## Requirements

- macOS, with Messages signed in
- Python 3 (comes with the Xcode command line tools)
- Claude Code
- The Google Drive connector in Claude, for the Sheet

## Privacy

The scripts open your Messages and Contacts databases read-only and write only to `~/gratitude-texts/`. Recent messages pass through Claude only for the people it drafts for. The list goes to the Google account you approve at the start, and nowhere else.

## License

MIT
