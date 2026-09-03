import type {
  ChoiceOption,
  GenerationRequest,
  Project,
  ProjectUpdate,
  ProviderInfo,
  SourceDocument,
  WizardOptions,
} from "../../api/types";
import { ModelPicker } from "../ModelPicker";
import { NumberStepper } from "../NumberStepper";
import { Select } from "../Select";
import { Toggle } from "../Toggle";

type Props = {
  request: GenerationRequest;
  onChange: <K extends keyof GenerationRequest>(key: K, value: GenerationRequest[K]) => void;
  options: WizardOptions | null;
  documents: SourceDocument[];
  providers: ProviderInfo[];
  project: Project | null;
  onProjectChange: (patch: ProjectUpdate) => void;
};

export function ConfigureStep({
  request,
  onChange,
  options,
  documents,
  providers,
  project,
  onProjectChange,
}: Props) {
  const indexed = documents.filter((doc) => doc.status === "indexed");

  const sourceOptions: ChoiceOption[] = [
    { value: "", label: "All materials", description: "Search across everything you uploaded." },
    ...indexed.map((doc) => ({
      value: String(doc.id),
      label: doc.filename,
      description: `${doc.chunk_count} chunks from this document only.`,
    })),
  ];

  return (
    <div className="step-body">
      <h2>Shape the task</h2>
      <p className="lede">
        These choices become the prompt. You can edit everything the model produces afterwards.
      </p>

      <label className="field-block">
        <span className="select-label">What should it be about?</span>
        <input
          className="text-input"
          value={request.topic}
          onChange={(event) => onChange("topic", event.target.value)}
          placeholder="factoring quadratic expressions"
        />
        <p className="field-hint">
          Also used to search your materials, so be specific about the concept.
        </p>
      </label>

      <div className="grid-2">
        <Select
          label="Task type"
          value={request.problem_type}
          options={options?.problem_types ?? []}
          onChange={(value) => onChange("problem_type", value)}
        />
        <Select
          label="Difficulty"
          value={request.difficulty}
          options={options?.difficulties ?? []}
          onChange={(value) => onChange("difficulty", value)}
        />
      </div>

      <div className="grid-3">
        <NumberStepper
          label="Steps"
          hint="Sub-questions the student answers."
          value={request.num_steps}
          min={1}
          max={7}
          onChange={(value) => onChange("num_steps", value)}
        />
        <NumberStepper
          label="Hints per step"
          hint="Help shown inside each step."
          value={request.num_hints}
          min={0}
          max={7}
          onChange={(value) => {
            onChange("num_hints", value);
            // A pathway of one is the answer, so there is nowhere to put a scaffold.
            if (value < 2) onChange("use_scaffolds", false);
          }}
        />
        <NumberStepper
          label="Context chunks"
          hint="How much source material to use."
          value={request.k}
          min={1}
          max={20}
          onChange={(value) => onChange("k", value)}
        />
      </div>

      <Toggle
        label="Let hints ask questions"
        hint="A scaffold asks the student for an intermediate value instead of telling them it. Needs at least two hints per step."
        checked={request.use_scaffolds}
        disabled={request.num_hints < 2}
        onChange={(value) => onChange("use_scaffolds", value)}
      />

      <Select
        label="Source"
        value={request.source_document_id === null ? "" : String(request.source_document_id)}
        options={sourceOptions}
        onChange={(value) => onChange("source_document_id", value ? Number(value) : null)}
      />

      <p className="field-hint">
        This will produce {request.num_steps} step{request.num_steps === 1 ? "" : "s"} and{" "}
        {request.num_steps * request.num_hints} hint
        {request.num_steps * request.num_hints === 1 ? "" : "s"} in total.
      </p>

      <div className="divider" />

      <h3>Which model writes it</h3>
      <p className="lede">
        Saved on the project, so it applies to everything you generate here. Your materials are
        embedded locally either way.
      </p>
      <ModelPicker providers={providers} project={project} onChange={onProjectChange} />
    </div>
  );
}
