import type { GenerationRequest, ProblemDraft, StepDraft } from "../../api/types";
import { MathText } from "../MathText";

type Props = {
  request: GenerationRequest;
  draft: ProblemDraft | null;
  busy: boolean;
  error: string | null;
  onGenerate: () => void;
};

function answerText(step: StepDraft): string {
  const answer = step.step_answer;
  if (answer.length > 0 && Array.isArray(answer[0])) {
    return (answer as string[][]).map((row) => row.join(" | ")).join("  /  ");
  }
  return (answer as string[]).join("  or  ");
}

export function GenerateStep({ request, draft, busy, error, onGenerate }: Props) {
  const generating = draft?.status === "generating";
  const ready = draft !== null && !generating && draft.status !== "failed";

  return (
    <div className="step-body">
      <h2>Generate</h2>
      <p className="lede">
        Your choices shape the prompt. The draft is saved as soon as it is generated, so you can
        come back to it.
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

      <button
        className="btn btn-primary btn-lg"
        onClick={onGenerate}
        disabled={busy || generating}
      >
        {busy || generating ? "Generating…" : draft ? "Generate another" : "Generate problem"}
      </button>

      {generating && (
        <p className="field-hint">
          <span className="spinner" /> Working. A hosted model takes seconds, a self-hosted one
          can take minutes. You can leave this page and come back.
        </p>
      )}

      {error && <p className="error">{error}</p>}
      {draft?.status === "failed" && <p className="error">{draft.error}</p>}

      {ready && (
        <article className="draft">
          <header className="draft-head">
            <h3>{draft.title}</h3>
            <code className="draft-id">{draft.oatutor_id}</code>
          </header>
          <MathText className="draft-body">{draft.body}</MathText>

          {draft.steps.map((step, index) => (
            <section key={step.id} className="draft-step">
              <h4>
                <span className="step-num">{index + 1}</span>
                {step.step_title}
              </h4>
              <p>
                <MathText>{step.step_body}</MathText>
              </p>

              {step.choices && (
                <ul className="draft-choices">
                  {step.choices.map((choice) => (
                    <li key={choice}>
                      <MathText>{choice}</MathText>
                    </li>
                  ))}
                </ul>
              )}

              <p className="draft-answer">
                <span className="chips">{step.answer_type}</span>
                <MathText>{answerText(step)}</MathText>
              </p>

              {step.hints.length > 0 && (
                <ol className="draft-hints">
                  {step.hints.map((hint) => (
                    <li key={hint.id} className={`hint hint-${hint.type}`}>
                      <span className="hint-title">{hint.title}</span>
                      <MathText className="hint-text">{hint.text}</MathText>
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
