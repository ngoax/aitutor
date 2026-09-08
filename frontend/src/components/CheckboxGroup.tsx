type Option = { value: string; label: string; description?: string };

type Props = {
  label: string;
  hint?: string;
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
};

export function CheckboxGroup({ label, hint, options, selected, onChange }: Props) {
  const toggle = (value: string) =>
    onChange(
      selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value],
    );

  return (
    <div className="field-block">
      <span className="select-label">{label}</span>
      {hint && <p className="field-hint">{hint}</p>}
      <ul className="check-list">
        {options.map((option) => (
          <li key={option.value}>
            <label className={`check ${selected.includes(option.value) ? "is-on" : ""}`}>
              <input
                type="checkbox"
                checked={selected.includes(option.value)}
                onChange={() => toggle(option.value)}
              />
              <span>
                <span className="check-label">{option.label}</span>
                {option.description && <span className="option-desc">{option.description}</span>}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
