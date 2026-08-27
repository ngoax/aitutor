import type {
  GenerationRequest,
  ProblemDraft,
  Project,
  ProviderInfo,
  SourceDocument,
  WizardOptions,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      // response had no JSON body; keep the status line
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  listProjects: () => request<Project[]>("/projects"),
  createProject: (name: string, sourceName: string) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name, source_name: sourceName }),
    }),

  deleteProject: (projectId: number) =>
    request<void>(`/projects/${projectId}`, { method: "DELETE" }),

  listDocuments: (projectId: number) =>
    request<SourceDocument[]>(`/projects/${projectId}/documents`),
  deleteDocument: (projectId: number, documentId: number) =>
    request<void>(`/projects/${projectId}/documents/${documentId}`, { method: "DELETE" }),
  uploadDocument: (projectId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    // No Content-Type header: the browser must set the multipart boundary itself.
    return request<SourceDocument>(`/projects/${projectId}/documents`, {
      method: "POST",
      body: form,
      headers: {},
    });
  },

  generateDraft: (projectId: number, payload: GenerationRequest) =>
    request<ProblemDraft>(`/projects/${projectId}/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  wizardOptions: () => request<WizardOptions>("/generation/options"),
  listProviders: () => request<ProviderInfo[]>("/providers"),

  testRetrieval: (projectId: number, params: Pick<GenerationRequest, "topic" | "k">) => {
    const query = new URLSearchParams({ query: params.topic, k: String(params.k) });
    return request<RetrievedChunk[]>(`/projects/${projectId}/retrieval/test?${query}`);
  },
};
