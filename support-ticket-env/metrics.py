"""Metrics tracker for SupportTicketEnv.

Tracks performance across tasks: total steps, success/failure counts,
rewards, and provides aggregated statistics via get_metrics().

All state is in-memory. Deterministic — no randomness.
"""

from typing import List, Dict, Any


class MetricsTracker:
    """Tracks and aggregates environment performance metrics."""

    def __init__(self):
        self._total_steps: int = 0
        self._successful_tasks: int = 0
        self._failed_tasks: int = 0
        self._rewards: List[float] = []
        self._task_results: List[Dict[str, Any]] = []
        self._ticket_counts: Dict[str, int] = {
            "total_tickets": 0,
            "open_tickets": 0,
            "in_progress_tickets": 0,
            "resolved_tickets": 0,
            "pending_tickets": 0,
        }

    def update_ticket_counts(self, counts: Dict[str, int]) -> None:
        """Update the ticket queue counters.

        Args:
            counts: Dictionary from env.get_ticket_counts().
        """
        self._ticket_counts = dict(counts)

    def record_task(
        self,
        task_name: str,
        success: bool,
        steps: int,
        score: float,
        rewards: List[float],
    ) -> None:
        """Record the result of a single task run.

        Args:
            task_name: Name of the task (easy_task, medium_task, hard_task).
            success: Whether the task was completed successfully.
            steps: Number of steps taken.
            score: Final grader score (0.0 to 1.0).
            rewards: List of step rewards.
        """
        self._total_steps += steps
        if success:
            self._successful_tasks += 1
        else:
            self._failed_tasks += 1
        self._rewards.extend(rewards)
        self._task_results.append({
            "task": task_name,
            "success": success,
            "steps": steps,
            "score": score,
            "rewards": rewards,
            "total_reward": sum(rewards),
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Return aggregated metrics.

        Returns:
            Dictionary with success_rate, avg_steps, avg_reward,
            ticket_counts, and detailed per-task breakdown.
        """
        total_tasks = self._successful_tasks + self._failed_tasks

        if total_tasks == 0:
            return {
                "success_rate": 0.0,
                "avg_steps": 0.0,
                "avg_reward": 0.0,
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_steps": 0,
                "ticket_counts": self._ticket_counts,
                "tasks": [],
            }

        success_rate = self._successful_tasks / total_tasks
        avg_steps = self._total_steps / total_tasks
        avg_reward = sum(self._rewards) / len(self._rewards) if self._rewards else 0.0

        return {
            "success_rate": round(success_rate, 4),
            "avg_steps": round(avg_steps, 2),
            "avg_reward": round(avg_reward, 4),
            "total_tasks": total_tasks,
            "successful_tasks": self._successful_tasks,
            "failed_tasks": self._failed_tasks,
            "total_steps": self._total_steps,
            "ticket_counts": self._ticket_counts,
            "tasks": list(self._task_results),
        }

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self._total_steps = 0
        self._successful_tasks = 0
        self._failed_tasks = 0
        self._rewards = []
        self._task_results = []

    def print_summary(self) -> None:
        """Print a formatted summary of all metrics."""
        m = self.get_metrics()

        print(f"\n{'='*60}")
        print("METRICS SUMMARY")
        print(f"{'='*60}")
        print(f"  Total tasks:      {m['total_tasks']}")
        print(f"  Successful:       {m['successful_tasks']}")
        print(f"  Failed:           {m['failed_tasks']}")
        print(f"  Success rate:     {m['success_rate']:.1%}")
        print(f"  Total steps:      {m['total_steps']}")
        print(f"  Avg steps/task:   {m['avg_steps']:.1f}")
        print(f"  Avg reward/step:  {m['avg_reward']:.4f}")
        print(f"{'='*60}")

        if m["tasks"]:
            print(f"\n  {'Task':<15s} {'Result':<10s} {'Score':<8s} {'Steps':<8s} {'Reward':<8s}")
            print(f"  {'-'*15} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
            for t in m["tasks"]:
                status = "PASS" if t["success"] else "FAIL"
                print(f"  {t['task']:<15s} {status:<10s} {t['score']:<8.2f} {t['steps']:<8d} {t['total_reward']:<+8.2f}")
