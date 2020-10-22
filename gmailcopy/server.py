import os
import sqlite3
import email
from flask import Flask, render_template
from collections import namedtuple


def get_app(backup_dir):
    app = Flask(__name__)
    Meta = namedtuple("Meta", ["gmid", "subject", "sender", "labels", "stamp"])

    dbpath = f"{backup_dir}/meta.db"
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute("pragma query_only=1;")
    meta = {}
    for row in cursor.execute("select * from email").fetchall():
        meta[row["gmid"]] = Meta(*row)
    conn.commit()
    conn.close()

    @app.route("/")
    def listing():
        return render_template("listing.html", meta=meta)

    @app.route("/<gmid>")
    def show_email(gmid):
        fpath = f"{backup_dir}/{gmid}.eml"
        with open(fpath, "rb") as fl:
            eml = email.message_from_binary_file(fl)
        return render_template("email.html", eml)
