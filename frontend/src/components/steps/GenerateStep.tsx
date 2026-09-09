import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { GenerationRequest, ProblemDraft } from "../../api/types";
import { DraftCard } from "../DraftCard";
import { ProgressBar } from "../ProgressBar";

type Props = {
  projectId: number;
  request: GenerationRequest;
  draft: ProblemDraft | null;
  busy: boolean;
  error: string | null;
  onGenerate: () => void;
  onSaved: () => void;
};

function progressLabels(request: GenerationRequest): string[] {
  const labels = ["Writing the problem"];
  for (let n = 1; n <= request.num_steps; n += 1) {
    labels.push(`Writing step ${n} of ${request.num_steps}`);
    if (request.num_hints > 0) labels.push(`Writing hints for step ${n}`);
  }
  labels.push("Saving the draft");
  return labels;
}

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

  async function regenerate(stepId: number) {
    setSaveError(null);
    setRegeneratingId(stepId);
    try {
      await api.regenerateStep(projectId, draft!.id, stepId);
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
        <>
          <ProgressBar
            done={draft?.progress_done ?? 0}
            total={draft?.progress_total ?? 0}
            labels={progressLabels(request)}
          />
          <p className="field-hint">You can leave this page and come back.</p>
        </>
      )}

      {error && <p className="error">{error}</p>}
      {saveError && <p className="error">Could not save — {saveError}</p>}
      {draft?.error && <p className="error">{draft.error}</p>}

      {ready && (
        <DraftCard
          projectId={projectId}
          draft={draft}
          busy={generating}
          onSaved={onSaved}
          onError={setSaveError}
          regeneratingId={regeneratingId}
          onRegenerate={regenerate}
        />
      )}
    </div>
  );
}
