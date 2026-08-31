import { useEffect, useRef, useState } from "react";
import type { ChoiceOption } from "../api/types";

type Props = {
  label: string;
  value: string;
  options: ChoiceOption[];
  onChange: (value: string) => void;
  placeholder?: string;
};

/** Replaces the native <select> so each option can show a description. */
export function Select({ label, value, options, onChange, placeholder = "Choose…" }: Props) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  const selected = options.find((option) => option.value === value) ?? null;

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (open) setActive(Math.max(0, options.findIndex((option) => option.value === value)));
  }, [open, options, value]);

  function nextEnabled(from: number, delta: number) {
    for (let hop = 1; hop <= options.length; hop++) {
      const index = (((from + delta * hop) % options.length) + options.length) % options.length;
      if (!options[index].disabled) return index;
    }
    return from;
  }

  function choose(index: number) {
    const option = options[index];
    if (!option || option.disabled) return;
    onChange(option.value);
    setOpen(false);
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (!open && (event.key === "Enter" || event.key === " " || event.key === "ArrowDown")) {
      event.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (event.key === "Escape") setOpen(false);
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => nextEnabled(i, 1));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => nextEnabled(i, -1));
    }
    if (event.key === "Enter") {
      event.preventDefault();
      choose(active);
    }
  }

  return (
    <div className="select" ref={rootRef}>
      <span className="select-label">{label}</span>
      <button
        type="button"
        className={`select-trigger ${open ? "is-open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKeyDown}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="select-value">
          {selected ? selected.label : <em className="muted">{placeholder}</em>}
        </span>
        <svg className="chev" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M6 8l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="2" />
        </svg>
      </button>

      {open && (
        <ul className="select-menu" role="listbox">
          {options.map((option, index) => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              aria-disabled={option.disabled}
              className={`select-option ${index === active ? "is-active" : ""} ${
                option.value === value ? "is-selected" : ""
              } ${option.disabled ? "is-disabled" : ""}`}
              onMouseEnter={() => !option.disabled && setActive(index)}
              onClick={() => choose(index)}
            >
              <span className="option-label">{option.label}</span>
              <span className="option-desc">{option.description}</span>
            </li>
          ))}
        </ul>
      )}

      {selected && <p className="field-hint">{selected.description}</p>}
    </div>
  );
}
