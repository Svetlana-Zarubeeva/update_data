import datetime
from typing import Optional

from sqlalchemy import (BigInteger, Boolean, CHAR, Column, Date, Double, ForeignKeyConstraint, DECIMAL,
                        Index, Integer, ForeignKey, JSON, PrimaryKeyConstraint, Sequence, SmallInteger, String, Table, Text, UniqueConstraint, text, Float)
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
    Справочник IT-ОКВЭД.
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


class OfdataFounderType(Base, IdMixin):
    __tablename__ = 'ofdata_founder_types'
    __table_args__ = (
        Index('idx_founder_types_code', 'type_code'),
    )

    type_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    type_name: Mapped[str] = mapped_column(String(100), nullable=False)


class OfdataAddress(Base, IdMixin, TimestampMixin):
    __tablename__ = 'ofdata_addresses'
    __table_args__ = (
        Index('idx_addresses_region', 'region'),
        Index('idx_directors_legal_entity_id', 'legal_entity_id'),
        Index('idx_addresses_city', 'city'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    index: Mapped[Optional[str]] = mapped_column(String(20))
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    house: Mapped[str] = mapped_column(String(255), nullable=False)
    full_address: Mapped[str] = mapped_column(Text, nullable=False)


class OfdataLegalEntity(Base, TimestampMixin, IdMixin):
    __tablename__ = 'ofdata_legal_entities'
    __table_args__ = (
        Index('idx_legal_entities_inn', 'inn'),
        Index('idx_legal_entities_ogrn', 'ogrn'),
        Index('idx_legal_entities_region_code', 'region_code'),
        Index('idx_legal_entities_okved_code', 'okved_code'),
        Index('idx_legal_entities_status', 'status'),
    )

    inn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(20))
    kpp: Mapped[Optional[str]] = mapped_column(String(10))
    short_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    reg_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    region_code: Mapped[str] = mapped_column(String(10), nullable=False)
    okved_code: Mapped[str] = mapped_column(String(20), nullable=False)
    okved_description: Mapped[str] = mapped_column(Text, nullable=False)


class OfdataDirector(Base, IdMixin):
    __tablename__ = 'ofdata_directors'
    __table_args__ = (
        Index('idx_directors_inn', 'inn'),
        Index('idx_directors_legal_entity_id', 'legal_entity_id'),
        Index('idx_directors_position', 'position'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    inn: Mapped[Optional[str]] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    is_disqualified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_inaccurate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)


class OfdataFounder(Base, IdMixin):
    __tablename__ = 'ofdata_founders'
    __table_args__ = (
        Index('idx_founders_inn', 'inn'),
        Index('idx_founders_legal_entity_id', 'legal_entity_id'),
        Index('idx_founders_type_id', 'founder_type_id'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('ofdata_legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    founder_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('ofdata_founder_types.id', ondelete='RESTRICT'),
        nullable=False
    )
    inn: Mapped[Optional[str]] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(20))
    kpp: Mapped[Optional[str]] = mapped_column(String(10))
    is_inaccurate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)


class PipelineMetric(Base, IdMixin):
    __tablename__ = 'pipeline_metrics'
    __table_args__ = (
        Index('idx_pipeline_metrics_name', 'pipeline_name'),
        Index('idx_pipeline_metrics_created_at', 'created_at'),
    )

    pipeline_name: Mapped[str] = mapped_column(String(50), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=0),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )