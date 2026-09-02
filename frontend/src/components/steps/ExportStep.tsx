import { useState } from "react";
import { api } from "../../api/client";
import type { ExportResult, Project, ProjectUpdate } from "../../api/types";

type Props = {
  projectId: number;
  project: Project | null;
  onProjectChange: (patch: ProjectUpdate) => void;
};

const SUGGESTED_LICENSE = "https://creativecommons.org/licenses/by/4.0/ <CC BY 4.0>";

export function ExportStep({ projectId, project, onProjectChange }: Props) {
  const [result, setResult] = useState<ExportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.exportProject(projectId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const skipped = Object.entries(result?.skipped ?? {});

  return (
    <div className="step-body">
      <h2>Export</h2>
      <p className="lede">
        Writes every problem in this project as an OATutor content source. Drop the folder into an
        OATutor checkout under <code>content-sources/</code>.
      </p>

      <div className="summary">
        <div>
          <span className="summary-key">Source name</span>
          <span className="summary-val">{project?.source_name ?? "-"}</span>
        </div>
      </div>

      <label className="field-block">
        <span className="select-label">Licence</span>
        <input
          key={`${project?.id}:${project?.license ?? ""}`}
          className="text-input"
          defaultValue={project?.license ?? ""}
          placeholder={SUGGESTED_LICENSE}
          onBlur={(event) => {
            const value = event.target.value.trim();
            if (value !== (project?.license ?? "")) onProjectChange({ license: value });
          }}
        />
        <p className="field-hint">Written onto every exported problem and hint.</p>
      </label>

      <button className="btn btn-primary btn-lg" onClick={run} disabled={busy}>
        {busy ? "Writing…" : result ? "Export again" : "Export to OATutor"}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <p className="field-hint">
            Written to <code>{result.root}</code>
          </p>

          <ul className="doc-list">
            {result.written.map((id) => (
              <li key={id} className="doc">
                <span className="doc-main">
                  <span className="doc-name">{id}</span>
                </span>
                <span className="pill pill-indexed">Exported</span>
              </li>
            ))}
            {skipped.map(([id, reason]) => (
              <li key={id} className="doc">
                <span className="doc-main">
                  <span className="doc-name">{id}</span>
                  <span className="doc-error">{reason}</span>
                </span>
                <span className="pill pill-failed">Skipped</span>
              </li>
            ))}
          </ul>

          {result.written.length === 0 && (
            <p className="field-hint">
              Nothing was written. Fix the problems above, or generate one first.
            </p>
          )}
        </>
      )}
    </div>
  );
}
