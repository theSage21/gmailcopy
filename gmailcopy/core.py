import os
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


@click.command()
@click.option("--email")
@click.option("--pwd")
@click.option("--backup_dir", default="backup")
@click.option("--seconds", default=0)
def run(email, pwd, backup_dir, seconds):
    while True:
        print("Checking", datetime.datetime.now())
        try:
            check_mail(email, pwd, backup_dir)
        except Exception as e:
            logging.exception(e)
        except KeyboardInterrupt:
            break
        if seconds == 0:
            break
        print("Sleeping", seconds)
        time.sleep(seconds)


def check_mail(email, pwd, backup_dir):
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
            backup_email(msgId, imapSession, backup_dir)
        except Exception as e:
            logging.exception(e)
        except KeyboardInterrupt:
            break
    imapSession.close()
    imapSession.logout()


def backup_email(msgid, imap, backup_dir):
    res, msg = imap.fetch(msgid, "(X-GM-MSGID)")
    gm_msgid = msg[0].decode().split()[-1].rstrip(")")
    if os.path.exists(f"{backup_dir}/{gm_msgid}.eml"):
        return
    res, msg = imap.fetch(msgid, "(RFC822)")
    msgpath = os.path.join(backup_dir, f"{gm_msgid}.eml")
    try:
        with open(msgpath, "wb") as fl:
            fl.write(msg[0][1])
    except KeyboardInterrupt:
        shutil.rmtree(msgdir)
        raise
