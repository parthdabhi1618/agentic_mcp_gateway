# backend/scheduler.py
import json
import uuid
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

SCHEDULED_FILE = "workspace/context/task_context/scheduled_tasks.json"
COMPLETED_FILE = "workspace/context/task_context/completed_tasks.json"

_scheduler = AsyncIOScheduler()

def _ensure_dirs():
    os.makedirs(os.path.dirname(SCHEDULED_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(COMPLETED_FILE),  exist_ok=True)

def load_scheduled():
    _ensure_dirs()
    if os.path.exists(SCHEDULED_FILE):
        with open(SCHEDULED_FILE) as f:
            return json.load(f)
    return []

def save_scheduled(tasks: list):
    _ensure_dirs()
    with open(SCHEDULED_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def log_completed(schedule_id: str, result: dict):
    _ensure_dirs()
    completed = []
    if os.path.exists(COMPLETED_FILE):
        with open(COMPLETED_FILE) as f:
            completed = json.load(f)
    completed.append({"schedule_id": schedule_id, "completed_at": datetime.utcnow().isoformat(), "result": result})
    with open(COMPLETED_FILE, "w") as f:
        json.dump(completed[-100:], f, indent=2)  # keep last 100

async def _execute_scheduled(schedule_id: str, steps: list):
    from jobs import create_job
    from executor import run_job
    job_id = create_job()
    await run_job(job_id, steps)
    log_completed(schedule_id, {"job_id": job_id, "steps_count": len(steps)})
    print(f"[Scheduler] Completed schedule {schedule_id}")

def schedule_task(plan_id: str, steps: list, schedule_config: dict) -> str:
    schedule_id = str(uuid.uuid4())
    sched_type = schedule_config.get("type", "once")

    if sched_type == "once":
        run_at = datetime.fromisoformat(schedule_config["run_at"])
        _scheduler.add_job(
            _execute_scheduled,
            trigger="date",
            run_date=run_at,
            args=[schedule_id, steps],
            id=schedule_id
        )
    elif sched_type == "recurring":
        from apscheduler.triggers.cron import CronTrigger
        cron = schedule_config.get("cron", "0 9 * * MON")
        _scheduler.add_job(
            _execute_scheduled,
            trigger=CronTrigger.from_crontab(cron),
            args=[schedule_id, steps],
            id=schedule_id
        )

    # Persist
    tasks = load_scheduled()
    tasks.append({
        "schedule_id": schedule_id,
        "plan_id": plan_id,
        "steps": steps,
        "schedule": schedule_config,
        "created_at": datetime.utcnow().isoformat()
    })
    save_scheduled(tasks)
    return schedule_id

def start():
    _scheduler.start()
    # Reload persisted tasks
    tasks = load_scheduled()
    valid_tasks = []
    
    for task in tasks:
        cfg = task["schedule"]
        if cfg.get("type") == "recurring":
            try:
                from apscheduler.triggers.cron import CronTrigger
                _scheduler.add_job(
                    _execute_scheduled,
                    trigger=CronTrigger.from_crontab(cfg["cron"]),
                    args=[task["schedule_id"], task["steps"]],
                    id=task["schedule_id"],
                    replace_existing=True
                )
                valid_tasks.append(task)
            except Exception as e:
                print(f"[Scheduler] Failed to reload {task['schedule_id']}: {e}")
        elif cfg.get("type") == "once":
            try:
                # Handle possible naive/aware mismatch by simple format parsing or naive comparison
                run_at = datetime.fromisoformat(cfg["run_at"].replace("Z", "+00:00"))
                # Use naive utcnow for comparison if run_at is naive, but fromisoformat handles tz
                # A safer approach is just to compare timestamps if both are aware,
                # or timezone-agnostic relative comparison.
                # Since datetime.utcnow() is naive, let's just make everything naive UTC or use datetime.now(timezone.utc)
                if run_at.timestamp() > datetime.utcnow().timestamp():
                    _scheduler.add_job(
                        _execute_scheduled,
                        trigger="date",
                        run_date=run_at,
                        args=[task["schedule_id"], task["steps"]],
                        id=task["schedule_id"],
                        replace_existing=True
                    )
                    valid_tasks.append(task)
                else:
                    print(f"[Scheduler] Skipping expired one-time job {task['schedule_id']}")
            except Exception as e:
                print(f"[Scheduler] Failed to reload one-time format {task['schedule_id']}: {e}")
                
    # Cleanup expired
    if len(valid_tasks) != len(tasks):
        save_scheduled(valid_tasks)

def stop():
    _scheduler.shutdown()
