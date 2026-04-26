import datetime
from typing import Optional

from sqlalchemy import (BigInteger, Boolean, CHAR, Column, Date, Double, ForeignKeyConstraint, DECIMAL,
                        Index, Integer, JSON, PrimaryKeyConstraint, Sequence, SmallInteger, String, Table, Text, UniqueConstraint, text, Float)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )


class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class OkvedItCode(Base, TimestampMixin):
    """
    Справочник IT-ОКВЭД из официального классификатора Росстата.
    """
    __tablename__ = 'okved_it_codes'
    __table_args__ = (
        PrimaryKeyConstraint('okved_code', name='okved_it_codes_pkey'),
        Index('okved_it_codes_section_idx', 'section'),
        Index('okved_it_codes_okved_code_idx', 'okved_code'),
    )

    okved_code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(String(2), nullable=False)


class OkvedPipelineMetric(Base, IdMixin):
    """
    Таблица метрик выполнения ETL-пайплайна для IT-ОКВЭД.
    """
    __tablename__ = 'okved_pipeline_metrics'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pipeline_metrics_pkey'),
    )

    pipeline_name: Mapped[str] = mapped_column(String(255), nullable=False)
    downloaded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    written_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )