from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    goal = Column(JSONB, default=dict)  # {"target_weight": 170, "timeline_weeks": 12, "activity_level": "moderate"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    daily_logs = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")
    weekly_summaries = relationship("WeeklySummary", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    workout_plan = Column(JSONB, default=dict)  # {"monday": {...}, "wednesday": {...}, ...}
    meal_plan = Column(JSONB, default=dict)      # {"monday": {"breakfast": ..., "lunch": ..., "dinner": ...}, ...}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="plans")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    meals = Column(JSONB, default=list)      # [{"name": "grilled chicken", "calories": 350, "protein": 40, ...}]
    workouts = Column(JSONB, default=list)   # [{"type": "push day", "exercises": [...], "duration_min": 60}]
    calories = Column(Integer, default=0)
    macros = Column(JSONB, default=dict)     # {"protein": 150, "carbs": 200, "fat": 60}

    user = relationship("User", back_populates="daily_logs")


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    summary = Column(JSONB, default=dict)
    # {
    #   "avg_calories": 1900,
    #   "workouts_completed": 3,
    #   "workouts_planned": 4,
    #   "weight_logged": 182,
    #   "goal_progress_pct": 35
    # }

    user = relationship("User", back_populates="weekly_summaries")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)   # "human" or "ai"
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
