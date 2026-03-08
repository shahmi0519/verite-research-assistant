from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Load the same embeddings model used during ingest
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load your saved FAISS index
vectorstore = FAISS.load_local(
    "./faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Test a few searches relevant to your PDFs
queries = [
    "labour rights",
    "economic policy",
    "governance reform",
]

for query in queries:
    print(f"\n Query: '{query}'")
    print("-" * 50)
    results = vectorstore.similarity_search(query, k=3)
    for r in results:
        print(f" {r.metadata['title']} | Page {r.metadata['page']}")
        print(f"   {r.page_content[:120].strip()}...")