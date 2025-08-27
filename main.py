
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os, random, uuid

app = FastAPI()

# CORS (relaxed; you can tighten later if same-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# SESSION MANAGEMENT
# -------------------
sessions = {}

@app.get("/api/session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "scenario": random.choice(["Warehouse Fire", "Residential Fire", "Wildland Fire"]),
        "injects": [],
        "log": []
    }
    return {"session_id": session_id, "scenario": sessions[session_id]["scenario"]}

# -------------------
# CHAT ENDPOINT
# -------------------
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or session_id not in sessions:
        return JSONResponse({"error": "Invalid session"}, status_code=400)

    session = sessions[session_id]
    session["log"].append({"user": message})

    response = f"Received: {message}. Continue managing {session['scenario']}."

    # Random inject (30% chance)
    if random.random() < 0.3:
        inject = random.choice([
            "Power lines are down near the incident.",
            "Weather is changing — high winds developing.",
            "An injured civilian is reported nearby.",
            "Water supply issues detected.",
            "Additional units delayed by traffic."
        ])
        session["injects"].append(inject)
        response += f" 🚨 Inject: {inject}"

    return {"response": response}

# -------------------
# REPORT (PDF) ENDPOINT
# -------------------
@app.get("/api/report/{session_id}")
def get_report(session_id: str):
    if session_id not in sessions:
        return JSONResponse({"error": "Invalid session"}, status_code=400)

    session = sessions[session_id]
    filename = f"report_{session_id}.pdf"
    # Use tmp path in container/host
    tmp_dir = "/tmp" if os.path.isdir("/tmp") else "."
    filepath = os.path.join(tmp_dir, filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Incident Command Training Report")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 75, f"Scenario: {session['scenario']}")

    # Student Actions
    y = height - 110
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Student Actions Log:")
    y -= 18
    c.setFont("Helvetica", 10)
    for entry in session["log"]:
        for line in wrap_text(f"- {entry['user']}", 90):
            c.drawString(60, y, line)
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 50

    # Injects
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Dynamic Injects Encountered:")
    y -= 18
    c.setFont("Helvetica", 10)
    if session["injects"]:
        for inj in session["injects"]:
            for line in wrap_text(f"- {inj}", 90):
                c.drawString(60, y, line)
                y -= 14
                if y < 50:
                    c.showPage()
                    y = height - 50
    else:
        c.drawString(60, y, "- None recorded")
        y -= 14

    # Feedback
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Feedback:")
    y -= 18
    c.setFont("Helvetica", 10)
    feedback = (
        "Good job applying ICS principles. Ensure each inject is addressed with clear ICS actions "
        "(e.g., RIT deployment, exposure protection, resource requests)."
    )
    for line in wrap_text(feedback, 95):
        c.drawString(60, y, line)
        y -= 14
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return FileResponse(filepath, filename=filename, media_type="application/pdf")


def wrap_text(text, max_chars):
    # simple greedy wrapper for PDF text
    words = text.split()
    lines = []
    cur = []
    n = 0
    for w in words:
        if n + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            n += len(w) + (1 if cur[:-1] else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            n = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

# -------------------
# SERVE REACT FRONTEND (build)
# -------------------
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "build")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/")
    def read_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/{full_path:path}")
    def serve_react_app(full_path: str):
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
