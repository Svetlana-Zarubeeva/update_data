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


class SilverDadataCompany(Base, TimestampMixin):
    """
    Нормализованная таблица компаний из DaData Bronze (MongoDB → PostgreSQL).
    Содержит расширенную информацию о компаниях, полученную из DaData API.
    Первичный ключ — ИНН компании.
    """
    __tablename__ = 'silver_dadata_companies'
    __table_args__ = (
        Index('silver_dadata_companies_inn_idx', 'inn'),
        Index('silver_dadata_companies_ogrn_idx', 'ogrn'),
        Index('silver_dadata_companies_status_idx', 'status'),
        Index('silver_dadata_companies_region_idx', 'region'),
        Index('silver_dadata_companies_city_idx', 'city'),
        Index('silver_dadata_companies_okved_main_idx', 'okved_main'),
        {'schema': 'silver'},
    )

    inn: Mapped[str] = mapped_column(String(12), primary_key=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))
    company_name: Mapped[Optional[str]] = mapped_column(String(500))
    short_name: Mapped[Optional[str]] = mapped_column(String(255))
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    registration_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    actuality_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    
    # Адрес
    address_full: Mapped[Optional[str]] = mapped_column(Text)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    street: Mapped[Optional[str]] = mapped_column(String(255))
    house: Mapped[Optional[str]] = mapped_column(String(50))
    flat: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))
    longitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))
    
    # Контактная информация
    phones: Mapped[Optional[dict]] = mapped_column(JSONB)
    emails: Mapped[Optional[dict]] = mapped_column(JSONB)
    websites: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Финансы
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    income: Mapped[Optional[float]] = mapped_column(Float)
    expense: Mapped[Optional[float]] = mapped_column(Float)
    tax_system: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Руководство
    management_name: Mapped[Optional[str]] = mapped_column(String(255))
    management_post: Mapped[Optional[str]] = mapped_column(String(255))
    management_start_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    
    # ОКВЭД
    okved_main: Mapped[Optional[str]] = mapped_column(String(20))
    okveds: Mapped[Optional[dict]] = mapped_column(JSONB)


class LegalEntity(Base, TimestampMixin, IdMixin):
    """
    Основная информация о юридическом лице в Gold-слое.
    """
    __tablename__ = 'legal_entities'
    __table_args__ = (
        Index('idx_entities_inn', 'inn'),
        Index('idx_entities_ogrn', 'ogrn'),
        Index('idx_entities_status', 'status'),
        Index('idx_entities_okved_code', 'okved_code'),
    )

    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    short_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    registration_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    okved_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        ForeignKey('okved_it_codes.okved_code', ondelete='SET NULL')
    )


class Address(Base, IdMixin, TimestampMixin):
    """
    Адрес юридического лица.
    """
    __tablename__ = 'addresses'
    __table_args__ = (
        Index('idx_addresses_entity_id', 'legal_entity_id'),
        Index('idx_addresses_postal_code', 'postal_code'),
        Index('idx_addresses_district', 'district'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    address_full: Mapped[str] = mapped_column(Text, nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[Optional[str]] = mapped_column(String(255))
    house: Mapped[Optional[str]] = mapped_column(String(50))
    flat: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))
    longitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))


class ContactInfo(Base, IdMixin, TimestampMixin):
    """
    Контактная информация юридического лица.
    """
    __tablename__ = 'contact_info'
    __table_args__ = (
        Index('idx_contacts_entity_id', 'legal_entity_id'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    phones: Mapped[Optional[dict]] = mapped_column(JSONB)
    emails: Mapped[Optional[dict]] = mapped_column(JSONB)
    websites: Mapped[Optional[dict]] = mapped_column(JSONB)


class Finance(Base, IdMixin, TimestampMixin):
    """
    Финансовая информация о юридическом лице.
    """
    __tablename__ = 'finance'
    __table_args__ = (
        Index('idx_finance_entity_id', 'legal_entity_id'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    income: Mapped[Optional[float]] = mapped_column(Float)
    expense: Mapped[Optional[float]] = mapped_column(Float)
    tax_system: Mapped[Optional[str]] = mapped_column(String(10))


class Management(Base, IdMixin, TimestampMixin):
    """
    Руководство юридического лица.
    """
    __tablename__ = 'management'
    __table_args__ = (
        Index('idx_management_entity_id', 'legal_entity_id'),
        Index('idx_management_name', 'name'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))
    post: Mapped[Optional[str]] = mapped_column(String(255))
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date)


class FounderType(Base, IdMixin):
    """
    Типы учредителей.
    """
    __tablename__ = 'founder_types'
    __table_args__ = (
        Index('idx_founder_types_code', 'type_code'),
    )

    type_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    type_name: Mapped[str] = mapped_column(String(100), nullable=False)


class Founder(Base, IdMixin, TimestampMixin):
    """
    Учредители юридического лица.
    """
    __tablename__ = 'founders'
    __table_args__ = (
        Index('idx_founders_entity_id', 'legal_entity_id'),
        Index('idx_founders_type_id', 'founder_type_id'),
    )

    legal_entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('legal_entities.id', ondelete='CASCADE'),
        nullable=False
    )
    founder_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('founder_types.id', ondelete='RESTRICT'),
        nullable=False
    )
    inn: Mapped[Optional[str]] = mapped_column(String(12))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_inaccurate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)


