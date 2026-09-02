export type Project = {
  id: number;
  name: string;
  source_name: string;
  license: string;
  chat_provider: string | null;
  chat_model: string | null;
  embedding_provider: string | null;
  embedding_model: string | null;
  created_at: string;
};

export type ProjectUpdate = Partial<{
  name: string;
  license: string;
  chat_provider: string | null;
  chat_model: string | null;
  embedding_provider: string | null;
  embedding_model: string | null;
}>;

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
  disabled?: boolean;
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
  is_default: boolean;
  default_model: string;
  structured_method: string;
  detail: string | null;
};

export type DraftStatus = "generating" | "failed" | "draft" | "edited" | "export_ready";

export type HintType = "hint" | "scaffold" | "solution";

export type HintEntry = {
  id: number;
  order_index: number;
  oatutor_id: string;
  type: HintType;
  title: string;
  text: string;
  dependencies: number[];
};

export type StepDraft = {
  id: number;
  problem_id: number;
  oatutor_id: string;
  order_index: number;
  problem_type: string;
  answer_type: string;
  step_title: string;
  step_body: string;
  step_answer: string[] | string[][];
  answer_validator: string;
  choices: string[] | null;
  num_rows: number | null;
  num_cols: number | null;
  skills: string[];
  hints: HintEntry[];
};

export type ProblemDraft = {
  id: number;
  project_id: number;
  oatutor_id: string;
  title: string;
  body: string;
  course_name: string;
  oer: string | null;
  topic: string | null;
  difficulty: string | null;
  status: DraftStatus;
  error: string | null;
  created_at: string;
  steps: StepDraft[];
};

export type ProblemUpdate = Partial<{
  title: string;
  body: string;
  course_name: string;
  oer: string | null;
  topic: string | null;
  difficulty: string | null;
}>;

export type StepUpdate = Partial<{
  problem_type: string;
  answer_type: string;
  step_title: string;
  step_body: string;
  step_answer: string[] | string[][];
  answer_validator: string;
  choices: string[] | null;
  num_rows: number | null;
  num_cols: number | null;
  skills: string[];
}>;

export type HintUpdate = Partial<{
  type: HintType;
  title: string;
  text: string;
}>;

export type ExportResult = {
  root: string;
  written: string[];
  skipped: Record<string, string>;
};

export type RetrievedChunk = {
  text: string;
  citation_page: number | null;
  source_document_id: number | null;
  chunk_index: number | null;
};
