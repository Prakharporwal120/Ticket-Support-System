"""Pydantic models for the SupportTicketEnv environment."""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# --- Enums ---

class ActionType(str, Enum):
    CATEGORIZE_TICKET = "categorize_ticket"
    ASSIGN_PRIORITY = "assign_priority"
    RESOLVE_TICKET = "resolve_ticket"
    CLOSE_TICKET = "close_ticket"


class TicketStatus(str, Enum):
    OPEN = "open"
    CATEGORIZED = "categorized"
    PRIORITIZED = "prioritized"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Category(str, Enum):
    BILLING = "billing"
    ACCOUNT = "account"
    TECHNICAL = "technical"
    DELIVERY = "delivery"
    REFUND = "refund"
    SECURITY = "security"
    SUBSCRIPTION = "subscription"
    ORDER = "order"
    PAYMENT = "payment"
    LOGIN = "login"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --- Action Model ---

class Action(BaseModel):
    """Action submitted by the agent at each step."""
    action_type: ActionType = Field(
        ..., description="Type of action to perform on the ticket."
    )
    value: str = Field(
        ..., description="Value associated with the action (e.g., category name, priority level, resolution text)."
    )


# --- Observation Model ---

class Observation(BaseModel):
    """Observation returned after each step."""
    ticket_id: int = Field(..., description="Unique identifier for the ticket.")
    ticket_text: str = Field(..., description="The original ticket text from the customer.")
    category: Optional[str] = Field(None, description="Assigned category (null if not yet categorized).")
    priority: Optional[str] = Field(None, description="Assigned priority (null if not yet prioritized).")
    status: str = Field(..., description="Current status of the ticket.")


# --- State Model ---

class State(BaseModel):
    """Full state of the environment."""
    current_ticket: Optional[Observation] = Field(
        None, description="The ticket currently being processed."
    )
    completed_steps: List[str] = Field(
        default_factory=list, description="List of completed action types in order."
    )
    status: str = Field(
        "idle", description="Overall environment status: idle, in_progress, or done."
    )


# --- Step Response ---

class StepResponse(BaseModel):
    """Response returned by the step endpoint."""
    observation: Observation
    reward: float = Field(..., description="Reward for the current step.")
    done: bool = Field(..., description="Whether the episode is complete.")
    info: dict = Field(default_factory=dict, description="Additional information.")


# --- Reset Request / Response ---

class ResetRequest(BaseModel):
    """Optional request body for reset."""
    task: str = Field("easy_task", description="Task to load: easy_task, medium_task, or hard_task.")
    ticket_id: Optional[int] = Field(None, description="Specific ticket ID to load (optional).")


class ResetResponse(BaseModel):
    """Response returned by the reset endpoint."""
    observation: Observation
    info: dict = Field(default_factory=dict, description="Additional information about the reset.")


# --- Ticket Data Model ---

class TicketData(BaseModel):
    """Raw ticket data loaded from tickets.json."""
    id: int
    text: str
    expected_category: str
    expected_priority: str
    status: str = "open"
