import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage


# PROMPT

SYSTEM_PROMPT = """You are Vera, a knowledgeable research assistant for Verité Research — \
a Sri Lankan think tank producing independent analysis on economics, politics, \
finance, and governance in South and Southeast Asia.

Your personality:
- Warm, precise, and intellectually curious
- You communicate clearly, referencing evidence from Verité publications
- You never speculate beyond what the documents support

Your rules (follow STRICTLY):
1. GREETINGS / SMALL TALK: Respond naturally and briefly. Do NOT search.
2. QUESTIONS FROM MEMORY: Answer from conversation history. Do NOT search again.
3. VERITE CONTENT QUESTIONS: Search and cite the source document, page number.
4. OUT-OF-SCOPE: Politely decline. Say you only assist with Verité publications.
5. BORDERLINE (general terms relevant to Verité's work e.g. "What is forced labour?"):
   Briefly define the concept, then show what Verité's research says about it.
6. CITATIONS: Always end with a Sources section — document title, page number, section.

Long-term context about this user (if any):
{long_term_context}
"""

INTENT_PROMPT = """Classify the user message into exactly one category.
Reply with ONLY the label — nothing else.

Categories:
- GREETING        (hello, hi, thanks, bye, small talk)
- MEMORY          (follow-up answerable from prior conversation)
- VERITE_SEARCH   (question about Verité Research publications content)
- OUT_OF_SCOPE    (unrelated to Verité's work)
- BORDERLINE      (general concept directly relevant to Verité topics)

Conversation so far (last 4 turns):
{history}

New message: {message}

Category:"""




#

FAISS_INDEX_PATH = os.environ.get("FAISS_INDEX_PATH", "./faiss_index")

class VeriteAgent:
    def __init__(self, user_id: str = "anonymous", long_term_context: str = ""):
        self.user_id = user_id
        self.long_term_context = long_term_context

        # LLM for answering
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0.3,
        )

        # LLM for classifying 
        self.classifier_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0.0,
        )

        # Short-term memory — last 10 turns
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history",
        )

        self.system_message = SYSTEM_PROMPT.format(
            long_term_context=long_term_context or "None yet."
        )

        self._load_retriever()
        
        
        
    # Hybrid search
    
    def _load_retriever(self):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        try:
            faiss_store = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            faiss_retriever = faiss_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4},
            )

            # BM25 - raw documents
            all_docs = list(faiss_store.docstore._dict.values())
            bm25_retriever = BM25Retriever.from_documents(all_docs, k=4)

            # Combine — 60% vector and 40% keyword
            self.retriever = EnsembleRetriever(
                retrievers=[faiss_retriever, bm25_retriever],
                weights=[0.6, 0.4],
            )
            self.retriever_loaded = True
            print("Retriever loaded ")

        except Exception as e:
            print(f"[WARNING] Could not load FAISS index: {e}")
            self.retriever = None
            self.retriever_loaded = False
            
    
    
    
    # Helper
    
    def _classify_intent(self, message: str) -> str:
        history_text = self._get_history_text(n=4)
        prompt = INTENT_PROMPT.format(
            history=history_text,
            message=message
        )
        result = self.classifier_llm.invoke([HumanMessage(content=prompt)])
        label = result.content.strip().upper()

        for valid in ["GREETING", "MEMORY", "VERITE_SEARCH", "OUT_OF_SCOPE", "BORDERLINE"]:
            if valid in label:
                return valid
        return "VERITE_SEARCH"  

    def _get_history_text(self, n: int = 10) -> str:
        messages = self.memory.chat_memory.messages[-(n * 2):]
        lines = []
        for m in messages:
            role = "User" if isinstance(m, HumanMessage) else "Vera"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines) if lines else "(no prior conversation)"

    def _format_sources(self, docs) -> list[dict]:
        sources = []
        seen = set()
        for doc in docs:
            meta = doc.metadata
            key = (meta.get("source", ""), meta.get("page", ""))
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "title": meta.get("title", "Unknown"),
                "page": meta.get("page", "?"),
                "chunk_preview": doc.page_content[:200].replace("\n", " "),
            })
        return sources
    
    
    async def chat(self, user_message: str) -> dict[str, Any]:
        intent = self._classify_intent(user_message)
        sources = []
        search_used = False
        history_text = self._get_history_text()

        messages = [SystemMessage(content=self.system_message)]

        if intent == "GREETING":
            messages.append(HumanMessage(content=user_message))

        elif intent == "OUT_OF_SCOPE":
            reply = (
                "I'm Vera, and I'm here specifically to help with Verité Research "
                "publications. That topic falls outside what I can assist with — but "
                "if you have questions about Verité's work on economics, governance, "
                "labour, or South Asian policy, I'd love to help!"
            )
            self.memory.chat_memory.add_user_message(user_message)
            self.memory.chat_memory.add_ai_message(reply)
            return {"reply": reply, "sources": [], "search_used": False}

        elif intent == "MEMORY":
            messages.append(HumanMessage(
                content=(
                    f"Conversation so far:\n{history_text}\n\n"
                    f"User: {user_message}\n\n"
                    "Answer using the conversation history above. Do not search."
                )
            ))

        elif intent in ("VERITE_SEARCH", "BORDERLINE"):
            if not self.retriever_loaded:
                reply = "My knowledge base isn't loaded yet. Please ensure the PDFs have been ingested."
                return {"reply": reply, "sources": [], "search_used": False}

            # Hybrid search
            docs = self.retriever.invoke(user_message)
            search_used = True
            sources = self._format_sources(docs)

            # Build context string from retrieved chunks
            context = "\n\n---\n\n".join(
                f"[Source: {d.metadata.get('title', '?')}, "
                f"Page {d.metadata.get('page', '?')}]\n{d.page_content}"
                for d in docs
            )

            borderline_note = (
                "\nThis is a borderline question. First briefly define the concept, "
                "then ground your answer in what Verité's documents say.\n"
                if intent == "BORDERLINE" else ""
            )

            messages.append(HumanMessage(
                content=(
                    f"Conversation so far:\n{history_text}\n\n"
                    f"Retrieved context from Verité publications:\n{context}\n\n"
                    f"{borderline_note}"
                    f"User question: {user_message}\n\n"
                    "Answer using the retrieved context and cite sources at the end."
                )
            ))

        
        response = self.llm.invoke(messages)
        reply = response.content.strip()

        # Save to short time memory
        self.memory.chat_memory.add_user_message(user_message)
        self.memory.chat_memory.add_ai_message(reply)

        return {"reply": reply, "sources": sources, "search_used": search_used}