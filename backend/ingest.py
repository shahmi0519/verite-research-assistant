import os
import argparse
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


def ingest(pdf_dir: str, index_dir: str):
    pdf_paths = list(Path(pdf_dir).glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found in {pdf_dir}")

    print(f"Found {len(pdf_paths)} PDFs")

    all_docs = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()

        # Attach metadata to every page
        title = pdf_path.stem.replace("_", " ").replace("-", " ").title()
        for page in pages:
            page.metadata["title"] = title
            page.metadata["source"] = pdf_path.name

        all_docs.extend(pages)
        print(f"  Loaded {len(pages)} pages from '{pdf_path.name}'")
        
    splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(all_docs)
    print(f"\nTotal chunks: {len(chunks)}")
    
    embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("Building FAISS index — this takes ~1 min...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(index_dir)
    print(f"FAISS index saved to '{index_dir}' ✓")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_dir",   default="./pdfs")
    parser.add_argument("--index_dir", default="./faiss_index")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    ingest(args.pdf_dir, args.index_dir)
    

