import os
import time
import imaplib
import base64
import os
import email
from email.header import decode_header
import shutil
import click
import logging
from tqdm import tqdm
import json


def exists(msgid, backup_dir):
    return os.path.exists(os.path.join(backup_dir, msgid))


@click.command()
@click.option("--email")
@click.option("--pwd")
@click.option("--backup_dir", default="backup")
@click.option("--seconds", default=60 * 60)
def run(email, pwd, backup_dir, seconds):
    while True:
        try:
            check_mail(email, pwd, backup_dir)
        except Exception as e:
            logging.exception(e)
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
    # Iterating over pending emails
    saved_emails = set(os.listdir(backup_dir))
    pending_emails = [
        id for id in (i.decode() for i in data[0].split()) if id not in saved_emails
    ]
    for msgId in tqdm(pending_emails):
        try:
            backup_email(msgId, imapSession, backup_dir)
        except Exception as e:
            logging.exception(e)
    imapSession.close()
    imapSession.logout()


def backup_email(msgid, imap, backup_dir):
    try:
        res, msg = imap.fetch(msgid, "(RFC822)")
        msgdir = os.path.join(backup_dir, msgid)
        msgpath = os.path.join(msgdir, "msg.eml")
        if not os.path.isdir(msgdir):
            os.mkdir(msgdir)
        with open(msgpath, "wb") as fl:
            fl.write(msg[0][1])
    except KeyboardInterrupt:
        shutil.rmtree(msgdir)
        raise
