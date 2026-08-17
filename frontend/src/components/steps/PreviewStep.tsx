import type { GenerationRequest, RetrievedChunk } from "../../api/types";

type Props = {
  request: GenerationRequest;
  chunks: RetrievedChunk[] | null;
  busy: boolean;
  error: string | null;
  onRun: () => void;
};

export function PreviewStep({ request, chunks, busy, error, onRun }: Props) {
  return (
    <div className="step-body">
      <h2>Review the grounding</h2>
      <p className="lede">
        This is the source material the model will see. Generation itself arrives in the next
        milestone — for now you can check the retrieval is finding the right passages.
      </p>

      <div className="summary">
        <div>
          <span className="summary-key">Topic</span>
          <span className="summary-val">{request.topic || "—"}</span>
        </div>
        <div>
          <span className="summary-key">Type</span>
          <span className="summary-val">{request.problem_type}</span>
        </div>
        <div>
          <span className="summary-key">Difficulty</span>
          <span className="summary-val">{request.difficulty}</span>
        </div>
        <div>
          <span className="summary-key">Structure</span>
          <span className="summary-val">
            {request.num_steps} × {request.num_hints} hints
          </span>
        </div>
      </div>

      <button className="btn btn-primary btn-lg" onClick={onRun} disabled={busy}>
        {busy ? "Searching materials…" : chunks ? "Search again" : "Preview context"}
      </button>

      {error && <p className="error">{error}</p>}

      {chunks && (
        <div className="chunks">
          <h3>
            {chunks.length} passage{chunks.length === 1 ? "" : "s"} retrieved
          </h3>
          {chunks.map((chunk, index) => (
            <article key={index} className="chunk" style={{ animationDelay: `${index * 60}ms` }}>
              <header>
                <span className="chunk-badge">page {chunk.citation_page ?? "?"}</span>
                <span className="chunk-idx">chunk {chunk.chunk_index ?? "?"}</span>
              </header>
              <p>{chunk.text.slice(0, 460)}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
