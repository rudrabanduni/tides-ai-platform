import os
import base64
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import UploadFile

# Database and services
from app.modules.startups.schemas import StartupCreate
from app.modules.startups.service import StartupService
from app.modules.startups.models import StartupApplication
from app.modules.documents.service import DocumentService
from app.core.enums import DocumentType
from app.modules.intelligence.service import IntelligenceService
from app.modules.intelligence.claim_engine import ClaimEngine
from app.modules.intelligence.repository import (
    StartupIntelligenceProfileRepository,
    StartupClaimRepository,
    StartupEvidenceRepository,
    FieldConflictRepository
)
from app.modules.intelligence.models import StartupIntelligenceProfile, StartupClaim, StartupEvidence, FieldConflict

# AI extraction models
from pydantic import BaseModel, Field
from app.modules.intelligence.ai.schemas import (
    DocumentExtraction, FounderInfo, ProductInfo, MarketInfo,
    FinancialInfo, TechnologyInfo, RiskInfo, ExtractedString, ExtractedFloat, ExtractedInt
)
from app.modules.ai.orchestrator.startup_profile_extraction import StartupProfileExtraction
# Services-layer LLM gateway (real LLM, not regex mock)
from app.services.ai.gateway import create_ai_gateway
from app.services.ai.schemas import AICompletionRequest

# AI Orchestration & Report components
from app.modules.ai.orchestrator.orchestrator import AIOrchestrator
from app.modules.ai.orchestrator.aggregator import AssessmentAggregator
from app.modules.ai.orchestrator.report_integration import integrate_assessment_to_graph
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.conflict_resolution.conflict_engine import ConflictResolutionEngine
from app.modules.evaluation.executive.executive_engine import ExecutiveEngine
from app.modules.evaluation.investment.investment_engine import InvestmentEngine
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_serializer import ReportSerializer
from app.modules.evaluation.committee.committee_engine import CommitteeDecisionEngine
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json

logger = logging.getLogger(__name__)



