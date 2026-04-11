"""
Backfill a month of workout history for a user.
Create users via the app's login screen before running this script.

Usage (run from backend/):
    python scripts/backfill_workouts.py --list-users
    python scripts/backfill_workouts.py --user-id <id-or-email>
    python scripts/backfill_workouts.py --user-id <id-or-email> --weeks 4 --overwrite
"""

import argparse
import os
import sys
import uuid
from datetime import date, timedelta

# Allow imports from the backend root (db.session, db.models)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

from db.session import SessionLocal
from db.models import User, DailyLog


# ---------------------------------------------------------------------------
# Workout templates — exercises_completed strings include sets/reps/weight
# so the agent can parse progression from the history text.
# Weights progress each week (index 0 = oldest week).
# ---------------------------------------------------------------------------
# starrting message
# i want to grow my strength through the use of normal gym workouts with one pull day one push day and one leg day.  for push i want to do bench press, overhead press, incline DB Press, lateral raises and tricep pushdowns. for pull days i want to do deadlift, barbell, pull-ups, face pulls, and barbell curls. for legs i want to do squats, Romanian deadlift, leg press, leg curl and calf raises
PUSH_DAYS = [
    # week 0 (oldest)
    [
        "Bench Press 4x8 @ 155lbs",
        "Overhead Press 3x8 @ 95lbs",
        "Incline DB Press 3x10 @ 55lbs",
        "Lateral Raises 3x15 @ 20lbs",
        "Tricep Pushdowns 3x12 @ 60lbs",
    ],
    # week 1
    [
        "Bench Press 4x8 @ 160lbs",
        "Overhead Press 3x8 @ 100lbs",
        "Incline DB Press 3x10 @ 57.5lbs",
        "Lateral Raises 3x15 @ 20lbs",
        "Tricep Pushdowns 3x12 @ 65lbs",
    ],
    # week 2
    [
        "Bench Press 4x8 @ 165lbs",
        "Overhead Press 3x8 @ 105lbs",
        "Incline DB Press 3x10 @ 60lbs",
        "Lateral Raises 3x15 @ 22.5lbs",
        "Tricep Pushdowns 3x12 @ 65lbs",
    ],
    # week 3 (most recent)
    [
        "Bench Press 4x8 @ 170lbs",
        "Overhead Press 3x8 @ 110lbs",
        "Incline DB Press 3x10 @ 62.5lbs",
        "Lateral Raises 3x15 @ 25lbs",
        "Tricep Pushdowns 3x12 @ 70lbs",
    ],
]

PULL_DAYS = [
    [
        "Deadlift 4x5 @ 225lbs",
        "Barbell Row 4x8 @ 135lbs",
        "Pull-ups 3x6",
        "Face Pulls 3x15 @ 40lbs",
        "Barbell Curl 3x10 @ 65lbs",
    ],
    [
        "Deadlift 4x5 @ 235lbs",
        "Barbell Row 4x8 @ 140lbs",
        "Pull-ups 3x8",
        "Face Pulls 3x15 @ 42.5lbs",
        "Barbell Curl 3x10 @ 70lbs",
    ],
    [
        "Deadlift 4x5 @ 245lbs",
        "Barbell Row 4x8 @ 145lbs",
        "Pull-ups 4x8",
        "Face Pulls 3x15 @ 45lbs",
        "Barbell Curl 3x10 @ 70lbs",
    ],
    [
        "Deadlift 4x5 @ 255lbs",
        "Barbell Row 4x8 @ 150lbs",
        "Pull-ups 4x10",
        "Face Pulls 3x15 @ 47.5lbs",
        "Barbell Curl 3x10 @ 75lbs",
    ],
]

LEG_DAYS = [
    [
        "Squat 4x6 @ 175lbs",
        "Romanian Deadlift 3x10 @ 135lbs",
        "Leg Press 3x12 @ 270lbs",
        "Leg Curl 3x12 @ 100lbs",
        "Calf Raises 4x15 @ 135lbs",
    ],
    [
        "Squat 4x6 @ 185lbs",
        "Romanian Deadlift 3x10 @ 145lbs",
        "Leg Press 3x12 @ 290lbs",
        "Leg Curl 3x12 @ 105lbs",
        "Calf Raises 4x15 @ 145lbs",
    ],
    [
        "Squat 4x6 @ 195lbs",
        "Romanian Deadlift 3x10 @ 155lbs",
        "Leg Press 3x12 @ 310lbs",
        "Leg Curl 3x12 @ 110lbs",
        "Calf Raises 4x15 @ 155lbs",
    ],
    [
        "Squat 4x6 @ 205lbs",
        "Romanian Deadlift 3x10 @ 165lbs",
        "Leg Press 3x12 @ 330lbs",
        "Leg Curl 3x12 @ 115lbs",
        "Calf Raises 4x15 @ 160lbs",
    ],
]

