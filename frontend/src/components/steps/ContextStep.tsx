import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { ContextSummary, GoalCritique, TutorContext, TutorContextUpdate } from "../../api/types";
import { CheckboxGroup } from "../CheckboxGroup";
import { NumberStepper } from "../NumberStepper";
import { Select } from "../Select";
import { TextArea } from "../TextArea";

type Props = {
  projectId: number;
  onConfirmedChange: (confirmed: boolean) => void;
};

const PLACEMENTS = [
  { value: "introduction", label: "Introduction to a new topic" },
  { value: "after_instruction", label: "After teacher-led instruction" },
  { value: "guided_practice", label: "Guided practice" },
  { value: "independent_practice", label: "Independent practice" },
  { value: "consolidation", label: "Consolidation" },
  { value: "revision", label: "Revision" },
  { value: "struggling", label: "Support for struggling learners" },
  { value: "transfer", label: "Transfer" },
  { value: "application", label: "Application" },
  { value: "homework", label: "Homework" },
  { value: "exam_preparation", label: "Exam preparation" },
];

const ROLES = [
  { value: "explain", label: "Explain", description: "Introduce or explain new content." },
  { value: "practice", label: "Practice", description: "Provide opportunities for practice." },
  { value: "diagnose", label: "Diagnose", description: "Identify misconceptions or gaps." },
  { value: "feedback", label: "Feedback", description: "Respond to learner answers." },
  { value: "differentiation", label: "Differentiation", description: "Extension or transfer." },
  { value: "review", label: "Review", description: "Retrieval and consolidation." },
];

const INTENTS = [
  { value: "no_gamification", label: "No gamification" },
  { value: "no_long_text", label: "No long explanatory texts" },
  { value: "explain_reasoning", label: "Learners should explain their reasoning" },
  { value: "class_examples", label: "Examples should connect to current classroom content" },
  { value: "class_terminology", label: "Use the terminology introduced in class" },
];

// TBA: the supervisors write the guidance shown against each knowledge type.
const KNOWLEDGE_TYPES = [
  { value: "fact", label: "Fact knowledge", description: "" },
  { value: "rule", label: "Rule-based knowledge", description: "" },
  { value: "principle", label: "Principle-based knowledge", description: "" },
];

// TBA: further feedback types.
const FEEDBACK_MODES = [
  {
    value: "corrective",
    label: "Corrective",
    description: "The correct answer is shown to the student.",
  },
  {
    value: "implicit",
    label: "Implicit",
    description: "Hints only, stopping short of the correct answer.",
  },
];

const SCOPES = [
  { value: "addition", label: "Addition to an external unit", description: "A few tasks." },
  { value: "partial", label: "Partial learning unit", description: "A medium set of tasks." },
  { value: "full", label: "Full learning unit", description: "A large set of tasks." },
];

function Critique({ critique }: { critique: GoalCritique }) {

  const flags = [
    {
      ok: critique.is_observable,
      yes: "names something you could observe",
      no: "does not name something you could observe",
    },
    {
      ok: critique.matches_knowledge_type,
      yes: "matches the knowledge type you chose",
      no: "does not match the knowledge type you chose",
    },
  ];
  return (
    <div className="critique">
      <ul className="critique-flags">
        {flags.map((flag) => (
          <li key={flag.yes} className={flag.ok ? "is-ok" : "is-warn"}>
            {flag.ok ? "✓" : "!"} {flag.ok ? flag.yes : flag.no}
          </li>
        ))}
      </ul>
      <p className="critique-comment">{critique.comment}</p>
      {critique.suggestion && (
        <p className="critique-suggestion">
          <span className="chips">one way to put it</span> {critique.suggestion}
        </p>
      )}
      <p className="field-hint">
        A second opinion, not a verdict. Rewrite the goal yourself if you agree.
      </p>
    </div>
  );
}