async def coordinate_evaluation_pipeline(
    db: Session,
    startup_name: str,
    sector: str,
    stage: str,
    files: List[UploadFile]
) -> Dict[str, Any]:
    """Coordinates the entire ingestion, parsing, AI extraction, multi-agent evaluation,
    aggregation, and report building pipeline in a single flow.
    """
    # 1. Create Startup Application
    startup_payload = StartupCreate(
        startup_name=startup_name,
        sector=sector,
        stage=stage,
        problem_statement="To be extracted",
        solution_summary="To be extracted",
        business_model="To be extracted",
        target_market="To be extracted"
    )
    startup_service = StartupService(db)
    startup = startup_service.create(startup_payload, actor_id=None)
    
    # 2. Upload and Parse Documents
    doc_service = DocumentService(db)
    intel_service = IntelligenceService(db)
    parsed_docs = []
    
    for upload_file in files:
        doc = doc_service.upload(
            startup.id,
            file=upload_file,
            document_type=DocumentType.PITCH_DECK,
            actor_id=None
        )
        # Process parsing synchronously
        intel_service.process_document(doc.id)
        db.refresh(doc)
        parsed_docs.append(doc)

    combined_text = "\n\n".join(d.parsed_text for d in parsed_docs if d.parsed_text)
    if not combined_text.strip():
        combined_text = f"Startup: {startup_name}\nSector: {sector}\nStage: {stage}\nNo pitch deck text could be extracted."

    # 3. AI Profile Extraction — uses the configured LLM via LiteLLM (never regex heuristics)
    _llm = create_ai_gateway()
    _extraction_req = AICompletionRequest(
        system_prompt=(
            "You are an expert venture capital analyst performing due diligence on a startup pitch deck. "
            "Your task is to extract specific, atomic facts from the document provided. "
            "Rules:\n"
            "1. Every field must be a single atomic value: one name, one sentence, one number, or one short phrase.\n"
            "2. Never include raw paragraphs, OCR text dumps, slide headers, bullet lists, roadmap text, "
            "email addresses, phone numbers, or multiple unrelated concepts in a single field.\n"
            "3. If a piece of information is not present in the document, return null for that field.\n"
            "4. Do not guess or hallucinate. Only extract what is explicitly stated."
        ),
        user_prompt=(
            f"Pitch deck text from '{startup_name}' ({sector}, {stage} stage):\n\n"
            f"{combined_text}\n\n"
            "Extract the startup profile fields as specified. Return only what is explicitly stated."
        ),
    )
    import asyncio as _asyncio
    import json as _json
    _extraction_result = await _asyncio.get_event_loop().run_in_executor(
        None, lambda: _llm.complete_json(_extraction_req, StartupProfileExtraction)
    )
    extracted: StartupProfileExtraction = _extraction_result.data

    # ── PRINT EXTRACTED JSON BEFORE ANY MAPPING ──────────────────────────────
    logger.info("[EXTRACTION] StartupProfileExtraction JSON (before mapping):\n%s",
                extracted.model_dump_json(indent=2))
    print("\n" + "="*70)
    print("[EXTRACTION] StartupProfileExtraction JSON (before mapping):")
    print(extracted.model_dump_json(indent=2))
    print("="*70 + "\n")
    

    db.add(startup)
    db.flush()

    # Seed Founders database table
    from app.modules.founders.models import Founder
    for i, fname in enumerate(extracted.founders):
        role = (
            extracted.founder_roles[i]
            if extracted.founder_roles and i < len(extracted.founder_roles)
            else "Founder"
        )
        if fname and fname.lower() not in ["n/a", "not specified", "unknown"]:
            founder = Founder(
                startup_id=startup.id,
                name=fname,
                role_in_startup=role
            )
            db.add(founder)
    db.flush()

    # 4. Map to ClaimEngine to populate claims & evidence in database
    def make_ext_str(val: str, snippet: str = "Extracted from deck.") -> ExtractedString:
        return ExtractedString(
            value=val,
            why_extracted="AI Extraction",
            supporting_evidence=snippet,
            document_section="Pitch Deck",
            confidence_score=0.9,
            confidence_reason="Clear textual evidence"
        )
        
    doc_ext = DocumentExtraction(
        founder=FounderInfo(
            founder_names=make_ext_str(", ".join(extracted.founders) if extracted.founders else "Not specified"),
            leadership_experience=make_ext_str(extracted.team or "Not specified"),
            domain_expertise=make_ext_str(extracted.team or "Not specified"),
            commitment_level=make_ext_str("Full-Time")
        ),
        product=ProductInfo(
            description=make_ext_str(extracted.solution or "Not specified"),
            problem_solved=make_ext_str(extracted.problem_statement or "Not specified"),
            solution_value_prop=make_ext_str(extracted.solution or "Not specified"),
            customers=make_ext_str(extracted.traction or "Not specified"),
            business_model=make_ext_str(extracted.business_model or "Not specified")
        ),
        market=MarketInfo(
            target_market=make_ext_str(extracted.market or "Not specified"),
            market_size=make_ext_str(extracted.market_size or extracted.market or "Not specified"),
            competitors=make_ext_str(extracted.competition or "Not specified"),
            competition_analysis=make_ext_str(extracted.competition or "Not specified")
        ),
        financial=FinancialInfo(
            revenue_model=make_ext_str(extracted.revenue_model or extracted.business_model or "Not specified"),
            funding_received=ExtractedFloat(value=0.0, why_extracted="N/A", supporting_evidence="N/A", confidence_score=0.9),
            current_revenue=ExtractedFloat(value=0.0, why_extracted="N/A", supporting_evidence="N/A", confidence_score=0.9),
            financial_metrics=make_ext_str(extracted.financial_information or "Not specified")
        ),
        technology=TechnologyInfo(
            description=make_ext_str(extracted.technology or "Not specified"),
            trl_level=ExtractedInt(value=4, why_extracted="Default", supporting_evidence="Default", confidence_score=0.9),
            ip_status=make_ext_str(extracted.patents or extracted.technology or "Not specified")
        ),
        risk=RiskInfo(
            major_risks=[make_ext_str("Execution Risk")]
        )
    )

    primary_doc_id = parsed_docs[0].id if parsed_docs else uuid.uuid4()
    claim_engine = ClaimEngine(db)
    claim_engine.process_extraction(startup.id, doc_ext, primary_doc_id)
    db.commit()

    # Load populated DB entities
    profile = StartupIntelligenceProfileRepository(db).get_by_startup(startup.id)
    claims = StartupClaimRepository(db).list_for_profile(profile.id)
    evidence = db.query(StartupEvidence).join(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()
    
    # 5. AI Multi-Agent Evaluation
    profile_dict = {
        "id": str(startup.id),
        "startup_id": str(startup.id),
        "startup_name": startup.startup_name,
        "sector": startup.sector,
        "stage": startup.stage
    }
    
    orchestrator = AIOrchestrator()
    state = await orchestrator.execute_workflow(
        startup_profile=profile_dict,
        claims=claims,
        evidence=evidence
    )
    
    # 6. Aggregate Results
    aggregated = AssessmentAggregator.aggregate(state.outputs)
    
    # 7. Execute all 8 experts & Populate ObservationGraph
    from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
    from app.modules.evaluation.founder_expert import FounderExpert
    from app.modules.evaluation.product_expert import ProductExpert
    from app.modules.evaluation.market_expert import MarketExpert
    from app.modules.evaluation.financial_expert import FinancialExpert
    from app.modules.evaluation.trl_expert import TRLExpert
    from app.modules.evaluation.competition_expert import CompetitionExpert
    from app.modules.evaluation.ip_expert import IPExpert
    from app.modules.evaluation.risk_expert import RiskExpert
    
    experts = [
        FounderExpert(), ProductExpert(), MarketExpert(), FinancialExpert(),
        TRLExpert(), CompetitionExpert(), IPExpert(), RiskExpert()
    ]

    assessments = []
    for expert in experts:
        draft = expert.evaluate(profile, claims, evidence, [], {})
        assessments.append(draft)

    # Build graph using standard graph builder
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments, [])
    graph.startup_name = startup.startup_name

    # Resolve graph downstream decision flows
    graph = ConflictResolutionEngine.resolve(graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)
    graph = CommitteeDecisionEngine.generate(graph)
    
    # 8. Update DB stats and status
    from app.core.enums import StartupStatus
    from app.modules.startup_profiles.models import AIAssessmentRecord
    
    decision = graph.committee_decision.recommendation if graph.committee_decision else "PENDING_DD"
    decision_str = str(decision.value) if hasattr(decision, "value") else str(decision)
    
    if decision_str == "INCUBATE":
        startup.current_status = StartupStatus.APPROVED_FOR_INCUBATION
        rec_status = "recommended"
    elif decision_str in ("DEFER", "REJECT"):
        startup.current_status = StartupStatus.REJECTED
        rec_status = "rejected"
    else: # PENDING_DD or other status
        startup.current_status = StartupStatus.UNDER_REVIEW
        rec_status = "review"
        
    db.add(startup)
    
    # Create AIAssessmentRecord
    exec_summary = getattr(graph.report, "executive_summary", None)
    exec_summary_str = "No executive summary available."
    if exec_summary:
        exec_summary_str = getattr(exec_summary, "content", "No executive summary content.")
        
    strengths = []
    weaknesses = []
    recs = []
    if graph.executive_assessment and graph.executive_assessment.summary:
        strengths = graph.executive_assessment.summary.strengths
        weaknesses = graph.executive_assessment.summary.weaknesses
        recs = graph.executive_assessment.summary.opportunities
        
    overall_score = int(getattr(graph.report, "overall_score", 0.9) * 100) if hasattr(graph.report, "overall_score") else 90
    if not overall_score and graph.investment_assessment:
        overall_score = int(graph.investment_assessment.investment_score)
    
    # Extract sub-scores
    innovation_score = int(getattr(aggregated.product_assessment, "overall_score", 0.9) * 100)
    market_score = int(getattr(aggregated.market_assessment, "overall_score", 0.9) * 100)
    execution_score = int(getattr(aggregated.founder_assessment, "overall_score", 0.9) * 100)
    
    assessment_record = AIAssessmentRecord(
        startup_id=startup.id,
        executive_summary=exec_summary_str,
        innovation_score=innovation_score,
        market_score=market_score,
        execution_score=execution_score,
        overall_score=overall_score,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recs,
        recommendation_status=rec_status,
        assessed_by=None
    )
    db.add(assessment_record)
    db.commit()
    
    # Save graph file to disk
    graphs_dir = os.path.join("uploads", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    path = os.path.join(graphs_dir, f"{graph.startup_id}.json")
    json_str = graph_to_json(graph)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # 9. Export PDF
    pdf_bytes = ReportSerializer.export_pdf_data(graph.report)
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    return {
        "evaluation_status": "COMPLETED",
        "assessment_identifier": graph.report.report_id,
        "generated_report": graph.report.model_dump() if hasattr(graph.report, "model_dump") else graph.report.__dict__,
        "pdf_url": f"/reports/{startup.id}/download",
        "pdf_base64": pdf_base64
    }
