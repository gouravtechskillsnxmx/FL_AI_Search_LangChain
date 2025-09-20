import os
import openai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Globals (simple)
CLIENT = None
COLLECTION = None
EMBED_MODEL = None
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

def init_chroma(chroma_dir="./chroma_db"):
    global CLIENT, COLLECTION, EMBED_MODEL
    # persistent local chroma
    CLIENT = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=chroma_dir))
    # use sentence-transformers to compute embeddings
    EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    # register embedding function adaptor
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    try:
        COLLECTION = CLIENT.get_collection("docs")
    except Exception:
        COLLECTION = CLIENT.create_collection("docs", embedding_function=ef)

def index_text_file(filename: str, text: str):
    global COLLECTION
    if COLLECTION is None:
        raise RuntimeError("Chroma not initialized")
    # naive split into chunks
    chunks = []
    chunk_size = 800
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    ids = [f"{filename}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]
    COLLECTION.add(ids=ids, documents=chunks, metadatas=metadatas)
    CLIENT.persist()

def retrieve(query: str, k=4):
    global COLLECTION
    if COLLECTION is None:
        raise RuntimeError("Chroma not initialized")
    res = COLLECTION.query(query_texts=[query], n_results=k)
    # result doc strings
    docs = []
    for docs_list in res['documents']:
        docs.extend(docs_list)
    return docs

def build_prompt(query: str, docs: list, options: dict):
    tone = options.get('tone', 'neutral')
    length = options.get('length', 'medium')
    # include retrieved docs as context
    ctx = "\n\n".join([f"Source: {d}" for d in docs])
    prompt = f"You are an assistant. Use the following context to answer the user's request.\n\nCONTEXT:\n{ctx}\n\nINSTRUCTION: {query}\n\nProvide a {length} length answer in a {tone} tone. Include short bullets if appropriate."
    return prompt

def call_model(prompt: str, max_tokens=512, temperature=0.7):
    if OPENAI_KEY:
        openai.api_key = OPENAI_KEY
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=temperature_from_value(temperature),
            max_tokens=max_tokens
        )
        return resp['choices'][0]['message']['content']
    else:
        # fallback: return prompt as stub when no OpenAI key provided
        return "[No OPENAI_API_KEY set] Prompt used:\n" + prompt[:2000]

def temperature_from_value(temp):
    try:
        t = float(temp)
    except Exception:
        t = 0.7
    return t

def generate_text(query: str, options: dict):
    docs = retrieve(query, k=4)
    prompt = build_prompt(query, docs, options)
    out = call_model(prompt, max_tokens=int(options.get('max_tokens',512)), temperature=options.get('temperature',0.7))
    return {"status":"succeeded", "output": out, "meta": {"retrieved": len(docs)}}
