import React, { useState } from "react";
import axios from "axios";
import "./App.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("Ready");
  const [dbPath, setDbPath] = useState("");
  const [pdfPath, setPdfPath] = useState("");

  const [ftsQuery, setFtsQuery] = useState("");
  const [ftsResults, setFtsResults] = useState([]);

  const [semanticQuery, setSemanticQuery] = useState("");
  const [semanticResults, setSemanticResults] = useState([]);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [threshold, setThreshold] = useState(0.35);

  const backend =
    import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";

  // ---------- OPEN PDF ----------
  function openPdf(page, highlight = "") {
    if (!pdfPath) return;

    let url = `${backend}/api/pdf?path=${encodeURIComponent(
      pdfPath
    )}#page=${page}`;

    if (highlight) {
      url += `&search=${encodeURIComponent(highlight)}`;
    }

    window.open(url, "_blank");
  }

  // ---------- UPLOAD ----------
  async function uploadAndIndex(e) {
    e.preventDefault();
    if (!file) return;

    setStatus("Uploading...");
    const fd = new FormData();
    fd.append("file", file);

    const res = await axios.post(`${backend}/api/index`, fd);
    setDbPath(res.data.db_path);
    setPdfPath(res.data.pdf_path);

    setStatus("Indexed");
    setAnswer("");
    setFtsResults([]);
    setSemanticResults([]);
  }

  // ---------- FTS SEARCH ----------
  async function doFtsSearch(e) {
    e.preventDefault();
    if (!dbPath) return;

    setStatus("Searching...");
    const res = await axios.post(`${backend}/api/search`, {
      db_path: dbPath,
      query: ftsQuery,
    });

    setFtsResults(res.data.results || []);
    setStatus("FTS done");
  }

  // ---------- SEMANTIC SEARCH ----------
  async function doSemanticSearch(e) {
    e.preventDefault();
    if (!dbPath) return;

    setStatus("Semantic searching...");
    const res = await axios.post(`${backend}/api/semantic_search`, {
      db_path: dbPath,
      query: semanticQuery,
      top_k: 6,
    });

    setSemanticResults(res.data.results || []);
    setStatus("Semantic done");
  }

  // ---------- ASK (JSON ONLY) ----------
  async function doAsk(e) {
    e.preventDefault();
    if (!dbPath) return;

    setAnswer("");
    setSources([]);
    setStatus("Thinking...");

    try {
      const res = await axios.post(`${backend}/api/ask`, {
        db_path: dbPath,
        question,
        threshold,
      });

      setAnswer(res.data.answer || "");
      setSources(res.data.sources || []);
      setStatus("Answered");
    } catch {
      setAnswer("Failed to get answer.");
      setStatus("Error");
    }
  }

  return (
    <div className="app">
      <div className="container">
        <h1>📘 PDF QA — Hybrid Search & Q&A</h1>

        {/* Upload */}
        <div className="card">
          <form onSubmit={uploadAndIndex} className="form-row">
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            <button>Upload & Index</button>
            <div className="status">{status}</div>
          </form>
          <div className="meta">DB: {dbPath || "none"}</div>
        </div>

        {/* FTS */}
        <div className="card">
          <h2>🔍 FTS Keyword Search</h2>
          <form onSubmit={doFtsSearch} className="form-row">
            <input
              value={ftsQuery}
              onChange={(e) => setFtsQuery(e.target.value)}
              placeholder="Search exact words"
            />
            <button>Search</button>
          </form>

          {ftsResults.map((r, i) => (
            <div
              key={i}
              className="result clickable"
              onClick={() => openPdf(r.page, ftsQuery)}
            >
              <div className="meta">Page {r.page}, Line {r.line}</div>
              <div dangerouslySetInnerHTML={{ __html: r.snippet }} />
            </div>
          ))}
        </div>

        {/* Semantic */}
        <div className="card">
          <h2>🧠 Semantic Search</h2>
          <form onSubmit={doSemanticSearch} className="form-row">
            <input
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              placeholder="Search by meaning"
            />
            <button>Semantic Search</button>
          </form>

          {semanticResults.map((r, i) => (
            <div
              key={i}
              className="result clickable"
              onClick={() => openPdf(r.page, semanticQuery)}
            >
              <div className="meta">
                Score {r.score.toFixed(3)} — Page {r.page}, Line {r.line}
              </div>
              <div className="snippet">{r.text}</div>
            </div>
          ))}
        </div>

        {/* Ask */}
        <div className="card">
          <h2>❓ Ask a Question</h2>
          <form onSubmit={doAsk} className="form-row">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about the document"
            />
            <button>Ask</button>
          </form>

          <div className="threshold">
            <label>
              Confidence threshold: <strong>{threshold}</strong>
            </label>
            <input
              type="range"
              min="0.2"
              max="0.7"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            />
          </div>

          <div className="output">{answer}</div>

          {sources.length > 0 && (
            <div className="sources">
              <h4>Sources</h4>
              {sources.map((s, i) => (
                <div key={i}>
                  Page {s.page}, Line {s.line} (score {s.score})
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
