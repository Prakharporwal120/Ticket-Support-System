"""Deterministic graders for each task in SupportTicketEnv.

Each grader returns a score between 0.0 and 1.0.
- 1.0  = fully correct
- 0.5  = partially correct
- 0.0  = incorrect

Graders are pure functions: same input always produces the same output.
"""

from typing import Dict, Any, List, Optional


def grade_easy_task(
    expected_category: str,
    assigned_category: Optional[str],
    completed_steps: List[str],
) -> float:
    """Grade the easy task: correct ticket categorization.

    Args:
        expected_category: The ground-truth category from ticket data.
        assigned_category: The category assigned by the agent.
        completed_steps: List of action types the agent has completed.

    Returns:
        Score between 0.0 and 1.0.
    """
    if "categorize_ticket" not in completed_steps:
        return 0.0

    if assigned_category is None:
        return 0.0

    if assigned_category.lower().strip() == expected_category.lower().strip():
        return 1.0

    # Partial credit: the agent tried but got the wrong category
    return 0.0


def grade_medium_task(
    expected_priority: str,
    assigned_priority: Optional[str],
    completed_steps: List[str],
) -> float:
    """Grade the medium task: correct priority assignment.

    Args:
        expected_priority: The ground-truth priority from ticket data.
        assigned_priority: The priority assigned by the agent.
        completed_steps: List of action types the agent has completed.

    Returns:
        Score between 0.0 and 1.0.
    """
    if "assign_priority" not in completed_steps:
        return 0.0

    if assigned_priority is None:
        return 0.0

    if assigned_priority.lower().strip() == expected_priority.lower().strip():
        return 1.0

    # Partial credit for valid priority but wrong level
    valid_priorities = {"low", "medium", "high"}
    if assigned_priority.lower().strip() in valid_priorities:
        return 0.5

    return 0.0


def grade_hard_task(
    expected_category: str,
    expected_priority: str,
    assigned_category: Optional[str],
    assigned_priority: Optional[str],
    completed_steps: List[str],
    ticket_status: str,
) -> float:
    """Grade the hard task: full workflow completion.

    The full workflow requires: categorize → prioritize → resolve → close.
    Score is computed as the fraction of correctly completed steps.

    Args:
        expected_category: Ground-truth category.
        expected_priority: Ground-truth priority.
        assigned_category: Category assigned by the agent.
        assigned_priority: Priority assigned by the agent.
        completed_steps: List of completed action types in order.
        ticket_status: Final status of the ticket.

    Returns:
        Score between 0.0 and 1.0.
    """
    required = ["categorize_ticket", "assign_priority", "resolve_ticket", "close_ticket"]
    total_parts = 4
    earned = 0.0

    # Check categorization (0.25 of total)
    if "categorize_ticket" in completed_steps and assigned_category is not None:
        if assigned_category.lower().strip() == expected_category.lower().strip():
            earned += 1.0
        else:
            earned += 0.5  # Partial credit for attempting

    # Check priority (0.25 of total)
    if "assign_priority" in completed_steps and assigned_priority is not None:
        if assigned_priority.lower().strip() == expected_priority.lower().strip():
            earned += 1.0
        else:
            earned += 0.5

    # Check resolution (0.25 of total)
    if "resolve_ticket" in completed_steps:
        earned += 1.0

    # Check close (0.25 of total)
    if "close_ticket" in completed_steps and ticket_status == "closed":
        earned += 1.0

    return round(earned / total_parts, 2)


def grade_task(
    task_name: str,
    expected_category: str,
    expected_priority: str,
    assigned_category: Optional[str],
    assigned_priority: Optional[str],
    completed_steps: List[str],
    ticket_status: str,
) -> float:
    """Unified grader dispatcher.

    Args:
        task_name: Name of the task being graded.
        expected_category: Ground-truth category.
        expected_priority: Ground-truth priority.
        assigned_category: Agent-assigned category.
        assigned_priority: Agent-assigned priority.
        completed_steps: List of completed action types.
        ticket_status: Current ticket status.

    Returns:
        Score between 0.0 and 1.0.

    Raises:
        ValueError: If task_name is unknown.
    """
    if task_name == "easy_task":
        return grade_easy_task(expected_category, assigned_category, completed_steps)
    elif task_name == "medium_task":
        return grade_medium_task(expected_priority, assigned_priority, completed_steps)
    elif task_name == "hard_task":
        return grade_hard_task(
            expected_category,
            expected_priority,
            assigned_category,
            assigned_priority,
            completed_steps,
            ticket_status,
        )
    else:
        raise ValueError(f"Unknown task for grading: '{task_name}'")
