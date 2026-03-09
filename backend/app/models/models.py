"""
SQLAlchemy ORM models for all database tables.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, Date,
    DateTime, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    url = Column(Text)
    reliability = Column(Float, default=0.5)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    contents = relationship("Content", back_populates="source")


class Content(Base):
    __tablename__ = "content"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    external_id = Column(String(255))
    title = Column(Text)
    body = Column(Text, nullable=False)
    url = Column(Text)
    author = Column(String(255))
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_type = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    engagement = Column(JSON, default=dict)
    metadata_ = Column("metadata", JSON, default=dict)
    is_spam = Column(Boolean, default=False)

    source = relationship("Source", back_populates="contents")
    embedding = relationship("Embedding", back_populates="content", uselist=False)


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), unique=True)
    embedding = Column(Vector(1536), nullable=False)
    model = Column(String(100), default="text-embedding-3-small")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    content = relationship("Content", back_populates="embedding")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    keywords = Column(JSON, default=list)
    content_count = Column(Integer, default=0)
    trend_score = Column(Float, default=0.0)
    first_seen = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen = Column(DateTime(timezone=True), default=datetime.utcnow)
    cluster_id = Column(Integer)


class TopicContent(Base):
    __tablename__ = "topic_content"

    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), primary_key=True)
    relevance = Column(Float, default=1.0)


class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"))
    trend_score = Column(Float, nullable=False)
    content_velocity = Column(Float, default=0.0)
    engagement_weight = Column(Float, default=0.0)
    source_authority = Column(Float, default=0.0)
    snapshot_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    topic = relationship("Topic")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False, unique=True)
    title = Column(String(500))
    summary = Column(Text)
    sections = Column(JSON, nullable=False, default=dict)
    source_refs = Column(JSON, default=list)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    model_used = Column(String(100))
