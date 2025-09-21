import os
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
from typing import List

# RAG imports
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Load env
API_KEY = os.getenv('API_KEY', 'dev-key-123')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
CHROMA_DIR = os.getenv('CHROMA_DIR', '/data/chroma')

# Initialize app
app = FastAPI(title='Simple TextGen with RAG')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

class GenRequest(BaseModel):
    query: str
    options: dict = {}

# Chroma globals
CLIENT = None
COLLECTION = None
EMBED_FN = None

def init_chroma(chroma_dir: str = CHROMA_DIR):
    global CLIENT, COLLECTION, EMBED_FN
    if CLIENT is not None:
        return
    # Create local chroma client persisted to chroma_dir
    CLIENT = chromadb.Client(Settings(chroma_db_impl='duckdb+parquet', persist_directory=chroma_dir))
    # Use sentence-transformers embedding adaptor
    EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-MiniLM-L6-v2')
    try:
        COLLECTION = CLIENT.get_collection('docs')
    except Exception:
        COLLECTION = CLIENT.create_collection('docs', embedding_function=EMBED_FN)

@app.on_event('startup')
def startup_event():
    init_chroma(CHROMA_DIR)

@app.get('/health')
def health():
    return {'status':'ok'}

@app.post('/v1/index')
async def index_file(file: UploadFile = File(...), authorization: str = Header(None)):
    # simple API key check
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing API key')
    if authorization.split()[1] != API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    # naive chunking
    chunk_size = 800
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]
    COLLECTION.add(ids=ids, documents=chunks, metadatas=metadatas)
    CLIENT.persist()
    return {'status':'indexed', 'filename': file.filename, 'chunks': len(chunks)}

def retrieve(query: str, k: int = 4) -> List[str]:
    if COLLECTION is None:
        return []
    res = COLLECTION.query(query_texts=[query], n_results=k)
    docs = []
    for lst in res['documents']:
        docs.extend(lst)
    return docs

def build_prompt(query: str, docs: List[str], options: dict):
    tone = options.get('tone', 'neutral')
    length = options.get('length', 'medium')
    ctx = "\n\n".join([f"Source: {d}" for d in docs]) if docs else ''
    prompt = f"You are an assistant. Use the following context when helpful:\n\nCONTEXT:\n{ctx}\n\nINSTRUCTION: {query}\n\nProvide a {length} length answer in a {tone} tone. If the context is not relevant, answer from general knowledge."
    return prompt

def call_model(prompt: str, max_tokens: int = 512, temperature: float = 0.7):
    if OPENAI_KEY:
        try:
            openai.api_key = OPENAI_KEY
            resp = openai.ChatCompletion.create(
                model='gpt-4o-mini',
                messages=[{'role':'user','content':prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp['choices'][0]['message']['content']
        except Exception as e:
            return f"[OpenAI call failed] {e}\n\nPrompt used:\n{prompt[:2000]}"
    else:
        # fallback
        return "[No OPENAI_API_KEY set] " + prompt[:2000]

@app.post('/v1/generate')
def generate(req: GenRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing API key')
    if authorization.split()[1] != API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    query = req.query
    options = req.options or {}
    docs = retrieve(query, k=4)
    prompt = build_prompt(query, docs, options)
    out = call_model(prompt, max_tokens=int(options.get('max_tokens', 512)), temperature=float(options.get('temperature', 0.7)))
    return {'status':'succeeded', 'output': out, 'meta': {'retrieved': len(docs)}}

# helper script trigger endpoint (for testing)
@app.post('/v1/index-sample')
def index_sample(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing API key')
    if authorization.split()[1] != API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    # index a bundled sample doc
    sample_path = os.path.join(os.path.dirname(__file__), 'sample_docs.txt')
    if not os.path.exists(sample_path):
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write('This is a sample document about intermittent fasting. It discusses benefits and common patterns for beginners.')
    with open(sample_path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    # chunk and add
    chunk_size = 800
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    ids = [f"sample_{i}" for i in range(len(chunks))]
    metadatas = [{"source": 'sample_docs', "chunk": i} for i in range(len(chunks))]
    COLLECTION.add(ids=ids, documents=chunks, metadatas=metadatas)
    CLIENT.persist()
    return {'status':'indexed_sample', 'chunks': len(chunks)}
