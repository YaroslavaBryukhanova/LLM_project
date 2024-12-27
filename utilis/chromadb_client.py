import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')
print(chromadb.__version__)
chroma_client = chromadb.PersistentClient(path="chroma_persist")