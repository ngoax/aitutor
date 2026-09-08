import { useEffect, useState } from "react";

type Props = {
  done: number;
  total: number;
  /** What each unit of work is, e.g. "problem", "step", "hints". */
  labels: string[];
};

export function ProgressBar({ done, total, labels }: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, []);

  const known = total > 0 && done > 0;
  const percent = known ? Math.round((done / total) * 100) : 0;
  const current = labels[Math.min(done, labels.length - 1)] ?? "Writing";

  return (
    <div className="progress">
      <div className={`progress-track ${known ? "" : "is-waiting"}`}>
        <div className="progress-fill" style={known ? { width: `${percent}%` } : undefined} />
      </div>
      <p className="progress-label">
        <span>{current}</span>
        <span className="progress-count">
          {known ? `${done} of ${total} · ` : ""}
          {elapsed}s
        </span>
      </p>
    </div>
  );
}
