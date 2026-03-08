import { useState, useRef, useEffect } from "react"
import ChatMessage from "./components/ChatMessage"
import { SourcePanel } from "./components/SourcePanel"
import TypingIndicator from "./components/TypingIndicator"
import "./App.css"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

const WELCOME = {
  id: "welcome",
  role: "assistant",
  content: "Hello! I'm **Vera**, your research guide to Verité Research publications. I can help you explore their work on economics, governance, labour rights, and South Asian policy.\n\nAsk me anything — or just say hi! ",
  sources: [],
  searchUsed: false,
}

export default function App() {
  const [messages, setMessages]     = useState([WELCOME])
  const [input, setInput]           = useState("")
  const [isLoading, setIsLoading]   = useState(false)
  const [sessionId, setSessionId]   = useState(null)
  const [activeSource, setActiveSource] = useState(null)

  const [userId] = useState(
    () => `user_${Math.random().toString(36).slice(2, 9)}`
  )

  const bottomRef = useRef(null)
  const inputRef  = useRef(null)


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const sendMessage = async () => {

    const text = input.trim()
    if (!text || isLoading) return


    setMessages(prev => [...prev, {
      id: Date.now(), role: "user", content: text, sources: []
    }])

    setInput("")
    setIsLoading(true)
    setActiveSource(null)


    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          user_id: userId,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Server error")

      setSessionId(data.session_id)

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: data.reply,
        sources: data.sources || [],
        searchUsed: data.search_used,
      }])
    } 


    catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: `⚠️ Error: ${err.message}`,
        sources: [],
        searchUsed: false,
      }])
    } 

    
    finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }

  }


  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }


  const suggestions = [
    "What does Verité say about labour rights?",
    "What is forced labour?",
    "What are Verité's economic findings?",
    "Tell me about governance research",
  ]



  return (
    <div className="app">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="sidebar-logo">
          <div className="logo-mark">V</div>
          <div className="logo-text">
            <span className="logo-title">Vera</span>
            <span className="logo-sub">Verité Research AI</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">About</p>
          <p className="sidebar-desc">
            Vera draws from Verité Research's publications on
            economics, governance, labour, and South Asian policy.
          </p>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Session</p>
          {sessionId
            ? <span className="session-active">● Active</span>
            : <span className="session-idle">○ Not started</span>
          }
        </div>

        <div className="sidebar-footer">
          <a href="https://www.veriteresearch.org" target="_blank" rel="noreferrer">
            veriteresearch.org ↗
          </a>
        </div>
      </aside>



      {/* Chat area */}
      <main className="chat-main">

        <header className="chat-header">
          <div>
            <span className="header-name">Vera</span>
            <span className="header-tag">Verité Research Assistant</span>
          </div>
          <div className="header-pill">Gemini · FAISS · LangChain</div>
        </header>

        <div className="messages-area">
          {messages.map(msg => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onSourceClick={setActiveSource}
            />
          ))}

          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />

        </div>

        {/* Suggestions — only on first load */}
        {messages.length === 1 && (
          <div className="suggestions">
            {suggestions.map(q => (
              <button
                key={q}
                className="suggestion-chip"
                onClick={() => setInput(q)}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input bar */}
        <div className="input-row">
          
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ask about Verité Research publications…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
          />
          
          <button
            className={`send-btn ${!input.trim() || isLoading ? "disabled" : ""}`}
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
          >
            ➤
          </button>
        </div>
      </main>



      {/* Source panel */}
      {activeSource && (
        <SourcePanel
          source={activeSource}
          onClose={() => setActiveSource(null)}
        />
      )}

      

    </div>
  )
}