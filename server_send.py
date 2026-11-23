#!/usr/bin/env python3
"""Server-side iCloud sender (runs in GitHub Actions). Never prints recipient addresses.
Env: ICLOUD_USER, ICLOUD_PASS, FROM_NAME. Files: queue.csv (email,subject,body), sent.log (appended).
Waits until 13:30 UTC (= 18:30 PKT) unless --now. Skips Sunday. Cap 40/day. Gap 3.0-3.2 min."""
import csv, datetime as dt, imaplib, os, random, smtplib, ssl, sys, time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
now_flag = "--now" in sys.argv
cap = int(os.environ.get("CAP", "40"))
user, pw, name = os.environ["ICLOUD_USER"], os.environ["ICLOUD_PASS"].replace(" ", ""), os.environ.get("FROM_NAME", "")
utc = dt.datetime.now(dt.timezone.utc)
today = str(utc.date())
if not now_flag and utc.weekday() == 6: sys.exit("Sunday, no send.")
log = open("sent.log").read().splitlines() if os.path.exists("sent.log") else []
done = {l.split("\t")[1] for l in log}
sent_today = sum(1 for l in log if l.startswith(today) and l.split("\t")[2] == "SENT")
rows = [r for r in csv.DictReader(open("queue.csv")) if r["email"].strip().lower() not in done]
if user.lower() in {r["email"].strip().lower() for r in rows}: sys.exit("Queue contains the sender itself.")
todo = rows[: max(0, cap - sent_today)]
print(f"{len(rows)} unsent, {sent_today} sent today, sending {len(todo)}", flush=True)
if not todo: sys.exit(0)
if not now_flag:
    t = utc.replace(hour=13, minute=30, second=0, microsecond=0)
    while dt.datetime.now(dt.timezone.utc) < t: time.sleep(20)
ctx = ssl.create_default_context()
def conn():
    s = smtplib.SMTP("smtp.mail.me.com", 587, timeout=60); s.starttls(context=ctx); s.login(user, pw); return s
s = conn()
imap = None
def save_sent(msg):
    global imap
    try:
        if imap is None:
            imap = imaplib.IMAP4_SSL("imap.mail.me.com", 993); imap.login(user, pw)
        imap.append("Sent Messages", "\\Seen", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
    except Exception:
        imap = None
for i, r in enumerate(todo, 1):
    m = EmailMessage(); m["From"] = formataddr((name, user)); m["To"] = r["email"].strip()
    m["Subject"] = r["subject"]; m["Message-ID"] = make_msgid(domain="icloud.com"); m.set_content(r["body"])
    try: s.send_message(m); status = "SENT"; save_sent(m)
    except Exception as e:
        status = "ERR"
        try: s.quit()
        except Exception: pass
        try: s = conn()
        except Exception: print("reconnect failed"); break
    with open("sent.log", "a") as f: f.write(f"{today}\t{r['email'].strip().lower()}\t{status}\t{dt.datetime.now(dt.timezone.utc):%H:%M:%S}\n")
    print(f"{i}/{len(todo)} {status}", flush=True)
    if i < len(todo): time.sleep(random.uniform(3.0, 3.2) * 60)
print("done")
