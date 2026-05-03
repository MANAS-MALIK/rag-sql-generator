# ============================================================
# RAG SQL Generator — FastAPI Backend
# ============================================================
# Run locally:  uvicorn main:app --reload
# Run via Docker: docker build -t rag-sql . && docker run -p 8000:8000 rag-sql
# ============================================================

import os
import numpy as np
import faiss
from docx import Document as DocxDocument
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import shutil

# ── App setup ──────────────────────────────────────────────
app = FastAPI(title="RAG SQL Generator", version="1.0.0")

# Allow any frontend (React, HTML) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production: replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Keys (loaded from environment variables — NEVER hardcode) ──
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_KEY   = os.environ.get("GROQ_API_KEY")

if not GEMINI_KEY or not GROQ_KEY:
    raise RuntimeError("Set GEMINI_API_KEY and GROQ_API_KEY environment variables")

genai.configure(api_key=GEMINI_KEY)

# ── In-memory store (loaded once when .docx is uploaded) ───
documents  = []   # list of { page_content, metadata, embedding }
faiss_index = None
EMBEDDING_DIM = 768   # gemini-embedding-001 produces 768-dim vectors


# ── Helper: get embedding from Gemini ──────────────────────
def get_embedding(text: str) -> list:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text
    )
    return result["embedding"]   # list of 768 floats


# ── Helper: parse .docx into structured documents ──────────
def parse_docx(filepath: str) -> list:
    doc = DocxDocument(filepath)
    parsed = []
    current_meta = {}
    current_sql  = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        if "Client:" in text and "Query:" in text:
            # Save previous block
            if current_meta and current_sql:
                parsed.append({
                    "client":     current_meta["client"],
                    "query_name": current_meta["query_name"],
                    "sql":        "\n".join(current_sql).strip()
                })
            # Parse new heading: "Client: Kate | Query: SKU Status"
            parts = text.split("|")
            current_meta = {
                "client":     parts[0].replace("Client:", "").strip(),
                "query_name": parts[1].replace("Query:", "").strip()
            }
            current_sql = []
        else:
            current_sql.append(text)

    # Don't forget last block
    if current_meta and current_sql:
        parsed.append({
            "client":     current_meta["client"],
            "query_name": current_meta["query_name"],
            "sql":        "\n".join(current_sql).strip()
        })

    return parsed


# ── Helper: build FAISS index from documents ───────────────
def build_index(docs: list):
    global documents, faiss_index

    documents = []
    for q in docs:
        page_content = f"Query: {q['query_name']}\n{q['sql']}"
        embedding    = get_embedding(page_content)
        documents.append({
            "page_content": page_content,
            "metadata":     {"client": q["client"], "query_name": q["query_name"]},
            "embedding":    embedding
        })

    vectors     = np.array([d["embedding"] for d in documents], dtype="float32")
    # Dynamically detect embedding dimension from actual embeddings
    actual_dim = vectors.shape[1]
    faiss_index = faiss.IndexFlatL2(actual_dim)
    faiss_index.add(vectors)


# ── Helper: retrieve best matching document ─────────────────
def retrieve(prompt: str, query_name_filter: str = None, top_k: int = 1) -> list:
    if not documents or faiss_index is None:
        return []

    # Step 1: Metadata filter
    candidates = [
        (i, d) for i, d in enumerate(documents)
        if (not query_name_filter or
            d["metadata"]["query_name"].lower() == query_name_filter.lower())
    ]
    if not candidates:
        return []

    # Step 2: Embed the query
    query_vec = np.array([get_embedding(prompt)], dtype="float32")

    # Step 3: Build sub-index from filtered candidates only
    filtered_vecs = np.array(
        [documents[i]["embedding"] for i, _ in candidates], dtype="float32"
    )
    actual_dim = filtered_vecs.shape[1]
    sub_index = faiss.IndexFlatL2(actual_dim)
    sub_index.add(filtered_vecs)

    # Step 4: Similarity search
    k = min(top_k, len(candidates))
    distances, indices = sub_index.search(query_vec, k)

    results = []
    for rank, idx in enumerate(indices[0]):
        _, orig_doc = candidates[idx]
        results.append({"rank": rank + 1, "document": orig_doc})

    return results


# ══════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════

# ── Health check ───────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "documents_loaded": len(documents),
        "index_ready": faiss_index is not None
    }


# ── Upload .docx → parse + embed + store in FAISS ──────────
@app.post("/upload")
async def upload_docx(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse and embed
    parsed = parse_docx(temp_path)
    if not parsed:
        raise HTTPException(400, "No queries found. Check .docx format.")

    build_index(parsed)

    return {
        "message": f"Loaded {len(documents)} queries into FAISS index",
        "queries": [
            {"client": d["metadata"]["client"], "query_name": d["metadata"]["query_name"]}
            for d in documents
        ]
    }


# ── Generate SQL for new client ─────────────────────────────
class GenerateRequest(BaseModel):
    new_client:       str
    reference_client: str
    query_type:       str
    modifications:    str

@app.post("/generate-sql")
def generate_sql(req: GenerateRequest):
    if not documents:
        raise HTTPException(400, "No documents loaded. Upload a .docx file first.")

    # Build retrieval prompt
    user_prompt = (
        f"Generate {req.query_type} SQL for {req.new_client}. "
        f"Based on {req.reference_client} logic. "
        f"Changes: {req.modifications}"
    )

    # Retrieve best matching SQL
    results = retrieve(user_prompt, query_name_filter=req.query_type, top_k=1)
    if not results:
        raise HTTPException(404, f"No query found with type: {req.query_type}")

    retrieved_doc = results[0]["document"]

    # Build LLM prompt
    prompt = f"""You are a SQL expert.

Reference SQL ({req.reference_client} - {req.query_type}):
{retrieved_doc['page_content']}

Generate a modified SQL for client: {req.new_client}
Modifications: {req.modifications}
Keep all other logic the same.
Return ONLY the SQL. No explanation."""

    # Call Groq (LLaMA) via direct HTTP request
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        verify=False  # Bypass SSL verification to avoid certificate issues
    )
    
    if response.status_code != 200:
        raise HTTPException(500, f"Groq API error: {response.text}")
    
    generated_sql = response.json()["choices"][0]["message"]["content"]

    return {
        "new_client":     req.new_client,
        "query_type":     req.query_type,
        "reference_used": retrieved_doc["metadata"]["client"],
        "generated_sql":  generated_sql
    }


# ── List all loaded queries ─────────────────────────────────
@app.get("/queries")
def list_queries():
    return {
        "total": len(documents),
        "queries": [
            {"client": d["metadata"]["client"], "query_name": d["metadata"]["query_name"]}
            for d in documents
        ]
    }
