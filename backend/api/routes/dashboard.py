import calendar as cal_module
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import User, Plan, DailyLog, WeeklySummary

router = APIRouter()


@router.get("/users/{user_id}/progress")
def get_progress(user_id: str, db: Session = Depends(get_db)):
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

    # Compute goal progress percentage
    goal = user.goal or {}
    goal_progress_pct = None
    if goal.get("current_weight") and goal.get("target_weight") and weekly_summary:
        sw = weekly_summary.summary.get("start_weight")
        cw = goal.get("current_weight")
        tw = goal.get("target_weight")
        if sw and sw != tw:
            goal_progress_pct = round(abs(sw - cw) / abs(sw - tw) * 100, 1)

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "goal": goal,
        },
        "current_plan": {
            "workout_plan": plan.workout_plan if plan else {},
            "meal_plan": plan.meal_plan if plan else {},
            "week_start": str(plan.week_start) if plan else None,
        },
        "today": {
            "date": str(today),
            "calories": daily_log.calories if daily_log else 0,
            "macros": daily_log.macros if daily_log else {},
            "meals_logged": len(daily_log.meals or []) if daily_log else 0,
            "workouts_logged": len(daily_log.workouts or []) if daily_log else 0,
        },
        "weekly_summary": weekly_summary.summary if weekly_summary else {},
        "goal_progress_pct": goal_progress_pct,
    }


@router.get("/users/{user_id}/logs")
def get_logs(user_id: str, limit: int = 7, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logs = (
        db.query(DailyLog)
        .filter(DailyLog.user_id == user_id)
        .order_by(DailyLog.date.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "date": str(log.date),
            "calories": log.calories,
            "macros": log.macros,
            "meals_count": len(log.meals or []),
            "workouts_count": len(log.workouts or []),
        }
        for log in logs
    ]


@router.get("/users/{user_id}/workouts/calendar")
def get_workout_calendar(
    user_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not (1 <= month <= 12):
        raise HTTPException(status_code=422, detail="month must be 1-12")

    first_day = date(year, month, 1)
    last_day = date(year, month, cal_module.monthrange(year, month)[1])

    logs = (
        db.query(DailyLog)
        .filter(
            DailyLog.user_id == user_id,
            DailyLog.date >= first_day,
            DailyLog.date <= last_day,
        )
        .order_by(DailyLog.date.asc())
        .all()
    )

    return [
        {
            "date": str(log.date),
            "workout_count": len(log.workouts or []),
            "workouts": [
                {
                    "type": w.get("entry", {}).get("type") or w.get("entry", {}).get("workout_type", "Workout"),
                    "duration_min": w.get("entry", {}).get("duration_min"),
                    "exercises_completed": w.get("entry", {}).get("exercises_completed", []),
                    "notes": w.get("entry", {}).get("notes", ""),
                }
                for w in (log.workouts or [])
            ],
        }
        for log in logs
    ]
