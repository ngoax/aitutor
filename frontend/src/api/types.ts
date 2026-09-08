export type Project = {
  id: number;
  name: string;
  source_name: string;
  license: string;
  chat_provider: string | null;
  chat_model: string | null;
  embedding_provider: string | null;
  embedding_model: string | null;
  study_condition: StudyCondition;
  created_at: string;
};

export type ProjectUpdate = Partial<{
  name: string;
  license: string;
  chat_provider: string | null;
  chat_model: string | null;
  embedding_provider: string | null;
  embedding_model: string | null;
  study_condition: StudyCondition;
}>;

export type StudyCondition = "control" | "context" | "review" | "context_review";
export type KnowledgeType = "fact" | "rule" | "principle";
export type FeedbackMode = "corrective" | "implicit";
export type TutorScope = "addition" | "partial" | "full";

export type TutorContext = {
  id: number;
  project_id: number;
  curricular_placement: string[];
  prior_knowledge: string;
  known_difficulties: string;
  knowledge_type: KnowledgeType;
  learning_goal: string;
  tutor_roles: string[];
  feedback_mode: FeedbackMode;
  scope: TutorScope;
  instructional_history: string;
  representations: string;
  terminology: string;
  heterogeneity: string;
  teacher_intents: string[];
  teacher_intent_note: string;
  duration_minutes: number | null;
  location: string;
  group_work: string;
  goal_critique: GoalCritique | Record<string, never>;
  confirmed_at: string | null;
};

export type TutorContextUpdate = Partial<Omit<TutorContext, "id" | "project_id" | "goal_critique" | "confirmed_at">>;

export type GoalCritique = {
  is_observable: boolean;
  matches_knowledge_type: boolean;
  comment: string;
  suggestion: string | null;
};

export type SummarySection = { heading: string; body: string };

export type Derivation = { field: string; value: unknown; reason: string };

export type ContextSummary = {
  sections: SummarySection[];
  derivations: Derivation[];
  num_slots: number;
  complete: boolean;
  confirmed: boolean;
  missing: string[];
};

export type RunStatus = "generating" | "ready" | "failed";

export type GenerationRun = {
  id: number;
  project_id: number;
  num_slots: number;
  num_alternatives: number;
  status: RunStatus;
  error: string | null;
  context_snapshot: Record<string, unknown>;
  request_snapshot: Record<string, unknown>;
  created_at: string;
};

export type RunSlot = { slot_index: number; alternatives: ProblemDraft[] };

export type RunDetail = GenerationRun & { slots: RunSlot[] };

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
  use_scaffolds: boolean;
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
  problem_type: string | null;
  answer_type: string | null;
  hint_answer: string[] | null;
  choices: string[] | null;
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
  stale: boolean;
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
  problem_type: string;
  answer_type: string;
  hint_answer: string[];
  choices: string[] | null;
}>;

export type ExportResult = {
  root: string;
  written: string[];
  skipped: Record<string, string>;
  note: string | null;
};

export type RetrievedChunk = {
  text: string;
  citation_page: number | null;
  source_document_id: number | null;
  chunk_index: number | null;
};
