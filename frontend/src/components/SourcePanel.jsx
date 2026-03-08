export function SourcePanel({ source, onClose }) {
  return (
    <div className="source-panel">

      <div className="source-panel-header">
        <span className="source-panel-title">Source</span>
        <button className="source-panel-close" onClick={onClose}>×</button>      
      </div>


      <div className="source-panel-body">
        <div className="source-meta">
          <strong>{source.title}</strong>
          Page {source.page}
        </div>

        <div className="source-chunk">
          "{source.chunk_preview}…"
        </div>
      </div>

    </div>
  )
}