from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentContext(BaseModel):
    startup_profile: Dict[str, Any] = Field(default_factory=dict)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    previous_outputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

def build_context(
    startup_profile: Dict[str, Any],
    claims: List[Any],
    evidence: List[Any],
    previous_outputs: Dict[str, Any],
    relevant_fields: Optional[List[str]] = None
) -> AgentContext:
    """Decouples and prunes raw startup, claims, and evidence to prevent context bloat."""
    filtered_claims = []
    filtered_evidence = []
    
    # If relevant_fields is specified, filter claims by field key
    if relevant_fields:
        relevant_set = {f.lower() for f in relevant_fields}
        
        key_aliases = {
            "founder_names": ["founders", "founder_names", "team"],
            "leadership_experience": ["experience", "team", "resumes", "leadership_experience"],
            "commitment_level": ["commitment", "commitment_level"],
            "domain_expertise": ["domain_expertise", "expertise"],
            "description": ["product_deck", "technical_claims", "description"],
            "problem_solved": ["technical_claims", "problem_solved"],
            "solution_value_prop": ["defensibility", "technical_claims", "solution_value_prop"],
            "customers": ["validation", "customers"],
            "business_model": ["business_model"],
            "target_market": ["market_slides", "tam", "sam", "som", "target_market"],
            "market_size": ["tam", "sam", "som", "market_size"],
            "competitors": ["competition", "competitors"],
            "competition_analysis": ["competition", "defensibility", "competition_analysis"],
        }
        
        # Helper to get field key safely
        for claim in claims:
            field_key = ""
            if isinstance(claim, dict):
                field_key = claim.get("field_key") or claim.get("field", {}).get("field_key") or ""
            else:
                field = getattr(claim, "field", None)
                field_key = getattr(claim, "field_key", getattr(field, "field_key", "")) if claim else ""
                
            is_relevant = False
            if field_key:
                fk_l = field_key.lower()
                if fk_l in relevant_set:
                    is_relevant = True
                else:
                    aliases = key_aliases.get(fk_l, [])
                    if any(a in relevant_set for a in aliases):
                        is_relevant = True
                        
            if is_relevant:
                # convert claim to dict representation
                if isinstance(claim, dict):
                    filtered_claims.append(claim)
                elif hasattr(claim, "model_dump"):
                    filtered_claims.append(claim.model_dump())
                elif hasattr(claim, "__dict__"):
                    # SQLAlchemy objects might lose relationship objects on dict serialization
                    claim_dict = {k: v for k, v in claim.__dict__.items() if not k.startswith("_")}
                    claim_dict["field_key"] = field_key
                    filtered_claims.append(claim_dict)
                else:
                    filtered_claims.append(str(claim))
                    
        # Filter evidence matching target claim IDs
        claim_ids = {str(c.get("id") or c.get("uuid") or id(c)) for c in filtered_claims}
        for ev in evidence:
            claim_id = ""
            if isinstance(ev, dict):
                claim_id = ev.get("claim_id") or ""
            else:
                claim_id = getattr(ev, "claim_id", "")
                
            if claim_id and str(claim_id) in claim_ids:
                if isinstance(ev, dict):
                    filtered_evidence.append(ev)
                elif hasattr(ev, "model_dump"):
                    filtered_evidence.append(ev.model_dump())
                elif hasattr(ev, "__dict__"):
                    filtered_evidence.append({k: v for k, v in ev.__dict__.items() if not k.startswith("_")})
                else:
                    filtered_evidence.append(str(ev))
    else:
        # Include all if no fields filter is specified
        for claim in claims:
            if isinstance(claim, dict):
                filtered_claims.append(claim)
            elif hasattr(claim, "model_dump"):
                filtered_claims.append(claim.model_dump())
            elif hasattr(claim, "__dict__"):
                filtered_claims.append({k: v for k, v in claim.__dict__.items() if not k.startswith("_")})
        for ev in evidence:
            if isinstance(ev, dict):
                filtered_evidence.append(ev)
            elif hasattr(ev, "model_dump"):
                filtered_evidence.append(ev.model_dump())
            elif hasattr(ev, "__dict__"):
                filtered_evidence.append({k: v for k, v in ev.__dict__.items() if not k.startswith("_")})
                
    return AgentContext(
        startup_profile=startup_profile,
        claims=filtered_claims,
        evidence=filtered_evidence,
        previous_outputs=previous_outputs,
        metadata={}
    )
