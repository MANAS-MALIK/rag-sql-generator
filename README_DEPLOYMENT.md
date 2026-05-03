# 🚀 Deployment Guide - RAG SQL Generator

## Deploy to Render (FREE)

### Prerequisites
1. GitHub account
2. Render account (sign up at https://render.com)

### Step 1: Push to GitHub

```bash
cd /Users/manasmalik/Desktop/rag_sql_project
git init
git add .
git commit -m "Initial commit - RAG SQL Generator"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy Backend on Render

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `rag-sql-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

5. **Add Environment Variables**:
   - `GEMINI_API_KEY` = `your_gemini_api_key_here`
   - `GROQ_API_KEY` = `your_groq_api_key_here`

6. Click **"Create Web Service"**

### Step 3: Update Frontend

Once deployed, Render will give you a URL like: `https://rag-sql-backend.onrender.com`

Update `frontend/index.html` line 65:
```javascript
const API = "https://rag-sql-backend.onrender.com";  // Your Render URL
```

### Step 4: Deploy Frontend (Optional)

**Option A: Netlify Drop**
1. Go to https://app.netlify.com/drop
2. Drag the `frontend` folder
3. Done! You'll get a URL like `https://your-app.netlify.app`

**Option B: Render Static Site**
1. New → Static Site
2. Connect GitHub repo
3. Publish directory: `frontend`
4. Done!

### Step 5: Test Your Deployment

1. Open your frontend URL
2. Upload `sample_queries.docx`
3. Generate SQL
4. Show to interviewer! 🎉

## Interview Talking Points

**"I deployed this full-stack RAG application using:"**
- ✅ FastAPI backend containerized with Docker
- ✅ Deployed on Render's free tier
- ✅ Environment variables for API key security (never hardcoded)
- ✅ CORS configured for frontend-backend communication
- ✅ Used Gemini for embeddings and FAISS for vector search
- ✅ Groq's LLaMA for SQL generation
- ✅ Simple HTML/JS frontend for demo purposes

**Architecture:**
- RAG pipeline: Document upload → Parse → Embed → FAISS index → Retrieve → LLM generation
- Production-ready: Docker, K8s configs included
- Scalable: Can handle multiple clients and query types
