type Props = {
  steps: string[];
  current: number;
  furthest: number;
  onJump: (index: number) => void;
};

export function Stepper({ steps, current, furthest, onJump }: Props) {
  return (
    <nav className="stepper" aria-label="Progress">
      {steps.map((label, index) => {
        const state = index === current ? "current" : index < furthest ? "done" : "todo";
        return (
          <button
            key={label}
            type="button"
            className={`step step-${state}`}
            disabled={index > furthest}
            onClick={() => onJump(index)}
          >
            <span className="step-dot">
              {index < furthest ? (
                <svg viewBox="0 0 20 20" aria-hidden="true">
                  <path
                    d="M5 10.5l3.5 3.5L15 7"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </span>
            <span className="step-label">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
