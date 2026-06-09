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
        return StartupProfileAgentOutput(
            executive_summary="Profile generation not implemented yet.",
            business_model="Unknown",
            customer_segments="Unknown",
            market_opportunity="Unknown",
            strengths=[],
            risks=[],
            missing_information=[],
        )