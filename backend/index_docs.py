# helper script to index files in backend/app/docs
import os
from generate import index_text_file, init_chroma

if __name__ == '__main__':
    CHROMA_DIR = os.getenv('CHROMA_DIR', './chroma_db')
    init_chroma(CHROMA_DIR)
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir, exist_ok=True)
        # create sample doc
        with open(os.path.join(docs_dir, 'sample.txt'), 'w') as f:
            f.write('This is a sample document for RAG. The tool should use it as context when relevant.')
    for fname in os.listdir(docs_dir):
        path = os.path.join(docs_dir, fname)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as fh:
                text = fh.read()
            index_text_file(fname, text)
            print('Indexed', fname)
