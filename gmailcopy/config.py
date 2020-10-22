import sqlite3
import arrow


def convert_arrowdatetime(s):
    return arrow.get(s)


def adapt_arrowdatetime(adt):
    return adt.isoformat()


sqlite3.register_adapter(arrow.arrow.Arrow, adapt_arrowdatetime)
sqlite3.register_converter("timestamp", convert_arrowdatetime)
