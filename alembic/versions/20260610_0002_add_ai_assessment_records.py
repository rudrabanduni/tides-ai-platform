"""Add ai_assessment_records table

Revision ID: 20260610_0002
Revises: 20260608_0001
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "20260610_0002"
down_revision = "20260608_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_assessment_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("startup_id", sa.Uuid(), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("innovation_score", sa.Integer(), nullable=False),
        sa.Column("market_score", sa.Integer(), nullable=False),
        sa.Column("execution_score", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("assessed_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["startup_id"],
            ["startup_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assessed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_assessment_records_startup_id"),
        "ai_assessment_records",
        ["startup_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_assessment_records_created_at"),
        "ai_assessment_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ai_assessment_records_created_at"),
        table_name="ai_assessment_records",
    )
    op.drop_index(
        op.f("ix_ai_assessment_records_startup_id"),
        table_name="ai_assessment_records",
    )
    op.drop_table("ai_assessment_records")
