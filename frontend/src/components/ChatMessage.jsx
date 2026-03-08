function renderMarkdown(text) {
  return text
    .split("\n\n")
    .map((para, i) => {
      let 
      
      html = para.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      html = html.replace(/\*(.*?)\*/g, "<em>$1</em>")
      html = html.replace(/`(.*?)`/g, "<code>$1</code>")
      html = html.replace(/\n/g, "<br/>")

      return `<p key="${i}">${html}</p>`
    })
    .join("")
}



export default function ChatMessage({ message, onSourceClick }) {
  const isUser = message.role === "user"

  return (
    <div className={`message ${message.role}`}>

      <div className="msg-avatar">{isUser ? "U" : "V"}</div>

      <div className="msg-body">
        {message.searchUsed && (
          <span className="search-badge">
            Retrieved from knowledge base
          </span>
        )}

        <div
          className="msg-bubble"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
        />

        {message.sources?.length > 0 && (
          <div className="sources-row">
            {message.sources.map((src, i) => (
              <button
                key={i}
                className="source-chip"
                onClick={() => onSourceClick(src)}
              >
                📓 {src.title} · p.{src.page}
              </button>
            ))}
          </div>
        )}
      </div>
      
    </div>
  )
}