from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "sale_app_product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(16))
    product_priority: Mapped[int] = mapped_column(Integer, default=1)
    product_type: Mapped[int] = mapped_column(Integer, default=1)
    product_info: Mapped[str] = mapped_column(String(256))


class Dataset(Base):
    __tablename__ = "sale_app_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1)
    dataset_name: Mapped[str] = mapped_column(String(16))
    dataset_type: Mapped[int] = mapped_column(Integer, default=1)
    dataset_info: Mapped[str] = mapped_column(String(256))
    dataset_status: Mapped[int] = mapped_column(Integer, default=1)
    embedding_model: Mapped[str] = mapped_column(String(16))
    embedding_model_provider: Mapped[str] = mapped_column(String(16))
    dataset_create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dataset_update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
