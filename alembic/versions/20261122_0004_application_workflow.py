"""Application workflow: application_submissions and evaluation_runs.

Revision ID: 20261122_0004
Revises: 5c34068cd4e0
Create Date: 2026-11-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20261122_0004"
down_revision = "5c34068cd4e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("application_ref", sa.String(32), nullable=False),
        sa.Column("startup_id", sa.Uuid(), sa.ForeignKey("startup_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("industry", sa.String(255)),
        sa.Column("location", sa.String(255)),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_email", sa.String(320)),
        sa.Column("contact_phone", sa.String(64)),
        sa.Column("website", sa.String(500)),
        sa.Column("product_technology", sa.Text()),
        sa.Column("revenue_information", sa.Text()),
        sa.Column("financial_information", sa.Text()),
        sa.Column("funding_requirement", sa.Text()),
        sa.Column("incubation_support_requirement", sa.Text()),
        sa.Column("declarations", sa.JSON(), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("submitted_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_application_submissions_application_ref", "application_submissions", ["application_ref"], unique=True)
    op.create_index("ix_application_submissions_startup_id", "application_submissions", ["startup_id"], unique=True)
    op.create_index("ix_application_submissions_idempotency_key", "application_submissions", ["idempotency_key"], unique=True)
    op.create_index("ix_application_submissions_submitted_by", "application_submissions", ["submitted_by"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("startup_id", sa.Uuid(), sa.ForeignKey("startup_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.Uuid(), sa.ForeignKey("application_submissions.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("current_stage", sa.String(128)),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stages", sa.JSON(), nullable=False),
        sa.Column("pipeline_status", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("report_id", sa.String(64)),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("started_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_runs_startup_id", "evaluation_runs", ["startup_id"])
    op.create_index("ix_evaluation_runs_application_id", "evaluation_runs", ["application_id"])
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"])
    op.create_index("ix_evaluation_runs_started_by", "evaluation_runs", ["started_by"])
    op.create_index("ix_evaluation_runs_startup_status", "evaluation_runs", ["startup_id", "status"])


def downgrade() -> None:
    op.drop_table("evaluation_runs")
    op.drop_table("application_submissions")
