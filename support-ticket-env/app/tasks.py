"""Task definitions for the SupportTicketEnv environment."""

from typing import Dict, Any, List


# Each task defines what steps are required and what constitutes success.
TASKS: Dict[str, Dict[str, Any]] = {
    "easy_task": {
        "name": "easy_task",
        "description": "Correctly categorize a customer support ticket.",
        "required_steps": ["categorize_ticket"],
        "default_ticket_id": 1,
        "max_steps": 3,
    },
    "medium_task": {
        "name": "medium_task",
        "description": "Assign the correct priority to a customer support ticket.",
        "required_steps": ["assign_priority"],
        "default_ticket_id": 3,
        "max_steps": 3,
    },
    "hard_task": {
        "name": "hard_task",
        "description": "Complete the full ticket resolution workflow: categorize, prioritize, resolve, and close.",
        "required_steps": [
            "categorize_ticket",
            "assign_priority",
            "resolve_ticket",
            "close_ticket",
        ],
        "default_ticket_id": 8,
        "max_steps": 10,
    },
}


def get_task(task_name: str) -> Dict[str, Any]:
    """Retrieve a task definition by name.

    Args:
        task_name: Name of the task (easy_task, medium_task, hard_task).

    Returns:
        Task definition dictionary.

    Raises:
        ValueError: If the task name is not found.
    """
    if task_name not in TASKS:
        raise ValueError(
            f"Unknown task: '{task_name}'. Available tasks: {list(TASKS.keys())}"
        )
    return TASKS[task_name]


def get_required_steps(task_name: str) -> List[str]:
    """Get the list of required action types for a task."""
    return get_task(task_name)["required_steps"]


def get_max_steps(task_name: str) -> int:
    """Get the maximum number of steps allowed for a task."""
    return get_task(task_name)["max_steps"]
