# ===================== UTF-8 FIX (MUST BE FIRST) =====================
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ===================== IMPORTS =====================

import os
import sqlite3
import numpy as np
import re
import subprocess

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from sentence_transformers import SentenceTransformer

# ===================== CONFIG =====================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OLLAMA_MODEL = "tinyllama"   # lightweight
TOP_K = 6
DEFAULT_THRESHOLD = 0.35

# ===================== APP =====================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ===================== SEMANTIC MODEL =====================

embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Semantic search ENABLED")

# ===================== DATABASE =====================

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    doc_id TEXT,
    page_num INTEGER,
    line_num INTEGER,
    content TEXT,
    embedding BLOB,
    PRIMARY KEY(doc_id, page_num, line_num)
);
"""

def create_fts(cur):
    cur.execute("DROP TABLE IF EXISTS pages_fts;")
    cur.execute("""
        CREATE VIRTUAL TABLE pages_fts USING fts5(
            content,
            doc_id UNINDEXED,
            page_num UNINDEXED,
            line_num UNINDEXED
        );
    """)

# ===================== OCR =====================

def ocr_page(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img)

# ===================== INDEXING =====================

def index_pdf(pdf_path, db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(DB_SCHEMA)
    create_fts(cur)

    doc = fitz.open(pdf_path)
    total = 0

    for p in range(len(doc)):
        page = doc[p]
        text = page.get_text("text").strip()

        if len(text) < 50:
            print(f"OCR triggered on page {p + 1}")
            text = ocr_page(page)

        lines = []
        for line in text.splitlines():
            line = re.sub(r"[^a-zA-Z0-9 ]+", " ", line)
            line = re.sub(r"\s+", " ", line).strip().lower()
            if len(line) > 3:
                lines.append(line)

        if not lines:
            continue

        embeddings = embedder.encode(lines, normalize_embeddings=True)

        for i, line in enumerate(lines, start=1):
            cur.execute(
                "INSERT INTO pages VALUES (?, ?, ?, ?, ?)",
                (pdf_path, p + 1, i, line, embeddings[i - 1].tobytes())
            )
            total += 1

    conn.commit()

    cur.execute("""
        INSERT INTO pages_fts (content, doc_id, page_num, line_num)
        SELECT content, doc_id, page_num, line_num FROM pages
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM pages_fts")
    print("📄 FTS rows:", cur.fetchone()[0])

    conn.close()
    return total

# ===================== SEMANTIC SEARCH =====================

def semantic_retrieve(db_path, query, top_k=TOP_K):
    q_emb = embedder.encode([query], normalize_embeddings=True)[0]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT page_num, line_num, content, embedding FROM pages")

    scored = []
    for p, l, text, emb_blob in cur.fetchall():
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        score = float(np.dot(q_emb, emb))
        scored.append((score, p, l, text))

    conn.close()
    scored.sort(reverse=True)
    return scored[:top_k]

# ===================== OLLAMA (FIXED) =====================

def ollama_answer(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",   # ✅ FIX
            errors="ignore",    # ✅ FIX
            timeout=60
        )

        if result.returncode != 0:
            return "LLM failed to generate an answer."

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        return "LLM timed out due to system limits."
    except Exception as e:
        return f"LLM error: {str(e)}"

# ===================== API: INDEX =====================

@app.route("/api/index", methods=["POST"])
def api_index():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(pdf_path)

    db_path = pdf_path + ".db"
    lines = index_pdf(pdf_path, db_path)

    return jsonify({
        "db_path": db_path,
        "pdf_path": pdf_path,
        "lines_indexed": lines
    })

# ===================== API: FTS SEARCH =====================

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(force=True)
    query = data.get("query", "").lower()
    db_path = data.get("db_path")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT page_num, line_num,
               snippet(pages_fts, -1, '[', ']', '...', 12)
        FROM pages_fts
        WHERE pages_fts MATCH ?
        LIMIT 20
    """, (f'"{query}"',))

    rows = cur.fetchall()
    conn.close()

    return jsonify({
        "results": [
            {"page": p, "line": l, "snippet": s}
            for p, l, s in rows
        ]
    })

# ===================== API: SEMANTIC SEARCH =====================

@app.route("/api/semantic_search", methods=["POST"])
def api_semantic():
    data = request.get_json(force=True)

    results = semantic_retrieve(
        data["db_path"],
        data["query"],
        data.get("top_k", TOP_K)
    )

    return jsonify({
        "results": [
            {
                "score": round(s, 4),
                "page": p,
                "line": l,
                "text": t
            }
            for s, p, l, t in results
        ]
    })

# ===================== API: ASK =====================

@app.route("/api/ask", methods=["POST"])
def api_ask():
    data = request.get_json(force=True)
    question = data.get("question", "")
    db_path = data.get("db_path")
    threshold = float(data.get("threshold", DEFAULT_THRESHOLD))

    results = semantic_retrieve(db_path, question)

    if not results or results[0][0] < threshold:
        return jsonify({
            "answer": "No confident answer found in the document.",
            "sources": []
        })

    context = "\n".join(
        f"(Page {p}) {text}"
        for s, p, _, text in results
        if s >= threshold
    )

    prompt = f"""
You are answering strictly from the context.
If the answer is not present, say "Not found in document".

Context:
{context}

Question:
{question}

Answer:
"""

    answer = ollama_answer(prompt)

    return jsonify({
        "answer": answer,
        "sources": [
            {"page": p, "line": l, "score": round(s, 3)}
            for s, p, l, _ in results
        ]
    })

# ===================== API: PDF =====================

@app.route("/api/pdf")
def api_pdf():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return "PDF not found", 404
    return send_file(path, mimetype="application/pdf")

# ===================== RUN =====================

if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5000")
    app.run(port=5000, debug=False)
