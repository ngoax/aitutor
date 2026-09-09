import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { GenerationRequest, ProblemDraft, RunDetail, RunSlot } from "../../api/types";
import { DraftCard } from "../DraftCard";
import { MathText } from "../MathText";
import { NumberStepper } from "../NumberStepper";
import { ProgressBar } from "../ProgressBar";

type Props = {
  projectId: number;
  request: GenerationRequest;
  numSlots: number;
  /** True once every task has a kept version, which is what the Export step needs. */
  onReadyChange: (ready: boolean) => void;
};

/** One label per candidate, in the order the backend writes them. */
function candidateLabels(slots: number, alternatives: number): string[] {
  const labels: string[] = [];
  for (let slot = 1; slot <= slots; slot += 1) {
    for (let n = 1; n <= alternatives; n += 1) {
      labels.push(`Writing task ${slot}, version ${n} of ${alternatives}`);
    }
  }
  return labels;
}

function chosenIn(slot: RunSlot): ProblemDraft | null {
  return slot.alternatives.find((candidate) => candidate.selected) ?? null;
}

export function AlternativesStep({ projectId, request, numSlots, onReadyChange }: Props) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [alternatives, setAlternatives] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);

  const written = run?.slots.reduce((total, slot) => total + slot.alternatives.length, 0) ?? 0;
  const chosen = run?.slots.filter((slot) => chosenIn(slot) !== null).length ?? 0;
  const generating =
    run?.status === "generating" ||
    (run?.slots.some((slot) => slot.alternatives.some((c) => c.status === "generating")) ?? false);

  const refresh = useCallback(async () => {
    if (run === null) return;
    try {
      setRun(await api.getRun(projectId, run.id));
    } catch (e) {
      setError((e as Error).message);
    }
  }, [projectId, run]);

  // The run writes candidates one at a time in the background, so poll until it settles.
  useEffect(() => {
    if (!generating) return setRegeneratingId(null);
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, [generating, refresh]);

  const slotCount = run?.slots.length ?? 0;
  useEffect(
    () => onReadyChange(slotCount > 0 && chosen === slotCount),
    [chosen, slotCount, onReadyChange],
  );

  // The most recent run, so a reload does not lose work that is already written.
  useEffect(() => {
    api
      .listRuns(projectId)
      .then((runs) => (runs.length > 0 ? api.getRun(projectId, runs[0].id) : null))
      .then(setRun)
      .catch(() => setRun(null));
  }, [projectId]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const started = await api.startRun(projectId, alternatives);
      setRun(await api.getRun(projectId, started.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function choose(problemId: number) {
    setError(null);
    try {
      setRun(await api.selectAlternative(projectId, run!.id, problemId));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function regenerate(problemId: number, stepId: number) {
    setError(null);
    setRegeneratingId(stepId);
    try {
      await api.regenerateStep(projectId, problemId, stepId);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="step-body">
      <h2>Generate</h2>
      <p className="lede">
        Each task is written {alternatives} ways. Read them against each other, keep the one that
        fits your class, and edit it from there. Only the version you keep is exported.
      </p>

      <div className="summary">
        <div>
          <span className="summary-key">Topic</span>
          <span className="summary-val">{request.topic || "not set"}</span>
        </div>
        <div>
          <span className="summary-key">Tasks</span>
          <span className="summary-val">{numSlots}</span>
        </div>
        <div>
          <span className="summary-key">Structure</span>
          <span className="summary-val">
            {request.num_steps} steps, {request.num_hints} hints each
            {request.use_scaffolds && ", some asking questions"}
          </span>
        </div>
      </div>

      <NumberStepper
        label="Versions of each task"
        hint="More to compare, one model call each."
        value={alternatives}
        min={2}
        max={5}
        onChange={setAlternatives}
      />

      <button className="btn btn-primary btn-lg" onClick={start} disabled={busy || generating}>
        {busy || generating ? "Generating…" : run ? "Start over" : "Generate tasks"}
      </button>

      {generating && run && (
        <>
          <ProgressBar
            done={written}
            total={run.num_slots * run.num_alternatives}
            labels={candidateLabels(run.num_slots, run.num_alternatives)}
          />
          <p className="field-hint">You can leave this page and come back.</p>
        </>
      )}

      {error && <p className="error">{error}</p>}
      {run?.error && <p className="error">{run.error}</p>}

      {run && run.slots.length > 0 && (
        <p className="field-hint">
          {chosen} of {slotCount} tasks chosen.
        </p>
      )}

      {run?.slots.map((slot) => {
        const keeper = chosenIn(slot);
        return (
          <section className="slot" key={slot.slot_index}>
            <h3 className="slot-head">Task {slot.slot_index + 1}</h3>

            <div className="candidates">
              {slot.alternatives.map((candidate, index) => (
                <article
                  key={candidate.id}
                  className={`candidate ${candidate.selected ? "is-chosen" : ""}`}
                >
                  <header className="candidate-head">
                    <span className="candidate-num">Version {index + 1}</span>
                    <MathText className="candidate-title">{candidate.title}</MathText>
                  </header>
                  <MathText className="candidate-body">{candidate.body}</MathText>
                  <ol className="candidate-steps">
                    {candidate.steps.map((step) => (
                      <li key={step.id}>
                        <MathText>{step.step_title}</MathText>
                      </li>
                    ))}
                  </ol>
                  <button
                    type="button"
                    className={`btn ${candidate.selected ? "btn-ghost" : "btn-primary"}`}
                    disabled={generating || candidate.status === "generating"}
                    onClick={() => choose(candidate.id)}
                  >
                    {candidate.selected ? "Kept" : "Keep this one"}
                  </button>
                </article>
              ))}
            </div>

            {keeper && (
              <DraftCard
                projectId={projectId}
                draft={keeper}
                busy={generating}
                onSaved={refresh}
                onError={setError}
                regeneratingId={regeneratingId}
                onRegenerate={(stepId) => regenerate(keeper.id, stepId)}
              />
            )}
          </section>
        );
      })}
    </div>
  );
}
