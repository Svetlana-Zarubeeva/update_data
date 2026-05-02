import datetime
from typing import Optional

from sqlalchemy import (BigInteger, Boolean, CHAR, Column, Date, Double, ForeignKeyConstraint, DECIMAL,
                        Index, Integer, JSON, PrimaryKeyConstraint, Sequence, SmallInteger, String, Table, Text, UniqueConstraint, text, Float)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
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


class SilverOfdataCompany(Base, TimestampMixin):
    """
    Нормализованная таблица компаний из Bronze (MongoDB → PostgreSQL).
    Первичный ключ — ИНН компании.
    """
    __tablename__ = 'silver_ofdata_companies'
    __table_args__ = (
        Index('silver_ofdata_companies_status_idx', 'status'),
        Index('silver_ofdata_companies_region_code_idx', 'region_code'),
        Index('silver_ofdata_companies_okved_code_idx', 'okved_code'),
        {'schema': 'silver'},
    )

    inn: Mapped[str] = mapped_column(String(20), primary_key=True)
    ogrn: Mapped[Optional[str]] = mapped_column(String(20))
    kpp: Mapped[Optional[str]] = mapped_column(String(10))
    short_name: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    reg_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(255))
    region_code: Mapped[Optional[str]] = mapped_column(String(10))
    address: Mapped[Optional[str]] = mapped_column(Text)
    okved_code: Mapped[Optional[str]] = mapped_column(String(20))
    okved_description: Mapped[Optional[str]] = mapped_column(Text)
    directors: Mapped[Optional[dict]] = mapped_column(JSONB)
    founders: Mapped[Optional[dict]] = mapped_column(JSONB)
    

class SilverPipelineMetric(Base, IdMixin):
    """
    Метрики выполнения Silver ETL-пайплайна.
    """
    __tablename__ = 'silver_pipeline_metrics'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='silver_pipeline_metrics_pkey'),
        {'schema': 'silver'},
    )

    pipeline_name: Mapped[str] = mapped_column(String(50), nullable=False, default='silver')
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
