import { useState } from "react";
import { api } from "../../api/client";
import type { GenerationRequest, ProblemDraft } from "../../api/types";
import { AnswerEditor } from "../AnswerEditor";
import { EditableText } from "../EditableText";

type Props = {
  projectId: number;
  request: GenerationRequest;
  draft: ProblemDraft | null;
  busy: boolean;
  error: string | null;
  onGenerate: () => void;
  onSaved: () => void;
};

export function GenerateStep({
  projectId,
  request,
  draft,
  busy,
  error,
  onGenerate,
  onSaved,
}: Props) {
  const [saveError, setSaveError] = useState<string | null>(null);
  const generating = draft?.status === "generating";
  const ready = draft !== null && !generating && draft.status !== "failed";

  async function save(run: () => Promise<unknown>) {
    setSaveError(null);
    try {
      await run();
   
    } catch (e) {
      setSaveError((e as Error).message);
    }
  }

  return (
    <div className="step-body">
      <h2>Generate</h2>
      <p className="lede">
        Your choices shape the prompt. The draft is saved as soon as it is generated, and every
        field below can be rewritten.
      </p>

      <div className="summary">
        <div>
          <span className="summary-key">Topic</span>
          <span className="summary-val">{request.topic || "not set"}</span>
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
            {request.num_steps} steps, {request.num_hints} hints each
          </span>
        </div>
      </div>

      <button className="btn btn-primary btn-lg" onClick={onGenerate} disabled={busy || generating}>
        {busy || generating ? "Generating…" : draft ? "Generate another" : "Generate problem"}
      </button>

      {generating && (
        <p className="field-hint">
          <span className="spinner" /> Working. A hosted model takes seconds, a self-hosted one can
          take minutes. You can leave this page and come back.
        </p>
      )}

      {error && <p className="error">{error}</p>}
      {saveError && <p className="error">Could not save — {saveError}</p>}
      {draft?.status === "failed" && <p className="error">{draft.error}</p>}

      {ready && (
        <article className="draft">
          <header className="draft-head">
            <h3>
              <EditableText
                value={draft.title}
                onSave={(title) => save(() => api.updateProblem(projectId, draft.id, { title }))}
              />
            </h3>
            <code className="draft-id">{draft.oatutor_id}</code>
          </header>

          <EditableText
            multiline
            className="draft-body"
            value={draft.body}
            placeholder="No problem text"
            onSave={(body) => save(() => api.updateProblem(projectId, draft.id, { body }))}
          />

          <p className="edit-note">Click any text to rewrite it. Press ESC to cancel.</p>

          {draft.steps.map((step, index) => (
            <section key={step.id} className="draft-step">
              <h4>
                <span className="step-num">{index + 1}</span>
                <EditableText
                  value={step.step_title}
                  onSave={(step_title) =>
                    save(() => api.updateStep(projectId, draft.id, step.id, { step_title }))
                  }
                />
              </h4>

              <EditableText
                multiline
                className="step-body-text"
                value={step.step_body}
                placeholder="No question text"
                onSave={(step_body) =>
                  save(() => api.updateStep(projectId, draft.id, step.id, { step_body }))
                }
              />

              <div className="draft-answer">
                <span className="chips">{step.answer_type}</span>
                <AnswerEditor
                  step={step}
                  onSave={(patch) =>
                    save(() => api.updateStep(projectId, draft.id, step.id, patch))
                  }
                />
              </div>

              {step.hints.length > 0 && (
                <ol className="draft-hints">
                  {step.hints.map((hint) => (
                    <li key={hint.id} className={`hint hint-${hint.type}`}>
                      <span className="hint-title">
                        <EditableText
                          value={hint.title}
                          onSave={(title) =>
                            save(() =>
                              api.updateHint(projectId, draft.id, step.id, hint.id, { title }),
                            )
                          }
                        />
                      </span>
                      <EditableText
                        multiline
                        className="hint-text"
                        value={hint.text}
                        onSave={(text) =>
                          save(() =>
                            api.updateHint(projectId, draft.id, step.id, hint.id, { text }),
                          )
                        }
                      />
                    </li>
                  ))}
                </ol>
              )}
            </section>
          ))}
        </article>
      )}
    </div>
  );
}
