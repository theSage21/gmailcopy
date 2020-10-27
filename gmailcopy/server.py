import os
import io
import click
import email
from flask import Flask, render_template, url_for, request, send_file, redirect
from collections import namedtuple
from gmailcopy.config import sqlite3


def render_ctypes(ctypes):
    MAP = {
        "text/plain": "",
        "text/csv": "📜",
        "text/xml": "📜",
        "text/x-markdown": "📜",
        "text/x-bibtex": "📜",
        "text/html": "",
        "text/x-python": "🐍",
        # "text/html": "🌐",
        "multipart/signed": "",
        "multipart/related": "",
        "multipart/alternative": "",
        "multipart/mixed": "",
        "application/pgp-signature": "",
        "application/octet-stream": "📚",
        "application/pdf": "📚",
        "application/vnd.oasis.opendocument.text": "📚",
        "application/vnd.ms-excel": "📚",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "📚",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📚",
        "application/vnd.oasis.opendocument.spreadsheet": "📚",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "📚",
        "application/msword": "📚",
        "application/zip": "🤐",
        "application/x-gzip": "🤐",
        "application/rar": "🤐",
        "application/x-zip-compressed": "🤐",
        "video/3gpp": "🎭",
        "video/mp4": "🎭",
        "video/x-matroska": "🎭",
        "audio/mp3": "🎶",
        "audio/mpeg": "🎶",
        "image/jpeg": "📷",
        "image/jpg": "📷",
        "image/gif": "📷",
        "image/bmp": "📷",
        "image/png": "📷",
    }
    return " ".join(MAP.get(c, c) for c in ctypes.split())


@click.command()
@click.option("--backup_dir", default="backup")
def run(backup_dir):
    app = Flask(__name__)
    app.jinja_env.globals["url_for"] = url_for
    app.jinja_env.globals["render_ctypes"] = render_ctypes
    Meta = namedtuple(
        "Meta", "gmid subject sender recipient labels ctypes search stamp"
    )

    meta = {}

    @app.route("/")
    def listing():
        return render_template("listing.html", meta=meta)

    @app.route("/refresh")
    def refresh_meta():
        dbpath = f"{backup_dir}/meta.db"
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute("pragma query_only=1;")
        for row in cursor.execute(
            "select * from email order by datetime(stamp) desc"
        ).fetchall():
            meta[row[0]] = Meta(*tuple(row))
        conn.commit()
        conn.close()
        return redirect(url_for("listing"))

    @app.route("/<gmid>")
    def show_email(gmid):
        idx = request.args.get("idx")
        fpath = f"{backup_dir}/{gmid}.eml"
        with open(fpath, "rb") as fl:
            eml = email.message_from_binary_file(fl)
        body = list(eml.walk())
        if idx is not None:
            fl = body[int(idx)]
            ctype = fl.get_content_type()
            return send_file(
                io.BytesIO(fl.get_payload(decode=True)),
                attachment_filename=fl.get_filename() or f"part-{idx}",
                as_attachment=True,
                mimetype=ctype,
            )
        priority = ["text/plain", "text/html"]
        body.sort(
            key=lambda x: priority.index(x.get_content_type())
            if x.get_content_type() in priority
            else float("inf")
        )
        body = body[0]
        return render_template("email.html", eml=eml, meta=meta, gmid=gmid, body=body)

    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    run()
