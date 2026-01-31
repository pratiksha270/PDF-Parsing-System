# test_sqlite.py - quick FTS5 + integrity check test
import sqlite3, os
p = r"C:\temp\test_sql.db"
if os.path.exists(p):
    os.remove(p)
con = sqlite3.connect(p)
print("sqlite library version:", sqlite3.sqlite_version)
cur = con.cursor()
cur.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, x TEXT);")
cur.execute("INSERT INTO t(x) VALUES('hello');")
# try create FTS5 table
try:
    cur.execute("CREATE VIRTUAL TABLE ft USING fts5(x);")
    cur.execute("INSERT INTO ft(rowid, x) VALUES(1, 'hello');")
    cur.execute("SELECT * FROM ft;")
    print('fts select ->', cur.fetchall())
except Exception as e:
    print('FTS5 create/insert error:', e)
cur.execute("PRAGMA integrity_check;")
print("integrity_check ->", cur.fetchone())
con.close()
print('test complete')
