type Props = {
  label: string;
  hint?: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
};

export function Toggle({ label, hint, checked, disabled, onChange }: Props) {
  return (
    <label className={`toggle ${disabled ? "is-disabled" : ""}`}>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="toggle-text">
        <span className="select-label">{label}</span>
        {hint && <p className="field-hint">{hint}</p>}
      </span>
    </label>
  );
}
