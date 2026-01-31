# repair_dbs_in_uploads.py
import sqlite3, os, shutil, time

BASE = os.path.abspath(os.getcwd())
UPLOADS = os.path.join(BASE, "uploads")
TS = time.strftime("%Y%m%d%H%M%S")

def find_dbs():
    if not os.path.isdir(UPLOADS):
        return []
    out = []
    for r, _, files in os.walk(UPLOADS):
        for f in files:
            if f.lower().endswith(".db"):
                out.append(os.path.join(r, f))
    return out

def backup(p):
    b = p + ".bak_" + TS
    shutil.copy2(p, b)
    print("[BACKUP]", p, "->", b)
    return b

def check(p):
    try:
        c = sqlite3.connect(p, check_same_thread=False)
        cur = c.cursor()
        cur.execute("PRAGMA integrity_check;")
        r = cur.fetchone()
        c.close()
        ok = bool(r and str(r[0]).lower() == "ok")
        return ok, r
    except Exception as e:
        return False, str(e)

def dump_restore(p):
    name = os.path.splitext(p)[0]
    dumpfile = name + "_dump_" + TS + ".sql"
    repaired = name + "_repaired_" + TS + ".db"
    try:
        con = sqlite3.connect(p, check_same_thread=False)
        with open(dumpfile, "w", encoding="utf-8") as f:
            for line in con.iterdump():
                f.write(line + "\n")
        con.close()
    except Exception as e:
        print("[DUMP-ERR]", e)
        return False, str(e)

    try:
        con2 = sqlite3.connect(repaired, check_same_thread=False)
        cur2 = con2.cursor()
        with open(dumpfile, "r", encoding="utf-8") as f:
            sql = f.read()
        cur2.executescript(sql)
        con2.commit()
        con2.execute("VACUUM;")
        con2.close()
        print("[RESTORED]", repaired)
        return True, repaired
    except Exception as e:
        print("[RESTORE-ERR]", e)
        try:
            if os.path.exists(repaired):
                os.remove(repaired)
        except:
            pass
        return False, str(e)

def create_empty_db(path):
    try:
        sqlite3.connect(path, check_same_thread=False).close()
        print("[EMPTY] Created empty DB at", path)
        return True
    except Exception as e:
        print("[EMPTY-ERR]", e)
        return False

def main():
    dbs = find_dbs()
    if not dbs:
        print("No .db files found in uploads.")
        return
    for db in dbs:
        print("="*60)
        print("[CHECK]", db)
        ok, raw = check(db)
        print("[INTEGRITY] ok=", ok, " raw=", raw)
        if ok:
            print("[SKIP] DB is healthy.")
            continue
        bak = backup(db)
        ok2, res = dump_restore(db)
        if ok2:
            print("[SUCCESS] Repaired DB created at:", res)
            continue
        else:
            print("[FAIL] Dump/restore failed:", res)
            try:
                corrupt_move = db + ".corrupt_" + TS
                shutil.move(db, corrupt_move)
                print("[MOVE] moved corrupt DB to:", corrupt_move)
            except Exception as e:
                print("[MOVE-ERR]", e)
            created = create_empty_db(db)
            if created:
                print("[FALLBACK] Empty DB created; please re-index the PDF.")
            else:
                print("[ERROR] Could not recover this DB automatically.")
    print("="*60)
    print("Done.")

if __name__ == '__main__':
    main()
