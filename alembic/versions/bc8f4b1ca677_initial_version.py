"""Initial version

Revision ID: bc8f4b1ca677
Revises: 
Create Date: 2023-08-13 12:19:25.119683

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "bc8f4b1ca677"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "enketo_form_metadata",
        sa.Column("project_id", sa.Unicode(length=64), nullable=False),
        sa.Column("form_id", sa.Unicode(length=120), nullable=False),
        sa.Column(
            "url_multi", mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"), nullable=True
        ),
        sa.Column(
            "url_off_multi",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.Column(
            "url_single",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.Column(
            "url_once", mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"), nullable=True
        ),
        sa.Column(
            "url_testing",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.Column(
            "url_embeddable",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.Column(
            "return_url_content",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "form_id"],
            ["odkform.project_id", "odkform.form_id"],
            name=op.f("fk_enketo_form_metadata_project_id_odkform"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "project_id", "form_id", name=op.f("pk_enketo_form_metadata")
        ),
    )
    op.create_table(
        "enketo_return_content",
        sa.Column("project_id", sa.Unicode(length=64), nullable=False),
        sa.Column("form_id", sa.Unicode(length=120), nullable=False),
        sa.Column("language_code", sa.Unicode(length=10), nullable=False),
        sa.Column("language_name", sa.Unicode(length=120), nullable=False),
        sa.Column(
            "return_url_content",
            mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "form_id"],
            ["enketo_form_metadata.project_id", "enketo_form_metadata.form_id"],
            name=op.f("fk_enketo_return_content_project_id_enketo_form_metadata"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "project_id",
            "form_id",
            "language_code",
            name=op.f("pk_enketo_return_content"),
        ),
    )


def downgrade():
    op.drop_table("enketo_return_content")
    op.drop_table("enketo_form_metadata")