# (workout_type, exercises_list, duration_min)
WEEKLY_SCHEDULE = [
    ("Push Day",  PUSH_DAYS, 65),   # Monday
    ("Pull Day",  PULL_DAYS, 60),   # Wednesday
    ("Leg Day",   LEG_DAYS,  70),   # Friday
]

# weekday offsets from Monday (0-based): Mon=0, Wed=2, Fri=4
WEEKDAY_OFFSETS = [0, 2, 4]


def build_workout_dates(num_weeks: int) -> list[tuple[date, int, int]]:
    """
    Return a list of (date, week_index, day_index) tuples going back num_weeks.
    week_index 0 = oldest week, week_index num_weeks-1 = most recent.
    day_index maps to WEEKLY_SCHEDULE.
    Skips any date that is in the future.
    """
    today = date.today()
    # Find the most recent Monday on or before today
    monday = today - timedelta(days=today.weekday())

    entries = []
    for week_offset in range(num_weeks - 1, -1, -1):  # oldest first
        week_monday = monday - timedelta(weeks=week_offset)
        week_index = num_weeks - 1 - week_offset
        for day_index, wd_offset in enumerate(WEEKDAY_OFFSETS):
            workout_date = week_monday + timedelta(days=wd_offset)
            if workout_date <= today:
                entries.append((workout_date, week_index, day_index))
    return entries


def make_workout_entry(week_index: int, day_index: int) -> dict:
    workout_type, exercise_weeks, duration = WEEKLY_SCHEDULE[day_index]
    # Clamp week_index to available progression data
    w = min(week_index, len(exercise_weeks) - 1)
    return {
        "log_type": "workout",
        "entry": {
            "type": workout_type,
            "exercises_completed": exercise_weeks[w],
            "duration_min": duration,
            "notes": "",
        },
    }


def list_users(db):
    users = db.query(User).order_by(User.created_at).all()
    if not users:
        print("No users found in the database.")
        return
    print(f"{'ID':<38}  {'Name':<20}  {'Email'}")
    print("-" * 80)
    for u in users:
        print(f"{u.id:<38}  {u.name:<20}  {u.email}")


def resolve_user(user_id_or_email: str, db) -> User:
    """Accept either a UUID or an email address."""
    user = db.query(User).filter(User.id == user_id_or_email).first()
    if not user:
        user = db.query(User).filter(User.email == user_id_or_email).first()
    return user


def backfill(user_id_or_email: str, num_weeks: int, overwrite: bool, db):
    user = resolve_user(user_id_or_email, db)
    if not user:
        print(f"Error: user '{user_id_or_email}' not found.")
        sys.exit(1)
    user_id = user.id

    print(f"Backfilling {num_weeks} weeks of workouts for {user.name} ({user_id})")

    workout_dates = build_workout_dates(num_weeks)
    inserted = skipped = 0

    for workout_date, week_index, day_index in workout_dates:
        existing = (
            db.query(DailyLog)
            .filter(DailyLog.user_id == user_id, DailyLog.date == workout_date)
            .first()
        )

        entry = make_workout_entry(week_index, day_index)

        if existing:
            if overwrite:
                existing.workouts = [entry]
                db.flush()
                print(f"  OVERWRITE  {workout_date}  {entry['entry']['type']}")
                inserted += 1
            else:
                print(f"  SKIP       {workout_date}  {entry['entry']['type']}  (log exists; use --overwrite to replace)")
                skipped += 1
        else:
            log = DailyLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=workout_date,
                meals=[],
                workouts=[entry],
                calories=0,
                macros={},
            )
            db.add(log)
            db.flush()
            print(f"  INSERT     {workout_date}  {entry['entry']['type']}")
            inserted += 1

    db.commit()
    print(f"\nDone. {inserted} inserted/updated, {skipped} skipped.")


def main():
    parser = argparse.ArgumentParser(description="Backfill workout history for testing.")
    parser.add_argument("--user-id", help="User ID or email to backfill workouts for")
    parser.add_argument("--list-users", action="store_true", help="List all users and exit")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks to backfill (default: 4)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing daily logs (default: skip)")
    args = parser.parse_args()

    if not args.list_users and not args.user_id:
        parser.error("Provide --user-id <id-or-email> or --list-users")

    db = SessionLocal()
    try:
        if args.list_users:
            list_users(db)
        else:
            backfill(args.user_id, args.weeks, args.overwrite, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
