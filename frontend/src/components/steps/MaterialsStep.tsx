import { useState } from "react";
import { api } from "../../api/client";
import type { SourceDocument } from "../../api/types";
import { DropZone } from "../DropZone";
import { ProgressBar } from "../ProgressBar";

type Props = {
  projectId: number;
  documents: SourceDocument[];
  onChanged: () => void;
};

/** Reading the document is one opaque call, so only indexing reports a count. */
const INGESTION_LABELS = ["Reading the document", "Indexing the text"];

const STATUS_TEXT: Record<SourceDocument["status"], string> = {
  pending: "Extracting…",
  indexed: "Ready",
  failed: "Failed",
};

export function MaterialsStep({ projectId, documents, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      await api.uploadDocument(projectId, file);
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(doc: SourceDocument) {
    if (!confirm(`Remove “${doc.filename}”? Its extracted text will be deleted too.`)) return;
    setRemoving(doc.id);
    setError(null);
    try {
      await api.deleteDocument(projectId, doc.id);
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRemoving(null);
    }
  }

  return (
    <div className="step-body">
      <h2>Add your materials</h2>
      <p className="lede">
        Textbook chapters, lecture slides, worksheets. Everything you generate will be grounded
        in these.
      </p>

      <DropZone onFile={upload} busy={busy} />
      {error && <p className="error">{error}</p>}

      {documents.length > 0 && (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.id} className={`doc doc-${doc.status}`}>
              <span className="doc-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path
                    d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <div className="doc-main">
                <span className="doc-name">{doc.filename}</span>
                {doc.error && <span className="doc-error">{doc.error}</span>}
                {doc.status === "pending" && (
                  <ProgressBar
                    done={doc.progress_done}
                    total={doc.progress_total}
                    labels={INGESTION_LABELS}
                  />
                )}
              </div>
              <span className="doc-meta">
                {doc.status === "indexed" && <span className="chips">{doc.chunk_count} chunks</span>}
                <span className={`pill pill-${doc.status}`}>{STATUS_TEXT[doc.status]}</span>
                <button
                  type="button"
                  className="icon-btn"
                  title={`Remove ${doc.filename}`}
                  aria-label={`Remove ${doc.filename}`}
                  disabled={removing === doc.id}
                  onClick={() => remove(doc)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      d="M6 6l12 12M18 6L6 18"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
