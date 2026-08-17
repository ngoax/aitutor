import { useState } from "react";
import { api } from "../../api/client";
import type { Project } from "../../api/types";

type Props = {
  projects: Project[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onCreated: () => void;
  onDeleted: (id: number) => void;
};

export function ProjectStep({ projects, selectedId, onSelect, onCreated, onDeleted }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // source_name becomes a directory in the OATutor export, and the backend
  // enforces ^[A-Za-z0-9_]+$ — so derive a safe slug from the title.
  const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const project = await api.createProject(name.trim(), slug);
      setName("");
      onCreated();
      onSelect(project.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(project: Project, event: React.MouseEvent) {
    // The delete button sits inside the project card button; without this the
    // click would also select the project we are about to delete.
    event.stopPropagation();
    const message =
      `Delete “${project.name}”?\n\n` +
      "This removes its uploaded materials, extracted text and any generated " +
      "problems. This cannot be undone.";
    if (!confirm(message)) return;
    setError(null);
    try {
      await api.deleteProject(project.id);
      onDeleted(project.id);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="step-body">
      <h2>Start a project</h2>
      <p className="lede">
        A project holds your materials and everything you generate from them. It becomes one
        OATutor content source.
      </p>

      <form onSubmit={create} className="create-row">
        <input
          className="text-input"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Elementary Algebra — Chapter 3"
        />
        <button className="btn btn-primary" type="submit" disabled={busy || !slug}>
          {busy ? "Creating…" : "Create"}
        </button>
      </form>
      {slug && (
        <p className="field-hint">
          Exports to <code>content-sources/{slug}/</code>
        </p>
      )}
      {error && <p className="error">{error}</p>}

      {projects.length > 0 && (
        <>
          <div className="divider">
            <span>or continue an existing one</span>
          </div>
          <div className="project-grid">
            {projects.map((project) => (
              // A <button> may not contain another <button>, so the card is a
              // wrapper with the picker and the delete control as siblings.
              <div
                key={project.id}
                className={`project-card ${project.id === selectedId ? "is-selected" : ""}`}
              >
                <button
                  type="button"
                  className="project-pick"
                  onClick={() => onSelect(project.id)}
                >
                  <span className="project-name">{project.name}</span>
                  <span className="project-slug">{project.source_name}</span>
                </button>
                <button
                  type="button"
                  className="icon-btn"
                  title={`Delete ${project.name}`}
                  aria-label={`Delete ${project.name}`}
                  onClick={(event) => remove(project, event)}
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
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
