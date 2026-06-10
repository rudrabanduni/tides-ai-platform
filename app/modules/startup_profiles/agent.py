from app.services.ai import create_ai_gateway
from app.modules.startup_profiles.context import StartupProfileContextBuilder
from app.modules.startup_profiles.schemas import StartupProfileAgentOutput, StartupEvaluationScore


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
            startup_profile=startup_profile,
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