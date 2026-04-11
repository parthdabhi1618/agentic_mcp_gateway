from pydantic import BaseModel
from typing import Any, Optional

class PlanRequest(BaseModel):
    prompt: str
    context_refs: list[str] = []

class StepWithPermission(BaseModel):
    step_id: str
    tool: str
    action: str
    args: dict[str, Any]
    permission_required: bool = True
    permission_status: str

class PlanResponse(BaseModel):
    plan_id: str
    steps: list[StepWithPermission]

class ExecuteRequest(BaseModel):
    plan_id: str
    steps: list[dict[str, Any]]

class ExecuteResponse(BaseModel):
    job_id: str

class ScheduledTask(BaseModel):
    name: str
    steps: list[dict[str, Any]]
    schedule_type: str
    schedule_value: str
    
class RunRequest(BaseModel):
    prompt: str
