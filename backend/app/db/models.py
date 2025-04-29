import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from .session import Base


def generate_uuid():
    """Generate a UUID string for model IDs."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and profile information."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    topic_progress = relationship("TopicProgress", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    question_responses = relationship("QuestionResponse", back_populates="user")
    knowledge_states = relationship("KnowledgeState", back_populates="user")


class Topic(Base):
    """Topic model for learning subjects or modules."""
    __tablename__ = "topics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    description = Column(String)
    parent_id = Column(String, ForeignKey("topics.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    content = Column(Text, nullable=True)  # Study material content
    prerequisite_ids = Column(JSON, nullable=True)  # JSON array of prerequisite topic IDs
    topic_metadata = Column(JSON, nullable=True)  # Additional metadata for the topic
    
    # Relationships
    children = relationship("Topic", back_populates="parent", foreign_keys=[parent_id])
    parent = relationship("Topic", back_populates="children", remote_side=[id])
    quizzes = relationship("Quiz", back_populates="topic")
    topic_progress = relationship("TopicProgress", back_populates="topic")
    concepts = relationship("Concept", back_populates="topic")


class Concept(Base):
    """Concept model for specific knowledge components within topics."""
    __tablename__ = "concepts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    topic_id = Column(String, ForeignKey("topics.id"))
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic", back_populates="concepts")
    questions = relationship("Question", back_populates="concept")
    knowledge_states = relationship("KnowledgeState", back_populates="concept")


class Quiz(Base):
    """Quiz model for assessments."""
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    topic_id = Column(String, ForeignKey("topics.id"))
    difficulty_level = Column(Float, default=0.5)  # 0.0-1.0 scale
    is_adaptive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    time_limit_minutes = Column(Integer, nullable=True)
    
    # Relationships
    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz")
    quiz_questions = relationship("QuizQuestion", back_populates="quiz")


class Question(Base):
    """Question model for quiz items."""
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=True)
    text = Column(String)
    options = Column(JSON)  # JSON array of answer options
    correct_answer = Column(String)  # Index or identifier of correct option
    explanation = Column(String, nullable=True)
    difficulty_level = Column(Float, default=0.5)  # 0.0-1.0 scale
    points = Column(Integer, default=1)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    concept = relationship("Concept", back_populates="questions")
    responses = relationship("QuestionResponse", back_populates="question")
    quiz_questions = relationship("QuizQuestion", back_populates="question")


class QuizQuestion(Base):
    """Junction model for organizing questions within a quiz."""
    __tablename__ = "quiz_questions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    order = Column(Integer)  # Position of question in quiz
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="quiz_questions")
    question = relationship("Question", back_populates="quiz_questions")


class QuizAttempt(Base):
    """Quiz attempt model to track user's quiz session."""
    __tablename__ = "quiz_attempts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    quiz_id = Column(String)  # Not FK since we may have practice quizzes not in the quiz table
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    responses = Column(JSON, nullable=True)  # Storing responses as JSON
    quiz_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    question_responses = relationship("QuestionResponse", back_populates="quiz_attempt")


class QuestionResponse(Base):
    """Model for user's responses to questions."""
    __tablename__ = "question_responses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_attempt_id = Column(String, ForeignKey("quiz_attempts.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    user_id = Column(String, ForeignKey("users.id"))
    selected_answer = Column(String)  # User's selection
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_attempt = relationship("QuizAttempt", back_populates="question_responses")
    question = relationship("Question", back_populates="responses")
    user = relationship("User", back_populates="question_responses")


class TopicProgress(Base):
    """Model to track user's progress in a topic."""
    __tablename__ = "topic_progress"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    topic_id = Column(String, ForeignKey("topics.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    completion_percentage = Column(Float, default=0.0)
    mastery_level = Column(Float, default=0.0)  # 0.0-1.0 scale
    
    # Relationships
    user = relationship("User", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="topic_progress")


class KnowledgeState(Base):
    """Model for tracking user's knowledge of specific concepts (Bayesian Knowledge Tracing)."""
    __tablename__ = "knowledge_states"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    concept_id = Column(String, ForeignKey("concepts.id"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # BKT parameters
    p_know = Column(Float, default=0.3)  # Probability of knowing the concept
    p_learn = Column(Float, default=0.2)  # Probability of learning if previously unknown
    p_guess = Column(Float, default=0.25)  # Probability of guessing correctly if unknown
    p_slip = Column(Float, default=0.1)  # Probability of making a mistake if known
    
    # Relationships
    user = relationship("User", back_populates="knowledge_states")
    concept = relationship("Concept", back_populates="knowledge_states")


class ContentItem(Base):
    """Model for generated learning content items."""
    __tablename__ = "content_items"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    topic_id = Column(String, ForeignKey("topics.id"))
    title = Column(String, nullable=True)
    content = Column(Text)
    format = Column(String, default="markdown")  # markdown, html, etc.
    difficulty_level = Column(Float, default=0.5)  # 0.0-1.0 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    content_type = Column(String, default="study_material")  # study_material, example, explanation
    
    # Relationships
    topic = relationship("Topic")