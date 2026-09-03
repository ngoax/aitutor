"""Write a project's drafts as an OATutor content source"""

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select

from app.core.config import settings
from app.export.markdown_utils import (
    ignored_delimiters,
    to_oatutor_text,
    unbalanced_delimiters,
)
from app.export.oatutor_schema import HintJson, ProblemJson, StepJson
from app.generation.persist import slugify
from app.models import (
    DraftStatus,
    HintType,
    Problem,
    ProblemType,
    Project,
    SkillDefault,
    Step,
)

PATHWAY_SUFFIX = "DefaultPathway"
GRID_TYPES = (ProblemType.GRID_INPUT, ProblemType.MATRIX_INPUT)
# Hint 'oer' records who wrote the hint; upstream uses "openai" for generated ones.
GENERATED_BY = "aitutor"
DEFAULT_MASTERY = 0.85
BKT_DEFAULTS = {"probMastery": 0.1, "probTransit": 0.1, "probSlip": 0.1, "probGuess": 0.1}
BKT_FILES = ("defaultBKTParams.json", "experimentalBKTParams.json")


class ExportResult(BaseModel):
    root: str
    written: list[str]
    skipped: dict[str, str]
    note: str | None = None


def _export_root(project: Project) -> Path:
    if settings.oatutor_content_dir is not None:
        return settings.oatutor_content_dir
    return settings.exports_dir / project.source_name


def _rebuild_problem_pool(root: Path) -> str:
    """OATutor serves a generated index, so new problems stay invisible until this runs."""
    tool = root.parent.parent / "tools" / "preprocessProblemPool.js"
    if not tool.exists():
        return f"Run the problem pool preprocessor yourself; {tool} was not found."
    try:
        result = subprocess.run(
            ["node", tool.name],
            cwd=tool.parent,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"Could not run {tool.name}: {exc}"
    if result.returncode != 0:
        return f"{tool.name} failed: {result.stderr.strip()[:300]}"
    return "Problem pool rebuilt. Restart the OATutor dev server to pick up the new lesson."


def _reject_ignored(field: str, value: str) -> None:
    ignored = ignored_delimiters(value)
    if ignored:
        raise ValueError(
            f"{field} wraps maths in {' and '.join(ignored)}, which OATutor prints "
            "as plain text. Use $$ instead."
        )


def _checked(field: str, text: str) -> str:
    value = to_oatutor_text(text)
    odd = unbalanced_delimiters(value)
    if odd:
        raise ValueError(f"{field} has an unclosed {' and '.join(odd)}")
    _reject_ignored(field, value)
    return value


def _checked_answers(field: str, values: list) -> list[str]:
    """Answers are graded rather than rendered, so they keep their text as written.
    A delimiter OATutor ignores still has to go: KAS would never parse it."""
    answers = [str(value) for value in values]
    for answer in answers:
        _reject_ignored(field, answer)
    return answers


def _answer_strings(step: Step) -> list[str]:
    """Grid answers are rows in the database and one stringified list of lists here."""
    answer = step.step_answer or []
    if step.problem_type in GRID_TYPES:
        return [json.dumps(answer)]
    return _checked_answers("stepAnswer", answer)


def _step_json(step: Step) -> StepJson:
    return StepJson(
        id=step.oatutor_id,
        step_answer=_answer_strings(step),
        problem_type=step.problem_type,
        answer_type=step.answer_type,
        step_title=_checked("stepTitle", step.step_title),
        step_body=_checked("stepBody", step.step_body),
        choices=[_checked("choice", choice) for choice in step.choices] if step.choices else None,
        num_rows=step.num_rows,
        num_cols=step.num_cols,
    )


def _pathway_json(step: Step, license_: str) -> list[HintJson]:
    hints = sorted(step.hints, key=lambda hint: hint.order_index)
    ids = [hint.oatutor_id for hint in hints]
    entries: list[HintJson] = []
    for hint in hints:
        scaffold = hint.type is HintType.SCAFFOLD
        entries.append(
            HintJson(
                id=hint.oatutor_id,
                # OATutor knows no "solution"; ours only marks which entry gives it away.
                type="scaffold" if scaffold else "hint",
                title=_checked("hint title", hint.title),
                text=_checked("hint text", hint.text),
                dependencies=[ids[i] for i in hint.dependencies if 0 <= i < len(ids)],
                oer=GENERATED_BY,
                license=license_,
                problem_type=hint.problem_type if scaffold else None,
                answer_type=hint.answer_type if scaffold else None,
                hint_answer=_checked_answers("hintAnswer", hint.hint_answer or [])
                if scaffold
                else None,
                choices=[_checked("choice", choice) for choice in hint.choices]
                if scaffold and hint.choices
                else None,
            )
        )
    return entries


def _problem_json(problem: Problem, project: Project, lesson_id: str) -> ProblemJson:
    return ProblemJson(
        id=problem.oatutor_id,
        title=_checked("title", problem.title),
        body=_checked("body", problem.body),
        oer=problem.oer or "",
        license=project.license,
        lesson=project.name,
        lesson_id=lesson_id,
        course_name=problem.course_name or project.name,
    )


def _problem_documents(
    problem: Problem, project: Project, lesson_id: str
) -> tuple[dict[Path, Any], dict[str, list[str]]]:
    base = Path("content-pool") / problem.oatutor_id
    documents: dict[Path, Any] = {
        base / f"{problem.oatutor_id}.json": _problem_json(problem, project, lesson_id)
    }
    skill = slugify(problem.topic or problem.title)
    skills = {}
    for step in sorted(problem.steps, key=lambda step: step.order_index):
        step_dir = base / "steps" / step.oatutor_id
        documents[step_dir / f"{step.oatutor_id}.json"] = _step_json(step)
        pathway = _pathway_json(step, project.license)
        documents[step_dir / "tutoring" / f"{step.oatutor_id}{PATHWAY_SUFFIX}.json"] = pathway
        skills[step.oatutor_id] = step.skills or [skill]
    return documents, skills


def _dump(payload: Any) -> Any:
    if isinstance(payload, list):
        return [item.model_dump(by_alias=True, exclude_none=True) for item in payload]
    return payload.model_dump(by_alias=True, exclude_none=True)


def _read_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text()) if path.exists() else fallback


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n")


