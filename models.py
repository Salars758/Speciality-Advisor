# models.py
from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, ForeignKey,
    Boolean, PrimaryKeyConstraint, DateTime
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(20), default="applicant", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("TestSession", back_populates="user", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")


class Trait(Base):
    __tablename__ = "traits"
    trait_id = Column(Integer, primary_key=True, autoincrement=True)
    trait_name = Column(String(255), nullable=False)
    trait_type = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    questions = relationship("Question", back_populates="trait")
    specializations = relationship("SpecializationTrait", back_populates="trait", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="trait", cascade="all, delete-orphan")
    

class Specialization(Base):
    __tablename__ = "specializations"
    specialization_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    traits = relationship("SpecializationTrait", back_populates="specialization", cascade="all, delete-orphan")


class SpecializationTrait(Base):
    __tablename__ = "specialization_traits"
    __table_args__ = (PrimaryKeyConstraint("specialization_id", "trait_id"),)
    specialization_id = Column(Integer, ForeignKey("specializations.specialization_id", ondelete="CASCADE"), nullable=False)
    trait_id = Column(Integer, ForeignKey("traits.trait_id", ondelete="CASCADE"), nullable=False)
    min_level = Column(DECIMAL(5, 2), nullable=False)
    weight = Column(DECIMAL(3, 2), nullable=False)

    specialization = relationship("Specialization", back_populates="traits")
    trait = relationship("Trait", back_populates="specializations")


class Test(Base):
    __tablename__ = "tests"
    test_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    instruction = Column(Text)
    is_active = Column(Boolean, default=True)

    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    sessions = relationship("TestSession", back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.test_id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    trait_id = Column(Integer, ForeignKey("traits.trait_id"), nullable=False)
    test = relationship("Test", back_populates="questions")
    trait = relationship("Trait", back_populates="questions")
    answer_options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = "answer_options"
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.question_id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(Text, nullable=False)
    score = Column(DECIMAL(5, 2), default=0.00, nullable=False)

    question = relationship("Question", back_populates="answer_options")
    user_answers = relationship("UserAnswer", back_populates="answer", cascade="all, delete-orphan")


class TestSession(Base):
    __tablename__ = "test_sessions"
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.test_id", ondelete="CASCADE"), nullable=False)
    total_score = Column(DECIMAL(5, 2), default=0.00, nullable=False)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    test = relationship("Test", back_populates="sessions")
    user_answers = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("test_sessions.session_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.question_id", ondelete="CASCADE"), nullable=False)
    answer_id = Column(Integer, ForeignKey("answer_options.answer_id", ondelete="CASCADE"), nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TestSession", back_populates="user_answers")
    question = relationship("Question", back_populates="user_answers")
    answer = relationship("AnswerOption", back_populates="user_answers")


class TestResult(Base):
    __tablename__ = "test_results"
    __table_args__ = (PrimaryKeyConstraint("user_id", "trait_id"),)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    trait_id = Column(Integer, ForeignKey("traits.trait_id", ondelete="CASCADE"), nullable=False)
    level = Column(DECIMAL(5, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")
    trait = relationship("Trait", back_populates="results")