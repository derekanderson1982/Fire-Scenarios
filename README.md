# ICS Trainer Bot (Single-Folder)

An Incident Command System (ICS) training chatbot with random fire scenarios, dynamic injects (30% per message), and PDF report export.

## 🚀 Run Locally

```bash
# Build frontend
cd frontend
npm install
npm run build

# Run backend (serves frontend too)
cd ..
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open: http://localhost:8000

## 🌐 Deploy on Render

1. Push this folder to GitHub
2. Go to https://render.com → New → Web Service → select repo
3. Render auto-detects `render.yaml` and deploys
4. Share your public URL with students

## 🧩 API Endpoints
- `GET /api/session` → creates a new session (returns `session_id`, scenario)
- `POST /api/chat` → body `{ session_id, message }` (returns bot response, with random injects)
- `GET /api/report/{session_id}` → downloads a PDF report
