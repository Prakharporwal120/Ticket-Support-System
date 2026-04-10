"""Evaluation script for SupportTicketEnv.

Runs all tasks (easy_task, medium_task, hard_task) against the environment
and prints a comprehensive summary with metrics.

Usage:
    1. Start the server:  uvicorn app.server:app --host 0.0.0.0 --port 8000
    2. Run evaluation:    python evaluate.py
"""

import os
import sys
import httpx
import json
from datetime import datetime
from metrics import MetricsTracker

# --- Configuration ---
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Deterministic correct actions for each task (using task default tickets)
TASK_ACTIONS = {
    "easy_task": {
        "ticket_id": 1,
        "actions": [
            {"action_type": "categorize_ticket", "value": "billing"},
        ],
    },
    "medium_task": {
        "ticket_id": 3,
        "actions": [
            {"action_type": "assign_priority", "value": "high"},
        ],
    },
    "hard_task": {
        "ticket_id": 8,
        "actions": [
            {"action_type": "categorize_ticket", "value": "technical"},
            {"action_type": "assign_priority", "value": "high"},
            {"action_type": "resolve_ticket", "value": "Production database issue has been resolved by the infrastructure team."},
            {"action_type": "close_ticket", "value": "Ticket resolved and verified by customer."},
        ],
    },
}


def evaluate_task(client: httpx.Client, task_name: str, task_config: dict) -> dict:
    """Evaluate a single task.

    Returns:
        Dict with success, score, steps, rewards.
    """
    print(f"\n  {'-'*50}")
    print(f"  Task: {task_name}")
    print(f"  {'-'*50}")

    # Reset
    reset_body = {"task": task_name}
    if task_config.get("ticket_id"):
        reset_body["ticket_id"] = task_config["ticket_id"]

    try:
        resp = client.post("/reset", json=reset_body)
        resp.raise_for_status()
        reset_data = resp.json()
    except Exception as e:
        print(f"    [XX] Reset failed: {e}")
        return {"success": False, "score": 0.0, "steps": 0, "rewards": []}

    obs = reset_data["observation"]
    print(f"    Ticket #{obs['ticket_id']}: \"{obs['ticket_text'][:60]}...\"")

    # Execute actions
    rewards = []
    step_count = 0
    done = False
    score = 0.0

    for action in task_config["actions"]:
        if done:
            break
        step_count += 1

        try:
            resp = client.post("/step", json=action)
            resp.raise_for_status()
            step_data = resp.json()

            reward = step_data["reward"]
            done = step_data["done"]
            info = step_data.get("info", {})
            reason = info.get("reason", "")
            error = info.get("error", None)
            rewards.append(reward)

            icon = "[OK]" if reward > 0 else ("[--]" if reward == 0 else "[XX]")
            err_str = f"  ({error})" if error else ""
            reason_str = f"  [{reason}]" if reason else ""

            print(f"    Step {step_count}: {action['action_type']:20s} -> reward={reward:+.2f} {icon}{reason_str}{err_str}")

            if done:
                score = info.get("score", 0.0)
        except Exception as e:
            print(f"    Step {step_count}: ERROR -> {e}")
            rewards.append(0.0)

    success = done and score >= 0.5
    result_str = "PASS" if success else "FAIL"
    print(f"    Result: {result_str}  |  score={score:.2f}  |  total_reward={sum(rewards):.2f}")

    return {"success": success, "score": score, "steps": step_count, "rewards": rewards}


def main():
    """Run evaluation across all tasks and print summary."""
    start_time = datetime.now()

    print("+" + "=" * 58 + "+")
    print("|" + " SupportTicketEnv -- Evaluation Suite ".center(58) + "|")
    print("|" + f" Server: {API_BASE_URL} ".center(58) + "|")
    print("|" + f" Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ".center(58) + "|")
    print("+" + "=" * 58 + "+")

    # Health check
    client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
    try:
        health = client.get("/health")
        health.raise_for_status()
        print(f"\n  Server health: [OK]")
    except Exception as e:
        print(f"\n  Server health: [FAIL] ({e})")
        print("  Make sure the server is running: uvicorn app.server:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    # Run all tasks
    tracker = MetricsTracker()

    for task_name, task_config in TASK_ACTIONS.items():
        result = evaluate_task(client, task_name, task_config)
        tracker.record_task(
            task_name=task_name,
            success=result["success"],
            steps=result["steps"],
            score=result["score"],
            rewards=result["rewards"],
        )

    client.close()

    # Print metrics
    tracker.print_summary()

    # Timing
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n  Evaluation completed in {elapsed:.1f}s")

    # Final verdict
    metrics = tracker.get_metrics()
    if metrics["success_rate"] == 1.0:
        print("\n  >> ALL TASKS PASSED -- Environment is hackathon-ready!")
    else:
        print(f"\n  >> {metrics['failed_tasks']} task(s) failed -- review required.")

    sys.exit(0 if metrics["success_rate"] == 1.0 else 1)


if __name__ == "__main__":
    main()
