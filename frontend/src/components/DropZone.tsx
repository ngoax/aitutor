import { useRef, useState } from "react";

type Props = {
  onFile: (file: File) => void;
  busy: boolean;
};

export function DropZone({ onFile, busy }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(event: React.DragEvent) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      className={`dropzone ${dragging ? "is-dragging" : ""} ${busy ? "is-busy" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !busy && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => event.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.pptx,.ppt,.docx,.md,.txt"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
          event.target.value = "";
        }}
      />

      <div className="dropzone-icon">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 16V4m0 0L7 9m5-5l5 5M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <p className="dropzone-title">
        {busy ? "Uploading…" : dragging ? "Drop to upload" : "Drag your course materials here"}
      </p>
      <p className="dropzone-sub">PDF, PowerPoint, Word, Markdown — or click to browse</p>
    </div>
  );
}
