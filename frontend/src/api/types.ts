export type Project = {
  id: number;
  name: string;
  source_name: string;
  created_at: string;
};

export type IngestionStatus = "pending" | "indexed" | "failed";

export type SourceDocument = {
  id: number;
  project_id: number;
  filename: string;
  content_type: string | null;
  status: IngestionStatus;
  chunk_count: number;
  error: string | null;
  created_at: string;
};

export type ChoiceOption = {
  value: string;
  label: string;
  description: string;
};

export type WizardOptions = {
  problem_types: ChoiceOption[];
  difficulties: ChoiceOption[];
};

export type GenerationRequest = {
  topic: string;
  problem_type: string;
  difficulty: string;
  num_steps: number;
  num_hints: number;
  source_document_id: number | null;
  k: number;
};

export type ProviderInfo = {
  provider: string;
  available: boolean;
  default_model: string;
  structured_method: string;
  detail: string | null;
};

export type RetrievedChunk = {
  text: string;
  citation_page: number | null;
  source_document_id: number | null;
  chunk_index: number | null;
};
