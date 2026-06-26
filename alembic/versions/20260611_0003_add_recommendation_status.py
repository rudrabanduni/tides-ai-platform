"""Add recommendation_status column to ai_assessment_records

Revision ID: 20260611_0003
Revises: 20260610_0002
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa

revision = "20260611_0003"
down_revision = "20260610_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_assessment_records",
        sa.Column(
            "recommendation_status",
            sa.String(length=16),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_ai_assessment_records_recommendation_status"),
        "ai_assessment_records",
        ["recommendation_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ai_assessment_records_recommendation_status"),
        table_name="ai_assessment_records",
    )
    op.drop_column("ai_assessment_records", "recommendation_status")
