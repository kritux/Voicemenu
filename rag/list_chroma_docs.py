from dotenv import load_dotenv
load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=OpenAIEmbeddings()
)

# This will return all documents in the vectorstore
all_docs = vectorstore.get()
print(f"Number of documents: {len(all_docs['documents'])}")
for i, doc in enumerate(all_docs['documents']):
    print(f"\n--- Document {i+1} ---")
    print(doc)
    print("Metadata:", all_docs['metadatas'][i])