class PipelineMetric(Base, IdMixin):
    """
    Метрики выполнения Gold ETL-пайплайна с детализацией по таблицам.
    """
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


class ApiKey(Base, TimestampMixin, IdMixin):
    """
    Таблица для хранения API-ключей различных сервисов.
    Поддерживает несколько ключей на один сервис.
    """
    __tablename__ = 'api_keys'
    __table_args__ = (
        Index('idx_api_keys_service_name', 'service_name'),
        Index('idx_api_keys_is_active', 'is_active'),
        Index('uq_api_keys_service_key', 'service_name', 'api_key', unique=True),
    )

    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer)
    used_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP)


class SilverCheckoCompany(Base, TimestampMixin):
    """
    Нормализованная таблица компаний из Checko Bronze (MongoDB → PostgreSQL).
    Содержит расширенную информацию о компаниях, полученную из Checko API.
    Первичный ключ — ИНН компании.
    """
    __tablename__ = 'silver_checko_companies'
    __table_args__ = (
        Index('silver_checko_companies_inn_idx', 'inn'),
        Index('silver_checko_companies_ogrn_idx', 'ogrn'),
        Index('silver_checko_companies_status_idx', 'status'),
        Index('silver_checko_companies_region_idx', 'region'),
        Index('silver_checko_companies_city_idx', 'city'),
        Index('silver_checko_companies_okved_main_idx', 'okved_main'),
        {'schema': 'silver'},
    )

    inn: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))
    company_name: Mapped[Optional[str]] = mapped_column(String(500))
    short_name: Mapped[Optional[str]] = mapped_column(String(255))
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    status: Mapped[Optional[str]] = mapped_column(String(255))  # Изменено с 50 на 255
    registration_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    actuality_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    
    # Адрес
    address_full: Mapped[Optional[str]] = mapped_column(Text)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    street: Mapped[Optional[str]] = mapped_column(String(255))
    house: Mapped[Optional[str]] = mapped_column(String(50))
    flat: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))
    longitude: Mapped[Optional[float]] = mapped_column(Float(precision=8))
    
    # Контактная информация
    phones: Mapped[Optional[dict]] = mapped_column(JSONB)
    emails: Mapped[Optional[dict]] = mapped_column(JSONB)
    websites: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Финансы
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    income: Mapped[Optional[float]] = mapped_column(Float)
    expense: Mapped[Optional[float]] = mapped_column(Float)
    tax_system: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Руководство
    management_name: Mapped[Optional[str]] = mapped_column(String(255))
    management_post: Mapped[Optional[str]] = mapped_column(String(255))
    management_start_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    
    # ОКВЭД
    okved_main: Mapped[Optional[str]] = mapped_column(String(20))
    okveds: Mapped[Optional[dict]] = mapped_column(JSONB)


class OfdataGoldEntity(Base, TimestampMixin, IdMixin):
    """
    Промежуточная таблица для хранения данных из OfData в Gold-слое.
    """
    __tablename__ = 'ofdata_gold_entities'
    __table_args__ = (
        Index('idx_ofdata_inn', 'inn'),
    )

    inn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(20))
    kpp: Mapped[Optional[str]] = mapped_column(String(10))
    short_name: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    reg_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(255))
    okved_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        ForeignKey('okved_it_codes.okved_code', ondelete='SET NULL')
    )


class DadataGoldEntity(Base, TimestampMixin, IdMixin):
    """
    Промежуточная таблица для хранения данных из DaData в Gold-слое.
    """
    __tablename__ = 'dadata_gold_entities'
    __table_args__ = (
        Index('idx_dadata_inn', 'inn'),
    )

    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    short_name: Mapped[Optional[str]] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    registration_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=0))
    okved_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        ForeignKey('okved_it_codes.okved_code', ondelete='SET NULL')
    )