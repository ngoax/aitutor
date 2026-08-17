type Props = {
  label: string;
  hint?: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
};

export function NumberStepper({ label, hint, value, min, max, onChange }: Props) {
  const clamp = (next: number) => onChange(Math.min(max, Math.max(min, next)));

  return (
    <div className="numstep">
      <span className="select-label">{label}</span>
      <div className="numstep-control">
        <button type="button" onClick={() => clamp(value - 1)} disabled={value <= min}>
          −
        </button>
        <span className="numstep-value">{value}</span>
        <button type="button" onClick={() => clamp(value + 1)} disabled={value >= max}>
          +
        </button>
      </div>
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}
