import { useState } from "react";
import { MathText } from "./MathText";

type Props = {
  value: string;
  onSave: (value: string) => void;
  className?: string;
  placeholder?: string;
  multiline?: boolean;
};

/**
 * Click-to-edit text. Idle it shows rendered maths; editing it shows LaTeX
 */
export function EditableText({
  value,
  onSave,
  className = "",
  placeholder = "Empty",
  multiline = false,
}: Props) {
  const [editing, setEditing] = useState(false);

  function commit(next: string) {
    setEditing(false);
    const trimmed = next.trim();
    if (trimmed && trimmed !== value) onSave(trimmed);
  }

  if (!editing) {
    return (
      <span
        className={`editable ${className} ${value ? "" : "is-empty"}`}
        role="button"
        tabIndex={0}
        title="Click to edit"
        onClick={() => setEditing(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setEditing(true);
          }
        }}
      >
        {value ? <MathText>{value}</MathText> : placeholder}
      </span>
    );
  }

  const shared = {
    autoFocus: true,
    className: `edit-input ${className}`,
    defaultValue: value,
    onBlur: (event: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      commit(event.target.value),
    onKeyDown: (event: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      if (event.key === "Escape") setEditing(false);
      // Enter commits a single line; in a textarea it has to stay a newline,
      // so there the shortcut is the usual modifier pair.
      if (event.key === "Enter" && (!multiline || event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        commit(event.currentTarget.value);
      }
    },
  };

  return multiline ? (
    <textarea {...shared} rows={Math.min(14, value.split("\n").length + 2)} />
  ) : (
    <input {...shared} />
  );
}
