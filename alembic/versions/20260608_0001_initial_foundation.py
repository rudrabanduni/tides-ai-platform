"""initial foundation schema

Revision ID: 20260608_0001
Revises:
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = "20260608_0001"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "startup_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("stage", sa.String(length=128), nullable=True),
        sa.Column("current_status", sa.String(length=64), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("solution_summary", sa.Text(), nullable=True),
        sa.Column("business_model", sa.Text(), nullable=True),
        sa.Column("target_market", sa.Text(), nullable=True),
        sa.Column("traction_summary", sa.Text(), nullable=True),
        sa.Column("funding_status", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_startup_applications_created_by"), "startup_applications", ["created_by"], unique=False)
    op.create_index(op.f("ix_startup_applications_current_status"), "startup_applications", ["current_status"], unique=False)
    op.create_index(op.f("ix_startup_applications_sector"), "startup_applications", ["sector"], unique=False)
    op.create_index(op.f("ix_startup_applications_startup_name"), "startup_applications", ["startup_name"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "startup_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("old_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_startup_status_history_changed_by"), "startup_status_history", ["changed_by"], unique=False)
    op.create_index(op.f("ix_startup_status_history_startup_id"), "startup_status_history", ["startup_id"], unique=False)

    op.create_table(
        "startup_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("solution_summary", sa.Text(), nullable=True),
        sa.Column("target_market", sa.Text(), nullable=True),
        sa.Column("business_model", sa.Text(), nullable=True),
        sa.Column("technology_summary", sa.Text(), nullable=True),
        sa.Column("traction_summary", sa.Text(), nullable=True),
        sa.Column("funding_summary", sa.Text(), nullable=True),
        sa.Column("ip_summary", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("startup_id"),
    )
    op.create_index(op.f("ix_startup_profiles_startup_id"), "startup_profiles", ["startup_id"], unique=False)

    op.create_table(
        "startup_profile_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_profile_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["startup_profile_id"], ["startup_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("startup_profile_id", "version_number", name="uq_startup_profile_versions_number"),
    )
    op.create_index(
        op.f("ix_startup_profile_versions_startup_profile_id"),
        "startup_profile_versions",
        ["startup_profile_id"],
        unique=False,
    )

    op.create_table(
        "founders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("experience_summary", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("role_in_startup", sa.String(length=255), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_founders_startup_id"), "founders", ["startup_id"], unique=False)

    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("incorporation_status", sa.String(length=128), nullable=True),
        sa.Column("registration_number", sa.String(length=128), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("team_size", sa.Integer(), nullable=True),
        sa.Column("revenue_status", sa.Text(), nullable=True),
        sa.Column("ip_status", sa.Text(), nullable=True),
        sa.Column("market_category", sa.String(length=128), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("startup_id"),
    )
    op.create_index(op.f("ix_company_profiles_startup_id"), "company_profiles", ["startup_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("stored_filename", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(length=64), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_startup_id"), "documents", ["startup_id"], unique=False)
    op.create_index(op.f("ix_documents_uploaded_by"), "documents", ["uploaded_by"], unique=False)

    op.create_table(
        "document_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_sources_document_id"), "document_sources", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_sources_source_type"), "document_sources", ["source_type"], unique=False)
    op.create_index(op.f("ix_document_sources_startup_id"), "document_sources", ["startup_id"], unique=False)

    op.create_table(
        "recommendation_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("min_score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_rules_active"), "recommendation_rules", ["active"], unique=False)

    op.create_table(
        "evaluation_rubrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_evaluation_rubrics_name_version"),
    )
    op.create_index(op.f("ix_evaluation_rubrics_is_active"), "evaluation_rubrics", ["is_active"], unique=False)

    op.create_table(
        "evaluation_criteria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rubric_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["rubric_id"], ["evaluation_rubrics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_criteria_is_active"), "evaluation_criteria", ["is_active"], unique=False)
    op.create_index(op.f("ix_evaluation_criteria_rubric_id"), "evaluation_criteria", ["rubric_id"], unique=False)

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("rubric_id", sa.Uuid(), nullable=False),
        sa.Column("startup_profile_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.String(length=128), nullable=True),
        sa.Column("recommendation_rule_id", sa.Uuid(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recommendation_rule_id"], ["recommendation_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rubric_id"], ["evaluation_rubrics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["startup_profile_version_id"], ["startup_profile_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluations_recommendation_rule_id"), "evaluations", ["recommendation_rule_id"], unique=False)
    op.create_index(op.f("ix_evaluations_startup_id"), "evaluations", ["startup_id"], unique=False)
    op.create_index(op.f("ix_evaluations_startup_profile_version_id"), "evaluations", ["startup_profile_version_id"], unique=False)
    op.create_index(op.f("ix_evaluations_status"), "evaluations", ["status"], unique=False)

    op.create_table(
        "evaluation_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_id", sa.Uuid(), nullable=False),
        sa.Column("criteria_id", sa.Uuid(), nullable=False),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("reviewer_score", sa.Float(), nullable=True),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["criteria_id"], ["evaluation_criteria.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_id", "criteria_id", name="uq_evaluation_scores_criterion"),
    )
    op.create_index(op.f("ix_evaluation_scores_criteria_id"), "evaluation_scores", ["criteria_id"], unique=False)
    op.create_index(op.f("ix_evaluation_scores_evaluation_id"), "evaluation_scores", ["evaluation_id"], unique=False)

    op.create_table(
        "evaluation_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_score_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(length=500), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_name", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_score_id"], ["evaluation_scores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["document_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_evidence_evaluation_score_id"), "evaluation_evidence", ["evaluation_score_id"], unique=False)

    op.create_table(
        "reviewer_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviewer_comments_evaluation_id"), "reviewer_comments", ["evaluation_id"], unique=False)
    op.create_index(op.f("ix_reviewer_comments_reviewer_id"), "reviewer_comments", ["reviewer_id"], unique=False)
    op.create_index(op.f("ix_reviewer_comments_startup_id"), "reviewer_comments", ["startup_id"], unique=False)

    op.create_table(
        "committee_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_id", sa.Uuid(), nullable=False),
        sa.Column("committee_member_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["committee_member_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["startup_id"], ["startup_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_committee_notes_committee_member_id"), "committee_notes", ["committee_member_id"], unique=False)
    op.create_index(op.f("ix_committee_notes_evaluation_id"), "committee_notes", ["evaluation_id"], unique=False)
    op.create_index(op.f("ix_committee_notes_startup_id"), "committee_notes", ["startup_id"], unique=False)

    op.create_table(
        "score_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_score_id", sa.Uuid(), nullable=False),
        sa.Column("original_score", sa.Float(), nullable=False),
        sa.Column("overridden_score", sa.Float(), nullable=False),
        sa.Column("overridden_by", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_score_id"], ["evaluation_scores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["overridden_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_score_overrides_evaluation_score_id"), "score_overrides", ["evaluation_score_id"], unique=False)
    op.create_index(op.f("ix_score_overrides_overridden_by"), "score_overrides", ["overridden_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_score_overrides_overridden_by"), table_name="score_overrides")
    op.drop_index(op.f("ix_score_overrides_evaluation_score_id"), table_name="score_overrides")
    op.drop_table("score_overrides")
    op.drop_index(op.f("ix_committee_notes_startup_id"), table_name="committee_notes")
    op.drop_index(op.f("ix_committee_notes_evaluation_id"), table_name="committee_notes")
    op.drop_index(op.f("ix_committee_notes_committee_member_id"), table_name="committee_notes")
    op.drop_table("committee_notes")
    op.drop_index(op.f("ix_reviewer_comments_startup_id"), table_name="reviewer_comments")
    op.drop_index(op.f("ix_reviewer_comments_reviewer_id"), table_name="reviewer_comments")
    op.drop_index(op.f("ix_reviewer_comments_evaluation_id"), table_name="reviewer_comments")
    op.drop_table("reviewer_comments")
    op.drop_index(op.f("ix_evaluation_evidence_evaluation_score_id"), table_name="evaluation_evidence")
    op.drop_table("evaluation_evidence")
    op.drop_index(op.f("ix_evaluation_scores_evaluation_id"), table_name="evaluation_scores")
    op.drop_index(op.f("ix_evaluation_scores_criteria_id"), table_name="evaluation_scores")
    op.drop_table("evaluation_scores")
    op.drop_index(op.f("ix_evaluations_status"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_startup_profile_version_id"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_startup_id"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_recommendation_rule_id"), table_name="evaluations")
    op.drop_table("evaluations")
    op.drop_index(op.f("ix_evaluation_criteria_rubric_id"), table_name="evaluation_criteria")
    op.drop_index(op.f("ix_evaluation_criteria_is_active"), table_name="evaluation_criteria")
    op.drop_table("evaluation_criteria")
    op.drop_index(op.f("ix_evaluation_rubrics_is_active"), table_name="evaluation_rubrics")
    op.drop_table("evaluation_rubrics")
    op.drop_index(op.f("ix_recommendation_rules_active"), table_name="recommendation_rules")
    op.drop_table("recommendation_rules")
    op.drop_index(op.f("ix_document_sources_startup_id"), table_name="document_sources")
    op.drop_index(op.f("ix_document_sources_source_type"), table_name="document_sources")
    op.drop_index(op.f("ix_document_sources_document_id"), table_name="document_sources")
    op.drop_table("document_sources")
    op.drop_index(op.f("ix_documents_uploaded_by"), table_name="documents")
    op.drop_index(op.f("ix_documents_startup_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_company_profiles_startup_id"), table_name="company_profiles")
    op.drop_table("company_profiles")
    op.drop_index(op.f("ix_founders_startup_id"), table_name="founders")
    op.drop_table("founders")
    op.drop_index(op.f("ix_startup_profile_versions_startup_profile_id"), table_name="startup_profile_versions")
    op.drop_table("startup_profile_versions")
    op.drop_index(op.f("ix_startup_profiles_startup_id"), table_name="startup_profiles")
    op.drop_table("startup_profiles")
    op.drop_index(op.f("ix_startup_status_history_startup_id"), table_name="startup_status_history")
    op.drop_index(op.f("ix_startup_status_history_changed_by"), table_name="startup_status_history")
    op.drop_table("startup_status_history")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_startup_applications_startup_name"), table_name="startup_applications")
    op.drop_index(op.f("ix_startup_applications_sector"), table_name="startup_applications")
    op.drop_index(op.f("ix_startup_applications_current_status"), table_name="startup_applications")
    op.drop_index(op.f("ix_startup_applications_created_by"), table_name="startup_applications")
    op.drop_table("startup_applications")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
