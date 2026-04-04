"""Add unique constraint on (project_id, applicant_id) in applications

Revision ID: 002
Revises: 001
Create Date: 2026-03-26 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_application_project_applicant',
        'applications',
        ['project_id', 'applicant_id'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_application_project_applicant', 'applications', type_='unique')
