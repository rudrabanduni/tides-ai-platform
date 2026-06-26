from app.services.ai import AICompletionRequest, create_ai_gateway
from app.modules.startup_profiles.context import StartupProfileContextBuilder
from app.modules.startup_profiles.schemas import (
    StartupProfileAgentOutput,
    StartupEvaluationScore,
    StartupEvaluationOutput,
    StartupAssessmentResult,
)


class StartupProfileAgentService:
    def __init__(self, db):
        self.db = db
        self.gateway = create_ai_gateway()

    def build_context(
        self,
        startup,
        founders=None,
        startup_profile=None,
        company_profile=None,
        documents=None,
    ):
        return StartupProfileContextBuilder().build(
            startup=startup,
            founders=founders or [],
            profile=startup_profile,
            company_profile=company_profile,
            documents=documents or [],
        )

    def generate_profile(self, context):
        startup = context.startup

        startup_name = startup.startup_name or "Unknown Startup"
        stage = startup.stage or "early-stage"
        problem = startup.problem_statement or "an identified market problem"
        solution = startup.solution_summary or "an innovative solution"
        market = startup.target_market or "an identified customer segment"
        business_model = startup.business_model or "to be determined"

        if business_model.lower() == "saas":
            executive_summary = (
                f"{startup_name} is an {stage.lower()} SaaS venture serving "
                f"{market}. The startup addresses {problem} through "
                f"{solution}."
            )
        else:
            executive_summary = (
                f"{startup_name} is an {stage.lower()} startup serving "
                f"{market}. The startup addresses {problem} through "
                f"{solution}."
            )

        strengths = []

        if startup.solution_summary:
            strengths.append("Clear solution articulation")

        if startup.target_market:
            strengths.append("Defined target market")

        if startup.business_model:
            strengths.append("Business model identified")

        risks = []

        if not startup.business_model:
            risks.append("Business model not defined")

        if not startup.traction_summary:
            risks.append("No traction information provided")

        missing_information = []

        if not startup.traction_summary:
            missing_information.append("Traction details")

        if not startup.funding_status:
            missing_information.append("Funding status")

        return StartupProfileAgentOutput(
            executive_summary=executive_summary,
            business_model=business_model,
            customer_segments=market,
            market_opportunity=f"Potential market opportunity within {market}.",
            strengths=strengths,
            risks=risks,
            missing_information=missing_information,
        )

    def evaluate_startup(self, context) -> StartupEvaluationScore:
        startup = context.startup

        solution_summary = getattr(startup, "solution_summary", None)
        target_market = getattr(startup, "target_market", None)
        business_model = getattr(startup, "business_model", None)
        traction_summary = getattr(startup, "traction_summary", None)
        funding_status = getattr(startup, "funding_status", None)

        innovation_score = 0
        market_score = 0
        execution_score = 0
        rationale = []

        if solution_summary:
            innovation_score += 3
            rationale.append("Has solution summary (+3 innovation)")
        else:
            rationale.append("Missing solution summary (0 innovation)")

        if target_market:
            market_score += 3
            rationale.append("Has target market (+3 market)")
        else:
            rationale.append("Missing target market (0 market)")

        if business_model:
            execution_score += 2
            rationale.append("Has business model (+2 execution)")
        else:
            rationale.append("Missing business model (0 execution)")

        if traction_summary:
            execution_score += 2
            rationale.append("Has traction summary (+2 execution)")
        else:
            rationale.append("Missing traction summary (0 execution)")

        if funding_status:
            execution_score += 1
            rationale.append("Has funding status (+1 execution)")
        else:
            rationale.append("Missing funding status (0 execution)")

        overall_score = innovation_score + market_score + execution_score

        return StartupEvaluationScore(
            innovation_score=innovation_score,
            market_score=market_score,
            execution_score=execution_score,
            overall_score=overall_score,
            rationale=rationale,
        )

    def build_evaluation_prompt(self, context) -> str:
        startup = context.startup

        startup_name = getattr(startup, "startup_name", None) or "Not specified"
        problem_statement = getattr(startup, "problem_statement", None) or "Not specified"
        solution_summary = getattr(startup, "solution_summary", None) or "Not specified"
        target_market = getattr(startup, "target_market", None) or "Not specified"
        stage = getattr(startup, "stage", None) or "Not specified"
        business_model = getattr(startup, "business_model", None) or "Not specified"
        traction_summary = getattr(startup, "traction_summary", None) or "Not specified"
        funding_status = getattr(startup, "funding_status", None) or "Not specified"

        # Extract and format supporting documents with limits
        MAX_DOC_CHARS = 3000
        MAX_TOTAL_DOC_CHARS = 10000

        parsed_docs = []
        docs_list = getattr(context, "documents", None) or []
        for doc in docs_list:
            status = getattr(doc, "processing_status", None)
            if hasattr(status, "value"):
                status = status.value
            if status != "parsed":
                continue

            doc_type = getattr(doc, "document_type", None)
            if hasattr(doc_type, "value"):
                doc_type = doc_type.value

            orig_filename = getattr(doc, "original_filename", None) or "Unknown"
            parsed_text = getattr(doc, "parsed_text", None) or ""

            parsed_docs.append({
                "document_type": doc_type or "Not specified",
                "original_filename": orig_filename,
                "parsed_text": parsed_text,
            })

        documents_section = ""
        if parsed_docs:
            documents_section = "\nSupporting Documents:\n"
            total_doc_context = ""
            for doc in parsed_docs:
                doc_type = doc["document_type"]
                orig_filename = doc["original_filename"]
                text = doc["parsed_text"]

                # Control 1: Per-document limit (2,000–3,000 characters)
                if len(text) > MAX_DOC_CHARS:
                    truncated_text = text[:MAX_DOC_CHARS] + "... [TRUNCATED]"
                else:
                    truncated_text = text

                doc_str = (
                    f"- Document Type: {doc_type}\n"
                    f"  Original Filename: {orig_filename}\n"
                    f"  Parsed Text: {truncated_text}\n"
                )

                # Control 2: Total document context limit (8,000–12,000 characters)
                if len(total_doc_context) + len(doc_str) > MAX_TOTAL_DOC_CHARS:
                    allowed_len = MAX_TOTAL_DOC_CHARS - len(total_doc_context)
                    if allowed_len > 0:
                        header = f"- Document Type: {doc_type}\n  Original Filename: {orig_filename}\n  Parsed Text: "
                        if allowed_len > len(header) + 15:
                            text_allowed_len = allowed_len - len(header) - 15
                            truncated_val = truncated_text[:text_allowed_len] + "... [TRUNCATED]\n"
                            doc_str = header + truncated_val
                        else:
                            doc_str = doc_str[:allowed_len]
                        total_doc_context += doc_str
                    break
                else:
                    total_doc_context += doc_str

            documents_section += total_doc_context

        prompt = f"""You are a startup evaluator for TIDES IIT Roorkee.

Evaluate the following startup details:
- Startup Name: {startup_name}
- Stage: {stage}
- Problem Statement: {problem_statement}
- Solution Summary: {solution_summary}
- Target Market: {target_market}
- Business Model: {business_model}
- Traction Summary: {traction_summary}
- Funding Status: {funding_status}
{documents_section}
Scoring Rubric:
1. Innovation (0-10)
   - Novelty
   - Technical differentiation
   - Defensibility
2. Market Potential (0-10)
   - Market size
   - Customer clarity
   - Scalability
3. Execution Readiness (0-10)
   - Business model maturity
   - Traction
   - Funding readiness

Rules:
- Use only supplied information.
- Do not invent facts.
- Penalize missing information.
- Explain reasoning briefly.
- Return JSON only.

Output Contract JSON:
{{
  "executive_summary": "",
  "innovation_score": 0,
  "market_score": 0,
  "execution_score": 0,
  "overall_score": 0,
  "strengths": [],
  "weaknesses": [],
  "recommendations": []
}}
"""
        return prompt

    def evaluate_startup_with_ai(self, context) -> StartupEvaluationOutput:
        prompt = self.build_evaluation_prompt(context)

        request = AICompletionRequest(
            system_prompt="You are a startup evaluator for TIDES IIT Roorkee.",
            user_prompt=prompt,
            prompt_version="v1",
        )

        result = self.gateway.complete_json(
            request,
            StartupEvaluationOutput,
        )

        evaluation = result.data

        raw_score = (
            evaluation.innovation_score
            + evaluation.market_score
            + evaluation.execution_score
        )

        evaluation.overall_score = round(
            (raw_score / 30) * 100
        )

        return evaluation

    def assess_startup(self, context) -> StartupAssessmentResult:
        """Run the full assessment pipeline: profile → rule score → AI evaluation."""
        profile = self.generate_profile(context)
        rule_based_score = self.evaluate_startup(context)
        ai_evaluation = self.evaluate_startup_with_ai(context)

        return StartupAssessmentResult(
            profile=profile,
            rule_based_score=rule_based_score,
            ai_evaluation=ai_evaluation,
        )