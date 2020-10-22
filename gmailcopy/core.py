import os
import arrow
import random
import datetime
import time
import imaplib
import base64
import hashlib
import os
import email
from email.header import decode_header
import shutil
import click
import logging
from tqdm import tqdm
import json
from gmailcopy.config import sqlite3


@click.command()
@click.option("--email")
@click.option("--pwd")
@click.option("--backup_dir", default="backup")
@click.option("--seconds", default=0)
def run(email, pwd, backup_dir, seconds):
    dbpath = f"{backup_dir}/meta.db"
    conn = sqlite3.connect(dbpath)
    ensure_tables(conn)
    conn.close()
    while True:
        print("Checking", datetime.datetime.now())
        try:
            conn = sqlite3.connect(dbpath)
            check_mail(email, pwd, backup_dir, conn)
        except Exception as e:
            logging.exception(e)
        except KeyboardInterrupt:
            break
        finally:
            conn.close()
        if seconds == 0:
            break
        print("Sleeping", seconds)
        time.sleep(seconds)


def check_mail(email, pwd, backup_dir, conn):
    imapSession = imaplib.IMAP4_SSL("imap.gmail.com")
    typ, accDetails = imapSession.login(email, pwd)
    if typ != "OK":
        raise RuntimeError("Unable to login")
    imapSession.select('"[Gmail]/All Mail"')
    typ, data = imapSession.search(None, "ALL")
    if typ != "OK":
        raise RuntimeError("Error searching inbox")
    # Iterating over all emails
    all_email = [id for id in ((i.decode() for i in data[0].split()))]
    for msgId in tqdm(all_email):
        try:
            backup_email(msgId, imapSession, backup_dir, conn)
        except Exception as e:
            logging.exception(e)
        except KeyboardInterrupt:
            break
    imapSession.close()
    imapSession.logout()


def parse_labels(string):
    labels = string.split()
    return labels


def backup_email(msgid, imap, backup_dir, conn):
    res, msg = imap.fetch(msgid, "(X-GM-MSGID)")
    gm_msgid = msg[0].decode().split()[-1].rstrip(")")
    if os.path.exists(f"{backup_dir}/{gm_msgid}.eml"):
        return
    res, msg = imap.fetch(msgid, "(X-GM-LABELS)")
    labels = parse_labels(msg[0].decode().rstrip(")").split("(X-GM-LABELS (")[1])
    res, msg = imap.fetch(msgid, "(RFC822)")
    msgpath = os.path.join(backup_dir, f"{gm_msgid}.eml")
    try:
        with open(msgpath, "wb") as fl:
            fl.write(msg[0][1])
        update_meta(gm_msgid, email.message_from_bytes(msg[0][1]), labels, conn)
    except KeyboardInterrupt:
        shutil.rmtree(msgdir)
        raise


def update_meta(gmid, eml, labels, conn):
    sql = "insert into email values (?, ?, ?, ?, ?);"
    args = (
        gmid,
        eml["subject"],
        eml["From"],
        " ".join(labels),
        arrow.get(time.mktime(email.utils.parsedate(eml["Date"]))),
    )
    cursor = conn.cursor()
    cursor.execute(sql, args)
    conn.commit()


def ensure_tables(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        create table if not exists email
        (
         gmid text primary key,
         subject text,
         sender text,
         labels text,
         stamp timestamp
         )
    """
    )
    conn.commit()


if __name__ == "__main__":
    run()
