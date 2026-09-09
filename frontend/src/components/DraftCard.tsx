import { api } from "../api/client";
import type { ProblemDraft } from "../api/types";
import { AnswerEditor } from "./AnswerEditor";
import { AnswerTypeToggle } from "./AnswerTypeToggle";
import { EditableText } from "./EditableText";

type Props = {
  projectId: number;
  draft: ProblemDraft;
  /** True while the server is writing to this draft, which disables the controls. */
  busy: boolean;
  onSaved: () => void;
  onError: (message: string) => void;
  regeneratingId: number | null;
  onRegenerate: (stepId: number) => void;
};

/** One generated problem with every field editable in place. */
export function DraftCard({
  projectId,
  draft,
  busy,
  onSaved,
  onError,
  regeneratingId,
  onRegenerate,
}: Props) {
  async function save(run: () => Promise<unknown>) {
    try {
      await run();
      onSaved();
    } catch (e) {
      onError((e as Error).message);
    }
  }

  return (
    <article className={`draft ${busy ? "is-busy" : ""}`}>
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
              disabled={busy}
              title="Discard this step and generate a different one"
              onClick={() => onRegenerate(step.id)}
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
                disabled={busy}
                onChange={(answer_type) =>
                  save(() => api.updateStep(projectId, draft.id, step.id, { answer_type }))
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
                        save(() => api.updateHint(projectId, draft.id, step.id, hint.id, { title }))
                      }
                    />
                  </span>
                  <EditableText
                    multiline
                    className="hint-text"
                    value={hint.text}
                    onSave={(text) =>
                      save(() => api.updateHint(projectId, draft.id, step.id, hint.id, { text }))
                    }
                  />
                  {hint.type === "scaffold" && (
                    <div className="draft-answer">
                      <span className="chips">the student answers this</span>
                      {hint.problem_type === "TextBox" && (
                        <AnswerTypeToggle
                          value={hint.answer_type ?? "arithmetic"}
                          disabled={busy}
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
  );
}
