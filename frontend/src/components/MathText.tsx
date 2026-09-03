import { useEffect, useRef } from "react";
import renderMathInElement from "katex/contrib/auto-render";
import "katex/dist/katex.min.css";

type Props = {
  children: string;
  className?: string;
};
const DELIMITERS = [{ left: "$$", right: "$$", display: false }];
/** Renders generated text, turning any LaTeX it contains into maths. */
export function MathText({ children, className }: Props) {
  const host = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const element = host.current;
    if (!element) return;
    // KaTeX writes the original source back into a MathML <annotation>, so a
    // second pass over its own output renders everything twice. Reset to the
    // plain text first to keep the effect idempotent.
    element.textContent = children;
    renderMathInElement(element, {
      delimiters: DELIMITERS,
      // A malformed expression should show as plain text, not blank the page.
      throwOnError: false,
    });
  }, [children]);

  return (
    <span ref={host} className={className}>
      {children}
    </span>
  );
}
