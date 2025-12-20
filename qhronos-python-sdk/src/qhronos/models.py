"""
Qhronos SDK Models
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# Enums
class ActionType(str, Enum):
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    APICALL = "apicall"
    SCRIPT = "script"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"


class EventStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    JOB = "job"
    WORKFLOW = "workflow"
    STEP = "step"
    API_CALL = "api_call"
    SCRIPT = "script"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    INTEGRATION = "integration"


class StepType(str, Enum):
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"
    LOOP = "loop"
    SUB_WORKFLOW = "sub_workflow"
    SET_VARIABLE = "set_variable"


class IntegrationType(str, Enum):
    LLM = "llm"
    NOTIFICATION = "notification"
    DATABASE = "database"
    SPREADSHEET = "spreadsheet"


class IntegrationProvider(str, Enum):
    # LLM
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    # Notification
    SES = "ses"
    TWILIO = "twilio"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    # Database
    MYSQL = "mysql"
    POSTGRES = "postgres"
    # Spreadsheet
    GOOGLE_SHEETS = "google_sheets"


# Base Models
class Action(BaseModel):
    type: ActionType
    params: dict[str, Any] = Field(default_factory=dict)


class ScheduleConfig(BaseModel):
    frequency: str
    interval: int | None = None
    by_day: list[str] | None = None
    by_month: list[int] | None = None
    by_month_day: list[int] | None = None
    count: int | None = None
    until: str | None = None


# Event Models
class Event(BaseModel):
    id: str
    name: str
    description: str | None = None
    start_time: datetime
    webhook: str | None = None
    action: Action | None = None
    metadata: dict[str, Any] | None = None
    schedule: ScheduleConfig | None = None
    tags: list[str] | None = None
    status: EventStatus
    hmac_secret: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class EventCreateParams(BaseModel):
    name: str
    description: str | None = None
    start_time: datetime | str
    webhook: str | None = None
    action: Action | None = None
    metadata: dict[str, Any] | None = None
    schedule: ScheduleConfig | None = None
    tags: list[str] | None = None
    hmac_secret: str | None = None


class EventUpdateParams(BaseModel):
    name: str | None = None
    description: str | None = None
    start_time: datetime | str | None = None
    webhook: str | None = None
    action: Action | None = None
    metadata: dict[str, Any] | None = None
    schedule: ScheduleConfig | None = None
    tags: list[str] | None = None
    status: EventStatus | None = None
    hmac_secret: str | None = None


# Job Models
class Job(BaseModel):
    id: str
    schedule_id: str | None = None
    type: JobType
    status: JobStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    parent_job_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class JobListParams(BaseModel):
    page: int | None = None
    limit: int | None = None
    type: JobType | None = None
    status: JobStatus | None = None
    event_id: str | None = None
    workflow_id: str | None = None
    parent_job_id: str | None = None


# Workflow Models
class WorkflowStep(BaseModel):
    id: str
    type: StepType
    name: str | None = None
    action: Action | None = None
    condition: str | None = None
    true_branch: str | None = None
    false_branch: str | None = None
    delay_seconds: int | None = None
    items: str | None = None
    max_iterations: int | None = None
    variable: str | None = None
    value: Any | None = None
    workflow_id: str | None = None
    steps: list["WorkflowStep"] | None = None
    next: str | None = None
    on_error: str | None = None
    timeout_ms: int | None = None
    retry: dict[str, Any] | None = None


class WorkflowDefinition(BaseModel):
    steps: list[WorkflowStep]
    entry_point: str | None = None


class Workflow(BaseModel):
    id: str
    name: str
    description: str | None = None
    definition: WorkflowDefinition
    version: int
    status: str
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class WorkflowCreateParams(BaseModel):
    name: str
    description: str | None = None
    definition: WorkflowDefinition
    tags: list[str] | None = None


class WorkflowUpdateParams(BaseModel):
    name: str | None = None
    description: str | None = None
    definition: WorkflowDefinition | None = None
    status: str | None = None
    tags: list[str] | None = None


class WorkflowExecuteParams(BaseModel):
    params: dict[str, Any] | None = None


# Script Models
class Script(BaseModel):
    id: str
    name: str
    description: str | None = None
    code: str
    version: int
    language: str = "javascript"
    status: str
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ScriptCreateParams(BaseModel):
    name: str
    description: str | None = None
    code: str
    tags: list[str] | None = None


class ScriptUpdateParams(BaseModel):
    name: str | None = None
    description: str | None = None
    code: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class ScriptExecuteParams(BaseModel):
    params: dict[str, Any] | None = None


# Integration Models
class Integration(BaseModel):
    id: str
    name: str
    type: IntegrationType
    provider: IntegrationProvider
    config: dict[str, Any]
    status: str
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class IntegrationCreateParams(BaseModel):
    name: str
    type: IntegrationType
    provider: IntegrationProvider
    config: dict[str, Any]
    tags: list[str] | None = None


class IntegrationUpdateParams(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    status: str | None = None
    tags: list[str] | None = None


# Pagination
class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    has_more: bool


class PaginatedResponse(BaseModel):
    data: list[Any]
    pagination: PaginationInfo

