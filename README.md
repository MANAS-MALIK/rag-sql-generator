# RAG SQL Generator — Full Project

## Project Structure
```
rag_sql_project/
├── backend/
│   ├── main.py            ← FastAPI app (all RAG logic)
│   ├── requirements.txt   ← Python dependencies
│   └── Dockerfile         ← Container definition
├── frontend/
│   └── index.html         ← Simple HTML UI
├── k8s/
│   └── deployment.yaml    ← Kubernetes config
├── docker-compose.yml     ← Run everything locally
├── .env.example           ← Copy to .env, add your keys
└── .gitignore
```

---

## Run Locally (without Docker)

```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
export GROQ_API_KEY=your_key
uvicorn main:app --reload
# API live at http://localhost:8000
# Docs at   http://localhost:8000/docs
```

---

## Run with Docker

```bash
# 1. Copy .env.example to .env and fill keys
cp .env.example .env

# 2. Build and run
docker-compose up --build

# API live at http://localhost:8000
```

---

## Deploy FREE on Render.com

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set Build Command: `pip install -r backend/requirements.txt`
5. Set Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
6. Add environment variables in Render dashboard:
   - GEMINI_API_KEY
   - GROQ_API_KEY
7. Deploy → get free public URL

---

## Deploy with Kubernetes (local via Minikube)

```bash
# Install minikube: https://minikube.sigs.k8s.io/docs/start/
minikube start

# Build image
docker build -t rag-sql:latest ./backend

# Load into minikube
minikube image load rag-sql:latest

# Create secrets
kubectl create secret generic rag-secrets \
  --from-literal=GEMINI_API_KEY=your_key \
  --from-literal=GROQ_API_KEY=your_key

# Deploy
kubectl apply -f k8s/deployment.yaml

# Get URL
minikube service rag-sql-service --url
```

---

## API Endpoints

| Method | URL | What it does |
|---|---|---|
| GET | /health | Check if API is running |
| POST | /upload | Upload .docx file |
| POST | /generate-sql | Generate SQL for new client |
| GET | /queries | List all loaded queries |

---

## Interview Answer — How did you deploy this?

> "I containerised the FastAPI backend using Docker and wrote a docker-compose file for local development. For free cloud deployment, I used Render.com which pulls from GitHub and auto-deploys. I also wrote a Kubernetes deployment.yaml with a Deployment and Service resource, which I tested locally using Minikube. API keys are stored as Kubernetes Secrets — never hardcoded."
