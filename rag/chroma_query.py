import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
import os
print("OPENAI_API_KEY:")
print(os.getenv("OPENAI_API_KEY"))

# Ajusta la ruta a tu base de datos ChromaDB
CHROMA_PATH = './chroma_db'

class ChromaRAG:
    def __init__(self):
        self.vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=OpenAIEmbeddings()
        )

    def query(self, query_text, n_results=3):
        print(f"[RAG] Query received: {query_text}")
        all_docs = self.vectorstore.get()
        print(f"Number of documents: {len(all_docs['documents'])}")
        for i, doc in enumerate(all_docs['documents']):
            print(f"\n--- Document {i+1} ---")
            print(doc)
            print("Metadata:", all_docs['metadatas'][i])
        sample_docs = self.vectorstore.get(limit=5, include=["documents", "metadatas"])
        print(f"Sample documents: {sample_docs['documents']}")
        print(f"Sample metadata: {sample_docs['metadatas']}")
        results = self.vectorstore.similarity_search(query_text, k=n_results)
        print(f"[RAG] Results found: {len(results)}")
        for r in results:
            print(f"[RAG] Document: {r.page_content}")
        # Formatear resultados para el endpoint
        return {
            "documents": [r.page_content for r in results],
            "metadatas": [r.metadata for r in results]
        }

if __name__ == '__main__':
    rag = ChromaRAG()
    query = input('Consulta: ')
    print(rag.query(query)) 