#!/usr/bin/env python3
"""Merge texts, email recipients and calendar guests into one master list.

Inputs (all in --dir):
  people.json      from find_people.py (texts)
  email_sent.txt   one address per line: people you emailed
  calendar.json    [{name, email, last, count}] meeting guests
Writes master_list.csv. Matches emails to names and phone numbers through
your macOS Contacts, so an email-only contact still gets a number to text
when Contacts has one. Read-only; sends nothing.
"""
import argparse, csv, glob, json, os, re, sqlite3

AB = os.path.expanduser("~/Library/Application Support/AddressBook")
SKIP = re.compile(r"^(no-?reply|noreply|tracker|info|hello|support|ai|business|mba|team|admin|billing|"
                  r"notifications?|member)@|unsubscribe|mailsuite|rmmservice|tldr\.tech", re.I)


def contacts_by_email():
    out = {}
    dbs = glob.glob(f"{AB}/AddressBook-v22.abcddb") + glob.glob(f"{AB}/Sources/*/AddressBook-v22.abcddb")
    for db in dbs:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        names = {pk: " ".join(x for x in (f, l) if x) or o for pk, f, l, o in
                 con.execute("select Z_PK, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION from ZABCDRECORD")}
        phones = {}
        for owner, num in con.execute("select ZOWNER, ZFULLNUMBER from ZABCDPHONENUMBER"):
            if num: phones.setdefault(owner, num)
        for owner, addr in con.execute("select ZOWNER, ZADDRESS from ZABCDEMAILADDRESS"):
            if addr:
                out.setdefault(addr.lower().strip(), {"name": names.get(owner), "phone": phones.get(owner)})
        con.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--self", nargs="*", default=[], help="your own addresses to drop")
    a = ap.parse_args()
    d = os.path.expanduser(a.dir)
    me = {s.lower() for s in a.self}
    cbe = contacts_by_email()

    rows = {}
    def key(name, phone, email):
        return ("n", name.lower()) if name else ("p", phone) if phone else ("e", email)

    texts = json.load(open(f"{d}/people.json"))["people"] if os.path.exists(f"{d}/people.json") else []
    for p in texts:
        phone = next((h for h in p["all_handles"] if "@" not in h), "")
        email = next((h for h in p["all_handles"] if "@" in h), "")
        k = key(p["name"], phone, email)
        rows[k] = {"name": p["name"] or "", "phone": phone, "email": email, "sources": {"text"},
                   "texts": p["total"], "last_text": p["last_message"], "last_email_or_meeting": ""}

    def add(email, name, source, last=""):
        email = email.lower().strip()
        if not email or email in me or SKIP.search(email):
            return
        c = cbe.get(email, {})
        name = c.get("name") or name or ""
        k = key(name, None, email) if name else ("e", email)
        r = rows.setdefault(k, {"name": name, "phone": c.get("phone") or "", "email": email,
                                "sources": set(), "texts": 0, "last_text": "", "last_email_or_meeting": ""})
        r["sources"].add(source)
        r["email"] = r["email"] or email
        r["phone"] = r["phone"] or c.get("phone") or ""
        r["last_email_or_meeting"] = max(r["last_email_or_meeting"], last)

    if os.path.exists(f"{d}/email_sent.txt"):
        for line in sorted(set(open(f"{d}/email_sent.txt"))):
            add(line, "", "email")
    if os.path.exists(f"{d}/calendar.json"):
        for c in json.load(open(f"{d}/calendar.json")):
            add(c["email"], c.get("name", ""), "calendar", c.get("last", ""))

    # Fold email-only rows into a texted person when the address spells their name
    # (jane@company.com + "Jane Doe" only if there is one Jane; jdoe@ / jane.doe@).
    texted = [r for r in rows.values() if "text" in r["sources"] and r["name"] and " " in r["name"]]
    firsts = {}
    for r in texted:
        firsts.setdefault(r["name"].split()[0].lower(), []).append(r)
    for k in [k for k, r in rows.items() if "text" not in r["sources"]]:
        r = rows[k]
        local, _, domain = r["email"].partition("@")
        local = re.sub(r"[^a-z]", "", local)
        hit = None
        for t in texted:
            parts = re.sub(r"[^a-z ]", "", t["name"].lower()).split()
            if len(parts) < 2 or len(parts[-1]) < 3:
                continue
            first, last = parts[0], parts[-1]
            if (last in local and (first in local or local.startswith(first[0]))) or \
               (local == first and last in domain):
                hit = t; break
        if not hit and local in firsts and len(firsts[local]) == 1 and r.get("name", "") == "":
            hit = firsts[local][0]
            hit.setdefault("_guess", True)
        if hit:
            hit["sources"] |= r["sources"]
            hit["email"] = hit["email"] or r["email"]
            hit["last_email_or_meeting"] = max(hit["last_email_or_meeting"], r["last_email_or_meeting"])
            del rows[k]

    out = []
    for r in rows.values():
        r["sources"] = "+".join(sorted(r["sources"]))
        r["textable"] = "y" if r["phone"] or (r["email"] and "text" in r["sources"]) else "n"
        out.append(r)
    out.sort(key=lambda r: (-r["sources"].count("+"), -r["texts"], r["name"] or r["email"]))
    cols = ["name", "phone", "email", "sources", "texts", "last_text", "last_email_or_meeting", "textable"]
    path = f"{d}/master_list.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    os.chmod(path, 0o600)
    from collections import Counter
    print(len(out), "people ->", path)
    print(Counter(r["sources"] for r in out))
    print("textable:", sum(r["textable"] == "y" for r in out))


if __name__ == "__main__":
    main()
