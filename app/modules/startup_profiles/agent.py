from app.services.ai import create_ai_gateway
from app.modules.startup_profiles.context import StartupProfileContextBuilder
from app.modules.startup_profiles.schemas import StartupProfileAgentOutput


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
        startup_name = "Unknown Startup"

        if context and hasattr(context, "startup"):
            startup_name = getattr(
                context.startup,
                "startup_name",
                startup_name,
            )

        return StartupProfileAgentOutput(
            executive_summary=f"{startup_name} is an early-stage startup.",
            business_model="To be determined",
            customer_segments="To be determined",
            market_opportunity="To be determined",
            strengths=[
                "Startup profile imported successfully"
            ],
            risks=[
                "Insufficient information available"
            ],
            missing_information=[
                "Business model details",
                "Customer validation",
                "Market sizing",
            ],
        )