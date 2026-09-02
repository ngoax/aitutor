import type { ChoiceOption, Project, ProjectUpdate, ProviderInfo } from "../api/types";
import { Select } from "./Select";

type Props = {
  providers: ProviderInfo[];
  project: Project | null;
  onChange: (patch: ProjectUpdate) => void;
};

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama (self-hosted)",
  nvidia: "NVIDIA NIM",
  azure: "Azure OpenAI",
};

export function ModelPicker({ providers, project, onChange }: Props) {
  const fallback = providers.find((provider) => provider.is_default) ?? null;
  const chosen = providers.find((provider) => provider.provider === project?.chat_provider) ?? null;
  const active = chosen ?? fallback;

  const providerOptions: ChoiceOption[] = providers.map((provider) => ({
    value: provider.provider,
    label: PROVIDER_LABELS[provider.provider] ?? provider.provider,
    description: provider.available
      ? (provider.detail ?? `Writes with ${provider.default_model}.`)
      : (provider.detail ?? "Not configured."),
    disabled: !provider.available,
  }));

  return (
    <div className="model-picker">
      <div className="grid-2">
        <Select
          label="Model provider"
          value={project?.chat_provider ?? ""}
          options={providerOptions}
          placeholder={fallback ? `Default (${fallback.provider})` : "Choose…"}
          onChange={(value) =>
            onChange({ chat_provider: value, chat_model: null })
          }
        />

        <label className="field-block">
          <span className="select-label">Model</span>
          <input
            key={`${project?.id}:${project?.chat_model ?? ""}`}
            className="text-input"
            defaultValue={project?.chat_model ?? ""}
            placeholder={active?.default_model ?? "Provider default"}
            disabled={project === null}
            onBlur={(event) => {
              const value = event.target.value.trim();
              if (value !== (project?.chat_model ?? "")) onChange({ chat_model: value || null });
            }}
          />
          <p className="field-hint">Leave empty to use the provider default.</p>
        </label>
      </div>

      {active && !active.available && (
        <p className="field-hint warn">
          {active.provider} is selected but not usable right now, so generation will fail.
        </p>
      )}
    </div>
  );
}
