import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type {
  GenerationRequest,
  Project,
  ProviderInfo,
  RetrievedChunk,
  SourceDocument,
  WizardOptions,
} from "./api/types";
import ethLogoBlack from "./assets/ethz_logo_black.svg";
import { Stepper } from "./components/Stepper";
import { ConfigureStep } from "./components/steps/ConfigureStep";
import { MaterialsStep } from "./components/steps/MaterialsStep";
import { PreviewStep } from "./components/steps/PreviewStep";
import { ProjectStep } from "./components/steps/ProjectStep";
import "./App.css";

const STEPS = ["Project", "Materials", "Configure", "Review"];

const INITIAL_REQUEST: GenerationRequest = {
  topic: "",
  problem_type: "TextBox",
  difficulty: "medium",
  num_steps: 3,
  num_hints: 1,
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
  const [chunks, setChunks] = useState<RetrievedChunk[] | null>(null);
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
      // If the deleted project was the active one, drop the state that belonged
      // to it and return to the first step — otherwise the walkthrough would
      // carry on against a project that no longer exists.
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

  // Ingestion is a background job — poll until nothing is pending.
  useEffect(() => {
    if (!documents.some((doc) => doc.status === "pending")) return;
    const timer = setInterval(loadDocuments, 2000);
    return () => clearInterval(timer);
  }, [documents, loadDocuments]);

  function update<K extends keyof GenerationRequest>(key: K, value: GenerationRequest[K]) {
    setRequest((previous) => ({ ...previous, [key]: value }));
  }

  async function runPreview() {
    if (selectedId === null) return;
    setBusy(true);
    setError(null);
    setChunks(null);
    try {
      setChunks(await api.testRetrieval(selectedId, { topic: request.topic, k: request.k }));
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
    false,
  ][step];
  const furthest = selectedId === null ? 0 : indexedCount === 0 ? 1 : request.topic.trim() ? 3 : 2;
  const usable = providers.filter((provider) => provider.available);

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
          <span className={`llm-badge ${usable.length ? "is-on" : "is-off"}`}>
            <span className="dot" />
            {usable.length
              ? `${usable[0].provider} · ${usable[0].default_model}`
              : "No model connected"}
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
            />
          )}
          {step === 3 && (
            <PreviewStep
              request={request}
              chunks={chunks}
              busy={busy}
              error={error}
              onRun={runPreview}
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
