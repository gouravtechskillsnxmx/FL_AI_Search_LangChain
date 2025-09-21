import os
from main import init_chroma, COLLECTION, CLIENT

if __name__ == '__main__':
    init_chroma()
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir, exist_ok=True)
        with open(os.path.join(docs_dir, 'sample.txt'), 'w', encoding='utf-8') as f:
            f.write('Sample document for RAG indexing.')
    for fname in os.listdir(docs_dir):
        path = os.path.join(docs_dir, fname)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as fh:
                text = fh.read()
            # naive chunking
            chunk_size = 800
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            ids = [f"{fname}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": fname, "chunk": i} for i in range(len(chunks))]
            COLLECTION.add(ids=ids, documents=chunks, metadatas=metadatas)
    CLIENT.persist()
    print('Indexed docs in', docs_dir)
