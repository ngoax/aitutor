import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type {
  GenerationRequest,
  Project,
  ProjectUpdate,
  ProviderInfo,
  ProblemDraft,
  SourceDocument,
  WizardOptions,
} from "./api/types";
import ethLogoBlack from "./assets/ethz_logo_black.svg";
import { Stepper } from "./components/Stepper";
import { ConfigureStep } from "./components/steps/ConfigureStep";
import { ExportStep } from "./components/steps/ExportStep";
import { GenerateStep } from "./components/steps/GenerateStep";
import { MaterialsStep } from "./components/steps/MaterialsStep";
import { ProjectStep } from "./components/steps/ProjectStep";
import "./App.css";

const STEPS = ["Project", "Materials", "Configure", "Generate", "Export"];

const INITIAL_REQUEST: GenerationRequest = {
  topic: "",
  problem_type: "TextBox",
  difficulty: "medium",
  num_steps: 3,
  num_hints: 1,
  use_scaffolds: false,
  source_document_id: null,
  k: 4,
};

export default function App() {
  const [step, setStep] = useState(0);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [options, setOptions] = useState<WizardOptions | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [request, setRequest] = useState<GenerationRequest>(INITIAL_REQUEST);
  const [draft, setDraft] = useState<ProblemDraft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState<string | null>(null);

  const loadProjects = useCallback(() => {
    api.listProjects().then(setProjects).catch((e: Error) => setOffline(e.message));
  }, []);

  const loadDocuments = useCallback(() => {
    if (selectedId === null) return;
    api.listDocuments(selectedId).then(setDocuments).catch(() => setDocuments([]));
  }, [selectedId]);

  const handleProjectDeleted = useCallback(
    (deletedId: number) => {
      loadProjects();
      // If the deleted project was the active one, reset to the first step.
      // Otherwise the walkthrough carries on against a project that is gone.
      if (deletedId === selectedId) {
        setSelectedId(null);
        setDocuments([]);
        setStep(0);
      }
    },
    [loadProjects, selectedId],
  );

  useEffect(() => {
    loadProjects();
    api.wizardOptions().then(setOptions).catch((e: Error) => setOffline(e.message));
    api.listProviders().then(setProviders).catch(() => setProviders([]));
  }, [loadProjects]);

  useEffect(loadDocuments, [loadDocuments]);

  const patchProject = useCallback(
    async (patch: ProjectUpdate) => {
      if (selectedId === null) return;
      try {
        const updated = await api.updateProject(selectedId, patch);
        setProjects((previous) => previous.map((p) => (p.id === updated.id ? updated : p)));
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [selectedId],
  );

  const refreshDraft = useCallback(async () => {
    if (selectedId === null || draft === null) return;
    try {
      setDraft(await api.getDraft(selectedId, draft.id));
    } catch (e) {
      setError((e as Error).message);
    }
  }, [selectedId, draft]);

  // Generation runs in the background too, so poll until it settles.
  useEffect(() => {
    if (selectedId === null || draft?.status !== "generating") return;
    const timer = setInterval(() => {
      api
        .getDraft(selectedId, draft.id)
        .then(setDraft)
        .catch((e: Error) => setError(e.message));
    }, 2000);
    return () => clearInterval(timer);
  }, [draft, selectedId]);

  // Ingestion runs in the background, so poll until nothing is pending.
  useEffect(() => {
    if (!documents.some((doc) => doc.status === "pending")) return;
    const timer = setInterval(loadDocuments, 2000);
    return () => clearInterval(timer);
  }, [documents, loadDocuments]);

  function update<K extends keyof GenerationRequest>(key: K, value: GenerationRequest[K]) {
    setRequest((previous) => ({ ...previous, [key]: value }));
  }

  async function runGenerate() {
    if (selectedId === null) return;
    setBusy(true);
    setError(null);
    setDraft(null);
    try {
      setDraft(await api.startDraft(selectedId, request));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const indexedCount = documents.filter((doc) => doc.status === "indexed").length;
  const canAdvance = [
    selectedId !== null,
    indexedCount > 0,
    request.topic.trim().length >= 3,
    draft !== null && draft.status !== "generating",
    false,
  ][step];
  const furthest =
    selectedId === null
      ? 0
      : indexedCount === 0
        ? 1
        : !request.topic.trim()
          ? 2
          : draft === null
            ? 3
            : 4;

  const project = projects.find((p) => p.id === selectedId) ?? null;
  // What generation will actually use: the project's choice, else the backend default.
  const activeProvider =
    providers.find((p) => p.provider === project?.chat_provider) ??
    providers.find((p) => p.is_default) ??
    null;
  const activeModel = project?.chat_model ?? activeProvider?.default_model;

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-inner">
          <span className="brand">
            <span className="brand-mark">AITutor</span>
          </span>
          <h1>
            Turn your course materials into <em>adaptive tutoring content</em>
          </h1>
          <p className="hero-sub">
            Upload what you already teach from. Get OATutor problems, steps and hints — grounded,
            editable, yours.
          </p>
          <span className={`llm-badge ${activeProvider?.available ? "is-on" : "is-off"}`}>
            <span className="dot" />
            {activeProvider ? `${activeProvider.provider} · ${activeModel}` : "No model connected"}
          </span>
        </div>
      </header>

      <main className="shell">
        {offline && <p className="error banner">Backend unreachable — {offline}</p>}

        <Stepper steps={STEPS} current={step} furthest={furthest} onJump={setStep} />

        <section className="panel" key={step}>
          {step === 0 && (
            <ProjectStep
              projects={projects}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onCreated={loadProjects}
              onDeleted={handleProjectDeleted}
            />
          )}
          {step === 1 && selectedId !== null && (
            <MaterialsStep
              projectId={selectedId}
              documents={documents}
              onChanged={loadDocuments}
            />
          )}
          {step === 2 && (
            <ConfigureStep
              request={request}
              onChange={update}
              options={options}
              documents={documents}
              providers={providers}
              project={project}
              onProjectChange={patchProject}
            />
          )}
          {step === 3 && selectedId !== null && (
            <GenerateStep
              projectId={selectedId}
              request={request}
              draft={draft}
              busy={busy}
              error={error}
              onGenerate={runGenerate}
              onSaved={refreshDraft}
            />
          )}

          {step === 4 && selectedId !== null && (
            <ExportStep
              projectId={selectedId}
              project={project}
              onProjectChange={patchProject}
            />
          )}

          <footer className="panel-nav">
            <button
              className="btn btn-ghost"
              onClick={() => setStep((s) => s - 1)}
              disabled={step === 0}
            >
              Back
            </button>
            {step < STEPS.length - 1 && (
              <button
                className="btn btn-primary"
                onClick={() => setStep((s) => s + 1)}
                disabled={!canAdvance}
              >
                Continue
              </button>
            )}
          </footer>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <img className="eth-logo" src={ethLogoBlack} alt="ETH Zürich" />
            <p className="footer-sub">Learning and Instruction Lab</p>
          </div>
          <div className="footer-links">
            <a href="https://github.com/CAHLR/OATutor" target="_blank" rel="noreferrer">
              OATutor
            </a>
            <a href="https://github.com/mohireza/prompthive" target="_blank" rel="noreferrer">
              PromptHive
            </a>
          </div>
        </div>
        <p className="footer-fine">
          Generates content for OATutor, an open-source adaptive tutoring system by CAHLR at UC
          Berkeley.
        </p>
      </footer>
    </div>
  );
}
