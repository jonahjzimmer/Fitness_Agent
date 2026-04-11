from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from db.session import get_db
from db.models import User, Plan, DailyLog, WeeklySummary, Conversation, ChatMessage
from agent.graph import app as agent_app
from agent.state import AgentState

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    name: str = "User"
    email: str | None = None
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    next_node: str
    user_id: str
    conversation_id: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class CreateConversationRequest(BaseModel):
    user_id: str


def _load_state(user_id: str, db: Session) -> AgentState:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    week_start = today.replace(day=today.day - today.weekday())

    plan = (
        db.query(Plan)
        .filter(Plan.user_id == user_id, Plan.week_start == week_start)
        .order_by(Plan.created_at.desc())
        .first()
    )

    daily_log = (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id, DailyLog.date == today)
        .first()
    )

    weekly_summary = (
        db.query(WeeklySummary)
        .filter(WeeklySummary.user_id == user_id, WeeklySummary.week_start == week_start)
        .first()
    )

    thirty_days_ago = today - timedelta(days=30)
    historical_logs = (
        db.query(DailyLog)
        .filter(
            DailyLog.user_id == user_id,
            DailyLog.date >= thirty_days_ago,
            DailyLog.date < today,
        )
        .order_by(DailyLog.date.asc())
        .all()
    )
    workout_history = [
        {
            "date": str(log.date),
            "workouts": log.workouts or [],
            "calories": log.calories or 0,
            "macros": log.macros or {},
        }
        for log in historical_logs
    ]

    return AgentState(
        messages=[],
        user_id=user_id,
        current_plan=(plan.workout_plan | {"meal_plan": plan.meal_plan}) if plan else {},
        goal=user.goal or {},
        daily_log=(daily_log.meals or []) + (daily_log.workouts or []) if daily_log else [],
        weekly_summary=weekly_summary.summary if weekly_summary else {},
        workout_history=workout_history,
        next_node="",
        response=None,
    )


def _persist_state(user_id: str, result: AgentState, db: Session):
    today = date.today()
    week_start = today.replace(day=today.day - today.weekday())

    # Update user goal if changed
    if result.get("goal"):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.goal = result["goal"]

    # Upsert plan if changed
    if result.get("current_plan"):
        plan = (
            db.query(Plan)
            .filter(Plan.user_id == user_id, Plan.week_start == week_start)
            .first()
        )
        cp = result["current_plan"]
        if plan:
            plan.workout_plan = cp.get("workout_plan", plan.workout_plan)
            plan.meal_plan = cp.get("meal_plan", plan.meal_plan)
        else:
            plan = Plan(
                user_id=user_id,
                week_start=week_start,
                workout_plan=cp.get("workout_plan", {}),
                meal_plan=cp.get("meal_plan", {}),
            )
            db.add(plan)

    # Upsert daily log if changed
    if result.get("daily_log") is not None:
        log = (
            db.query(DailyLog)
            .filter(DailyLog.user_id == user_id, DailyLog.date == today)
            .first()
        )
        meals = [e for e in result["daily_log"] if e.get("log_type") == "meal"]
        workouts = [e for e in result["daily_log"] if e.get("log_type") == "workout"]
        total_cal = sum(e.get("entry", {}).get("estimated_calories", 0) for e in meals)
        macros = {
            "protein": sum(e.get("entry", {}).get("estimated_protein_g", 0) for e in meals),
            "carbs": sum(e.get("entry", {}).get("estimated_carbs_g", 0) for e in meals),
            "fat": sum(e.get("entry", {}).get("estimated_fat_g", 0) for e in meals),
        }
        if log:
            log.meals = meals
            log.workouts = workouts
            log.calories = total_cal
            log.macros = macros
        else:
            log = DailyLog(
                user_id=user_id,
                date=today,
                meals=meals,
                workouts=workouts,
                calories=total_cal,
                macros=macros,
            )
            db.add(log)

    # Upsert weekly summary if changed
    if result.get("weekly_summary"):
        summary = (
            db.query(WeeklySummary)
            .filter(WeeklySummary.user_id == user_id, WeeklySummary.week_start == week_start)
            .first()
        )
        if summary:
            summary.summary = result["weekly_summary"]
        else:
            summary = WeeklySummary(
                user_id=user_id,
                week_start=week_start,
                summary=result["weekly_summary"],
            )
            db.add(summary)

    db.commit()


@router.get("/chat/conversations", response_model=list[ConversationOut])
def list_conversations(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    convos = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in convos
    ]


@router.post("/chat/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(req: CreateConversationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    convo = Conversation(user_id=req.user_id, title="New Chat")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return ConversationOut(
        id=convo.id,
        title=convo.title,
        created_at=convo.created_at.isoformat(),
        updated_at=convo.updated_at.isoformat(),
    )


@router.get("/chat/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in convo.messages
    ]


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    # Auto-create user if not exists
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        email = req.email or f"{req.user_id}@fitnessagent.local"
        user = User(id=req.user_id, name=req.name, email=email)
        db.add(user)
        db.commit()

    # Resolve or create conversation
    if req.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = Conversation(user_id=req.user_id, title="New Chat")
        db.add(convo)
        db.flush()

    # Auto-title on first message
    if convo.title == "New Chat":
        raw = req.message.strip()
        convo.title = (raw[:40] + "...") if len(raw) > 40 else raw

    # Persist human message
    db.add(ChatMessage(conversation_id=convo.id, role="human", content=req.message))

    state = _load_state(req.user_id, db)
    state["messages"] = [HumanMessage(content=req.message)]

    result = agent_app.invoke(state)

    _persist_state(req.user_id, result, db)

    ai_response = result.get("response", "Something went wrong. Please try again.")

    # Persist AI message and touch updated_at
    db.add(ChatMessage(conversation_id=convo.id, role="ai", content=ai_response))
    convo.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        response=ai_response,
        next_node=result.get("next_node", ""),
        user_id=req.user_id,
        conversation_id=convo.id,
    )
