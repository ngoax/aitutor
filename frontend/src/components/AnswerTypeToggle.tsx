const TYPES = ["arithmetic", "string"] as const;

const EXPLAIN: Record<string, string> = {
  arithmetic: "Parsed, so equivalent forms are accepted. Cannot contain a comma.",
  string: "Compared literally. Use for words, or for an answer listing several values.",
};

type Props = {
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function AnswerTypeToggle({ value, disabled, onChange }: Props) {
  const next = TYPES[(TYPES.indexOf(value as (typeof TYPES)[number]) + 1) % TYPES.length];

  return (
    <button
      type="button"
      className="chip-toggle"
      disabled={disabled}
      title={`${EXPLAIN[value] ?? ""} Click to switch to ${next}.`}
      onClick={() => onChange(next)}
    >
      {value}
    </button>
  );
}
