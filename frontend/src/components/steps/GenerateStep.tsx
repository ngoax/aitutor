import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { GenerationRequest, ProblemDraft } from "../../api/types";
import { AnswerEditor } from "../AnswerEditor";
import { AnswerTypeToggle } from "../AnswerTypeToggle";
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
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);
  const generating = draft?.status === "generating";
  // Steps stay on screen while one of them is being replaced.
  const ready = draft !== null && draft.status !== "failed" && draft.steps.length > 0;

  useEffect(() => {
    if (!generating) setRegeneratingId(null);
  }, [generating]);

  async function save(run: () => Promise<unknown>) {
    setSaveError(null);
    try {
      await run();
      onSaved();
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
            {request.use_scaffolds && ", some asking questions"}
          </span>
        </div>
      </div>

      <button className="btn btn-primary btn-lg" onClick={onGenerate} disabled={busy || generating}>
        {busy || generating ? "Generating…" : draft ? "Generate another" : "Generate problem"}
      </button>

      {generating && (
        <p className="field-hint">
          <span className="spinner" /> Tasks are being generated. You can leave this page and come back.
        </p>
      )}

      {error && <p className="error">{error}</p>}
      {saveError && <p className="error">Could not save — {saveError}</p>}
      {draft?.error && <p className="error">{draft.error}</p>}

      {ready && (
        <article className={`draft ${generating ? "is-busy" : ""}`}>
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
            <section key={step.id} className={`draft-step ${step.stale ? "is-stale" : ""}`}>
              <h4>
                <span className="step-num">{index + 1}</span>
                <EditableText
                  value={step.step_title}
                  onSave={(step_title) =>
                    save(() => api.updateStep(projectId, draft.id, step.id, { step_title }))
                  }
                />
                <button
                  type="button"
                  className="btn btn-ghost step-regen"
                  disabled={generating}
                  title="Discard this step and generate a different one"
                  onClick={() => {
                    setRegeneratingId(step.id);
                    save(() => api.regenerateStep(projectId, draft.id, step.id));
                  }}
                >
                  {regeneratingId === step.id ? "Regenerating…" : "Regenerate"}
                </button>
              </h4>

              {step.stale && (
                <p className="stale-note">
                  An earlier step was rewritten after this one, so it may no longer follow on.
                  Regenerate it, or edit it to dismiss this.
                </p>
              )}

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
                {step.problem_type === "TextBox" ? (
                  <AnswerTypeToggle
                    value={step.answer_type}
                    disabled={generating}
                    onChange={(answer_type) =>
                      save(() =>
                        api.updateStep(projectId, draft.id, step.id, { answer_type }),
                      )
                    }
                  />
                ) : (
                  <span className="chips">{step.answer_type}</span>
                )}
                <AnswerEditor
                  problemType={step.problem_type}
                  answer={step.step_answer}
                  choices={step.choices}
                  onSave={({ answer, choices, numRows, numCols }) =>
                    save(() =>
                      api.updateStep(projectId, draft.id, step.id, {
                        step_answer: answer,
                        choices,
                        num_rows: numRows,
                        num_cols: numCols,
                      }),
                    )
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
                      {hint.type === "scaffold" && (
                        <div className="draft-answer">
                          <span className="chips">the student answers this</span>
                          {hint.problem_type === "TextBox" && (
                            <AnswerTypeToggle
                              value={hint.answer_type ?? "arithmetic"}
                              disabled={generating}
                              onChange={(answer_type) =>
                                save(() =>
                                  api.updateHint(projectId, draft.id, step.id, hint.id, {
                                    answer_type,
                                  }),
                                )
                              }
                            />
                          )}
                          <AnswerEditor
                            problemType={hint.problem_type ?? "TextBox"}
                            answer={hint.hint_answer ?? []}
                            choices={hint.choices}
                            onSave={({ answer, choices }) =>
                              save(() =>
                                api.updateHint(projectId, draft.id, step.id, hint.id, {
                                  hint_answer: answer as string[],
                                  choices,
                                }),
                              )
                            }
                          />
                        </div>
                      )}
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
