type Props = {
  label: string;
  hint?: string;
  value: string;
  placeholder?: string;
  rows?: number;
  onSave: (value: string) => void;
};

/** Saves on blur, like every other field in the wizard. */
export function TextArea({ label, hint, value, placeholder, rows = 3, onSave }: Props) {
  return (
    <label className="field-block">
      <span className="select-label">{label}</span>
      <textarea
        key={value}
        className="text-input"
        rows={rows}
        defaultValue={value}
        placeholder={placeholder}
        onBlur={(event) => {
          const next = event.target.value.trim();
          if (next !== value) onSave(next);
        }}
      />
      {hint && <p className="field-hint">{hint}</p>}
    </label>
  );
}
