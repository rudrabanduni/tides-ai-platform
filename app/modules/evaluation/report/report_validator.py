import re
from typing import Any, Dict, List
from app.modules.evaluation.graph.graph_models import ObservationGraph


class ReportValidator:
    """Validator for DueDiligenceReport structure, referential integrity, and traceability mappings."""

    FORBIDDEN_ENERGY_TERMS = [
        "electrochemical",
        "mineral pricing",
        "cell scale-up",
        "pilot line yields",
        "circular raw material",
        "circular precursor",
        "precursor chemical",
        "battery testing",
        "continuous synthesis",
        "CleanPower",
        "energy storage and advanced materials",
        "disodium terephthalate",
        "solvolytic conversion",
        "PET solvolysis",
    ]

    MEDTECH_CONTEXT_TERMS = [
        "lung",
        "respiratory",
        "screening",
        "diagnostic",
        "medical",
        "clinical",
        "impedance",
        "auscultation",
    ]

    FORBIDDEN_MEDTECH_TERMS = [
        "copd",
        "auscultation",
        "pulmonary",
        "lung screening",
        "lung pathology",
        "pneumonia",
        "stethoscope",
        "stethaim",
    ]

    REQUIRED_SECTIONS = [
        "executive_summary", "investment_recommendation", "founder_assessment",
        "product_technology", "market_opportunity", "business_model",
        "competition", "financial_overview", "risks",
        "investment_thesis", "follow_up_questions",
    ]

    KNOWN_PORTFOLIO_ENTITIES = [
        "cleanpower",
        "cleanpower systems",
        "stethaim",
        "petrevolt",
    ]

    MISSING_PLACEHOLDERS = {
        "", "none", "null", "missing", "missing from application",
        "none disclosed (conditional field)", "optional field not provided",
        "not disclosed", "not provided", "not mentioned", "unknown",
    }

    @staticmethod
    def _issue(code: str, severity: str, message: str, section: str | None = None) -> Dict[str, Any]:
        return {
            "code": code,
            "severity": severity,
            "section": section,
            "message": message,
        }

    @classmethod
    def _extract_sector(cls, graph: ObservationGraph) -> str:
        sector = ""
        profile = getattr(graph, "startup_profile", None)
        if profile and isinstance(profile, dict):
            sector = str(profile.get("sector", ""))
        elif profile:
            sector = str(getattr(profile, "sector", ""))

        if not sector:
            for c in graph.claims.values():
                if ":" in c.claim_text:
                    k, _, v = c.claim_text.partition(":")
                    if k.strip().lower() in ("sector", "cm_03_sector"):
                        sector = v.strip()
                        break
        return sector

    @classmethod
    def _get_ps09_status(cls, graph: ObservationGraph) -> str | None:
        dom_source = getattr(graph, "domain_reports", None) or getattr(graph, "domain_assessments", None) or {}
        for rep in dom_source.values():
            crit_map = rep.get("criteria_evaluations") if isinstance(rep, dict) else getattr(rep, "criteria_evaluations", None)
            if crit_map and "PS-09" in crit_map:
                item = crit_map["PS-09"]
                v_raw = item.get("verification_status") if isinstance(item, dict) else getattr(item, "verification_status", None)
                return getattr(v_raw, "value", str(v_raw)) if v_raw is not None else None
        return None

    @classmethod
    def validate_cross_contamination(cls, graph: ObservationGraph) -> List[str]:
        """Validates that report content belongs strictly to the target venture with no cross-startup contamination."""
        errors: List[str] = []
        report = graph.report
        if not report:
            return errors

        sector = cls._extract_sector(graph)
        sector_lower = sector.lower()
        startup_lower = (graph.startup_name or "").lower()

        is_medtech = "med" in sector_lower or "health" in sector_lower or "bio" in sector_lower or "stethaim" in startup_lower
        is_cleantech = (
            "clean" in sector_lower
            or "energy" in sector_lower
            or "storage" in sector_lower
            or "battery" in sector_lower
            or "climate" in sector_lower
            or "petrevolt" in startup_lower
        ) and not is_medtech
        is_other_sector = bool(sector_lower) and not is_medtech and not is_cleantech

        # 1. Check forbidden cross-startup energy/battery terms in MedTech or unrelated sectors
        if is_medtech or is_other_sector:
            for field in cls.REQUIRED_SECTIONS:
                sec = getattr(report, field, None)
                if not sec or not sec.content:
                    continue
                content_lower = sec.content.lower()
                for term in cls.FORBIDDEN_ENERGY_TERMS:
                    if term.lower() in content_lower:
                        errors.append(
                            f"Cross-Contamination: Section '{field}' contains forbidden energy/battery term "
                            f"'{term}' for {sector or 'MedTech'} venture '{graph.startup_name}'."
                        )

        # 1b. Check forbidden MedTech terms in CleanTech or unrelated sectors
        if is_cleantech or is_other_sector:
            for field in cls.REQUIRED_SECTIONS:
                sec = getattr(report, field, None)
                if not sec or not sec.content:
                    continue
                content_lower = sec.content.lower()
                for term in cls.FORBIDDEN_MEDTECH_TERMS:
                    if term.lower() in content_lower:
                        errors.append(
                            f"Cross-Contamination: Section '{field}' contains forbidden MedTech/pulmonary term "
                            f"'{term}' for {sector or 'CleanTech'} venture '{graph.startup_name}'."
                        )

        # 2. Check foreign startup entity contamination
        for field in cls.REQUIRED_SECTIONS:
            sec = getattr(report, field, None)
            if not sec or not sec.content:
                continue
            content_lower = sec.content.lower()
            for foreign in cls.KNOWN_PORTFOLIO_ENTITIES:
                if foreign in content_lower and foreign not in startup_lower:
                    errors.append(
                        f"Foreign Startup Contamination: Section '{field}' refers to foreign startup "
                        f"'{foreign}' instead of '{graph.startup_name}'."
                    )

        # 3. Check positive MedTech context presence
        if is_medtech:
            exec_sec = getattr(report, "executive_summary", None)
            prod_sec = getattr(report, "product_technology", None)
            combined_text = (getattr(exec_sec, "content", "") + " " + getattr(prod_sec, "content", "")).lower()
            if not any(term in combined_text for term in cls.MEDTECH_CONTEXT_TERMS):
                errors.append(
                    f"Context Error: MedTech report for '{graph.startup_name}' lacks core clinical/product domain terminology."
                )

        # 4. Check supervisory rationale vs recommendation consistency
        sr = getattr(graph, "supervisory_review", None)
        if sr:
            if isinstance(sr, dict):
                rationale = (sr.get("recommendation_rationale", "") or "").lower()
                rec = (sr.get("overall_recommendation", "") or "").upper()
            else:
                rationale = (getattr(sr, "recommendation_rationale", "") or "").lower()
                rec = (getattr(sr, "overall_recommendation", "") or "").upper()
            if ("defer is not warranted" in rationale or "milestone-gated conditions" in rationale) and rec == "DEFER":
                errors.append(
                    "Recommendation Inconsistency: Supervisory review rationale states full DEFER is not warranted and conditions are proportionate, but overall_recommendation is DEFER."
                )

        # 5. Check multi-body recommendation reconciliation
        inv_sec = getattr(report, "investment_recommendation", None)
        if inv_sec and inv_sec.content:
            content = inv_sec.content
            if getattr(graph, "supervisory_review", None) and getattr(graph, "committee_decision", None):
                if not ("Governance" in content or "Reconciliation" in content or "Operational Policy" in content):
                    errors.append(
                        "Recommendation Governance Error: Investment recommendation lacks multi-body governance reconciliation."
                    )

        # 6. Check unsupported cap table claims
        for field in cls.REQUIRED_SECTIONS:
            sec = getattr(report, field, None)
            if not sec or not sec.content:
                continue
            if re.search(r"\bclean\s+cap\s+table\b", sec.content, re.IGNORECASE):
                errors.append(
                    f"Unsupported Cap Table Claim: Section '{field}' asserts a 'clean cap table' without verification or cap table disclosure."
                )

        # 7. Check unsupported / unverified TRL claims
        ps09_status = cls._get_ps09_status(graph)
        ps09_verified = ps09_status == "VERIFIED_DOCUMENTED"
        for field in cls.REQUIRED_SECTIONS:
            sec = getattr(report, field, None)
            if not sec or not sec.content:
                continue
            if not ps09_verified and re.search(r"\b(verified|certified|proven)\s+trl\s*\d+(?:\.\d+)?\b", sec.content, re.IGNORECASE):
                errors.append(
                    f"Unsupported TRL Claim: Section '{field}' asserts verified/certified TRL, but Criterion PS-09 is self-reported or unverified."
                )

        # 8. Check conflicting recommendation narratives
        sr_rec = ((sr.get("overall_recommendation") if isinstance(sr, dict) else getattr(sr, "overall_recommendation", None)) or "").upper() if sr else ""
        if sr_rec == "CONDITIONAL":
            for field in ["executive_summary", "investment_recommendation", "investment_thesis"]:
                sec = getattr(report, field, None)
                if sec and sec.content:
                    c_upper = sec.content.upper()
                    if "OVERALL RECOMMENDATION: DEFER" in c_upper or "RECOMMENDATION: DEFER" in c_upper:
                        errors.append(
                            f"Conflicting Recommendation Narrative: Section '{field}' asserts DEFER while supervisory review is CONDITIONAL."
                        )

        return errors

    @classmethod
    def validate_structured(cls, graph: ObservationGraph, strict_canonical: bool = False) -> Dict[str, Any]:
        """Performs machine-readable multi-severity validation across structure, governance, identity, and factuality."""
        issues: List[Dict[str, Any]] = []
        report = graph.report
        if not report:
            return {
                "valid": True,
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "errors": [],
                "warnings": [],
                "informational": [],
                "issues": [],
            }

        # 1. Identity & Hash Checks
        if not getattr(report, "report_id", None):
            issues.append(cls._issue("MISSING_REPORT_ID", "ERROR", "Missing Report ID: DueDiligenceReport.report_id is empty."))

        report_meta = getattr(report, "metadata", None) if isinstance(getattr(report, "metadata", None), dict) else {}
        report_startup_name = getattr(report, "startup_name", None) or report_meta.get("startup_name")
        if report_startup_name and graph.startup_name and str(report_startup_name).strip().lower() != str(graph.startup_name).strip().lower():
            issues.append(
                cls._issue(
                    "STARTUP_NAME_MISMATCH",
                    "ERROR",
                    f"Identity Mismatch: Report targets '{report_startup_name}' while graph targets '{graph.startup_name}'.",
                )
            )
        report_startup_id = report_meta.get("startup_id")
        if report_startup_id and graph.startup_id and str(report_startup_id) != str(graph.startup_id):
            issues.append(
                cls._issue(
                    "STARTUP_ID_MISMATCH",
                    "ERROR",
                    f"Identity Mismatch: Report startup_id '{report_startup_id}' does not match graph.startup_id '{graph.startup_id}'.",
                )
            )

        if not getattr(graph, "graph_hash", None):
            issues.append(cls._issue("MISSING_GRAPH_HASH", "WARNING", "Missing Graph Hash: ObservationGraph.graph_hash is unset."))
        elif report_meta.get("graph_hash") and report_meta.get("graph_hash") != graph.graph_hash:
            issues.append(
                cls._issue(
                    "GRAPH_HASH_MISMATCH",
                    "ERROR",
                    f"Graph Hash Mismatch: Report metadata graph_hash '{report_meta.get('graph_hash')}' mismatches '{graph.graph_hash}'.",
                )
            )

        # 2. Report Completeness, Confidence, Traceability & Reference Integrity
        section_ids = set()
        section_titles = set()
        for field in cls.REQUIRED_SECTIONS:
            sec = getattr(report, field, None)
            if not sec:
                issues.append(cls._issue("MISSING_SECTION", "ERROR", f"Missing Section: Report is incomplete. Field '{field}' is missing.", section=field))
                continue

            if sec.section_id in section_ids:
                issues.append(cls._issue("DUPLICATE_SECTION_ID", "ERROR", f"Duplicate Section ID: '{sec.section_id}' is defined multiple times.", section=field))
            section_ids.add(sec.section_id)

            title_lower = sec.title.strip().lower()
            if title_lower in section_titles:
                issues.append(cls._issue("DUPLICATE_SECTION_TITLE", "ERROR", f"Duplicate Section Title: '{sec.title}' is used multiple times.", section=field))
            section_titles.add(title_lower)

            if not sec.content or len(sec.content.strip()) < 50:
                issues.append(
                    cls._issue(
                        "EMPTY_SECTION",
                        "ERROR",
                        f"Empty Section: Mandatory section '{field}' is empty or has insufficient content ({len(sec.content.strip()) if sec.content else 0} chars).",
                        section=field,
                    )
                )
            else:
                if not (0.0 <= sec.confidence <= 1.0):
                    issues.append(
                        cls._issue(
                            "INVALID_CONFIDENCE",
                            "ERROR",
                            f"Invalid Confidence: Section '{sec.section_id}' has confidence {sec.confidence} which is outside [0.0, 1.0].",
                            section=field,
                        )
                    )

                if sec.section_id not in report.traceability:
                    issues.append(
                        cls._issue(
                            "MISSING_TRACEABILITY",
                            "ERROR",
                            f"Missing Traceability: Section '{sec.section_id}' has no traceability mapping.",
                            section=field,
                        )
                    )

                for nid in sec.supporting_nodes:
                    node = graph.get_node(nid)
                    if not node and graph.executive_assessment:
                        findings = graph.executive_assessment.key_observations + graph.executive_assessment.major_risks
                        if not any(f.finding_id == nid for f in findings):
                            issues.append(
                                cls._issue(
                                    "BROKEN_REFERENCE",
                                    "ERROR",
                                    f"Broken Reference: Section '{sec.section_id}' references supporting node '{nid}' which does not exist in the graph.",
                                    section=field,
                                )
                            )
                    elif not node:
                        issues.append(
                            cls._issue(
                                "BROKEN_REFERENCE",
                                "ERROR",
                                f"Broken Reference: Section '{sec.section_id}' references supporting node '{nid}' which does not exist in the graph.",
                                section=field,
                            )
                        )

        # 3. Check appendices
        appendix_ids = set()
        for app in report.appendices:
            if app.appendix_id in appendix_ids:
                issues.append(cls._issue("DUPLICATE_APPENDIX", "ERROR", f"Duplicate Appendix ID: '{app.appendix_id}' is defined multiple times."))
            appendix_ids.add(app.appendix_id)
            if not app.title or not app.content:
                issues.append(cls._issue("MALFORMED_APPENDIX", "ERROR", f"Malformed Appendix: '{app.appendix_id}' is missing title or content."))
            if app.appendix_id == "appendix_d" and ("mock" in app.content.lower() or "simulated" in app.content.lower()):
                if "[mock]" not in app.content.lower() and "[simulated" not in app.content.lower():
                    issues.append(cls._issue("UNLABELED_MOCK_EVIDENCE", "WARNING", "Appendix D contains simulated research items without explicit [MOCK]/[SIMULATED] markers."))

        # 4. Cross-startup contamination & narrative governance checks
        for cc_err in cls.validate_cross_contamination(graph):
            issues.append(cls._issue("CROSS_CONTAMINATION_OR_GOVERNANCE", "ERROR", cc_err))

        # 5. Stale final_review check
        fr = getattr(graph, "final_review", None)
        sr = getattr(graph, "supervisory_review", None)
        if fr and sr:
            fr_rec = (getattr(fr, "overall_recommendation", None) or (fr.get("overall_recommendation") if isinstance(fr, dict) else None) or "").upper()
            sr_rec = (getattr(sr, "overall_recommendation", None) or (sr.get("overall_recommendation") if isinstance(sr, dict) else None) or "").upper()
            if fr_rec and sr_rec and fr_rec != sr_rec:
                issues.append(
                    cls._issue(
                        "STALE_FINAL_REVIEW",
                        "ERROR",
                        f"Stale Final Review: final_review overall_recommendation ('{fr_rec}') does not match supervisory review ('{sr_rec}').",
                    )
                )

        # 6. Domain assessment counts & criterion factuality checks
        dom_source = getattr(graph, "domain_reports", None) or getattr(graph, "domain_assessments", None) or {}
        dom_count = len(dom_source)
        if dom_count > 0:
            meta_count = report_meta.get("domain_assessments_count")
            if meta_count is not None and meta_count != dom_count:
                issues.append(
                    cls._issue(
                        "ASSESSMENT_COUNT_MISMATCH",
                        "ERROR",
                        f"Assessment Count Mismatch: Metadata reports domain_assessments_count={meta_count}, expected {dom_count}.",
                    )
                )
            for app in report.appendices:
                if app.appendix_id == "appendix_c" and app.content:
                    m = re.search(r"Expert Assessments:\s*(\d+)", app.content)
                    if m and int(m.group(1)) != dom_count:
                        issues.append(
                            cls._issue(
                                "ASSESSMENT_COUNT_MISMATCH",
                                "ERROR",
                                f"Assessment Count Mismatch: Appendix C reports Expert Assessments: {int(m.group(1))}, expected {dom_count}.",
                            )
                        )

            total_criteria = 0
            for dkey, rep in dom_source.items():
                crit_map = rep.get("criteria_evaluations") if isinstance(rep, dict) else getattr(rep, "criteria_evaluations", None)
                if not isinstance(crit_map, dict):
                    continue
                total_criteria += len(crit_map)
                for cid, ce in crit_map.items():
                    if isinstance(ce, dict):
                        v_raw = ce.get("verification_status")
                        v_status = getattr(v_raw, "value", str(v_raw)) if v_raw is not None else ""
                        ev_ids = ce.get("evidence_ids") or []
                        extracted = ce.get("extracted_startup_response")
                    else:
                        v_raw = getattr(ce, "verification_status", None)
                        v_status = getattr(v_raw, "value", str(v_raw)) if v_raw is not None else ""
                        ev_ids = getattr(ce, "evidence_ids", None) or []
                        extracted = getattr(ce, "extracted_startup_response", None)

                    extracted_clean = str(extracted).strip().lower() if extracted is not None else ""
                    if v_status == "VERIFIED_DOCUMENTED" and not ev_ids:
                        if extracted is None or extracted_clean in cls.MISSING_PLACEHOLDERS:
                            issues.append(
                                cls._issue(
                                    "PHANTOM_VERIFIED_CRITERION",
                                    "ERROR",
                                    f"Missing-Evidence Violation: Criterion '{cid}' in domain '{dkey}' is marked VERIFIED_DOCUMENTED with empty evidence and missing value.",
                                )
                            )
                        else:
                            issues.append(
                                cls._issue(
                                    "UNLINKED_VERIFIED_CRITERION",
                                    "WARNING",
                                    f"Unlinked Verification: Criterion '{cid}' in domain '{dkey}' is VERIFIED_DOCUMENTED without evidence_ids.",
                                )
                            )

            canonical_keys = {"problem_solution", "market_opportunity", "founder_team", "commercialisation", "innovation_impact", "financials_support"}
            if set(dom_source.keys()) & canonical_keys and total_criteria < 81:
                severity = "ERROR" if strict_canonical else "WARNING"
                issues.append(
                    cls._issue(
                        "INCOMPLETE_DOMAIN_CRITERIA",
                        severity,
                        f"Incomplete Canonical Matrix: Expected 81 domain criteria across 6 domains, found {total_criteria}.",
                    )
                )

            # Strict 87-criterion validation checks
            if strict_canonical:
                # 6 domain summaries present and non-empty
                for ck in canonical_keys:
                    rep_obj = dom_source.get(ck)
                    if not rep_obj:
                        issues.append(cls._issue("MISSING_CANONICAL_DOMAIN", "ERROR", f"Missing canonical domain report: '{ck}'."))
                    else:
                        summary_val = getattr(rep_obj, "summary", None) or (rep_obj.get("summary") if isinstance(rep_obj, dict) else "")
                        if not summary_val or len(str(summary_val).strip()) < 15:
                            issues.append(cls._issue("MISSING_DOMAIN_SUMMARY", "ERROR", f"Domain '{ck}' summary is empty or missing."))

                # All 6 cover criteria accounted for (CM-01..06)
                claim_keys = set()
                for c in graph.claims.values():
                    t = getattr(c, "claim_text", "")
                    if ":" in t:
                        claim_keys.add(t.split(":", 1)[0].strip().lower())
                cover_map = {
                    "CM-01": ("cm_01", "company_name", "startup_name"),
                    "CM-02": ("cm_02", "tagline", "value_prop"),
                    "CM-03": ("cm_03", "sector"),
                    "CM-04": ("cm_04", "stage"),
                    "CM-05": ("cm_05", "geography", "location"),
                    "CM-06": ("cm_06", "application_date", "submission_date"),
                }
                for cm_id, matchers in cover_map.items():
                    found_cm = any(any(m in ck for m in matchers) for ck in claim_keys)
                    if not found_cm and graph.startup_profile:
                        for m in matchers:
                            if getattr(graph.startup_profile, m, None) or (isinstance(graph.startup_profile, dict) and graph.startup_profile.get(m)):
                                found_cm = True
                                break
                    if not found_cm and graph.startup_name and cm_id == "CM-01":
                        found_cm = True
                    if not found_cm:
                        issues.append(cls._issue("MISSING_COVER_CRITERIA", "ERROR", f"Missing cover metadata criterion: '{cm_id}'."))

                # Referential integrity: criteria evidence IDs must resolve to nodes in graph.evidence
                for dkey, rep in dom_source.items():
                    crit_map = rep.get("criteria_evaluations") if isinstance(rep, dict) else getattr(rep, "criteria_evaluations", None)
                    if isinstance(crit_map, dict):
                        for cid, ce in crit_map.items():
                            ev_ids = ce.get("evidence_ids") if isinstance(ce, dict) else getattr(ce, "evidence_ids", [])
                            for eid in (ev_ids or []):
                                if eid and eid not in graph.evidence:
                                    issues.append(cls._issue("UNRESOLVED_EVIDENCE_REFERENCE", "ERROR", f"Criterion '{cid}' references evidence '{eid}' not present in graph.evidence."))

        # 7. Evaluation mode informational notice
        eval_mode = getattr(graph, "evaluation_mode", None) or report_meta.get("evaluation_mode")
        if eval_mode:
            issues.append(cls._issue("EVALUATION_MODE_INFO", "INFORMATIONAL", f"Evaluation mode recorded as '{eval_mode}'."))

        errors = [i for i in issues if i["severity"] == "ERROR"]
        warnings = [i for i in issues if i["severity"] == "WARNING"]
        informational = [i for i in issues if i["severity"] == "INFORMATIONAL"]
        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(informational),
            "errors": errors,
            "warnings": warnings,
            "informational": informational,
            "issues": issues,
        }

    @classmethod
    def validate(cls, graph: ObservationGraph) -> List[str]:
        """Returns ERROR-level validation messages for backwards compatibility."""
        structured = cls.validate_structured(graph)
        return [issue["message"] for issue in structured["errors"]]

    @classmethod
    def validate_canonical_87_report(cls, graph: ObservationGraph) -> Dict[str, Any]:
        """Strictly validates complete 87-criterion report integrity, rejecting incomplete evaluations."""
        return cls.validate_structured(graph, strict_canonical=True)