export function ContextStep({ projectId, onConfirmedChange }: Props) {
  const [context, setContext] = useState<TutorContext | null>(null);
  const [summary, setSummary] = useState<ContextSummary | null>(null);
  const [deeper, setDeeper] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [loaded, computed] = await Promise.all([
        api.getContext(projectId),
        api.contextSummary(projectId),
      ]);
      setContext(loaded);
      setSummary(computed);
      onConfirmedChange(loaded.confirmed_at !== null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [projectId, onConfirmedChange]);

  useEffect(() => {
    load();
  }, [load]);

  async function save(patch: TutorContextUpdate) {
    setError(null);
    try {
      setContext(await api.updateContext(projectId, patch));
      setSummary(await api.contextSummary(projectId));
      onConfirmedChange(false);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function run(action: () => Promise<TutorContext>) {
    setBusy(true);
    setError(null);
    try {
      const updated = await action();
      setContext(updated);
      setSummary(await api.contextSummary(projectId));
      onConfirmedChange(updated.confirmed_at !== null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (context === null) {
    return (
      <div className="step-body">
        <h2>Your teaching context</h2>
        {error ? <p className="error">{error}</p> : <p className="lede">Loading…</p>}
      </div>
    );
  }

  const critique = "comment" in context.goal_critique ? context.goal_critique : null;

  return (
    <div className="step-body">
      <h2>Your teaching context</h2>
      <p className="lede">
        Every answer here changes what gets generated. Nothing is asked that does not.
      </p>

      {error && <p className="error">{error}</p>}

      <CheckboxGroup
        label="Where will this tutor be used in your teaching sequence?"
        options={PLACEMENTS}
        selected={context.curricular_placement}
        onChange={(curricular_placement) => save({ curricular_placement })}
      />

      <TextArea
        label="What can learners already do that the tutor can build on?"
        value={context.prior_knowledge}
        placeholder="Expanding brackets; factoring out a common factor"
        onSave={(prior_knowledge) => save({ prior_knowledge })}
      />

      <TextArea
        label="What difficulties or misconceptions do you expect?"
        value={context.known_difficulties}
        placeholder="Sign errors when the constant term is negative"
        onSave={(known_difficulties) => save({ known_difficulties })}
      />

      <div className="divider" />

      <h3>The learning goal</h3>
      <Select
        label="What kind of knowledge should learners acquire?"
        value={context.knowledge_type}
        options={KNOWLEDGE_TYPES}
        onChange={(knowledge_type) => save({ knowledge_type: knowledge_type as never })}
      />
      <TextArea
        label="Describe the learning goal in one sentence"
        rows={2}
        value={context.learning_goal}
        placeholder="Learners can factor a quadratic with a non-unit leading coefficient"
        onSave={(learning_goal) => save({ learning_goal })}
      />
      <button
        className="btn btn-ghost"
        disabled={busy || !context.learning_goal}
        onClick={() => run(() => api.critiqueGoal(projectId))}
      >
        {busy ? "Reading…" : critique ? "Ask again" : "Ask for a second opinion"}
      </button>
      {critique && <Critique critique={critique as GoalCritique} />}

      <div className="divider" />

      <h3>What the tutor is for</h3>
      <CheckboxGroup
        label="What role should it play?"
        options={ROLES}
        selected={context.tutor_roles}
        onChange={(tutor_roles) => save({ tutor_roles })}
      />
      <div className="grid-2">
        <Select
          label="What kind of feedback should it give?"
          value={context.feedback_mode}
          options={FEEDBACK_MODES}
          onChange={(feedback_mode) => save({ feedback_mode: feedback_mode as never })}
        />
        <Select
          label="How much of the unit does it cover?"
          value={context.scope}
          options={SCOPES}
          onChange={(scope) => save({ scope: scope as never })}
        />
      </div>

      <div className="divider" />

      <button className="btn btn-ghost" onClick={() => setDeeper(!deeper)}>
        {deeper ? "Hide" : "Add"} more detail (optional)
      </button>

      {deeper && (
        <div className="deeper">
          <TextArea
            label="How has the topic been taught so far?"
            value={context.instructional_history}
            onSave={(instructional_history) => save({ instructional_history })}
          />
          <TextArea
            label="Which representations have learners already seen?"
            value={context.representations}
            onSave={(representations) => save({ representations })}
          />
          <TextArea
            label="Which terminology do they already know?"
            value={context.terminology}
            onSave={(terminology) => save({ terminology })}
          />
          <TextArea
            label="How different are learners in prior knowledge?"
            value={context.heterogeneity}
            onSave={(heterogeneity) => save({ heterogeneity })}
          />
          <CheckboxGroup
            label="Anything the tutor should or should not do?"
            options={INTENTS}
            selected={context.teacher_intents}
            onChange={(teacher_intents) => save({ teacher_intents })}
          />
          <TextArea
            label="Anything else that matters to you here?"
            rows={2}
            value={context.teacher_intent_note}
            onSave={(teacher_intent_note) => save({ teacher_intent_note })}
          />
          <div className="grid-3">
            <NumberStepper
              label="Minutes"
              hint="How long learners work with it."
              value={context.duration_minutes ?? 20}
              min={5}
              max={120}
              onChange={(duration_minutes) => save({ duration_minutes })}
            />
            <Select
              label="Where"
              value={context.location}
              options={[
                { value: "in class", label: "In class", description: "" },
                { value: "at home", label: "At home", description: "" },
              ]}
              onChange={(location) => save({ location })}
            />
            <Select
              label="How"
              value={context.group_work}
              options={[
                { value: "individually", label: "Individually", description: "" },
                { value: "in pairs", label: "In pairs", description: "" },
                { value: "in groups", label: "In groups", description: "" },
              ]}
              onChange={(group_work) => save({ group_work })}
            />
          </div>
        </div>
      )}

      <div className="divider" />

      <h3>Your context summary</h3>
      {summary && (
        <>
          <dl className="summary-list">
            {summary.sections.map((section) => (
              <div key={section.heading}>
                <dt>{section.heading}</dt>
                <dd>{section.body}</dd>
              </div>
            ))}
          </dl>

          <p className="field-hint">This is what shapes every task the tutor writes.</p>

          {summary.missing.length > 0 && (
            <p className="field-hint warn">Still to answer: {summary.missing.join(", ")}.</p>
          )}

          {context.confirmed_at ? (
            <p className="confirmed-note">
              ✓ Confirmed. Editing anything above will ask you to confirm again.
            </p>
          ) : (
            <button
              className="btn btn-primary btn-lg"
              disabled={busy || !summary.complete}
              onClick={() => run(() => api.confirmContext(projectId))}
            >
              This is my context
            </button>
          )}
        </>
      )}
    </div>
  );
}
