"""SupportTicketEnv -- OpenEnv-compatible environment for customer support ticket resolution.

Implements the OpenEnv interface: reset(), step(action), state().
All logic is deterministic. No randomness, no external dependencies.

Features:
  - Ticket queue: reset() loads the first open ticket
  - Auto-load: after closing a ticket, the next open ticket is available
  - Resolved history: get_resolved_tickets() returns all resolved tickets
  - Persistent status: ticket status is saved back to tickets.json
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.models import (
    Action,
    ActionType,
    Observation,
    State,
    StepResponse,
    TicketData,
    TicketStatus,
)
from app.tasks import get_task, get_required_steps, get_max_steps
from app.graders import grade_task


# Path to the tickets data file
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TICKETS_FILE = DATA_DIR / "tickets.json"


class SupportTicketEnv:
    """OpenEnv-compatible environment for simulating customer support ticket resolution."""

    def __init__(self):
        self._tickets: List[TicketData] = []
        self._current_ticket: Optional[TicketData] = None
        self._task_name: str = "easy_task"
        self._completed_steps: List[str] = []
        self._status: str = "idle"  # idle | in_progress | done
        self._step_count: int = 0
        self._assigned_category: Optional[str] = None
        self._assigned_priority: Optional[str] = None
        self._resolution_text: Optional[str] = None
        self._ticket_status: str = TicketStatus.OPEN.value
        self._rewards: List[float] = []
        self._resolved_tickets: List[Dict[str, Any]] = []
        self._load_tickets()

    def _load_tickets(self) -> None:
        """Load ticket data from the JSON file."""
        if not TICKETS_FILE.exists():
            raise FileNotFoundError(f"Tickets file not found: {TICKETS_FILE}")
        with open(TICKETS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._tickets = [TicketData(**t) for t in raw]

    def _save_tickets(self) -> None:
        """Save current ticket states back to the JSON file."""
        data = [t.model_dump() for t in self._tickets]
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_ticket_by_id(self, ticket_id: int) -> TicketData:
        """Retrieve a ticket by its ID."""
        for ticket in self._tickets:
            if ticket.id == ticket_id:
                return ticket
        raise ValueError(f"Ticket with id {ticket_id} not found.")

    def _get_first_open_ticket(self) -> Optional[TicketData]:
        """Get the first ticket with status 'open'."""
        for ticket in self._tickets:
            if ticket.status == "open":
                return ticket
        return None

    def _mark_ticket_resolved(self, ticket_id: int) -> None:
        """Mark a ticket as resolved in the internal list and save to file."""
        for ticket in self._tickets:
            if ticket.id == ticket_id:
                ticket.status = "resolved"
                break
        self._save_tickets()

    def _mark_ticket_in_progress(self, ticket_id: int) -> None:
        """Mark a ticket as in_progress in the internal list and save to file."""
        for ticket in self._tickets:
            if ticket.id == ticket_id:
                ticket.status = "in_progress"
                break
        self._save_tickets()

    def _build_observation(self) -> Observation:
        """Build the current observation from internal state."""
        if self._current_ticket is None:
            raise RuntimeError("No ticket loaded. Call reset() first.")
        return Observation(
            ticket_id=self._current_ticket.id,
            ticket_text=self._current_ticket.text,
            category=self._assigned_category,
            priority=self._assigned_priority,
            status=self._ticket_status,
        )

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def get_resolved_tickets(self) -> List[Dict[str, Any]]:
        """Return the list of all resolved tickets with their details."""
        return list(self._resolved_tickets)

    def get_ticket_counts(self) -> Dict[str, int]:
        """Return counts of total, open, in_progress, and resolved tickets."""
        total = len(self._tickets)
        open_count = sum(1 for t in self._tickets if t.status == "open")
        in_progress = sum(1 for t in self._tickets if t.status == "in_progress")
        resolved = sum(1 for t in self._tickets if t.status == "resolved")
        return {
            "total_tickets": total,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress,
            "resolved_tickets": resolved,
            "pending_tickets": open_count + in_progress,
        }

    # ------------------------------------------------------------------
    # OpenEnv Interface
    # ------------------------------------------------------------------

    def reset(
        self,
        task: str = "easy_task",
        ticket_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Reset the environment for a new episode.

        If ticket_id is provided, loads that specific ticket.
        Otherwise, loads the first ticket with status == 'open'.
        If no open tickets exist, returns a message.

        Args:
            task: Task name -- one of easy_task, medium_task, hard_task.
            ticket_id: Optional specific ticket ID. Defaults to first open ticket.

        Returns:
            Dictionary with 'observation' and 'info'.
        """
        task_def = get_task(task)
        self._task_name = task

        # Determine which ticket to load
        if ticket_id is not None:
            self._current_ticket = self._get_ticket_by_id(ticket_id)
        else:
            # Feature 1: Load the first open ticket from the queue
            open_ticket = self._get_first_open_ticket()
            if open_ticket is None:
                # All tickets resolved
                self._status = "done"
                self._current_ticket = None
                return {
                    "observation": None,
                    "info": {
                        "task": self._task_name,
                        "message": "All tickets resolved",
                        "ticket_counts": self.get_ticket_counts(),
                    },
                }
            self._current_ticket = open_ticket

        # Mark the ticket as in_progress
        self._mark_ticket_in_progress(self._current_ticket.id)

        # Reset all mutable state
        self._completed_steps = []
        self._status = "in_progress"
        self._step_count = 0
        self._assigned_category = None
        self._assigned_priority = None
        self._resolution_text = None
        self._ticket_status = TicketStatus.OPEN.value
        self._rewards = []

        observation = self._build_observation()
        info = {
            "task": self._task_name,
            "ticket_id": self._current_ticket.id,
            "required_steps": get_required_steps(self._task_name),
            "max_steps": get_max_steps(self._task_name),
            "ticket_counts": self.get_ticket_counts(),
        }
        return {"observation": observation.model_dump(), "info": info}

    def step(self, action: Action) -> Dict[str, Any]:
        """Execute one step in the environment.

        Args:
            action: The action to perform.

        Returns:
            Dictionary with 'observation', 'reward', 'done', and 'info'.
        """
        if self._status != "in_progress":
            raise RuntimeError(
                "Environment is not in progress. Call reset() before step()."
            )
        if self._current_ticket is None:
            raise RuntimeError("No ticket loaded. Call reset() first.")

        self._step_count += 1
        reward = 0.0
        done = False
        info: Dict[str, Any] = {"step": self._step_count}

        action_type = action.action_type.value
        value = action.value.strip()

        # --- Check for repeated action ---
        if action_type in self._completed_steps:
            reward = -0.1
            info["reason"] = "repeated_action"
            info["error"] = f"Action '{action_type}' already completed."
            self._rewards.append(reward)
            observation = self._build_observation()
            return {
                "observation": observation.model_dump(),
                "reward": reward,
                "done": done,
                "info": info,
            }

        # --- Process action ---
        if action_type == ActionType.CATEGORIZE_TICKET.value:
            self._assigned_category = value
            self._ticket_status = TicketStatus.CATEGORIZED.value
            if value.lower() == self._current_ticket.expected_category.lower():
                reward = 0.4
                info["reason"] = "correct_category"
            else:
                reward = -0.2
                info["reason"] = "wrong_category"
                info["error"] = f"Wrong category: expected '{self._current_ticket.expected_category}', got '{value}'."

        elif action_type == ActionType.ASSIGN_PRIORITY.value:
            self._assigned_priority = value
            self._ticket_status = TicketStatus.PRIORITIZED.value
            if value.lower() == self._current_ticket.expected_priority.lower():
                reward = 0.3
                info["reason"] = "correct_priority"
            else:
                reward = -0.2
                info["reason"] = "wrong_priority"
                info["error"] = f"Wrong priority: expected '{self._current_ticket.expected_priority}', got '{value}'."

        elif action_type == ActionType.RESOLVE_TICKET.value:
            self._resolution_text = value
            self._ticket_status = TicketStatus.RESOLVED.value
            # Resolution is always accepted if provided
            if len(value) > 0:
                reward = 0.3
                info["reason"] = "valid_resolution"
            else:
                reward = -0.2
                info["reason"] = "empty_resolution"
                info["error"] = "Resolution text cannot be empty."

        elif action_type == ActionType.CLOSE_TICKET.value:
            # Close the ticket and mark as resolved in persistent storage
            self._ticket_status = TicketStatus.CLOSED.value
            reward = 0.0
            info["reason"] = "ticket_closed"

            # Feature 2 & 3: Mark ticket as resolved and record to history
            self._mark_ticket_resolved(self._current_ticket.id)
            self._resolved_tickets.append({
                "ticket_id": self._current_ticket.id,
                "text": self._current_ticket.text,
                "category": self._assigned_category,
                "priority": self._assigned_priority,
                "resolution": self._resolution_text,
                "status": "resolved",
            })

            # Feature 3: Check if there's a next open ticket
            next_ticket = self._get_first_open_ticket()
            if next_ticket is not None:
                info["next_ticket_id"] = next_ticket.id
                info["next_ticket_preview"] = next_ticket.text[:80]
            else:
                info["message"] = "All tickets resolved"

        else:
            reward = -0.2
            info["reason"] = "unknown_action"
            info["error"] = f"Unknown action type: '{action_type}'."

        self._completed_steps.append(action_type)
        self._rewards.append(reward)

        # --- Check if episode is done ---
        required = get_required_steps(self._task_name)
        max_steps = get_max_steps(self._task_name)

        all_required_done = all(step in self._completed_steps for step in required)

        if all_required_done or self._step_count >= max_steps:
            done = True
            self._status = "done"
            # Compute final score
            score = grade_task(
                task_name=self._task_name,
                expected_category=self._current_ticket.expected_category,
                expected_priority=self._current_ticket.expected_priority,
                assigned_category=self._assigned_category,
                assigned_priority=self._assigned_priority,
                completed_steps=self._completed_steps,
                ticket_status=self._ticket_status,
            )
            info["score"] = score
            info["total_rewards"] = self._rewards
            info["ticket_counts"] = self.get_ticket_counts()
            if all_required_done:
                info["reason"] = "task_completed"

        observation = self._build_observation()
        return {
            "observation": observation.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }

    def state(self) -> Dict[str, Any]:
        """Return the full current state of the environment.

        Returns:
            Dictionary representation of the State model, plus ticket counts.
        """
        current_obs = None
        if self._current_ticket is not None:
            current_obs = self._build_observation().model_dump()

        state = State(
            current_ticket=current_obs,
            completed_steps=list(self._completed_steps),
            status=self._status,
        )
        result = state.model_dump()
        result["ticket_counts"] = self.get_ticket_counts()
        result["resolved_tickets"] = self.get_resolved_tickets()
        return result
