import os
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Gift Sniper Dashboard")
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

DATA_DIR = os.getenv("DATA_DIR", "/data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")
LOG_PATH = os.path.join(DATA_DIR, "sniper.log")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme123")

def auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True

def read_json(path):
    if not os.path.exists(path): return {} if "config" in path else []
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, dependencies=[Depends(auth)])
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/config", dependencies=[Depends(auth)])
async def get_config(): return JSONResponse(read_json(CONFIG_PATH))

@app.post("/api/config", dependencies=[Depends(auth)])
async def update_config(payload: dict):
    required = ["api_id", "api_hash", "phone"]
    if not all(k in payload for k in required):
        raise HTTPException(400, "Missing required fields")
    write_json(CONFIG_PATH, payload)
    return {"status": "saved"}

@app.get("/api/events", dependencies=[Depends(auth)])
async def get_events(): return JSONResponse(read_json(EVENTS_PATH))

@app.get("/api/logs", dependencies=[Depends(auth)])
async def get_logs():
    if not os.path.exists(LOG_PATH): return ""
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return f.read()[-20000:]
