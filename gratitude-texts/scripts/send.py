#!/usr/bin/env python3
"""Send approved messages from review.csv through the macOS Messages app.

Dry run by default: prints what would go out. Nothing sends without --send.
Only rows with send=y are used. Every send is logged to sent.log next to the
CSV, and anyone already in the log is skipped, so re-running is safe.

Usage:
  python3 send.py DIR/review.csv                      # dry run
  python3 send.py DIR/review.csv --test-to +15551234  # send row 1's text to yourself
  python3 send.py DIR/review.csv --send               # real send
"""
import argparse
import csv
import os
import random
import subprocess
import sys
import time
from datetime import datetime

SCRIPT = '''
on run argv
  set theHandle to item 1 of argv
  set theText to item 2 of argv
  tell application "Messages"
    try
      set svc to 1st account whose service type = iMessage
      send theText to participant theHandle of svc
    on error
      set svc to 1st account whose service type = SMS
      send theText to participant theHandle of svc
    end try
  end tell
end run
'''


def osa_send(handle, text):
    r = subprocess.run(["osascript", "-e", SCRIPT, handle, text],
                       capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stderr or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--send", action="store_true", help="actually send")
    ap.add_argument("--test-to", help="send the first approved message to this handle only")
    ap.add_argument("--min-delay", type=float, default=4)
    ap.add_argument("--max-delay", type=float, default=10)
    args = ap.parse_args()

    log_path = os.path.join(os.path.dirname(os.path.abspath(args.csv)), "sent.log")
    already = set()
    if os.path.exists(log_path):
        with open(log_path) as f:
            already = {line.split("\t")[1] for line in f if "\tOK\t" in line}

    with open(args.csv, newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r.get("send", "").strip().lower() in ("y", "yes", "x", "1")]
    rows = [r for r in rows if r["handle"] not in already]
    if not rows:
        sys.exit("Nothing to send (no rows marked send=y, or all already sent).")

    if args.test_to:
        ok, err = osa_send(args.test_to, rows[0]["message"])
        print(("sent test to " + args.test_to) if ok else ("FAILED: " + err))
        return

    if not args.send:
        for r in rows:
            print(f"--- {r.get('name') or r['handle']} ({r['handle']})\n{r['message']}\n")
        print(f"DRY RUN: {len(rows)} messages. Add --send to send them.")
        return

    sent = 0
    with open(log_path, "a") as log:
        for i, r in enumerate(rows, 1):
            ok, err = osa_send(r["handle"], r["message"])
            status = "OK" if ok else "FAIL"
            log.write(f"{datetime.now().isoformat()}\t{r['handle']}\t{status}\t{err}\n")
            log.flush()
            print(f"[{i}/{len(rows)}] {status} {r.get('name') or r['handle']}" + (f": {err}" if err else ""))
            sent += ok
            if i < len(rows):
                time.sleep(random.uniform(args.min_delay, args.max_delay))
    print(f"Done: {sent}/{len(rows)} sent. Log: {log_path}")


if __name__ == "__main__":
    main()
