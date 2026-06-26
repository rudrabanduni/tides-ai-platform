import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple
from app.modules.evaluation.versioning.version_models import DeltaReport, DeltaItem, VersionSnapshot
from app.modules.evaluation.versioning import version_events


class DeltaEngine:
    """Orchestrates change detection between different startup evaluation versions."""

    @staticmethod
    def compare_versions(
        startup_id: str,
        from_version: int,
        to_version: int,
        from_snapshot: VersionSnapshot,
        to_snapshot: VersionSnapshot
    ) -> DeltaReport:
        """Loads two version snapshots and returns a complete DeltaReport of differences."""
        # Publish event
        version_events.publish_version_compared(startup_id, from_version, to_version)

        # Generate delta report
        report = DeltaEngine.generate_delta(from_snapshot, to_snapshot)
        report.from_version = from_version
        report.to_version = to_version

        # Publish generated event
        version_events.publish_delta_generated(report.delta_id, from_version, to_version)

        return report

    @staticmethod
    def generate_delta(from_snapshot: VersionSnapshot, to_snapshot: VersionSnapshot) -> DeltaReport:
        """Run all semantic checkers and compile the changes into a DeltaReport."""
        delta_id = f"DEL-{str(uuid.uuid4())[:8].upper()}"

        added = []
        removed = []
        modified = []

        # List of checkers to invoke
        checkers = [
            DeltaEngine.detect_founder_changes,
            DeltaEngine.detect_product_changes,
            DeltaEngine.detect_market_changes,
            DeltaEngine.detect_competition_changes,
            DeltaEngine.detect_financial_changes,
            DeltaEngine.detect_trl_changes,
            DeltaEngine.detect_risk_changes,
            DeltaEngine.detect_claim_changes,
            DeltaEngine.detect_observation_changes,
            DeltaEngine.detect_evidence_changes,
            DeltaEngine.detect_committee_changes,
            DeltaEngine.detect_workflow_changes,
            DeltaEngine.detect_portfolio_changes
        ]

        for check_func in checkers:
            items = check_func(from_snapshot, to_snapshot)
            for item in items:
                if item.change_type == "ADDED":
                    added.append(item)
                elif item.change_type == "REMOVED":
                    removed.append(item)
                else:
                    modified.append(item)

        # Collect changed fields
        changed_fields = sorted(list(set(item.field for item in (added + removed + modified))))

        # Summary text
        summary = (
            f"Detected {len(added)} additions, {len(removed)} removals, and {len(modified)} modifications "
            f"across {len(changed_fields)} distinct elements between snapshots."
        )

        # Confidence averaging
        all_items = added + removed + modified
        overall_confidence = (
            sum(item.confidence for item in all_items) / len(all_items)
            if all_items else 1.0
        )

        return DeltaReport(
            delta_id=delta_id,
            from_version=0,  # will be set by caller
            to_version=0,    # will be set by caller
            summary=summary,
            changed_fields=changed_fields,
            added_items=added,
            removed_items=removed,
            modified_items=modified,
            overall_change_confidence=round(overall_confidence, 4),
            generated_at=datetime.utcnow()
        )

    # --- Generic Comparer Helper ---

    @staticmethod
    def _compare_list_entities(
        from_items: List[Dict[str, Any]],
        to_items: List[Dict[str, Any]],
        key_field: str,
        name_field: str,
        val_fields: List[str],
        category: str,
        default_confidence: float = 0.95
    ) -> List[DeltaItem]:
        deltas = []
        from_map = {item.get(key_field): item for item in from_items if item.get(key_field)}
        to_map = {item.get(key_field): item for item in to_items if item.get(key_field)}

        # Additions
        for key, item in to_map.items():
            if key not in from_map:
                name = item.get(name_field) or key
                deltas.append(DeltaItem(
                    category=category,
                    field=name,
                    previous_value=None,
                    current_value=item,
                    change_type="ADDED",
                    confidence=default_confidence,
                    reasoning=f"New {category.lower()} element '{name}' was added to the snapshot."
                ))

        # Removals
        for key, item in from_map.items():
            if key not in to_map:
                name = item.get(name_field) or key
                deltas.append(DeltaItem(
                    category=category,
                    field=name,
                    previous_value=item,
                    current_value=None,
                    change_type="REMOVED",
                    confidence=default_confidence,
                    reasoning=f"{category} element '{name}' was removed from the snapshot."
                ))

        # Modifications
        for key, to_item in to_map.items():
            if key in from_map:
                from_item = from_map[key]
                changed = []
                for f in val_fields:
                    if from_item.get(f) != to_item.get(f):
                        changed.append(f)
                if changed:
                    name = to_item.get(name_field) or key
                    # Calculate mean confidence of item or fallback
                    conf = to_item.get("confidence", default_confidence)
                    deltas.append(DeltaItem(
                        category=category,
                        field=name,
                        previous_value={f: from_item.get(f) for f in val_fields},
                        current_value={f: to_item.get(f) for f in val_fields},
                        change_type="MODIFIED",
                        confidence=conf,
                        reasoning=f"{category} element '{name}' was modified. Fields changed: {', '.join(changed)}."
                    ))

        return deltas

    # --- Domain Checkers ---

    @staticmethod
    def detect_founder_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect modifications under Founder/Team category."""
        # Check observations with domain == founder/team
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") in ("founder", "team")]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") in ("founder", "team")]

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="Founder"
        )

    @staticmethod
    def detect_product_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect product changes."""
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "product"]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "product"]

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="Product"
        )

    @staticmethod
    def detect_market_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect market changes."""
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "market"]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "market"]

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="Market"
        )

    @staticmethod
    def detect_competition_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect competition changes."""
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "competition"]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "competition"]

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="Competition"
        )

    @staticmethod
    def detect_financial_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect financial changes."""
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "financial"]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "financial"]

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="Financial"
        )

    @staticmethod
    def detect_trl_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Detect technology readiness level changes."""
        from_obs = [o for o in from_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "trl"]
        to_obs = [o for o in to_snap.observation_graph.get("observations", {}).values() if o.get("domain") == "trl"]

        # Also compare TRL scores in investment assessments
        trl_deltas = DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence"],
            category="TRL"
        )

        from_inv = from_snap.investment_report or {}
        to_inv = to_snap.investment_report or {}
        from_trl_score = from_inv.get("technology_score")
        to_trl_score = to_inv.get("technology_score")

        if from_trl_score != to_trl_score and from_trl_score is not None and to_trl_score is not None:
            trl_deltas.append(DeltaItem(
                category="TRL",
                field="technology_score",
                previous_value=from_trl_score,
                current_value=to_trl_score,
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"TRL technology score progressed from {from_trl_score} to {to_trl_score}."
            ))

        return trl_deltas

    @staticmethod
    def detect_risk_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare active risks category."""
        return DeltaEngine._compare_list_entities(
            from_snap.risks, to_snap.risks,
            key_field="risk_id",
            name_field="description",
            val_fields=["description", "confidence", "category"],
            category="Risk"
        )

    @staticmethod
    def detect_claim_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare all profile claims."""
        # Convert field_id (UUID) to string to compare
        from_claims = [{**c, "id_str": str(c.get("id") or c.get("field_id"))} for c in from_snap.claims]
        to_claims = [{**c, "id_str": str(c.get("id") or c.get("field_id"))} for c in to_snap.claims]

        return DeltaEngine._compare_list_entities(
            from_claims, to_claims,
            key_field="id_str",
            name_field="id_str",
            val_fields=["value_string", "value_number", "value_boolean", "confidence_score", "is_preferred"],
            category="Claims"
        )

    @staticmethod
    def detect_observation_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare observations lists."""
        from_obs = list(from_snap.observation_graph.get("observations", {}).values())
        to_obs = list(to_snap.observation_graph.get("observations", {}).values())

        return DeltaEngine._compare_list_entities(
            from_obs, to_obs,
            key_field="observation_id",
            name_field="observation",
            val_fields=["observation", "confidence", "domain"],
            category="Observation Graph"
        )

    @staticmethod
    def detect_evidence_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare evidence snippets list."""
        return DeltaEngine._compare_list_entities(
            from_snap.evidence, to_snap.evidence,
            key_field="evidence_id",
            name_field="evidence_snippet",
            val_fields=["evidence_snippet", "confidence_score"],
            category="Evidence"
        )

    @staticmethod
    def detect_committee_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare committee reports/recommendations."""
        deltas = []
        from_comm = from_snap.committee_report or {}
        to_comm = to_snap.committee_report or {}

        from_rec = from_comm.get("recommendation") or from_comm.get("recommendations", {}).get("recommendation")
        to_rec = to_comm.get("recommendation") or to_comm.get("recommendations", {}).get("recommendation")
 
        if from_rec != to_rec and from_rec is not None and to_rec is not None:
            deltas.append(DeltaItem(
                category="Committee Decision",
                field="recommendation",
                previous_value=str(from_rec),
                current_value=str(to_rec),
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"Committee verdict recommendation changed from '{from_rec}' to '{to_rec}'."
            ))
 
        from_conf = from_comm.get("decision_confidence") or from_comm.get("decision", {}).get("overall_confidence")
        to_conf = to_comm.get("decision_confidence") or to_comm.get("decision", {}).get("overall_confidence")
        if from_conf != to_conf and from_conf is not None and to_conf is not None:
            deltas.append(DeltaItem(
                category="Committee Decision",
                field="overall_confidence",
                previous_value=from_conf,
                current_value=to_conf,
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"Committee overall confidence rating shifted from {from_conf} to {to_conf}."
            ))

        return deltas

    @staticmethod
    def detect_workflow_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare workflow states."""
        deltas = []
        from_wf = from_snap.workflow_state or {}
        to_wf = to_snap.workflow_state or {}

        from_state = from_wf.get("current_state")
        to_state = to_wf.get("current_state")

        if from_state != to_state and from_state is not None and to_state is not None:
            deltas.append(DeltaItem(
                category="Workflow",
                field="current_state",
                previous_value=from_state,
                current_value=to_state,
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"Startup application stage transitioned from '{from_state}' to '{to_state}'."
            ))

        return deltas

    @staticmethod
    def detect_portfolio_changes(from_snap: VersionSnapshot, to_snap: VersionSnapshot) -> List[DeltaItem]:
        """Compare portfolio positions/scores."""
        deltas = []
        from_port = from_snap.portfolio_snapshot or {}
        to_port = to_snap.portfolio_snapshot or {}

        from_rank = from_port.get("rank")
        to_rank = to_port.get("rank")

        if from_rank != to_rank and from_rank is not None and to_rank is not None:
            deltas.append(DeltaItem(
                category="Portfolio",
                field="rank",
                previous_value=from_rank,
                current_value=to_rank,
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"Portfolio rank position changed from {from_rank} to {to_rank}."
            ))

        from_score = from_port.get("investment_score")
        to_score = to_port.get("investment_score")
        if from_score != to_score and from_score is not None and to_score is not None:
            deltas.append(DeltaItem(
                category="Portfolio",
                field="investment_score",
                previous_value=from_score,
                current_value=to_score,
                change_type="MODIFIED",
                confidence=1.0,
                reasoning=f"Portfolio evaluation score shifted from {from_score} to {to_score}."
            ))

        return deltas
