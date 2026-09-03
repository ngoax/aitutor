import { EditableText } from "./EditableText";
export type AnswerPatch = {
  answer: string[] | string[][];
  choices?: string[] | null;
  numRows?: number;
  numCols?: number;
};

type Props = {
  problemType: string;
  answer: string[] | string[][];
  choices: string[] | null;
  onSave: (patch: AnswerPatch) => void;
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

export function AnswerEditor({ problemType, answer, choices, onSave }: Props) {
  if (problemType === "MultipleChoice") {
    const options = choices ?? [];
    const selected = (answer as string[])[0];

    const save = (next: string[], nextAnswer: string | undefined) =>
      onSave({ answer: nextAnswer === undefined ? [] : [nextAnswer], choices: next });

    return (
      <div className="answer-editor">
        <ul className="choice-list">
          {options.map((choice, index) => (
            <li key={index} className={`choice ${choice === selected ? "is-answer" : ""}`}>
              <button
                type="button"
                className="choice-mark"
                title="Mark as the correct answer"
                aria-pressed={choice === selected}
                onClick={() => save(options, choice)}
              >
                <span className="radio" />
              </button>
              <EditableText
                className="choice-text"
                value={choice}
                onSave={(text) => {
                  const next = options.map((c, i) => (i === index ? text : c));
                  // Keep the answer pointing at this option after a rewording
                  save(next, choice === selected ? text : selected);
                }}
              />
              <button
                type="button"
                className="icon-btn"
                title="Remove this choice"
                onClick={() =>
                  save(
                    options.filter((_, i) => i !== index),
                    choice === selected ? undefined : selected,
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
          onClick={() => save([...options, "New choice"], selected)}
        >
          Add choice
        </button>
      </div>
    );
  }

  const grid = GRID_TYPES.includes(problemType);

  return (
    <div className="answer-editor">
      <EditableText
        multiline
        className="answer-text"
        value={toText(answer)}
        placeholder="No answer set"
        onSave={(text) => {
          const lines = toLines(text);
          if (!grid) return onSave({ answer: lines });
          const rows = lines.map((line) => line.split("|").map((cell) => cell.trim()));
          // Derived, never typed, so they cannot drift from the answer.
          onSave({ answer: rows, numRows: rows.length, numCols: rows[0]?.length ?? 0 });
        }}
      />
      <p className="field-hint">
        {grid ? "One row per line, cells separated by |." : "One accepted answer per line."}
      </p>
    </div>
  );
}
