from pydantic import BaseModel
from typing import Any

class RunRequest(BaseModel):
    prompt: str

class Step(BaseModel):
    tool: str
    args: dict[str, Any]

class Log(BaseModel):
    step: str
    status: str  # must be "success" or "failed"

class RunResponse(BaseModel):
    steps: list[Step]
    logs: list[Log]
