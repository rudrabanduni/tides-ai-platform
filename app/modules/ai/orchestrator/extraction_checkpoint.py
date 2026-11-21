"""Persistent checkpointing and stage configuration for 10-stage startup extraction.

Enables resilient recovery from mid-extraction failures (e.g., provider output
truncation on an individual stage) without rerunning previously completed stages
or breaking database/test isolation.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from pydantic import BaseModel

from app.modules.ai.orchestrator.startup_profile_extraction import (
    CommercialisationExtraction,
    CoverIntakeExtraction,
    FounderCoreExtraction,
    FinancialsSupportExtraction,
    ImpactStrategicAlignmentExtraction,
    InnovationImpactExtraction,
    InnovationIpPatentsExtraction,
    MarketOpportunityExtraction,
    ProblemNeedExtraction,
    PrototypeTechnicalExtraction,
    SolutionProductExtraction,
    TeamAdvisoryExtraction,
    merge_innovation_impact_subsegments,
)


@dataclass(frozen=True)
class ExtractionStageSpec:
    """Single canonical definition of a staged extraction pass."""

    key: str
    schema_cls: type[BaseModel]
    title: str
    scope: str


EXTRACTION_STAGE_SPECS: tuple[ExtractionStageSpec, ...] = (
    ExtractionStageSpec(
        key="cover_intake",
        schema_cls=CoverIntakeExtraction,
        title="Cover & Application Intake (CM-01..06)",
        scope=(
            "Extract company name, tagline, sector, stage, geography, and application "
            "submission date. Do not extract problem, solution, market, or financial details here."
        ),
    ),
    ExtractionStageSpec(
        key="problem_need",
        schema_cls=ProblemNeedExtraction,
        title="Problem & Need (PS-01..05)",
        scope=(
            "Extract core problem statement, target audience / who is affected, current "
            "workarounds, quantitative evidence/metrics of the problem, and why the problem "
            "persists (structural/technical barriers). Do not extract product solution or prototype details here."
        ),
    ),
    ExtractionStageSpec(
        key="solution_product",
        schema_cls=SolutionProductExtraction,
        title="Solution & Product (PS-06..08)",
        scope=(
            "Extract product/service core solution description, key features & benefits "
            "(up to 3 core capabilities), and unique value proposition (UVP delta). Do not "
            "extract TRL, prototype status, technology architecture, or validation results here."
        ),
    ),
    ExtractionStageSpec(
        key="prototype_technical",
        schema_cls=PrototypeTechnicalExtraction,
        title="Prototype & Technical Evidence (PS-09..13)",
        scope=(
            "Extract self-reported TRL (1-9) & justification, demo/prototype link, prototype "
            "maturity stage (PoC, Lab Prototype, MVP, Pilot-Ready), core technology architecture "
            "stack, and technical validation results / lab benchmarks / clinical test data. Do not "
            "extract solution overview or market details here."
        ),
    ),
    ExtractionStageSpec(
        key="market_opportunity",
        schema_cls=MarketOpportunityExtraction,
        title="Market Opportunity (MO-01..10)",
        scope=(
            "Extract TAM (market size), SAM, SOM (3-5 year), market CAGR %, CAGR source, key "
            "market drivers, geographic/segment market description, direct competitor details "
            "(name, country, funding, approach, advantage), and sustainable competitive advantage (moat)."
        ),
    ),
    ExtractionStageSpec(
        key="founder_core",
        schema_cls=FounderCoreExtraction,
        title="Founder & Core Leadership (FT-01..06)",
        scope=(
            "Extract structured founder records (name, role, equity percentage, linkedin URL, "
            "education degree/institution/graduation year, relevant experience, domain expertise, "
            "prior startups, key achievement), and overall team capabilities summary. Do not "
            "extract advisors, hiring plan, or non-founder team members here."
        ),
    ),
    ExtractionStageSpec(
        key="team_advisory",
        schema_cls=TeamAdvisoryExtraction,
        title="Team Organization, Hiring & Advisory Governance (FT-07..13)",
        scope=(
            "Extract core non-founder key team members, critical skill gaps, hiring plan & timing, "
            "named advisors/mentors, primary mentor contribution, secondary mentor contribution, "
            "and institutional/incubator affiliations. Do not extract founder personal biographies here."
        ),
    ),
    ExtractionStageSpec(
        key="commercialisation",
        schema_cls=CommercialisationExtraction,
        title="Business Model & Commercialisation (BC-01..13)",
        scope=(
            "Extract business model, revenue model, pricing strategy, customer acquisition channels, "
            "CAC, expected gross margin, payback period, path to first revenue, user counts "
            "(free vs paying), current revenue, pilot agreements / LOIs, awards & grants, "
            "research validation endorsements, and customer quotes."
        ),
    ),
    ExtractionStageSpec(
        key="innovation_impact",
        schema_cls=InnovationImpactExtraction,
        title="Innovation, IP & Impact (II-01..11)",
        scope=(
            "Extract proprietary technology moat, data advantage flywheel, network effects, "
            "switching costs, brand moat, regulatory/licensing barriers, patent details "
            "(title, application number, status, jurisdiction), primary impact, SDG alignments, "
            "impact metrics, and negative externalities mitigation."
        ),
    ),
    ExtractionStageSpec(
        key="financials_support",
        schema_cls=FinancialsSupportExtraction,
        title="Financials & Incubation Support (FI-01..21)",
        scope=(
            "Extract 3-year projections (revenue, gross margin, customers, headcount), monthly burn "
            "rate, break-even timing, financial assumptions, funding raised to date, operating costs, "
            "incubation support requests (lab facilities, mentorship, industry connections, legal/IP, "
            "market access, training; max 4 concise <=10-word items per list), 6-quarter roadmaps "
            "(product, market, team, funding; <=10 words per quarter milestone), authorized contact, "
            "and applicant declaration. Omit or leave null any unstated forecast or metric."
        ),
    ),
)

STAGE_SPECS_BY_KEY: Dict[str, ExtractionStageSpec] = {spec.key: spec for spec in EXTRACTION_STAGE_SPECS}


def normalize_extraction_stage_name(raw_stage: str) -> str:
    """Normalize 'financials_support' or 'extraction_financials_support' to canonical stage key."""
    key = (raw_stage or "").strip().lower()
    if key.startswith("extraction_"):
        key = key[len("extraction_"):]
    if key == "auto":
        return "auto"
    if key in ("innovation_ip_patents", "impact_strategic_alignment"):
        return key
    if key not in STAGE_SPECS_BY_KEY:
        raise ValueError(
            f"Unknown extraction stage '{raw_stage}'. Expected one of: {list(STAGE_SPECS_BY_KEY.keys())}"
        )
    return key


def normalize_uuid_hex(value: uuid.UUID | str) -> str:
    """Return canonical lowercase 32-char UUID hex string for safe equality checks."""
    return str(value).strip().lower().replace("-", "")


def resolve_extraction_checkpoint_path(
    upload_dir: str | Path,
    startup_id: uuid.UUID | str,
    evaluation_id: str,
) -> Path:
    """Resolve isolated per-evaluation extraction checkpoint path under upload_dir.

    During pytest runs using the default workspace upload directory, redirects to a
    system temporary folder so test execution never pollutes workspace uploads/.
    """
    safe_eval = str(evaluation_id).strip().replace("/", "_").replace("\\", "_")
    safe_startup = str(startup_id).strip().replace("/", "_").replace("\\", "_")
    base_dir = Path(upload_dir)
    if os.environ.get("PYTEST_CURRENT_TEST"):
        default_workspace_uploads = (Path(__file__).resolve().parents[4] / "uploads").resolve()
        try:
            if base_dir.resolve() == default_workspace_uploads:
                base_dir = Path(tempfile.gettempdir()) / "tides_pytest_uploads"
        except Exception:
            pass
    return base_dir / "extraction_checkpoints" / f"{safe_startup}_{safe_eval}.json"


def save_extraction_checkpoint(
    checkpoint_path: Path,
    *,
    evaluation_id: str,
    startup_id: uuid.UUID | str,
    startup_name: str,
    completed_stages: Mapping[str, BaseModel],
    failed_stage: str | None = None,
    completed: bool = False,
    document_ids: Iterable[str] = (),
    parent_evaluation_id: str | None = None,
    subsegments: Mapping[str, BaseModel] | None = None,
) -> Path:
    """Atomically persist completed extraction stages and subsegments to disk."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_stages: Dict[str, Any] = {}
    for spec in EXTRACTION_STAGE_SPECS:
        model_obj = completed_stages.get(spec.key)
        if model_obj is not None:
            serialized_stages[spec.key] = model_obj.model_dump()

    serialized_subsegments: Dict[str, Any] = {}
    if subsegments:
        for skey, sobj in subsegments.items():
            if sobj is not None and hasattr(sobj, "model_dump"):
                serialized_subsegments[skey] = sobj.model_dump()

    payload = {
        "evaluation_id": str(evaluation_id),
        "parent_evaluation_id": parent_evaluation_id,
        "startup_id": str(startup_id),
        "startup_name": startup_name,
        "document_ids": list(document_ids),
        "stage_order": [spec.key for spec in EXTRACTION_STAGE_SPECS],
        "completed_stages": serialized_stages,
        "subsegments": serialized_subsegments,
        "failed_stage": failed_stage,
        "completed": completed,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    tmp_path = checkpoint_path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, checkpoint_path)
    return checkpoint_path


