import os
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .generate import generate_text, index_text_file, init_chroma
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-key-123")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

app = FastAPI(title="TextGen-RAG Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# initialize chroma
init_chroma(CHROMA_DIR)

class GenRequest(BaseModel):
    query: str
    options: dict = {}

@app.post("/v1/index")
async def index(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    if authorization.split()[1] != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    content = await file.read()
    text = content.decode('utf-8')
    index_text_file(file.filename, text)
    return {"status":"indexed", "filename": file.filename}

@app.post("/v1/generate")
async def generate(req: GenRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    if authorization.split()[1] != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    out = generate_text(req.query, req.options)
    return out

@app.get("/health")
async def health():
    return {"status":"ok"}
