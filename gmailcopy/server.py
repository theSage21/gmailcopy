import os
import io
import click
import email
from flask import Flask, render_template, url_for, request, send_file
from collections import namedtuple
from gmailcopy.config import sqlite3


@click.command()
@click.option("--backup_dir", default="backup")
def run(backup_dir):
    app = Flask(__name__)
    app.jinja_env.globals["url_for"] = url_for
    Meta = namedtuple("Meta", "gmid subject sender labels stamp")

    dbpath = f"{backup_dir}/meta.db"
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute("pragma query_only=1;")
    meta = {}
    for row in cursor.execute(
        "select * from email order by datetime(stamp) desc"
    ).fetchall():
        meta[row[0]] = Meta(*tuple(row))
    conn.commit()
    conn.close()

    @app.route("/")
    def listing():
        return render_template("listing.html", meta=meta)

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