def _merge_course_plans(plans: list[dict], project: Project, lesson: dict) -> list[dict]:
    course = next((c for c in plans if c.get("courseName") == project.name), None)
    if course is None:
        course = {
            "courseName": project.name,
            "language": "en",
            "courseOER": "",
            "courseLicense": project.license,
            "lessons": [],
        }
        plans.append(course)
    lessons = course.setdefault("lessons", [])
    for index, existing in enumerate(lessons):
        if existing.get("id") == lesson["id"]:
            lessons[index] = lesson
            return plans
    lessons.append(lesson)
    return plans


def export_project(session: Session, project: Project) -> ExportResult:
    root = _export_root(project)
    lesson_id = f"{project.source_name}-lesson"

    problems = session.exec(
        select(Problem).where(Problem.project_id == project.id).order_by(Problem.id)
    ).all()

    documents: dict[Path, Any] = {}
    skill_model: dict[str, list[str]] = {}
    written: list[str] = []
    skipped: dict[str, str] = {}

    for problem in problems:
        if problem.status in (DraftStatus.GENERATING, DraftStatus.FAILED):
            skipped[problem.oatutor_id] = f"status is {problem.status.value}"
            continue
        if not problem.steps:
            skipped[problem.oatutor_id] = "has no steps"
            continue
        try:
            problem_documents, skills = _problem_documents(problem, project, lesson_id)
        except (ValidationError, ValueError) as exc:
            skipped[problem.oatutor_id] = str(exc)
            continue
        documents.update(problem_documents)
        skill_model.update(skills)
        written.append(problem.oatutor_id)

    if not written:
        return ExportResult(root=str(root), written=written, skipped=skipped)

    for path, payload in documents.items():
        _write_json(root / path, _dump(payload))

    merged_skills = _read_json(root / "skillModel.json", {}) | skill_model
    _write_json(root / "skillModel.json", merged_skills)

    used = sorted({skill for names in merged_skills.values() for skill in names})
    lesson = {
        "id": lesson_id,
        "name": project.name,
        "topics": "",
        "allowRecycle": True,
        "chat_display_mode": "Window",
        "learningObjectives": {skill: DEFAULT_MASTERY for skill in used},
    }
    plans = _read_json(root / "coursePlans.json", [])
    _write_json(root / "coursePlans.json", _merge_course_plans(plans, project, lesson))

    tuned = {
        default.skill: {
            "probMastery": default.prob_mastery,
            "probTransit": default.prob_transit,
            "probSlip": default.prob_slip,
            "probGuess": default.prob_guess,
        }
        for default in session.exec(
            select(SkillDefault).where(SkillDefault.project_id == project.id)
        ).all()
    }
    for name in BKT_FILES:
        bkt_path = root / "bkt-params" / name
        bkt = _read_json(bkt_path, {})
        for skill in used:
            # setdefault so parameters a teacher has already tuned survive a re-export.
            bkt.setdefault(skill, tuned.get(skill, dict(BKT_DEFAULTS)))
        _write_json(bkt_path, bkt)

    note = _rebuild_problem_pool(root) if settings.oatutor_content_dir is not None else None
    return ExportResult(root=str(root), written=written, skipped=skipped, note=note)