def load_extraction_checkpoint(
    checkpoint_path: Path,
    *,
    expected_startup_id: uuid.UUID | str,
    expected_evaluation_id: str,
) -> Dict[str, Any]:
    """Load and validate an extraction checkpoint, failing closed on ID mismatch."""
    if not checkpoint_path.exists():
        return {
            "exists": False,
            "completed_stages": {},
            "subsegments": {},
            "failed_stage": None,
            "completed": False,
        }

    with open(checkpoint_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    ckpt_eval_id = str(payload.get("evaluation_id") or "")
    if ckpt_eval_id != str(expected_evaluation_id):
        raise ValueError(
            f"Extraction checkpoint evaluation ID mismatch: expected '{expected_evaluation_id}', "
            f"found '{ckpt_eval_id}'."
        )

    ckpt_startup_id = str(payload.get("startup_id") or "")
    if normalize_uuid_hex(ckpt_startup_id) != normalize_uuid_hex(expected_startup_id):
        raise ValueError(
            f"Extraction checkpoint startup ID mismatch: expected '{expected_startup_id}', "
            f"found '{ckpt_startup_id}'."
        )

    raw_stages = payload.get("completed_stages") or {}
    deserialized: Dict[str, BaseModel] = {}
    for spec in EXTRACTION_STAGE_SPECS:
        stage_data = raw_stages.get(spec.key)
        if stage_data is not None:
            deserialized[spec.key] = spec.schema_cls.model_validate(stage_data)

    raw_subsegments = payload.get("subsegments") or {}
    deserialized_subsegments: Dict[str, BaseModel] = {}
    if "innovation_ip_patents" in raw_subsegments:
        deserialized_subsegments["innovation_ip_patents"] = (
            InnovationIpPatentsExtraction.model_validate(raw_subsegments["innovation_ip_patents"])
        )
    if "impact_strategic_alignment" in raw_subsegments:
        deserialized_subsegments["impact_strategic_alignment"] = (
            ImpactStrategicAlignmentExtraction.model_validate(raw_subsegments["impact_strategic_alignment"])
        )

    return {
        "exists": True,
        "completed_stages": deserialized,
        "subsegments": deserialized_subsegments,
        "failed_stage": payload.get("failed_stage"),
        "completed": bool(payload.get("completed")),
        "raw": payload,
    }
