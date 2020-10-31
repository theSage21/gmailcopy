import os
import io
import click
import email
import arrow
from flask import Flask, render_template, url_for, request, send_file, redirect
from collections import namedtuple
from gmailcopy.config import sqlite3


Label = namedtuple("Label", "text value url cancel_url")


def label_from_val(lab):
    txt = lab.strip().replace('"', "").strip().lstrip("\\")
    qlist = request.args.getlist("q")
    url = url_for("listing", q=list(sorted(set(qlist + [lab]))))
    cancel = url_for("listing", q=list(sorted({l for l in qlist if l != lab})))
    return Label(txt, lab, url, cancel)


def build_labels(string):
    labels = [label_from_val(l) for l in string.split()]
    return labels


def short_time(dt):
    now = arrow.utcnow()
    if now.date == dt.date:
        return dt.format("HH:mm")
    if now.month == dt.month:
        return dt.format("MMM DD")
    return dt.format("YY MMM")


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
    app.jinja_env.globals["short_time"] = short_time
    app.jinja_env.globals["build_labels"] = build_labels
    app.jinja_env.globals["label_from_val"] = label_from_val
    Meta = namedtuple(
        "Meta", "gmid subject sender recipient labels ctypes search stamp"
    )

    meta = {}
    revidx = {}

    @app.route("/")
    def listing():
        qlist = request.args.getlist("q")
        listed = {} if qlist else meta
        if qlist:
            ids = set()
            for q in qlist:
                ids |= revidx[q]
            listed = dict(sorted(((k, meta[k]) for k in ids), key=lambda x: x[1].stamp))
        return render_template(
            "listing.html", listed=listed, qlist=qlist, n_listed=len(listed)
        )

    @app.route("/refresh")
    def refresh_meta():
        dbpath = f"{backup_dir}/meta.db"
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute("pragma query_only=1;")
        for row in cursor.execute(
            "select * from email order by datetime(stamp) desc"
        ).fetchall():
            gmid = row[0]
            M = Meta(*tuple(list(row[:-1]) + [arrow.get(row[-1])]))
            meta[gmid] = M
            for lab in build_labels(M.labels):
                if lab.value not in revidx:
                    revidx[lab.value] = set()
                revidx[lab.value].add(gmid)
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

    app.run(debug=True, host="0.0.0.0", port=5001)


if __name__ == "__main__":
    run()
