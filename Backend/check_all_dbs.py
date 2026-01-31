# check_all_dbs.py -- find .db files under project and temp and run PRAGMA integrity_check
import glob, os, sqlite3, time

roots = [
    os.path.join(os.getcwd()),                               # backend project folder
    os.path.join(os.getcwd(), ".."),                         # project root (pdf-parser)
    os.path.join(os.environ.get('TEMP') or os.environ.get('TMP') or r'C:\Windows\Temp')
]

seen = set()
results = []
for root in roots:
    pattern = os.path.join(os.path.abspath(root), "**", "*.db")
    for db in glob.glob(pattern, recursive=True):
        if db in seen:
            continue
        seen.add(db)
        try:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            r = cur.fetchone()
            cur.close(); conn.close()
            results.append((db, r))
        except Exception as e:
            results.append((db, f"ERROR: {e}"))

# print a neat summary
ok = [r for r in results if r[1] and str(r[1][0]).lower() == "ok"]
bad = [r for r in results if not (r[1] and str(r[1][0]).lower() == "ok")]
print(f"Checked {len(results)} DB files. OK: {len(ok)}  BAD: {len(bad)}\n")
if ok:
    print("OK files:")
    for p, r in ok:
        print("  ", p)
if bad:
    print("\nBAD or UNREADABLE files:")
    for p, r in bad:
        print("  ", p, "->", r)
