from pydantic import BaseModel, Field

class ExpertMetadata(BaseModel):
    expert_name: str = Field(..., description="Unique code identifier of the expert (e.g. 'FounderExpert')")
    domain: str = Field(..., description="Focus domain key (e.g. 'founder')")
    version: str = Field(..., description="Agent semantic version")
    description: str = Field(..., description="Qualitative evaluation description")
    supported_claims: list[str] = Field(default_factory=list, description="Claim field keys analyzed by this expert")
    supported_evidence_types: list[str] = Field(default_factory=list, description="Evidence categories accepted")
    prompt_name: str = Field(..., description="Template prompt file directory name")
    prompt_version: str = Field(..., description="Minimum compatible prompt version")
    agent_version: str = Field(..., description="Underlying python class version")
    enabled: bool = Field(default=True, description="Registry execution flag")
    tags: list[str] = Field(default_factory=list, description="Descriptive classification tags")
