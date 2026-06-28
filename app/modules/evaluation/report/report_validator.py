from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph


class ReportValidator:
    """Validator for DueDiligenceReport structure, referential integrity, and traceability mappings."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []
        report = graph.report
        if not report:
            return errors

        # List of required section fields (11 structured sections)
        required_sections = [
            "executive_summary", "investment_recommendation", "founder_assessment",
            "product_technology", "market_opportunity", "business_model",
            "competition", "financial_overview", "risks",
            "investment_thesis", "follow_up_questions"
        ]

        # 1. Report Completeness Check
        for field in required_sections:
            sec = getattr(report, field, None)
            if not sec:
                errors.append(f"Missing Section: Report is incomplete. Field '{field}' is missing.")
            else:
                # 2. Check confidence bounds [0.0, 1.0]
                if not (0.0 <= sec.confidence <= 1.0):
                    errors.append(
                        f"Invalid Confidence: Section '{sec.section_id}' has confidence "
                        f"{sec.confidence} which is outside [0.0, 1.0]."
                    )

                # 3. Check section traceability
                if sec.section_id not in report.traceability:
                    errors.append(f"Missing Traceability: Section '{sec.section_id}' has no traceability mapping.")

                # 4. Check referential integrity / no orphan references
                for nid in sec.supporting_nodes:
                    node = graph.get_node(nid)
                    if not node and graph.executive_assessment:
                        # Check in executive finding lists too
                        findings = graph.executive_assessment.key_observations + graph.executive_assessment.major_risks
                        found = any(f.finding_id == nid for f in findings)
                        if not found:
                            errors.append(
                                f"Broken Reference: Section '{sec.section_id}' references supporting "
                                f"node '{nid}' which does not exist in the graph."
                            )
                    elif not node:
                        errors.append(
                            f"Broken Reference: Section '{sec.section_id}' references supporting "
                            f"node '{nid}' which does not exist in the graph."
                        )

        # 5. Check no duplicate sections (by title or ID)
        section_ids = set()
        section_titles = set()
        for field in required_sections:
            sec = getattr(report, field, None)
            if sec:
                if sec.section_id in section_ids:
                    errors.append(f"Duplicate Section ID: '{sec.section_id}' is defined multiple times.")
                section_ids.add(sec.section_id)

                title_lower = sec.title.strip().lower()
                if title_lower in section_titles:
                    errors.append(f"Duplicate Section Title: '{sec.title}' is used multiple times.")
                section_titles.add(title_lower)

        # 6. Check appendices (referential check and uniqueness)
        appendix_ids = set()
        for app in report.appendices:
            if app.appendix_id in appendix_ids:
                errors.append(f"Duplicate Appendix ID: '{app.appendix_id}' is defined multiple times.")
            appendix_ids.add(app.appendix_id)

            if not app.title or not app.content:
                errors.append(f"Malformed Appendix: '{app.appendix_id}' is missing title or content.")

        return errors
