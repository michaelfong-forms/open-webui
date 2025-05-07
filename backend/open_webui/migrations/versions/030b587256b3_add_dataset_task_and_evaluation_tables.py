"""Add dataset, task, and evaluation tables

Revision ID: 030b587256b3
Revises: 3781e22d8b01
Create Date: 2025-05-07 00:51:26.034044

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "030b587256b3"
down_revision = "3781e22d8b01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dataset table
    op.create_table(
        "dataset",
        sa.Column("id", sa.Text(), nullable=False, primary_key=True, unique=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=True, server_default="1.0"),
        sa.Column(
            "evaluation_method",
            sa.Text(),
            nullable=True,
            server_default="Criteria Based",
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("access_control", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
    )

    # Create task table
    op.create_table(
        "dataset_task",
        sa.Column("id", sa.Text(), nullable=False, primary_key=True, unique=True),
        sa.Column("dataset_id", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("evaluation_criteria", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "is_training_example",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        sa.Column("access_control", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
    )

    # Create evaluation table
    op.create_table(
        "dataset_evaluation",
        sa.Column("id", sa.Text(), nullable=False, primary_key=True, unique=True),
        sa.Column("dataset_id", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("target_model_id", sa.Text(), nullable=True),
        sa.Column("judge_model_id", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True, server_default="pending"),
        sa.Column("task_ids", sa.JSON(), nullable=True),
        sa.Column("passed_task_ids", sa.JSON(), nullable=True),
        sa.Column("access_control", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("dataset_evaluation")
    op.drop_table("dataset_task")
    op.drop_table("dataset")
