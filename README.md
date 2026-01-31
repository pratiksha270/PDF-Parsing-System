# 📄 Hybrid PDF Parser with OCR, Full‑Text Search & Semantic Search

A full‑stack web application that allows users to upload and index PDFs, perform **full‑text search**, **semantic search**, and **question answering** with source references. The system supports **OCR for scanned PDFs** and provides an interactive **PDF viewer** for opening results directly at the relevant page.

This project is designed as an academic + portfolio‑ready implementation of a **RAG‑style PDF parser**.

---

## 🚀 Features

* 📤 Upload and index single or multiple PDF files
* 🧾 OCR support for scanned / image‑based PDFs (Tesseract)
* 🔍 Full‑Text Search using SQLite FTS
* 🧠 Semantic Search using Sentence Transformers embeddings
* ❓ Question Answering over PDF content
* 📌 Source tracking with page‑level references
* 📄 Clickable search results that open the PDF at the correct page
* 🌐 React frontend with Flask backend

---

## 🛠️ Tech Stack

### Frontend

* React
* Vite
* Axios
* HTML, CSS

### Backend

* Python
* Flask
* Flask‑CORS
* SQLite (FTS5)
* PyMuPDF (PDF parsing & viewer support)
* Tesseract OCR (pytesseract)
* Sentence‑Transformers (`all‑MiniLM‑L6‑v2`)

---

## 📁 Project Structure

```
pdf-parser-project/
│
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   ├── uploads/        # ignored in git
│   └── venv/           # ignored in git
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## ▶️ How to Run Locally

### 🔧 Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python server.py
```

Backend will start at:

```
http://127.0.0.1:5000
```

---

### 🎨 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:

```
http://localhost:5173
```

---

## 🔄 Application Workflow

1. User uploads PDF(s) from the frontend
2. Backend extracts text using PyMuPDF
3. OCR is applied if the PDF is scanned
4. Text is stored in SQLite with FTS indexing
5. Sentence embeddings are generated for semantic search
6. User performs:

   * Full‑Text Search
   * Semantic Search
   * Question Answering
7. Results show relevant text snippets with page numbers
8. Clicking a result opens the PDF at the exact page

---

## 📌 Use Cases

* Academic document search
* Research paper analysis
* Legal or policy document parsing
* PDF‑based question answering systems
* Learning RAG (Retrieval‑Augmented Generation) concepts

---

## 📈 Future Enhancements

* 🚀 Vector database integration (FAISS / Chroma)
* ☁️ Cloud deployment (AWS / Render / Vercel)
* 🔐 User authentication
* ✍️ PDF annotations and highlights
* ⚡ Faster embedding and indexing pipeline

---

## 👩‍💻 Author

**Aditi Rawat**
Computer Science Engineering Student

---

## ⭐ Acknowledgements

* PyMuPDF
* Tesseract OCR
* Sentence Transformers
* React & Flask open‑source community

---

If you find this project useful, feel free to ⭐ star the repository!
