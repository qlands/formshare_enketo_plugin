from formshare.models.meta import Base
from formshare.models.formshare import Odkform
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    Unicode,
)


class EnketoFormMetadata(Base):
    __tablename__ = "enketo_form_metadata"

    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "form_id"],
            ["odkform.project_id", "odkform.form_id"],
            ondelete="CASCADE",
        ),
    )

    project_id = Column(Unicode(64), primary_key=True, nullable=False)
    form_id = Column(Unicode(120), primary_key=True, nullable=False)
    url_multi = Column(Unicode(120))
    url_off_multi = Column(Unicode(120))
    url_single = Column(Unicode(120))
    url_once = Column(Unicode(120))
    url_testing = Column(Unicode(120))
    url_embeddable = Column(Unicode(120))
    return_url_content = Column(MEDIUMTEXT(collation="utf8mb4_unicode_ci"))

    project = relationship("Odkform")


class EnketoReturnContent(Base):
    __tablename__ = "enketo_return_content"

    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "form_id"],
            ["enketo_form_metadata.project_id", "enketo_form_metadata.form_id"],
            ondelete="CASCADE",
        ),
    )

    project_id = Column(Unicode(64), primary_key=True, nullable=False)
    form_id = Column(Unicode(120), primary_key=True, nullable=False)
    language_code = Column(Unicode(10), primary_key=True, nullable=False)
    return_url_content = Column(MEDIUMTEXT(collation="utf8mb4_unicode_ci"))

    project = relationship("EnketoFormMetadata")
