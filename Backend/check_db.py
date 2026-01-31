# check_db.py - find sqlite .db files created by the app and run PRAGMA integrity_check
import glob, os, sqlite3
tmp = os.environ.get('TEMP') or os.environ.get('TMP') or r'C:\Windows\Temp'
pattern = os.path.join(tmp, "pdf_parser_*", "**", "*.db")
files = glob.glob(pattern, recursive=True)
if not files:
    print("No pdf_parser_*.db files found under", tmp)
else:
    print("Found", len(files), "db file(s). Checking integrity...\n")
for db in files:
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        r = cur.fetchone()
        cur.close()
        conn.close()
        print(db, "->", r)
    except Exception as e:
        print(db, "-> ERROR:", e)
