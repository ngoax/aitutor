import type { StepDraft, StepUpdate } from "../api/types";
import { EditableText } from "./EditableText";

type Props = {
  step: StepDraft;
  onSave: (patch: StepUpdate) => void;
};

const GRID_TYPES = ["GridInput", "MatrixInput"];

function toText(answer: string[] | string[][]): string {
  if (answer.length > 0 && Array.isArray(answer[0])) {
    return (answer as string[][]).map((row) => row.join(" | ")).join("\n");
  }
  return (answer as string[]).join("\n");
}

function toLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function AnswerEditor({ step, onSave }: Props) {
  if (step.problem_type === "MultipleChoice") {
    const choices = step.choices ?? [];
    const answer = (step.step_answer as string[])[0];

    const save = (next: string[], nextAnswer: string | undefined) =>
      onSave({ choices: next, step_answer: nextAnswer === undefined ? [] : [nextAnswer] });

    return (
      <div className="answer-editor">
        <ul className="choice-list">
          {choices.map((choice, index) => (
            <li key={index} className={`choice ${choice === answer ? "is-answer" : ""}`}>
              <button
                type="button"
                className="choice-mark"
                title="Mark as the correct answer"
                aria-pressed={choice === answer}
                onClick={() => save(choices, choice)}
              >
                <span className="radio" />
              </button>
              <EditableText
                className="choice-text"
                value={choice}
                onSave={(text) => {
                  const next = choices.map((c, i) => (i === index ? text : c));
                  // Keep the answer pointing at this option after a rewording
                  save(next, choice === answer ? text : answer);
                }}
              />
              <button
                type="button"
                className="icon-btn"
                title="Remove this choice"
                onClick={() =>
                  save(
                    choices.filter((_, i) => i !== index),
                    choice === answer ? undefined : answer,
                  )
                }
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => save([...choices, "New choice"], answer)}
        >
          Add choice
        </button>
      </div>
    );
  }

  const grid = GRID_TYPES.includes(step.problem_type);

  return (
    <div className="answer-editor">
      <EditableText
        multiline
        className="answer-text"
        value={toText(step.step_answer)}
        placeholder="No answer set"
        onSave={(text) => {
          const lines = toLines(text);
          if (!grid) return onSave({ step_answer: lines });
          const rows = lines.map((line) => line.split("|").map((cell) => cell.trim()));
          // Derived, never typed, so they cannot drift from the answer.
          onSave({ step_answer: rows, num_rows: rows.length, num_cols: rows[0]?.length ?? 0 });
        }}
      />
      <p className="field-hint">
        {grid ? "One row per line, cells separated by |." : "One accepted answer per line."}
      </p>
    </div>
  );
}
